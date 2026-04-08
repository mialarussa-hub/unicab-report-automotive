"""Firecrawl API client wrapper (firecrawl-py v4).

Features used:
- search() with scrapeOptions — get full markdown from search results directly
- scrape() — single URL scrape with actions support
- map() — discover all URLs on a site for 1 credit
"""

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


@dataclass
class MapResponse:
    urls: list[dict] = field(default_factory=list)  # [{url, title, description}]
    credits_used: int = 1
    error: str | None = None


# Scrape options: do NOT use only_main_content (it cuts off forum comments)
SCRAPE_KWARGS = {
    "block_ads": True,
    "exclude_tags": ["script", "style", "iframe", ".cookie-banner", ".advertisement"],
    "formats": ["markdown"],
    "timeout": 20000,
}


class FirecrawlClient:
    def __init__(self):
        api_key = os.environ.get("FIRECRAWL_API_KEY", "")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not set")
        self.app = FirecrawlApp(api_key=api_key)

    def search(
        self,
        query: str,
        limit: int = 3,
        recent_only: bool = True,
        with_markdown: bool = False,
    ) -> FirecrawlResponse:
        """Search the web. Set with_markdown=True to get full page content directly."""
        try:
            kwargs = {"limit": limit, "location": "Italy"}
            if recent_only:
                kwargs["tbs"] = "qdr:y"
            if with_markdown:
                kwargs["scrapeOptions"] = {"formats": ["markdown"]}
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
                    # Prefer markdown (from scrapeOptions), fall back to description
                    content = ""
                    if hasattr(item, 'markdown') and item.markdown:
                        content = item.markdown
                    elif hasattr(item, 'description') and item.description:
                        content = item.description
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

            # Credits: 1 per search call + 1 per result if with_markdown
            credits = 1 if not with_markdown else max(1, len(results) + 1)

            return FirecrawlResponse(results=results, credits_used=credits)

        except Exception as e:
            logger.error(f"Firecrawl search error for '{query}': {e}")
            return FirecrawlResponse(error=str(e))

    def scrape(self, url: str, actions: list[dict] | None = None) -> FirecrawlResponse:
        """Scrape a single URL. Optionally pass actions (click, wait, scroll)."""
        try:
            kwargs = dict(SCRAPE_KWARGS)
            if actions:
                kwargs["actions"] = actions
            response = self.app.scrape(url, **kwargs)

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

    def map(self, url: str, search: str = "", limit: int = 100) -> MapResponse:
        """Discover all URLs on a site. 1 credit regardless of results.

        Args:
            url: Base URL of the site (e.g. "https://forum.quattroruote.it")
            search: Filter/rank URLs by keyword relevance
            limit: Max URLs to return
        """
        try:
            kwargs = {"limit": limit}
            if search:
                kwargs["search"] = search
            response = self.app.map(url, **kwargs)

            urls = []
            # Response can be a list of strings, list of dicts, or object with .urls/.links
            items = []
            if isinstance(response, list):
                items = response
            elif hasattr(response, 'links') and response.links:
                items = response.links
            elif hasattr(response, 'urls') and response.urls:
                items = response.urls
            elif hasattr(response, 'data') and response.data:
                items = response.data

            for item in items:
                if isinstance(item, str):
                    urls.append({"url": item, "title": "", "description": ""})
                elif isinstance(item, dict):
                    urls.append({
                        "url": item.get("url") or item.get("link") or "",
                        "title": item.get("title") or "",
                        "description": item.get("description") or "",
                    })
                elif hasattr(item, 'url'):
                    urls.append({
                        "url": item.url or "",
                        "title": getattr(item, 'title', "") or "",
                        "description": getattr(item, 'description', "") or "",
                    })

            return MapResponse(urls=urls, credits_used=1)

        except Exception as e:
            logger.error(f"Firecrawl map error for '{url}': {e}")
            return MapResponse(error=str(e))
