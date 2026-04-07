"""Scraping test endpoint — proxies requests to scrapers container."""

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

SCRAPERS_URL = "http://scrapers:8001"


class ScrapeTestRequest(BaseModel):
    brand: str
    model: str = ""


@router.post("/run")
async def run_scraping_test(
    request: ScrapeTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Proxy scraping test request to scrapers container."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{SCRAPERS_URL}/scrape/test",
            json={"brand": request.brand, "model": request.model},
        )
        return resp.json()
