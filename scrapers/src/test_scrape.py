"""Scraping test orchestrator — runs all sources in parallel."""

import asyncio
import time
import logging
from dataclasses import dataclass, field, asdict

from scrapers.src.forums import scrape_forums
from scrapers.src.youtube import scrape_youtube
from scrapers.src.facebook_ads import scrape_facebook_ads
from scrapers.src.google_ads import scrape_google_ads

logger = logging.getLogger(__name__)


@dataclass
class SourceResult:
    source: str
    status: str  # ok, partial, error
    result_count: int = 0
    credits_used: int = 0
    error: str | None = None
    items: list[dict] = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class TestScrapeResponse:
    brand: str
    model: str
    sources: list[SourceResult] = field(default_factory=list)
    total_credits: int = 0
    total_duration_ms: int = 0


async def run_test_scrape(brand: str, model: str = "") -> dict:
    """Run all scrapers in parallel and return aggregated results."""
    start = time.time()

    # Run all sources in parallel
    results = await asyncio.gather(
        _scrape_forums(brand, model),
        _scrape_youtube(brand, model),
        _scrape_facebook_ads(brand, model),
        _scrape_google_ads(brand, model),
        return_exceptions=True,
    )

    sources = []
    total_credits = 0

    for result in results:
        if isinstance(result, Exception):
            sources.append(SourceResult(
                source="unknown",
                status="error",
                error=str(result),
            ))
        elif isinstance(result, SourceResult):
            sources.append(result)
            total_credits += result.credits_used

    total_ms = int((time.time() - start) * 1000)

    response = TestScrapeResponse(
        brand=brand,
        model=model,
        sources=sources,
        total_credits=total_credits,
        total_duration_ms=total_ms,
    )

    return asdict(response)


async def _scrape_forums(brand: str, model: str) -> SourceResult:
    start = time.time()
    try:
        resp = await scrape_forums(brand, model)
        items = [{"url": r.url, "title": r.title, "content": r.content, "is_priority": r.is_priority_forum} for r in resp.results]
        return SourceResult(
            source="forums",
            status="error" if resp.error else ("ok" if items else "partial"),
            result_count=len(items),
            credits_used=resp.credits_used,
            error=resp.error,
            items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(source="forums", status="error", error=str(e), duration_ms=int((time.time() - start) * 1000))


async def _scrape_youtube(brand: str, model: str) -> SourceResult:
    start = time.time()
    try:
        resp = await scrape_youtube(brand, model)
        items = [{
            "url": r.url,
            "title": r.title,
            "channel": r.channel,
            "view_count": r.view_count,
            "like_count": r.like_count,
            "description": r.description,
            "comments": r.comments,
        } for r in resp.results]
        return SourceResult(
            source="youtube",
            status="error" if resp.error else ("ok" if items else "partial"),
            result_count=len(items),
            credits_used=0,
            error=resp.error,
            items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(source="youtube", status="error", error=str(e), duration_ms=int((time.time() - start) * 1000))


async def _scrape_facebook_ads(brand: str, model: str) -> SourceResult:
    start = time.time()
    try:
        resp = await scrape_facebook_ads(brand, model)
        items = [{"url": r.url, "title": r.title, "content": r.content} for r in resp.results]
        return SourceResult(
            source="facebook_ads",
            status="error" if resp.error else ("ok" if items else "partial"),
            result_count=len(items),
            credits_used=resp.credits_used,
            error=resp.error,
            items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(source="facebook_ads", status="error", error=str(e), duration_ms=int((time.time() - start) * 1000))


async def _scrape_google_ads(brand: str, model: str) -> SourceResult:
    start = time.time()
    try:
        resp = await scrape_google_ads(brand, model)
        items = [{"url": r.url, "title": r.title, "content": r.content} for r in resp.results]
        return SourceResult(
            source="google_ads",
            status="error" if resp.error else ("ok" if items else "partial"),
            result_count=len(items),
            credits_used=resp.credits_used,
            error=resp.error,
            items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(source="google_ads", status="error", error=str(e), duration_ms=int((time.time() - start) * 1000))
