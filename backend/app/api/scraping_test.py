"""Scraping test endpoint — proxies requests to scrapers container."""

import uuid

import httpx
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models.source import Source
from app.models.user import User

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
    """Proxy scraping test request to scrapers container, passing configured sources."""
    # Fetch active sources from DB
    result = await db.execute(select(Source).where(Source.is_active == True))
    sources = result.scalars().all()

    sources_list = [
        {"name": s.name, "url": s.url, "source_type": s.source_type}
        for s in sources
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{SCRAPERS_URL}/scrape/test",
            json={
                "brand": request.brand,
                "model": request.model,
                "sources": sources_list,
            },
        )
        return resp.json()
