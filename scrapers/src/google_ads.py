"""Google Ads Transparency Center scraper using Firecrawl."""

import logging
from dataclasses import dataclass, field

from scrapers.src.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)


@dataclass
class GoogleAdResult:
    url: str
    title: str
    content: str


@dataclass
class GoogleAdsResponse:
    results: list[GoogleAdResult] = field(default_factory=list)
    credits_used: int = 0
    error: str | None = None


async def scrape_google_ads(brand: str, model: str = "") -> GoogleAdsResponse:
    """Search for Google advertising data for a brand.

    Strategy:
    1. Try direct scrape of Google Ads Transparency Center
    2. Fallback to Firecrawl search for public ad data
    """
    try:
        client = FirecrawlClient()
    except ValueError as e:
        return GoogleAdsResponse(error=str(e))

    search_term = f"{brand} {model}".strip()
    total_credits = 0
    all_results: list[GoogleAdResult] = []

    # Strategy 1: Try direct Transparency Center scrape
    transparency_url = f"https://adstransparency.google.com/?region=IT&query={brand.replace(' ', '+')}"
    fc_response = client.scrape(transparency_url)
    total_credits += fc_response.credits_used

    if not fc_response.error and fc_response.results and fc_response.results[0].content:
        r = fc_response.results[0]
        if len(r.content) > 100:  # Got real content
            all_results.append(GoogleAdResult(
                url=r.url,
                title=f"Google Ads Transparency — {brand}",
                content=r.content[:2000],
            ))
            return GoogleAdsResponse(results=all_results, credits_used=total_credits)

    # Strategy 2: Fallback to search
    query = f"google ads transparency {search_term} italia pubblicita automotive"
    fc_response = client.search(query, limit=3)
    total_credits += fc_response.credits_used

    if fc_response.error:
        logger.warning(f"Google Ads search error: {fc_response.error}")
    else:
        for r in fc_response.results:
            all_results.append(GoogleAdResult(
                url=r.url,
                title=r.title,
                content=r.content[:1500] if r.content else "",
            ))

    return GoogleAdsResponse(results=all_results, credits_used=total_credits)
