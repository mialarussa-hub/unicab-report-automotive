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


# Scrape keyword arguments for cleaner content
SCRAPE_KWARGS = {
    "only_main_content": True,
    "block_ads": True,
    "exclude_tags": ["nav", "footer", "header", "aside", "script", "style", "iframe"],
    "formats": ["markdown"],
    "timeout": 15000,
}


class FirecrawlClient:
    def __init__(self):
        api_key = os.environ.get("FIRECRAWL_API_KEY", "")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not set")
        self.app = FirecrawlApp(api_key=api_key)

    def search(self, query: str, limit: int = 3, recent_only: bool = True) -> FirecrawlResponse:
        """Search the web and return scraped results."""
        try:
            # tbs="qdr:y" = last year, "qdr:m6" = last 6 months
            kwargs = {"limit": limit}
            if recent_only:
                kwargs["tbs"] = "qdr:y"
            response = self.app.search(query, **kwargs)

            results = []

            # firecrawl-py v4 SearchData has .web, .news, .images
            items = []
            if hasattr(response, 'web') and response.web:
                items.extend(response.web)
            if hasattr(response, 'news') and response.news:
                items.extend(response.news)
            if not items and hasattr(response, 'data') and response.data:
                items = response.data

            for item in items:
                url = ""
                title = ""
                content = ""

                if hasattr(item, 'url'):
                    url = (item.url or "") if hasattr(item, 'url') else ""
                    title = (item.title or "") if hasattr(item, 'title') else ""
                    content = (item.description or "") if hasattr(item, 'description') else ""
                    if not content and hasattr(item, 'markdown'):
                        content = item.markdown or ""
                elif isinstance(item, dict):
                    url = item.get("url") or ""
                    title = item.get("title") or ""
                    content = item.get("markdown") or item.get("content") or item.get("description") or ""

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
        """Scrape a single URL with clean content extraction."""
        try:
            response = self.app.scrape(url, **SCRAPE_KWARGS)

            content = ""
            title = url

            if hasattr(response, 'markdown'):
                content = response.markdown or ""
                title = (response.title or url) if hasattr(response, 'title') else url
            elif isinstance(response, dict):
                content = response.get("markdown") or response.get("content") or ""
                meta = response.get("metadata") or {}
                title = meta.get("title") or url

            result = FirecrawlResult(url=url, title=title, content=content)
            return FirecrawlResponse(results=[result], credits_used=1)

        except Exception as e:
            logger.error(f"Firecrawl scrape error for '{url}': {e}")
            return FirecrawlResponse(error=str(e))
