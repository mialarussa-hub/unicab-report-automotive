"""Perplexity Sonar API client — web search with cited answers.

Docs: https://docs.perplexity.ai/api-reference/chat-completions

Returns a synthesized answer plus a list of source citations (URLs + optional
titles/snippets). Ideal for L2 (media/editorial coverage) — complements
Firecrawl search by giving a pre-synthesized view with explicit sources.
"""

import os
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"
DEFAULT_TIMEOUT = 45.0


@dataclass
class PerplexityCitation:
    url: str
    title: str = ""
    snippet: str = ""


@dataclass
class PerplexityResponse:
    query: str
    answer: str = ""
    citations: list[PerplexityCitation] = field(default_factory=list)
    model: str = ""
    error: str | None = None


class PerplexityClient:
    """Minimal Sonar client — one query, one synthesized answer with citations."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        self.model = model

    async def ask(
        self,
        query: str,
        system_prompt: str | None = None,
        recency: str = "year",
        domain_filter: list[str] | None = None,
    ) -> PerplexityResponse:
        """Run one Sonar query. Returns answer + citations.

        Args:
            query: user question / search intent
            system_prompt: optional override for the assistant persona
            recency: "hour", "day", "week", "month", "year" — Sonar search recency
            domain_filter: optional list of domains to restrict search to
        """
        if not self.api_key:
            return PerplexityResponse(
                query=query,
                error="PERPLEXITY_API_KEY not set",
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "return_citations": True,
            "return_related_questions": False,
        }
        if recency:
            payload["search_recency_filter"] = recency
        if domain_filter:
            payload["search_domain_filter"] = domain_filter

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                resp = await client.post(PERPLEXITY_API_URL, headers=headers, json=payload)

            if resp.status_code != 200:
                err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                logger.warning(f"Perplexity API error for '{query}': {err}")
                return PerplexityResponse(query=query, error=err)

            data = resp.json()
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            answer = (message.get("content") or "").strip()

            citations = _parse_citations(data)

            return PerplexityResponse(
                query=query,
                answer=answer,
                citations=citations,
                model=data.get("model") or self.model,
            )

        except Exception as e:
            logger.error(f"Perplexity request failed for '{query}': {e}")
            return PerplexityResponse(query=query, error=str(e))


def _parse_citations(data: dict) -> list[PerplexityCitation]:
    """Extract citations from Sonar response.

    Sonar returns two shapes across API versions:
    - top-level "citations": [url, url, ...]
    - top-level "search_results": [{url, title, snippet}, ...]  (newer)
    We accept both and merge by URL.
    """
    by_url: dict[str, PerplexityCitation] = {}

    raw_urls = data.get("citations") or []
    for u in raw_urls:
        if isinstance(u, str) and u and u not in by_url:
            by_url[u] = PerplexityCitation(url=u)

    search_results = data.get("search_results") or []
    for sr in search_results:
        if not isinstance(sr, dict):
            continue
        url = sr.get("url") or ""
        if not url:
            continue
        cit = by_url.get(url) or PerplexityCitation(url=url)
        cit.title = sr.get("title") or cit.title
        cit.snippet = (sr.get("snippet") or sr.get("description") or cit.snippet or "")[:400]
        by_url[url] = cit

    return list(by_url.values())
