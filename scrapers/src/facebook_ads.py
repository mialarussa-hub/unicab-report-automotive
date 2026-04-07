"""Facebook Ads Library scraper using Firecrawl search."""

import logging
from dataclasses import dataclass, field

from src.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)


@dataclass
class FacebookAdResult:
    url: str
    title: str
    content: str


@dataclass
class FacebookAdsResponse:
    results: list[FacebookAdResult] = field(default_factory=list)
    credits_used: int = 0
    error: str | None = None


async def scrape_facebook_ads(brand: str, model: str = "") -> FacebookAdsResponse:
    """Search for Facebook/Meta ad activity for a brand.

    Note: Facebook Ads Library blocks direct scraping. We use Firecrawl search
    to find public information about the brand's advertising activity.
    """
    try:
        client = FirecrawlClient()
    except ValueError as e:
        return FacebookAdsResponse(error=str(e))

    search_term = f"{brand} {model}".strip()
    queries = [
        f"facebook ads library {search_term} italia automotive",
        f"meta ads {search_term} pubblicita auto",
    ]

    all_results: list[FacebookAdResult] = []
    total_credits = 0

    for query in queries:
        fc_response = client.search(query, limit=3)
        total_credits += fc_response.credits_used

        if fc_response.error:
            logger.warning(f"Facebook Ads search error: {fc_response.error}")
            continue

        for r in fc_response.results:
            all_results.append(FacebookAdResult(
                url=r.url,
                title=r.title,
                content=r.content[:1500] if r.content else "",
            ))

    return FacebookAdsResponse(results=all_results, credits_used=total_credits)
