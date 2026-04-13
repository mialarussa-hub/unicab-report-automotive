"""Scraping test endpoint — proxies requests to scrapers container and saves results."""

import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.database import get_db
from app.models.source import Source
from app.models.user import User
from app.models.scraping import ScrapingSession, ScrapingResult

router = APIRouter()

SCRAPERS_URL = "http://scrapers:8001"


class ScrapeTestRequest(BaseModel):
    brand: str
    model: str = ""


async def get_user_from_cookie(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via cookie (frontend pages use httponly cookies)."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


@router.post("/run")
async def run_scraping_test(
    request: ScrapeTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_from_cookie),
):
    """Proxy scraping test request to scrapers container, save results to DB."""
    # Fetch active sources from DB
    result = await db.execute(select(Source).where(Source.is_active == True))
    sources = result.scalars().all()

    sources_list = [
        {"name": s.name, "url": s.url, "source_type": s.source_type}
        for s in sources
    ]

    # Create session BEFORE scraping
    session = ScrapingSession(
        brand=request.brand,
        model=request.model or None,
        status="running",
        total_sources=len(sources_list),
        created_by=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    try:
        # No timeout — scraping can take several minutes with multi-page forum crawling
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{SCRAPERS_URL}/scrape/test",
                json={
                    "brand": request.brand,
                    "model": request.model,
                    "sources": sources_list,
                },
            )
            data = resp.json()

        # Save results to DB
        total_results = 0
        total_comments = 0

        for source_data in data.get("sources", []):
            for item in source_data.get("items", []):
                ai_comments = item.get("ai_comments")
                comment_count = item.get("ai_comment_count", 0)
                if not comment_count and ai_comments:
                    comment_count = len(ai_comments)

                scraping_result = ScrapingResult(
                    session_id=session.id,
                    source_name=source_data.get("source", ""),
                    source_type=source_data.get("source_type", ""),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    summary=item.get("summary"),
                    content=item.get("content", "")[:10000],  # cap at 10K chars
                    ai_comments=ai_comments,
                    comment_count=comment_count,
                    view_count=item.get("view_count"),
                    like_count=item.get("like_count"),
                    channel=item.get("channel"),
                    official_info=item.get("ai_official_info"),  # L1: structured brand info
                )
                db.add(scraping_result)
                total_results += 1
                total_comments += comment_count

        # Update session
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.total_results = total_results
        session.total_comments = total_comments
        session.total_credits = data.get("total_credits", 0)
        session.duration_ms = data.get("total_duration_ms", 0)

        await db.commit()

        # Include session_id in response
        data["session_id"] = str(session.id)
        return data

    except Exception as e:
        session.status = "failed"
        session.completed_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_from_cookie),
):
    """List all scraping sessions for the current user."""
    result = await db.execute(
        select(ScrapingSession)
        .where(ScrapingSession.created_by == current_user.id)
        .order_by(desc(ScrapingSession.started_at))
        .limit(50)
    )
    sessions = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "brand": s.brand,
            "model": s.model,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "status": s.status,
            "total_sources": s.total_sources,
            "total_results": s.total_results,
            "total_comments": s.total_comments,
            "total_credits": s.total_credits,
            "duration_ms": s.duration_ms,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_from_cookie),
):
    """Get session details with all results, formatted like scraper response."""
    result = await db.execute(
        select(ScrapingSession)
        .options(selectinload(ScrapingSession.results))
        .where(
            ScrapingSession.id == uuid.UUID(session_id),
            ScrapingSession.created_by == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Group results by source
    sources_map: dict[str, dict] = {}
    for r in session.results:
        key = r.source_name
        if key not in sources_map:
            sources_map[key] = {
                "source": r.source_name,
                "source_type": r.source_type,
                "status": "ok",
                "result_count": 0,
                "credits_used": 0,
                "items": [],
                "duration_ms": 0,
            }
        sources_map[key]["result_count"] += 1

        item = {
            "url": r.url,
            "title": r.title,
            "summary": r.summary,
            "content": r.content,
            "ai_comments": r.ai_comments,
            "ai_comment_count": r.comment_count,
            "content_length": len(r.content) if r.content else 0,
            "scraped": True,
        }
        if r.view_count is not None:
            item["view_count"] = r.view_count
            item["like_count"] = r.like_count
            item["channel"] = r.channel
        if r.official_info is not None:
            item["ai_official_info"] = r.official_info

        sources_map[key]["items"].append(item)

    return {
        "session_id": str(session.id),
        "brand": session.brand,
        "model": session.model,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "status": session.status,
        "sources": list(sources_map.values()),
        "total_credits": session.total_credits,
        "total_duration_ms": session.duration_ms,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_from_cookie),
):
    """Delete a scraping session and all its results."""
    result = await db.execute(
        select(ScrapingSession).where(
            ScrapingSession.id == uuid.UUID(session_id),
            ScrapingSession.created_by == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"ok": True}
