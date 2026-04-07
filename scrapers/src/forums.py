"""Forum scraper for Italian automotive forums using Firecrawl."""

import logging
from dataclasses import dataclass, field

from scrapers.src.firecrawl_client import FirecrawlClient, FirecrawlResult

logger = logging.getLogger(__name__)

# Priority Italian automotive forums
PRIORITY_DOMAINS = [
    "forum.quattroruote.it",
    "autopareri.com",
    "clubalfa.it",
    "clubfiat.it",
    "bmwpassion.com",
    "audisport.net",
]

# Italian search queries for automotive sentiment
QUERY_TEMPLATES = [
    "{brand} {model} opinioni forum",
    "{brand} {model} problemi difetti",
    "{brand} {model} recensione proprietari",
]


@dataclass
class ForumResult:
    url: str
    title: str
    content: str
    query: str
    is_priority_forum: bool = False


@dataclass
class ForumResponse:
    results: list[ForumResult] = field(default_factory=list)
    credits_used: int = 0
    error: str | None = None


async def scrape_forums(brand: str, model: str = "") -> ForumResponse:
    """Scrape Italian automotive forums for brand/model mentions."""
    try:
        client = FirecrawlClient()
    except ValueError as e:
        return ForumResponse(error=str(e))

    search_term = f"{brand} {model}".strip()
    all_results: list[ForumResult] = []
    total_credits = 0

    for template in QUERY_TEMPLATES:
        query = template.format(brand=brand, model=model or "")
        query = query.strip()

        fc_response = client.search(query, limit=3)
        total_credits += fc_response.credits_used

        if fc_response.error:
            logger.warning(f"Forum search error for '{query}': {fc_response.error}")
            continue

        for r in fc_response.results:
            is_priority = any(domain in r.url for domain in PRIORITY_DOMAINS)
            all_results.append(ForumResult(
                url=r.url,
                title=r.title,
                content=r.content[:2000] if r.content else "",
                query=query,
                is_priority_forum=is_priority,
            ))

    # Sort: priority forums first
    all_results.sort(key=lambda r: (not r.is_priority_forum, r.title))

    return ForumResponse(results=all_results, credits_used=total_credits)
