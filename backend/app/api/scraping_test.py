"""Scraping test endpoint — async scraping with per-source progress tracking."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.database import get_db, async_session
from app.models.source import Source
from app.models.user import User
from app.models.scraping import ScrapingSession, ScrapingResult

router = APIRouter()
logger = logging.getLogger(__name__)

SCRAPERS_URL = "http://scrapers:8001"


class ScrapeTestRequest(BaseModel):
    brand: str
    model: str = ""
    phase: str = "all"  # all, L1, L2, L3


# Phase → source_type mapping (mirror of frontend LEVELS)
PHASE_SOURCE_TYPES = {
    "L1": {"official"},
    "L2": {"news", "perplexity"},
    "L3": {"forum", "youtube", "social"},
}


class SourceCompleteRequest(BaseModel):
    session_id: str
    source_result: dict


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
    """Launch scraping asynchronously — returns immediately with session_id.

    The frontend polls GET /sessions/{id} to track progress in real time.
    """
    # Validate phase
    phase = request.phase if request.phase in ("all", "L1", "L2", "L3") else "all"

    # Fetch active sources from DB, filtered by phase
    query = select(Source).where(Source.is_active == True)
    if phase != "all":
        allowed_types = PHASE_SOURCE_TYPES[phase]
        query = query.where(Source.source_type.in_(allowed_types))
    result = await db.execute(query)
    sources = result.scalars().all()

    sources_list = [
        {"name": s.name, "url": s.url, "source_type": s.source_type}
        for s in sources
    ]

    if not sources_list:
        raise HTTPException(
            status_code=400,
            detail=f"Nessuna fonte attiva per la fase '{phase}'",
        )

    # Create session
    session = ScrapingSession(
        brand=request.brand,
        model=request.model or None,
        status="running",
        total_sources=len(sources_list),
        phase_filter=phase,
        created_by=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Launch scraping in background — returns immediately
    asyncio.create_task(
        _run_scraping_background(str(session.id), request.brand, request.model, sources_list)
    )

    return {
        "session_id": str(session.id),
        "status": "running",
        "total_sources": len(sources_list),
        "sources_names": [s["name"] for s in sources_list],
        "phase_filter": phase,
    }


async def _run_scraping_background(
    session_id: str, brand: str, model: str, sources_list: list[dict]
):
    """Background task: call scrapers service, finalize session on completion."""
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{SCRAPERS_URL}/scrape/test",
                json={
                    "brand": brand,
                    "model": model,
                    "sources": sources_list,
                    "session_id": session_id,
                    "callback_url": "http://api:8000/api/scraping-test/source-complete",
                },
            )
            data = resp.json()

        # Finalize session — update totals from any sources not already saved via callback
        async with async_session() as db:
            result = await db.execute(
                select(ScrapingSession).where(ScrapingSession.id == uuid.UUID(session_id))
            )
            session = result.scalar_one_or_none()
            if not session:
                return

            # Check which sources were already saved via callback
            existing = await db.execute(
                select(ScrapingResult.source_name)
                .where(ScrapingResult.session_id == uuid.UUID(session_id))
            )
            saved_sources = {r[0] for r in existing.fetchall()}

            total_results = 0
            total_comments = 0

            for source_data in data.get("sources", []):
                source_name = source_data.get("source", "")

                # Skip if already saved via callback
                if source_name in saved_sources:
                    # Count existing results
                    for item in source_data.get("items", []):
                        total_results += 1
                        total_comments += item.get("ai_comment_count", 0) or (
                            len(item.get("ai_comments") or [])
                        )
                    continue

                # Save results not yet saved
                for item in source_data.get("items", []):
                    ai_comments = item.get("ai_comments")
                    comment_count = item.get("ai_comment_count", 0)
                    if not comment_count and ai_comments:
                        comment_count = len(ai_comments)

                    scraping_result = ScrapingResult(
                        session_id=uuid.UUID(session_id),
                        source_name=source_name,
                        source_type=source_data.get("source_type", ""),
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        summary=item.get("summary"),
                        content=item.get("content", "")[:10000],
                        ai_comments=ai_comments,
                        comment_count=comment_count,
                        view_count=item.get("view_count"),
                        like_count=item.get("like_count"),
                        channel=item.get("channel"),
                        official_info=item.get("ai_official_info"),
                    )
                    db.add(scraping_result)
                    total_results += 1
                    total_comments += comment_count

            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            session.total_results = total_results
            session.total_comments = total_comments
            session.total_credits = data.get("total_credits", 0)
            session.duration_ms = data.get("total_duration_ms", 0)
            await db.commit()
            logger.info(f"Session {session_id} completed: {total_results} results")

    except Exception as e:
        logger.error(f"Background scraping error for session {session_id}: {e}")
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(ScrapingSession).where(ScrapingSession.id == uuid.UUID(session_id))
                )
                session = result.scalar_one_or_none()
                if session:
                    session.status = "failed"
                    session.completed_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception:
            pass


@router.post("/source-complete")
async def source_complete(
    request: SourceCompleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Callback from scrapers service — saves one source's results incrementally.

    Called by the scrapers container each time a source finishes scraping.
    This allows the frontend to see results as they arrive via polling.
    """
    session_id = request.session_id
    source_data = request.source_result

    # Verify session exists
    result = await db.execute(
        select(ScrapingSession).where(ScrapingSession.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    source_name = source_data.get("source", "")
    source_type = source_data.get("source_type", "")
    items = source_data.get("items", [])

    saved_count = 0
    saved_comments = 0

    for item in items:
        ai_comments = item.get("ai_comments")
        comment_count = item.get("ai_comment_count", 0)
        if not comment_count and ai_comments:
            comment_count = len(ai_comments)

        scraping_result = ScrapingResult(
            session_id=uuid.UUID(session_id),
            source_name=source_name,
            source_type=source_type,
            url=item.get("url", ""),
            title=item.get("title", ""),
            summary=item.get("summary"),
            content=item.get("content", "")[:10000],
            ai_comments=ai_comments,
            comment_count=comment_count,
            view_count=item.get("view_count"),
            like_count=item.get("like_count"),
            channel=item.get("channel"),
            official_info=item.get("ai_official_info"),
        )
        db.add(scraping_result)
        saved_count += 1
        saved_comments += comment_count

    # Update session running totals
    session.total_results = (session.total_results or 0) + saved_count
    session.total_comments = (session.total_comments or 0) + saved_comments

    await db.commit()
    logger.info(f"[{source_name}] Saved {saved_count} results for session {session_id}")

    return {"ok": True, "saved": saved_count}


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
            "phase_filter": s.phase_filter,
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
        "phase_filter": session.phase_filter,
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
