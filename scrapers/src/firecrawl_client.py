"""Firecrawl API client wrapper for web scraping."""

import os
import logging
from dataclasses import dataclass, field

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)


@dataclass
class FirecrawlResult:
    url: str
    title: str
    content: str  # markdown
    source_query: str = ""


@dataclass
class FirecrawlResponse:
    results: list[FirecrawlResult] = field(default_factory=list)
    credits_used: int = 0
    error: str | None = None


class FirecrawlClient:
    def __init__(self):
        api_key = os.environ.get("FIRECRAWL_API_KEY", "")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not set")
        self.app = FirecrawlApp(api_key=api_key)

    def search(self, query: str, limit: int = 3) -> FirecrawlResponse:
        """Search the web and return scraped results."""
        try:
            response = self.app.search(query, params={"limit": limit})

            results = []
            if isinstance(response, dict) and "data" in response:
                items = response["data"]
            elif isinstance(response, list):
                items = response
            else:
                items = []

            for item in items:
                if isinstance(item, dict):
                    results.append(FirecrawlResult(
                        url=item.get("url", ""),
                        title=item.get("title", item.get("metadata", {}).get("title", "No title")),
                        content=item.get("markdown", item.get("content", item.get("extract", ""))),
                        source_query=query,
                    ))

            return FirecrawlResponse(
                results=results,
                credits_used=max(1, len(results)),
            )

        except Exception as e:
            logger.error(f"Firecrawl search error for '{query}': {e}")
            return FirecrawlResponse(error=str(e))

    def scrape(self, url: str) -> FirecrawlResponse:
        """Scrape a single URL and return clean content."""
        try:
            response = self.app.scrape_url(url)

            if isinstance(response, dict):
                content = response.get("markdown", response.get("content", ""))
                title = response.get("metadata", {}).get("title", url)
            else:
                content = str(response)
                title = url

            result = FirecrawlResult(url=url, title=title, content=content)
            return FirecrawlResponse(results=[result], credits_used=1)

        except Exception as e:
            logger.error(f"Firecrawl scrape error for '{url}': {e}")
            return FirecrawlResponse(error=str(e))
