"""Scraping test orchestrator — runs scrapers on configured sources."""

import asyncio
import time
import logging
from dataclasses import dataclass, field, asdict

from src.firecrawl_client import FirecrawlClient
from src.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


@dataclass
class SourceResult:
    source: str
    source_type: str
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


async def run_test_scrape(brand: str, model: str = "", sources: list[dict] = None) -> dict:
    """Run scrapers on configured sources and return aggregated results."""
    start = time.time()

    if not sources:
        return asdict(TestScrapeResponse(brand=brand, model=model))

    # Group sources by type
    tasks = []
    for source in sources:
        tasks.append(_scrape_source(brand, model, source))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    source_results = []
    total_credits = 0

    for result in results:
        if isinstance(result, Exception):
            source_results.append(SourceResult(
                source="unknown", source_type="unknown", status="error", error=str(result),
            ))
        elif isinstance(result, SourceResult):
            source_results.append(result)
            total_credits += result.credits_used

    total_ms = int((time.time() - start) * 1000)

    response = TestScrapeResponse(
        brand=brand,
        model=model,
        sources=source_results,
        total_credits=total_credits,
        total_duration_ms=total_ms,
    )

    return asdict(response)


async def _scrape_source(brand: str, model: str, source: dict) -> SourceResult:
    """Scrape a single configured source."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    source_type = source.get("source_type", "news")
    search_term = f"{brand} {model}".strip()

    try:
        if source_type == "youtube":
            return await _scrape_youtube_source(brand, model, name, url, start)
        else:
            return await _scrape_web_source(brand, model, name, url, source_type, start)

    except Exception as e:
        logger.error(f"Scrape error for {name}: {e}")
        return SourceResult(
            source=name, source_type=source_type, status="error",
            error=str(e), duration_ms=int((time.time() - start) * 1000),
        )


async def _scrape_web_source(brand: str, model: str, name: str, url: str, source_type: str, start: float) -> SourceResult:
    """Scrape a web source (forum, news, social) using Firecrawl."""
    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type=source_type, status="error", error=str(e))

    search_term = f"{brand} {model}".strip()

    # Search specifically on this source's domain
    domain = url.replace("https://", "").replace("http://", "").rstrip("/")
    queries = [
        f"site:{domain} {search_term}",
        f"{name} {search_term} opinioni",
    ]

    all_items = []
    total_credits = 0

    for query in queries:
        resp = client.search(query, limit=5)
        total_credits += resp.credits_used

        if resp.error:
            logger.warning(f"Search error for {name} '{query}': {resp.error}")
            continue

        for r in resp.results:
            all_items.append({
                "url": r.url,
                "title": r.title,
                "content": r.content[:2000] if r.content else "",
            })

    duration = int((time.time() - start) * 1000)

    return SourceResult(
        source=name,
        source_type=source_type,
        status="ok" if all_items else "partial",
        result_count=len(all_items),
        credits_used=total_credits,
        items=all_items,
        duration_ms=duration,
    )


async def _scrape_youtube_source(brand: str, model: str, name: str, url: str, start: float) -> SourceResult:
    """Scrape a YouTube source (channel or general search)."""
    client = YouTubeClient()

    try:
        search_term = f"{brand} {model}".strip()

        # If URL contains a specific channel, search within it
        channel_name = ""
        if "youtube.com" in url or "youtu.be" in url:
            # Extract channel context for search
            parts = url.rstrip("/").split("/")
            channel_name = parts[-1] if parts else ""

        query = f"{channel_name} {search_term}".strip() if channel_name else f"{search_term} recensione"
        response = await client.collect(query, max_videos=5, max_comments=10)

        if response.error:
            return SourceResult(
                source=name, source_type="youtube", status="error",
                error=response.error, duration_ms=int((time.time() - start) * 1000),
            )

        items = [{
            "url": v.url,
            "title": v.title,
            "channel": v.channel,
            "view_count": v.view_count,
            "like_count": v.like_count,
            "description": v.description[:500],
            "comments": v.comments[:10],
        } for v in response.videos]

        return SourceResult(
            source=name,
            source_type="youtube",
            status="ok" if items else "partial",
            result_count=len(items),
            credits_used=0,
            items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(
            source=name, source_type="youtube", status="error",
            error=str(e), duration_ms=int((time.time() - start) * 1000),
        )
    finally:
        await client.close()
