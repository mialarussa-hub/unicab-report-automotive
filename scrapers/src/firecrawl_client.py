"""Firecrawl API client wrapper for web scraping (firecrawl-py v4)."""

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
            response = self.app.search(query, limit=limit)

            results = []

            # firecrawl-py v4 returns a SearchData object with .data attribute
            items = []
            if hasattr(response, 'data'):
                items = response.data or []
            elif isinstance(response, dict) and "data" in response:
                items = response["data"]
            elif isinstance(response, list):
                items = response

            for item in items:
                url = ""
                title = ""
                content = ""

                if hasattr(item, 'url'):
                    url = item.url or ""
                    title = item.title if hasattr(item, 'title') else ""
                    content = item.markdown if hasattr(item, 'markdown') else (item.content if hasattr(item, 'content') else "")
                elif isinstance(item, dict):
                    url = item.get("url", "")
                    title = item.get("title", "")
                    content = item.get("markdown", item.get("content", ""))

                if url or content:
                    results.append(FirecrawlResult(
                        url=url,
                        title=title or url,
                        content=content,
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
            response = self.app.scrape(url)

            content = ""
            title = url

            if hasattr(response, 'markdown'):
                content = response.markdown or ""
                title = response.title if hasattr(response, 'title') else url
            elif isinstance(response, dict):
                content = response.get("markdown", response.get("content", ""))
                title = response.get("metadata", {}).get("title", url)

            result = FirecrawlResult(url=url, title=title, content=content)
            return FirecrawlResponse(results=[result], credits_used=1)

        except Exception as e:
            logger.error(f"Firecrawl scrape error for '{url}': {e}")
            return FirecrawlResponse(error=str(e))
