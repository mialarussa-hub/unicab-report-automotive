"""Scraping test orchestrator — 3-step: search → scrape → clean with AI."""

import asyncio
import os
import re
import time
import logging
from dataclasses import dataclass, field, asdict

from src.firecrawl_client import FirecrawlClient
from src.youtube_client import YouTubeClient
from src.reddit_client import RedditClient
from src.perplexity_client import PerplexityClient
from src.content_cleaner import clean_and_extract
from src.auto_brands import build_model_context, get_official_urls
from src.relevance import filter_and_rank


def _normalize_forum_url(url: str) -> str:
    """Strip pagination from forum URLs to get page 1 (which has the most comments).

    Examples:
        .../thread.149852/page-2  → .../thread.149852/
        .../?page=188             → .../
        .../?&page=3#comments     → .../#comments
    """
    # XenForo: /page-N at the end
    url = re.sub(r'/page-\d+/?', '/', url)
    # IPS/generic: ?page=N or ?&page=N
    url = re.sub(r'[?&]page=\d+', '', url)
    # Clean up leftover ? or &
    url = re.sub(r'\?&', '?', url)
    url = re.sub(r'\?$', '', url)
    return url

logger = logging.getLogger(__name__)

def _find_pagination_urls(markdown: str, base_url: str) -> list[str]:
    """Extract pagination URLs from forum markdown.

    Looks for patterns like:
    - IPS: ?&page=2, ?&page=3 (autopareri.com)
    - XenForo: /page-2, /page-3 (quattroruote.it)
    """
    pages = set()

    # IPS pattern: links to ?&page=N or ?page=N
    for match in re.finditer(r'(?:href=["\']|]\()([^"\')\s]*[?&]page=(\d+)[^"\')\s]*)', markdown):
        page_num = int(match.group(2))
        if 2 <= page_num <= 10:
            pages.add(page_num)

    # Also look for plain text pagination links in markdown: [2](url?page=2)
    for match in re.finditer(r'\[(\d+)\]\(([^)]*[?&]page=\d+[^)]*)\)', markdown):
        page_num = int(match.group(1))
        url = match.group(2)
        if 2 <= page_num <= 10:
            pages.add(page_num)

    # XenForo pattern: /page-N links
    for match in re.finditer(r'\[(\d+)\]\(([^)]*?/page-(\d+)[^)]*)\)', markdown):
        page_num = int(match.group(3))
        if 2 <= page_num <= 10:
            pages.add(page_num)

    if not pages:
        return []

    # Build full URLs for pages 2, 3, etc.
    sorted_pages = sorted(pages)
    result = []
    for page_num in sorted_pages:
        # Construct page URL based on base URL format
        if "autopareri.com" in base_url:
            # IPS: append ?&page=N
            clean_base = re.sub(r'[?&]page=\d+', '', base_url).rstrip('/')
            result.append(f"{clean_base}/?&page={page_num}#comments")
        elif "quattroruote.it" in base_url:
            # XenForo: append /page-N
            clean_base = re.sub(r'/page-\d+/?', '/', base_url).rstrip('/')
            result.append(f"{clean_base}/page-{page_num}")
        else:
            # Generic: try ?page=N
            clean_base = re.sub(r'[?&]page=\d+', '', base_url).rstrip('/')
            sep = '&' if '?' in clean_base else '?'
            result.append(f"{clean_base}{sep}page={page_num}")

    return result


def _build_search_terms(brand: str, model: str, model_context: dict) -> list[str]:
    """Generate search term variants from brand aliases and model name.

    For "Volkswagen Golf" returns: ["Volkswagen Golf", "VW Golf"]
    This way forums with "VW Golf" in titles get found too.
    """
    terms = [f"{brand} {model}".strip()]
    for alias in model_context.get("brand_aliases", []):
        variant = f"{alias} {model}".strip()
        if variant not in terms:
            terms.append(variant)
    return terms

# Max extra pages to scrape for paginated forum threads
MAX_EXTRA_PAGES = 3


@dataclass
class ScrapedPage:
    url: str
    title: str
    snippet: str  # from search
    full_content: str  # from scrape
    content_length: int = 0


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


async def run_test_scrape(
    brand: str, model: str = "", sources: list[dict] = None,
    alimentazione: str | None = None, cilindrata: float | None = None,
    session_id: str | None = None, callback_url: str | None = None,
) -> dict:
    """Run 2-step scrapers on configured sources.

    If session_id and callback_url are provided, sends per-source results
    to the backend as each source completes (for real-time progress tracking).
    """
    start = time.time()

    if not sources:
        return asdict(TestScrapeResponse(brand=brand, model=model))

    async def _scrape_and_notify(source: dict) -> SourceResult:
        """Scrape one source and optionally notify backend when done."""
        result = await _scrape_source(brand, model, source, alimentazione, cilindrata)

        # Generate summaries for this source immediately
        if result.items:
            await _generate_summaries_batch([result])

        # Notify backend that this source is done (for real-time progress)
        if callback_url and session_id:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(callback_url, json={
                        "session_id": session_id,
                        "source_result": asdict(result),
                    })
                logger.warning(f"[{source.get('name', '?')}] Callback sent to backend")
            except Exception as e:
                logger.warning(f"[{source.get('name', '?')}] Callback failed: {e}")

        return result

    tasks = [_scrape_and_notify(source) for source in sources]
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

    return asdict(TestScrapeResponse(
        brand=brand, model=model, sources=source_results,
        total_credits=total_credits, total_duration_ms=total_ms,
    ))


async def _scrape_source(brand: str, model: str, source: dict,
                         alimentazione: str | None = None,
                         cilindrata: float | None = None) -> SourceResult:
    """Route to the right scraper based on source type and URL."""
    source_type = source.get("source_type", "news")
    url = source.get("url", "")

    if source_type == "perplexity":
        return await _scrape_perplexity_source(brand, model, source)
    elif "reddit.com" in url:
        return await _scrape_reddit_source(brand, model, source)
    elif source_type == "youtube":
        return await _scrape_youtube_source(brand, model, source)
    else:
        return await _scrape_web_source(brand, model, source, alimentazione, cilindrata)


async def _scrape_web_source(brand: str, model: str, source: dict,
                             alimentazione: str | None = None,
                             cilindrata: float | None = None) -> SourceResult:
    """Route to platform-specific strategy."""
    source_type = source.get("source_type", "news")
    url = source.get("url", "")

    if source_type == "official":
        return await _scrape_official_source(brand, model, source, alimentazione, cilindrata)
    elif source_type == "forum":
        return await _scrape_forum_source(brand, model, source)
    elif "alvolante.it" in url:
        # AlVolante: editorial pages WITH user comments — use forum strategy
        # (search → scrape → parse comments) but with news-style queries
        return await _scrape_alvolante_source(brand, model, source)
    else:
        return await _scrape_news_source(brand, model, source)


async def _scrape_forum_source(brand: str, model: str, source: dict) -> SourceResult:
    """Forum strategy: time-filtered search → relevance filter → scrape all matches.

    Uses Google's tbs=qdr:y (last 12 months) via Firecrawl search to only find
    recent threads. Multiple query variants for coverage.
    """
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    domain = url.replace("https://", "").replace("http://", "").rstrip("/")
    search_term = f"{brand} {model}".strip()
    model_context = build_model_context(brand, model)
    search_terms = _build_search_terms(brand, model, model_context)

    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type="forum", status="error", error=str(e))

    # --- STEP 1: Search with time filter (last 12 months) ---
    found_urls = {}
    total_credits = 0

    # Multiple query suffixes for coverage
    suffixes = ["", "opinioni", "problemi difetti", "proprietari esperienza", "consumi"]

    # Also search with just the brand (catches generic brand threads like "BYD supera Tesla")
    all_terms = list(search_terms)
    if model:
        all_terms.append(brand)  # brand-only query as fallback

    for term in all_terms:
        for suffix in suffixes:
            query = f"site:{domain} {term} {suffix}".strip()
            logger.warning(f"[{name}] SEARCH: '{query}'")
            resp = client.search(query, limit=10, recent_only=True)
            total_credits += resp.credits_used

            if resp.error:
                logger.warning(f"[{name}] Search error: {resp.error}")
                continue

            for r in resp.results:
                if r.url:
                    clean_url = _normalize_forum_url(r.url)
                    if clean_url not in found_urls:
                        found_urls[clean_url] = {
                            "title": r.title or "",
                            "snippet": (r.content or "")[:300],
                        }

    if not found_urls:
        return SourceResult(
            source=name, source_type="forum", status="partial",
            credits_used=total_credits, error="No recent URLs found in search",
            duration_ms=int((time.time() - start) * 1000),
        )

    logger.warning(f"[{name}] STEP 1 done: {len(found_urls)} unique URLs from last 12 months")

    # --- STEP 2: Relevance scoring and filtering ---
    ranked = filter_and_rank(found_urls, brand, model, model_context)

    if not ranked:
        return SourceResult(
            source=name, source_type="forum", status="partial",
            credits_used=total_credits,
            error=f"Found {len(found_urls)} URLs but none passed relevance filter for '{search_term}'",
            duration_ms=int((time.time() - start) * 1000),
        )

    # --- STEP 3: Scrape the top-ranked threads (with multi-page for forums) ---
    items = []

    for page_url, meta in ranked:
        relevance_score = meta.get("score", 0)
        logger.warning(f"[{name}] SCRAPE: {page_url} (relevance={relevance_score})")
        resp = client.scrape(page_url)
        total_credits += resp.credits_used

        if resp.error:
            logger.warning(f"[{name}] Scrape error for {page_url}: {resp.error}")
            items.append({
                "url": page_url, "title": meta.get("title", ""),
                "content": meta.get("snippet", ""), "content_length": 0,
                "relevance_score": relevance_score, "scraped": False,
            })
            continue

        full_content = resp.results[0].content if resp.results else ""
        title = resp.results[0].title if resp.results else meta.get("title", "")
        logger.warning(f"[{name}] Scraped page 1: {len(full_content)} chars")

        # Multi-page: scrape additional pages if pagination detected
        extra_pages = _find_pagination_urls(full_content, page_url)
        if extra_pages:
            logger.warning(f"[{name}] Found {len(extra_pages)} additional pages, scraping...")
            for extra_url in extra_pages[:MAX_EXTRA_PAGES]:
                extra_resp = client.scrape(extra_url)
                total_credits += extra_resp.credits_used
                if extra_resp.results and extra_resp.results[0].content:
                    extra_content = extra_resp.results[0].content
                    full_content += f"\n\n--- PAGE ---\n\n{extra_content}"
                    logger.warning(f"[{name}] Scraped extra page: +{len(extra_content)} chars")

        logger.warning(f"[{name}] Total content for {page_url}: {len(full_content)} chars")

        items.append({
            "url": page_url,
            "title": title,
            "content": (full_content or meta.get("snippet", ""))[:5000],
            "_full_content": full_content,
            "content_length": len(full_content),
            "relevance_score": relevance_score,
            "scraped": True,
        })

    # --- STEP 4: Clean with Claude AI (uses full content, not truncated) ---
    await _clean_items_with_ai(items, name)

    # Remove _full_content before returning (not needed in API response)
    for item in items:
        item.pop("_full_content", None)

    return SourceResult(
        source=name, source_type="forum",
        status="ok" if items else "partial",
        result_count=len(items), credits_used=total_credits,
        items=items, duration_ms=int((time.time() - start) * 1000),
    )


async def _scrape_alvolante_source(brand: str, model: str, source: dict) -> SourceResult:
    """AlVolante strategy: search for articles → scrape full pages → parse comments.

    AlVolante articles (prova, primo_contatto, news) have user comments embedded
    in the page — up to 100+ per article. No pagination needed.
    """
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    domain = url.replace("https://", "").replace("http://", "").rstrip("/")
    model_context = build_model_context(brand, model)
    search_terms = _build_search_terms(brand, model, model_context)

    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type="news", status="error", error=str(e))

    # Search for articles with comments (prova, primo_contatto, news sections)
    found_urls = {}
    total_credits = 0

    all_terms = list(search_terms)
    if model:
        all_terms.append(brand)

    for term in all_terms:
        for suffix in ["prova", "primo contatto", "news", "opinioni"]:
            query = f"site:{domain} {term} {suffix}"
            logger.warning(f"[{name}] SEARCH: '{query}'")
            resp = client.search(query, limit=10, recent_only=True)
            total_credits += resp.credits_used

            if resp.error:
                logger.warning(f"[{name}] Search error: {resp.error}")
                continue

            for r in resp.results:
                if r.url and r.url not in found_urls:
                    found_urls[r.url] = {
                        "title": r.title or "",
                        "snippet": (r.content or "")[:300],
                    }

    if not found_urls:
        return SourceResult(
            source=name, source_type="news", status="partial",
            credits_used=total_credits, error="No articles found",
            duration_ms=int((time.time() - start) * 1000),
        )

    logger.warning(f"[{name}] Found {len(found_urls)} articles, scoring relevance...")
    ranked = filter_and_rank(found_urls, brand, model, model_context)

    if not ranked:
        return SourceResult(
            source=name, source_type="news", status="partial",
            credits_used=total_credits,
            error=f"No articles passed relevance filter",
            duration_ms=int((time.time() - start) * 1000),
        )

    # Scrape full articles (comments are embedded — no multi-page needed)
    items = []
    for page_url, meta in ranked:
        relevance_score = meta.get("score", 0)
        logger.warning(f"[{name}] SCRAPE: {page_url} (relevance={relevance_score})")
        resp = client.scrape(page_url)
        total_credits += resp.credits_used

        if resp.error:
            logger.warning(f"[{name}] Scrape error: {resp.error}")
            continue

        full_content = resp.results[0].content if resp.results else ""
        title = resp.results[0].title if resp.results else meta.get("title", "")
        logger.warning(f"[{name}] Scraped {page_url}: {len(full_content)} chars")

        items.append({
            "url": page_url,
            "title": title,
            "content": full_content[:5000],
            "_full_content": full_content,
            "content_length": len(full_content),
            "relevance_score": relevance_score,
            "scraped": True,
        })

    # Parse comments with Claude AI
    await _clean_items_with_ai(items, name)

    for item in items:
        item.pop("_full_content", None)

    return SourceResult(
        source=name, source_type="news",
        status="ok" if items else "partial",
        result_count=len(items), credits_used=total_credits,
        items=items, duration_ms=int((time.time() - start) * 1000),
    )


async def _scrape_news_source(brand: str, model: str, source: dict) -> SourceResult:
    """News strategy: search with scrapeOptions → get full markdown directly, no separate scrape."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    domain = url.replace("https://", "").replace("http://", "").rstrip("/")
    search_term = f"{brand} {model}".strip()
    model_context = build_model_context(brand, model)
    search_terms = _build_search_terms(brand, model, model_context)

    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type="news", status="error", error=str(e))

    # --- STEP 1: Search with full markdown (eliminates separate scrape) ---
    found_urls = {}
    total_credits = 0

    for term in search_terms:
        for suffix in ["recensione", "prova su strada"]:
            query = f"site:{domain} {term} {suffix}"
            logger.warning(f"[{name}] SEARCH+MD: '{query}'")
            resp = client.search(query, limit=5, with_markdown=True)
            total_credits += resp.credits_used

            if resp.error:
                logger.warning(f"[{name}] Search error: {resp.error}")
                continue

            for r in resp.results:
                if r.url and r.url not in found_urls:
                    found_urls[r.url] = {
                        "title": r.title or "",
                        "snippet": (r.content or "")[:300],
                        "full_content": r.content or "",
                    }

    if not found_urls:
        return SourceResult(
            source=name, source_type="news", status="partial",
            credits_used=total_credits, error="No URLs found in search",
            duration_ms=int((time.time() - start) * 1000),
        )

    logger.warning(f"[{name}] Found {len(found_urls)} URLs with markdown, scoring relevance...")

    # --- STEP 2: Relevance scoring ---
    ranked = filter_and_rank(found_urls, brand, model, model_context)

    if not ranked:
        return SourceResult(
            source=name, source_type="news", status="partial",
            credits_used=total_credits,
            error=f"Found {len(found_urls)} URLs but none passed relevance filter for '{search_term}'",
            duration_ms=int((time.time() - start) * 1000),
        )

    # --- STEP 3: Build items directly from search results (already have markdown!) ---
    items = []
    for page_url, meta in ranked:
        full_content = found_urls[page_url].get("full_content", "")
        has_content = len(full_content) > 200
        logger.warning(f"[{name}] Result: {page_url} — {len(full_content)} chars (relevance={meta.get('score', 0)})")

        items.append({
            "url": page_url,
            "title": meta.get("title", ""),
            "content": full_content[:5000],
            "_full_content": full_content,
            "content_length": len(full_content),
            "relevance_score": meta.get("score", 0),
            "scraped": has_content,
        })

    # --- STEP 4: Clean with Claude AI (uses full content) ---
    await _clean_items_with_ai(items, name)

    for item in items:
        item.pop("_full_content", None)

    return SourceResult(
        source=name, source_type="news",
        status="ok" if items else "partial",
        result_count=len(items), credits_used=total_credits,
        items=items, duration_ms=int((time.time() - start) * 1000),
    )


async def _clean_items_with_ai(items: list[dict], source_name: str):
    """Run Claude AI comment extraction on scraped items."""
    logger.warning(f"[{source_name}] AI: cleaning {len(items)} pages")
    for item in items:
        # Use full content for parsing (not the truncated 5K version)
        ai_content = item.get("_full_content") or item.get("content", "")
        if item.get("scraped") and len(ai_content) > 200:
            cleaned = await clean_and_extract(ai_content, source_name, item["url"])
            if cleaned.get("cleaned") and cleaned.get("comments"):
                item["ai_comments"] = cleaned["comments"]
                item["ai_comment_count"] = cleaned["comment_count"]
                logger.warning(f"[{source_name}] AI extracted {cleaned['comment_count']} comments from {item['url']}")
            elif cleaned.get("error"):
                logger.warning(f"[{source_name}] AI error: {cleaned['error']}")


async def _scrape_reddit_source(brand: str, model: str, source: dict) -> SourceResult:
    """Reddit strategy: PullPush.io archive API — posts + full comments, free, no IP blocks."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")

    # Extract subreddit from URL
    subreddit = "ItalyMotori"
    if "/r/" in url:
        parts = url.split("/r/")
        if len(parts) > 1:
            subreddit = parts[1].strip("/").split("/")[0]

    model_context = build_model_context(brand, model)
    search_terms = _build_search_terms(brand, model, model_context)

    client = RedditClient()
    try:
        # Reddit-specific queries: users type "Golf" not "Volkswagen Golf"
        reddit_queries = [model]  # Just the model name first (most common on Reddit)
        reddit_queries.extend(search_terms)  # Also try "Volkswagen Golf", "VW Golf"

        logger.warning(f"[{name}] Arctic Shift: searching r/{subreddit} with queries {reddit_queries}")
        response = await client.collect(
            subreddit, reddit_queries, max_posts=25, max_comments=50, min_comments=2,
        )

        if response.error:
            return SourceResult(
                source=name, source_type="forum", status="partial",
                error=response.error, duration_ms=int((time.time() - start) * 1000),
            )

        if not response.posts:
            return SourceResult(
                source=name, source_type="forum", status="partial",
                error=f"No Reddit posts with comments found for r/{subreddit}",
                duration_ms=int((time.time() - start) * 1000),
            )

        # Build items with structured comment data
        items = []
        total_comments = 0
        for post in response.posts:
            # Build AI-ready comment list directly (no parsing needed — already structured)
            ai_comments = []
            for c in post.comments:
                ai_comments.append({
                    "author": c.author,
                    "text": c.text,
                    "sentiment": "neutro",  # will be overwritten by AI
                    "topics": [],
                })

            # Build display content
            content_parts = []
            if post.selftext:
                content_parts.append(post.selftext)
            for c in post.comments:
                content_parts.append(f"[{c.author}] (score: {c.score}): {c.text}")
            full_content = "\n\n".join(content_parts)

            total_comments += len(post.comments)

            items.append({
                "url": post.url,
                "title": f"{post.title} (score: {post.score}, {post.num_comments} commenti)",
                "content": full_content[:5000],
                "content_length": len(full_content),
                "ai_comments": ai_comments if ai_comments else None,
                "ai_comment_count": len(ai_comments),
                "scraped": True,
            })

        logger.warning(f"[{name}] Arctic Shift: {len(items)} posts, {total_comments} comments total")

        # Run sentiment analysis in ONE batch (not per-post — too many API calls)
        all_comments = []
        comment_map = []  # (item_index, comment_index) to map back
        for i, item in enumerate(items):
            if item.get("ai_comments"):
                for j, c in enumerate(item["ai_comments"]):
                    all_comments.append(c)
                    comment_map.append((i, j))

        if all_comments:
            logger.warning(f"[{name}] Running sentiment on {len(all_comments)} Reddit comments (1 batch)")
            analyzed = await _run_batch_sentiment(all_comments, name, "Reddit")
            if analyzed:
                # Map results back to items
                for idx, (i, j) in enumerate(comment_map):
                    if idx < len(analyzed):
                        items[i]["ai_comments"][j] = analyzed[idx]

        return SourceResult(
            source=name, source_type="forum",
            status="ok" if items else "partial",
            result_count=len(items), credits_used=0,
            items=items, duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(
            source=name, source_type="forum", status="error",
            error=str(e), duration_ms=int((time.time() - start) * 1000),
        )
    finally:
        await client.close()


async def _generate_summaries_batch(source_results: list) -> None:
    """Generate AI summaries for all scraped items across all sources (1 call per source)."""
    import os, json
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return

    for source in source_results:
        items = source.items or []
        # Only summarize items that have content and were actually scraped
        items_to_summarize = [
            (i, item) for i, item in enumerate(items)
            if item.get("scraped") and item.get("content") and len(item.get("content", "")) > 100
        ]

        if not items_to_summarize:
            continue

        # Build batch prompt
        items_text = ""
        for idx, (i, item) in enumerate(items_to_summarize):
            title = item.get("title", "Senza titolo")
            content = item.get("content", "")[:2000]  # first 2000 chars per item
            items_text += f"\n\n--- ARTICOLO [{idx+1}] ---\nTitolo: {title}\nContenuto:\n{content}"

        if len(items_text) > 40000:
            items_text = items_text[:40000]

        from src.motore import prompt_enum_description
        alim_enum = prompt_enum_description()
        prompt = f"""Riassumi ogni articolo/thread/video qui sotto in 2-3 frasi in italiano.
Concentrati su: argomento principale, opinione dominante, punti chiave.

Inoltre estrai le motorizzazioni principali oggetto dell'articolo/thread/video.
`alimentazione` DEVE essere uno di: {alim_enum}.
`cilindrata` è un numero decimale in litri (es. 1.0, 1.5, 2.0); usa null se elettrico puro o non indicata.
Se l'articolo non cita motorizzazioni specifiche, "motore_info": {{"versioni": []}}.

Restituisci un JSON array con UN oggetto per OGNI articolo, nello stesso ordine:
[{{"summary": "riassunto 2-3 frasi", "motore_info": {{"versioni": [{{"alimentazione": "benzina", "cilindrata": 1.0, "descrizione": "1.0 TSI"}}]}}}}]

SOLO il JSON array, nient'altro.

{items_text}"""

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if resp.status_code != 200:
                    logger.warning(f"[{source.source}] Summary API error: {resp.status_code}")
                    continue

                data = resp.json()
                text = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text += block.get("text", "")
                text = text.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1])

                summaries = json.loads(text)
                from src.motore import normalize_alimentazione, normalize_cilindrata
                for idx, (i, item) in enumerate(items_to_summarize):
                    if idx < len(summaries):
                        item["summary"] = summaries[idx].get("summary", "")
                        mi = summaries[idx].get("motore_info") or {}
                        versioni = mi.get("versioni") or []
                        clean = []
                        for v in versioni:
                            if not isinstance(v, dict):
                                continue
                            a = normalize_alimentazione(v.get("alimentazione"))
                            c = normalize_cilindrata(v.get("cilindrata"))
                            if not a and c is None:
                                continue
                            clean.append({
                                "alimentazione": a,
                                "cilindrata": c,
                                "descrizione": v.get("descrizione") or None,
                            })
                        item["motore_info"] = {"versioni": clean}

                logger.warning(f"[{source.source}] Generated {len(summaries)} summaries")

        except Exception as e:
            logger.warning(f"[{source.source}] Summary generation error: {e}")


async def _run_batch_sentiment(comments: list[dict], source_name: str,
                               source_label: str = "Reddit") -> list[dict] | None:
    """Run Claude sentiment analysis on pre-structured comments (Reddit, YouTube, etc.)."""
    import os, json
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    comments_text = "\n\n".join(
        f"[{i+1}] {c['author']}: {c['text'][:500]}"
        for i, c in enumerate(comments)
    )
    if len(comments_text) > 30000:
        comments_text = comments_text[:30000]

    from src.motore import prompt_enum_description
    alim_enum = prompt_enum_description()
    prompt = f"""Analizza questi commenti {source_label} di utenti italiani su auto.
Per OGNI commento restituisci sentiment, topics e (se menzionata) la motorizzazione.

Topics possibili: prezzo, motore, design, affidabilità, consumi, cambio, comfort, qualità, spazio, tecnologia, assistenza, valore, guida, rumorosità, sicurezza, batteria, autonomia, ricarica

`motore_menzionato` deve essere null se il commento NON cita alcuna motorizzazione/alimentazione.
Se lo cita: {{"alimentazione": "{alim_enum}", "cilindrata": 1.0}} (cilindrata decimale in litri, null se elettrico puro o non citata).

Restituisci un JSON array con UN oggetto per OGNI commento, nello stesso ordine:
[{{"sentiment": "positivo|negativo|neutro|misto", "topics": ["topic1"], "motore_menzionato": null}}]

SOLO il JSON array.

Commenti:

{comments_text}"""

    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 8192,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            sentiments = json.loads(text)
            from src.motore import normalize_alimentazione, normalize_cilindrata
            for i, c in enumerate(comments):
                if i < len(sentiments):
                    c["sentiment"] = sentiments[i].get("sentiment", "neutro")
                    c["topics"] = sentiments[i].get("topics", [])
                    mm = sentiments[i].get("motore_menzionato")
                    if isinstance(mm, dict):
                        a = normalize_alimentazione(mm.get("alimentazione"))
                        cc = normalize_cilindrata(mm.get("cilindrata"))
                        c["motore_menzionato"] = (
                            {"alimentazione": a, "cilindrata": cc}
                            if (a or cc is not None) else None
                        )
                    else:
                        c["motore_menzionato"] = None

            logger.warning(f"[{source_name}] {source_label} AI analyzed {len(comments)} comments")
            return comments
    except Exception as e:
        logger.warning(f"[{source_name}] {source_label} sentiment error: {e}")
        return None


async def _scrape_youtube_source(brand: str, model: str, source: dict) -> SourceResult:
    """Scrape YouTube source with comments and sentiment analysis."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")

    client = YouTubeClient()
    try:
        search_term = f"{brand} {model}".strip()

        # Search WITHOUT channel name — YouTube relevance is better without it
        # If we lock to a channel name, we get random results when the channel
        # doesn't have content for that specific model
        queries = [
            f"{search_term} recensione",
            f"{search_term} prova su strada",
            f"{search_term} test drive",
            f"{search_term} opinioni",
        ]

        # Filter to videos from the last 18 months
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=540)).strftime("%Y-%m-%dT00:00:00Z")

        # Build relevance keywords for filtering
        brand_lower = brand.lower()
        model_lower = model.lower() if model else ""
        # Split model into parts for flexible matching (e.g. "500 XL" -> ["500", "xl"])
        model_parts = model_lower.split() if model_lower else []

        all_videos = {}
        for query in queries:
            response = await client.collect(query, max_videos=5, max_comments=15,
                                            published_after=cutoff)
            if response.error:
                logger.warning(f"[{name}] YouTube error for '{query}': {response.error}")
                continue
            for v in response.videos:
                if v.video_id in all_videos:
                    continue
                # Relevance filter: title must mention brand or model
                title_lower = v.title.lower()
                desc_lower = v.description[:500].lower() if v.description else ""
                text = f"{title_lower} {desc_lower}"

                has_brand = brand_lower in text
                has_model = any(p in text for p in model_parts) if model_parts else False

                if has_brand or has_model:
                    all_videos[v.video_id] = v
                else:
                    logger.warning(f"[{name}] Skipped irrelevant video: '{v.title}'")

        if not all_videos:
            return SourceResult(
                source=name, source_type="youtube", status="error",
                error="No YouTube results (API key may not be configured)",
                duration_ms=int((time.time() - start) * 1000),
            )

        # Build items with structured comments (same pattern as Reddit)
        items = []
        total_comments = 0
        for v in all_videos.values():
            # Sort comments by like_count descending, take top 15
            sorted_comments = sorted(v.comments, key=lambda c: c.get("like_count", 0), reverse=True)[:15]

            # Build ai_comments structure
            ai_comments = []
            for c in sorted_comments:
                ai_comments.append({
                    "author": c.get("author", ""),
                    "text": c.get("text", ""),
                    "sentiment": "neutro",
                    "topics": [],
                })

            # Build display content
            content_parts = [v.description[:500]] if v.description else []
            for c in sorted_comments:
                content_parts.append(f"[{c.get('author', '')}] (likes: {c.get('like_count', 0)}): {c.get('text', '')}")
            full_content = "\n\n".join(content_parts)

            total_comments += len(ai_comments)

            items.append({
                "url": v.url,
                "title": f"{v.title} ({v.channel})",
                "channel": v.channel,
                "view_count": v.view_count,
                "like_count": v.like_count,
                "content": full_content[:5000],
                "content_length": len(full_content),
                "ai_comments": ai_comments if ai_comments else None,
                "ai_comment_count": len(ai_comments),
                "scraped": True,
            })

        logger.warning(f"[{name}] YouTube: {len(items)} videos, {total_comments} comments total")

        # Run sentiment analysis in ONE batch (same pattern as Reddit)
        all_comments = []
        comment_map = []
        for i, item in enumerate(items):
            if item.get("ai_comments"):
                for j, c in enumerate(item["ai_comments"]):
                    all_comments.append(c)
                    comment_map.append((i, j))

        if all_comments:
            logger.warning(f"[{name}] Running sentiment on {len(all_comments)} YouTube comments (1 batch)")
            analyzed = await _run_batch_sentiment(all_comments, name, "YouTube")
            if analyzed:
                for idx, (i, j) in enumerate(comment_map):
                    if idx < len(analyzed):
                        items[i]["ai_comments"][j] = analyzed[idx]

        return SourceResult(
            source=name, source_type="youtube", status="ok" if items else "partial",
            result_count=len(items), credits_used=0, items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(
            source=name, source_type="youtube", status="error",
            error=str(e), duration_ms=int((time.time() - start) * 1000),
        )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# L1: Official manufacturer communication scraper
# ---------------------------------------------------------------------------

async def _scrape_official_source(
    brand: str, model: str, source: dict,
    alimentazione: str | None = None, cilindrata: float | None = None,
) -> SourceResult:
    """L1 strategy: gather official manufacturer communication.

    Layered approach:
    A) Direct brand website — product pages, pricing, promotions (Firecrawl)
    B) Direct brand YouTube channel — videos on the model
    C) Consolidated research via Perplexity Sonar Pro — citations from dealer
       network, listini, spec sheets that report official data. Always runs;
       crucial for brands with poor indexable websites (EVO, DR, etc.).
    """
    start = time.time()
    name = source.get("name", "Unknown")
    official = get_official_urls(brand)

    all_items = []
    total_credits = 0

    # A) Scrape official website (if brand has one configured)
    if official and official.get("website"):
        web_items, web_credits = await _scrape_official_website(
            brand, model, official["website"], name
        )
        all_items.extend(web_items)
        total_credits += web_credits

    # B) Scrape official YouTube channel (if configured)
    if official and official.get("youtube_channel_id"):
        yt_items = await _scrape_official_youtube(
            brand, model, official["youtube_channel_id"], name
        )
        all_items.extend(yt_items)

    # C) Perplexity Sonar Pro — always runs, consolidates official data across
    # dealer network, listini, schede tecniche. Key fallback for low-presence brands.
    pplx_items = await _scrape_official_perplexity(brand, model, name, alimentazione, cilindrata)
    all_items.extend(pplx_items)

    # D) L1 Driver analysis — ONE consolidated positioning JSON across ALL sources
    # (direct scrapes + Perplexity answer). Output: 9-driver ranking + quotes + tagline.
    # Replaces the legacy technical-specs aggregate (see L1_LEGACY_AGGREGATE flag below).
    driver_items = [it for it in all_items if not it.get("perplexity_citation")]
    driver_result = None
    if driver_items:
        from src.content_cleaner import analyze_communication_drivers
        driver_result = await analyze_communication_drivers(driver_items, brand, model)

    # Legacy tech-specs aggregate — DISABLED for Phase A pilot (Paolo's feedback: specs
    # are already sourced from Quattroruote). Kept here, gated by env flag, so we can
    # reactivate quickly without code archaeology if the scope changes.
    if os.environ.get("L1_LEGACY_AGGREGATE") == "1" and driver_items:
        from src.content_cleaner import aggregate_official_content
        legacy_aggregate = await aggregate_official_content(
            driver_items, brand, model, alimentazione, cilindrata,
        )
    else:
        legacy_aggregate = None

    # Attach driver analysis to the consolidated Perplexity item (if present),
    # otherwise synthesize one so the UI always has a featured card.
    if driver_result:
        target = next((it for it in all_items if it.get("perplexity_consolidated")), None)
        if target is None:
            target = {
                "url": "driver-analysis://l1-consolidated",
                "title": f"{brand} {model} — Driver comunicativi ufficiali",
                "content": "",
                "source_type": "official",
                "scraped": True,
                "perplexity_consolidated": True,
                "perplexity_citations": [],
            }
            all_items.insert(0, target)

        driver_result["fonte_consolidata"] = True
        driver_result["fonti_citate"] = target.get("perplexity_citations", [])
        # Re-use the existing `ai_official_info` JSONB slot (no DB migration needed).
        # The UI distinguishes by the `is_driver_analysis` flag inside the payload.
        target["ai_official_info"] = driver_result

    if legacy_aggregate:
        target = next((it for it in all_items if it.get("perplexity_consolidated")), None)
        if target is not None:
            legacy_aggregate["fonte_consolidata"] = True
            legacy_aggregate["fonti_citate"] = target.get("perplexity_citations", [])
            target["ai_official_info"] = legacy_aggregate
            motori = legacy_aggregate.get("motorizzazioni") or []
            versioni = []
            for m in motori:
                if not isinstance(m, dict):
                    continue
                a = m.get("alimentazione")
                c = m.get("cilindrata_l")
                if a or c is not None:
                    versioni.append({
                        "alimentazione": a,
                        "cilindrata": c,
                        "descrizione": m.get("nome_commerciale"),
                    })
            if versioni:
                target["motore_info"] = {"versioni": versioni}
                for it in all_items:
                    if it.get("perplexity_citation"):
                        it["motore_info"] = target["motore_info"]

    return SourceResult(
        source=name, source_type="official", status="ok" if all_items else "partial",
        result_count=len(all_items), credits_used=total_credits, items=all_items,
        error=None if all_items else "No official content found",
        duration_ms=int((time.time() - start) * 1000),
    )


async def _scrape_official_perplexity(
    brand: str, model: str, source_name: str,
    alimentazione: str | None = None, cilindrata: float | None = None,
) -> list[dict]:
    """L1 research via Perplexity Sonar Pro — consolidated official communication.

    One focused query, narrowed by alimentazione/cilindrata if provided.
    Returns 1 synthesized item with full answer as content + citations listed
    in the item's metadata. Consumed downstream by analyze_official_content to
    extract structured official_info.
    """
    from src.perplexity_client import PerplexityClient

    client = PerplexityClient(model="sonar-pro")
    if not client.api_key:
        logger.warning(f"[{source_name}] PERPLEXITY_API_KEY not set, skipping L1 Perplexity")
        return []

    # Build focused user query
    from src.motore import ALIMENTAZIONE_LABEL_IT
    variant_parts = []
    if cilindrata is not None:
        variant_parts.append(f"{cilindrata:.1f}".rstrip("0").rstrip("."))
    if alimentazione:
        variant_parts.append(ALIMENTAZIONE_LABEL_IT.get(alimentazione, alimentazione))
    variant_suffix = f" {' '.join(variant_parts)}" if variant_parts else ""

    # Build a domain hint for the system prompt — helps Perplexity stay on-brand
    from src.auto_brands import get_official_domains, is_official_domain
    brand_domains = get_official_domains(brand)
    domain_hint = ", ".join(brand_domains) if brand_domains else "sito web ufficiale del costruttore"

    system = (
        "Sei un analista della comunicazione ufficiale di brand automotive italiani. "
        f"Rispondi ESCLUSIVAMENTE con contenuti provenienti dai CANALI UFFICIALI del brand {brand} "
        f"(sito web ufficiale: {domain_hint}; comunicati stampa del brand; canale YouTube e social "
        "ufficiali del costruttore; materiale pubblicitario del brand). "
        "NON includere, NON citare, NON considerare: rete dealer/concessionari/rivenditori, "
        "portali multi-brand (es. automoto.it, automobile.it, tuo-auto.it, autoscout24, subito.it), "
        "riviste di settore (Quattroruote, AlVolante, Motor1, AutoExpress), blog/forum indipendenti, "
        "listini di terzi. "
        "Il tuo scopo è descrivere COME IL BRAND COMUNICA il modello sui suoi canali, non raccogliere "
        "dati di mercato. Se un'informazione non è presente sui canali ufficiali, dichiaralo esplicitamente."
    )

    user = (
        f"Analizza la comunicazione UFFICIALE di {brand} per il modello {brand} {model}{variant_suffix}. "
        "Riporta ESCLUSIVAMENTE ciò che il brand comunica sui propri canali proprietari "
        "(sito, comunicati stampa, social ufficiali, advertising del brand).\n\n"
        "Concentrati sul POSIZIONAMENTO e sul MESSAGGIO:\n"
        "- Claim, payoff e tagline ufficiali\n"
        "- Su quali driver il brand insiste: design/linea, prezzo/accessibilità, tecnologia/innovazione, "
        "sicurezza/ADAS, consumi/sostenibilità, prestazioni/piacere di guida, spazio/praticità, "
        "heritage/identità, lifestyle/emozione\n"
        "- Target comunicato (a chi si rivolge il brand)\n"
        "- Tono, atmosfera, narrazione\n"
        "- Key selling points che il brand enfatizza\n\n"
        "NON concentrarti su: prezzi di mercato, promozioni di dealer, recensioni di riviste, "
        "opinioni di giornalisti, commenti utente, schede tecniche redazionali. "
        "Cita solo fonti brand-owned."
    )

    resp = await client.ask(query=user, system_prompt=system, recency="year")

    if resp.error:
        logger.warning(f"[{source_name}] Perplexity L1 error: {resp.error}")
        return []

    if not resp.answer:
        logger.warning(f"[{source_name}] Perplexity L1 returned empty answer")
        return []

    # Post-filter citations: keep ONLY brand-owned domains (Paolo's Phase A perimeter).
    # Dealer chains, multi-brand portals, trade magazines get stripped here even if the
    # model ignored the system prompt — defense in depth.
    all_citations = list(resp.citations)
    kept_citations = [c for c in all_citations if is_official_domain(c.url, brand)]
    dropped_count = len(all_citations) - len(kept_citations)
    if dropped_count > 0:
        dropped_hosts = sorted({(c.url or "").split("/")[2] for c in all_citations if not is_official_domain(c.url, brand)})
        logger.warning(
            f"[{source_name}] Perplexity L1: filtered {dropped_count}/{len(all_citations)} "
            f"non-official citations. Dropped hosts: {dropped_hosts[:10]}"
        )

    citations_list = [
        {"url": c.url, "title": c.title, "snippet": c.snippet}
        for c in kept_citations
    ]
    # Use top kept citation as canonical URL, fallback to brand website or marker
    if kept_citations:
        top_url = kept_citations[0].url
    elif brand_domains:
        top_url = f"https://{brand_domains[0]}"
    else:
        top_url = "perplexity://consolidated"
    title_suffix = f" ({variant_suffix.strip()})" if variant_suffix else ""

    # Embed (filtered) citations inline at the end of content so Claude sees them during extraction
    citations_text = ""
    if citations_list:
        citations_text = "\n\n--- Fonti ufficiali citate ---\n" + "\n".join(
            f"- {c['title'] or c['url']}: {c['url']}" for c in citations_list
        )

    logger.warning(
        f"[{source_name}] Perplexity L1 returned {len(resp.answer)} chars, "
        f"{len(citations_list)} official citations (dropped {dropped_count})"
    )

    items: list[dict] = []

    # 1) Consolidated synthesis item — feeds Claude analysis for structured fields
    items.append({
        "url": top_url,
        "title": f"{brand} {model}{title_suffix} — Sintesi ufficiale consolidata",
        "content": (resp.answer + citations_text)[:15000],
        "content_length": len(resp.answer) + len(citations_text),
        "source_type": "official",
        "scraped": True,
        "perplexity_citations": citations_list,
        "perplexity_consolidated": True,
    })

    # 2) One lightweight item per cited source — so the user sees N fonti as in Perplexity UI
    for c in citations_list:
        items.append({
            "url": c["url"],
            "title": c["title"] or c["url"],
            "content": c["snippet"] or "",
            "content_length": len(c["snippet"] or ""),
            "source_type": "official",
            "scraped": False,  # only the snippet, not a full scrape
            "perplexity_citation": True,
        })

    return items


def _model_url_variants(model: str, registry_variants: list[str]) -> list[str]:
    """Generate URL-friendly permutations of a model name for substring matching.

    Example: "DR 3.0" → {"dr 3.0", "dr-3.0", "dr3.0", "dr 30", "dr-30", "dr30",
                        "dr 3-0", "dr-3-0", "dr3-0"}.
    Covers common URL slug conventions: dots→hyphens, spaces→hyphens/stripped.
    """
    seen: set[str] = set()
    def _add(s: str) -> None:
        s = s.strip().lower()
        if s and s not in seen:
            seen.add(s)

    bases = [model] + list(registry_variants)
    for raw in bases:
        if not raw:
            continue
        r = raw.strip().lower()
        _add(r)
        _add(r.replace(" ", "-"))
        _add(r.replace(" ", ""))
        _add(r.replace(".", "-"))
        _add(r.replace(".", ""))
        _add(r.replace(".", "-").replace(" ", "-"))
        _add(r.replace(".", "").replace(" ", "-"))
        _add(r.replace(".", "").replace(" ", ""))
    return list(seen)


JUNK_URL_SEGMENTS = (
    "/thank-you", "/thankyou", "/grazie", "/success",
    "/login", "/signin", "/sign-in", "/register", "/registrati",
    "/cookie", "/privacy", "/disclaimer", "/cond-gen",
    "/newsletter", "/rss", "/sitemap", "/404", "/error",
    "/appointment-confirm", "/booking-confirm", "/confirm",
    "/account", "/profile", "/my-area",
)


def _is_junk_url(url: str) -> bool:
    """Filter out obvious non-content pages (thank-you, login, cookie policies, etc.)."""
    u = (url or "").lower()
    return any(seg in u for seg in JUNK_URL_SEGMENTS)


async def _scrape_official_website(
    brand: str, model: str, website_url: str, source_name: str
) -> tuple[list[dict], int]:
    """Scrape manufacturer's official website for model-specific pages.

    Strategy: map() to discover URLs → filter by model URL variants → scrape top pages.
    Augment with search() if map yields few results (common for small brands).

    Returns (items, credits_used).
    """
    try:
        client = FirecrawlClient()
    except ValueError as e:
        logger.error(f"[{source_name}] Firecrawl not available: {e}")
        return [], 0

    model_context = build_model_context(brand, model)
    # Generate URL-friendly variants to catch /dr-3-0, /dr30, /dr3.0, etc.
    variant_terms = _model_url_variants(model, model_context.get("model_variants", []))

    total_credits = 0
    items = []

    # Step 1: Discover URLs on the brand site using map()
    logger.warning(f"[{source_name}] MAP: {website_url} search='{model}'")
    map_resp = client.map(website_url, search=model, limit=20)
    total_credits += map_resp.credits_used

    relevant_urls = []
    seen_urls: set[str] = set()
    if not map_resp.error and map_resp.urls:
        for u in map_resp.urls:
            url = u.get("url", "")
            if not url or url in seen_urls or _is_junk_url(url):
                continue
            title = u.get("title", "")
            desc = u.get("description", "")
            combined = f"{url} {title} {desc}".lower()

            # Require a model variant match in the combined text
            if any(term in combined for term in variant_terms):
                relevant_urls.append(u)
                seen_urls.add(url)

    # Augment with search() when map yields < 3 relevant URLs (small/JS-heavy brands)
    if len(relevant_urls) < 3:
        domain = website_url.replace("https://", "").replace("http://", "").rstrip("/")
        search_query = f"site:{domain} {brand} {model}"
        logger.warning(
            f"[{source_name}] Only {len(relevant_urls)} from MAP, AUGMENT SEARCH: '{search_query}'"
        )
        search_resp = client.search(search_query, limit=10, recent_only=False)
        total_credits += search_resp.credits_used
        if not search_resp.error:
            for r in search_resp.results:
                if not r.url or r.url in seen_urls or _is_junk_url(r.url):
                    continue
                relevant_urls.append({
                    "url": r.url, "title": r.title, "description": r.content[:200],
                })
                seen_urls.add(r.url)

    if not relevant_urls:
        logger.warning(f"[{source_name}] No relevant official pages found for {brand} {model}")
        return [], total_credits

    logger.warning(
        f"[{source_name}] Found {len(relevant_urls)} relevant official pages "
        f"(variants={variant_terms[:6]}...)"
    )

    # Step 2: scrape the PRIMARY page first so we can discover trim slugs from its content.
    MAX_PAGES = 15
    scraped_urls: set[str] = set()

    def _scrape_one(u: dict) -> int:
        """Scrape a single URL, append to items, return credits used. Tolerant to failures."""
        page_url = u.get("url", "")
        if not page_url or page_url in scraped_urls:
            return 0
        scraped_urls.add(page_url)
        logger.warning(f"[{source_name}] SCRAPE: {page_url}")
        resp = client.scrape(page_url)
        credits = resp.credits_used
        if resp.error or not resp.results:
            logger.warning(f"[{source_name}] Scrape error: {resp.error}")
            return credits
        content = resp.results[0].content
        title = resp.results[0].title
        if not content or len(content) < 100:
            return credits
        items.append({
            "url": page_url,
            "title": title or u.get("title", ""),
            "content": content[:10000],
            "content_length": len(content),
            "source_type": "official",
            "scraped": True,
        })
        return credits

    primary = relevant_urls[0]
    total_credits += _scrape_one(primary)

    # Step 3: AI discovers trim slugs from the primary page content
    primary_content = items[0]["content"] if items else ""
    trim_slugs: list[str] = []
    if primary_content:
        try:
            from src.content_cleaner import discover_trim_slugs
            trim_slugs = await discover_trim_slugs(primary_content, brand, model)
        except Exception as e:
            logger.warning(f"[{source_name}] Trim slug discovery error: {e}")

    # Step 4: rank remaining URLs with L1-aware boosts, then scrape up to MAX_PAGES total
    SPEC_KEYWORDS = (
        "technical-data", "technical_data", "specifiche-tecniche", "specifiche_tecniche",
        "scheda-tecnica", "scheda_tecnica", "dati-tecnici", "dati_tecnici", "spec-sheet",
    )
    PRICING_KEYWORDS = (
        "configuratore", "configurator", "listino", "prezzi", "allestimenti",
        "versioni", "trim", "equipaggiamenti", "dotazione", "dotazioni",
    )

    def _boost(url_item: dict) -> int:
        url = (url_item.get("url") or "").lower()
        title = (url_item.get("title") or "").lower()
        path_parts = [p for p in url.split("/") if p]
        score = 0
        # Trim slug in any path segment: +30 per distinct match
        if trim_slugs:
            for seg in path_parts:
                for slug in trim_slugs:
                    if slug and slug in seg:
                        score += 30
                        break
        # Spec / tech pages: +25
        if any(kw in url for kw in SPEC_KEYWORDS):
            score += 25
        # Pricing / configurator / trim listing: +20
        if any(kw in url for kw in PRICING_KEYWORDS):
            score += 20
        # PDF brochure/spec sheet: +15
        if url.endswith(".pdf") or ".pdf" in url:
            score += 15
        return score

    # Score all remaining URLs (skip the primary we already scraped)
    candidates = [u for u in relevant_urls[1:] if u.get("url") not in scraped_urls]
    for u in candidates:
        u["_l1_boost"] = _boost(u)
    # Sort: boost desc, original order preserved as tiebreaker via stable sort
    candidates.sort(key=lambda u: u.get("_l1_boost", 0), reverse=True)

    slots_left = MAX_PAGES - len(scraped_urls)
    for u in candidates[:slots_left]:
        total_credits += _scrape_one(u)

    logger.warning(
        f"[{source_name}] Scraped {len(items)} official pages "
        f"(trim slugs found: {trim_slugs or 'none'})"
    )

    return items, total_credits


async def _scrape_official_youtube(
    brand: str, model: str, channel_id: str, source_name: str
) -> list[dict]:
    """Scrape official brand YouTube channel for model-specific videos.

    Uses channelId filter to only get videos from the brand's official channel.
    NO comments (L1 = official communication only, user comments are L3).
    """
    from src.youtube_client import YouTubeClient
    from datetime import datetime, timedelta

    client = YouTubeClient()
    if not client.api_key:
        logger.warning(f"[{source_name}] YouTube API key not set, skipping official YouTube")
        return []

    try:
        # Search for model in official channel (last 18 months)
        published_after = (datetime.utcnow() - timedelta(days=548)).strftime("%Y-%m-%dT00:00:00Z")
        query = f"{brand} {model}"
        logger.warning(f"[{source_name}] YouTube official channel search: '{query}' (channel={channel_id})")

        results = await client.search_videos(
            query, max_results=5,
            published_after=published_after,
            channel_id=channel_id,
        )

        if not results:
            logger.warning(f"[{source_name}] No official YouTube videos found")
            await client.close()
            return []

        # Get video details (views, likes)
        video_ids = [
            r["id"]["videoId"] for r in results
            if r.get("id", {}).get("videoId")
        ]

        details = {}
        if video_ids:
            details = await client.get_video_details(video_ids)

        items = []
        for r in results:
            vid_id = r.get("id", {}).get("videoId", "")
            snippet = r.get("snippet", {})
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            channel = snippet.get("channelTitle", "")

            # Check relevance — title or description should mention the model
            model_context = build_model_context(brand, model)
            model_lower = model.lower()
            variant_terms = [model_lower] + [v.lower() for v in model_context.get("model_variants", [])]
            combined = f"{title} {description}".lower()

            if not any(term in combined for term in variant_terms):
                continue

            vid_details = details.get(vid_id, {})
            stats = vid_details.get("statistics", {})

            items.append({
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "title": title,
                "content": description[:5000],
                "content_length": len(description),
                "source_type": "official",
                "scraped": True,
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "channel": channel,
            })

        logger.warning(f"[{source_name}] Found {len(items)} relevant official YouTube videos")
        return items

    except Exception as e:
        logger.error(f"[{source_name}] Official YouTube error: {e}")
        return []
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Perplexity (L2 media coverage via Sonar — synthesized answers with citations)
# ---------------------------------------------------------------------------

# Each tuple is (query_suffix, title_label). Multiple angles to get broader coverage.
PERPLEXITY_QUERIES = [
    ("recensioni prova su strada opinioni giornalisti", "Rassegna recensioni"),
    ("prezzo listino allestimenti versioni italia", "Prezzo e allestimenti"),
    ("problemi difetti critiche punti deboli", "Criticita e punti deboli"),
]

PERPLEXITY_SYSTEM_PROMPT = (
    "Sei un analista del mercato automotive italiano. Rispondi in italiano, "
    "sintetico ma con fatti concreti. Cita fonti italiane (testate automotive, "
    "siti ufficiali, forum) quando disponibili. Se non trovi informazioni "
    "affidabili dillo esplicitamente."
)


async def _scrape_perplexity_source(brand: str, model: str, source: dict) -> SourceResult:
    """Run 3 Sonar queries (reviews / pricing / issues) in parallel for this brand+model.

    Each query becomes one item with:
    - content: full synthesized answer from Perplexity
    - summary: first 2-3 sentences (generated by Perplexity itself)
    - ai_comments: list of citation URLs rendered as fake 'comments' so the
      existing frontend can display them without schema changes.
    """
    start = time.time()
    name = source.get("name", "Perplexity")
    search_term = f"{brand} {model}".strip() or brand

    client = PerplexityClient()
    if not client.api_key:
        return SourceResult(
            source=name, source_type="perplexity", status="error",
            error="PERPLEXITY_API_KEY not set",
            duration_ms=int((time.time() - start) * 1000),
        )

    # Fire all queries in parallel
    async def _run(suffix: str, label: str) -> tuple[str, str, "PerplexityResponse"]:
        query = f"{search_term} {suffix}".strip()
        logger.warning(f"[{name}] SONAR: '{query}'")
        resp = await client.ask(query, system_prompt=PERPLEXITY_SYSTEM_PROMPT)
        return label, query, resp

    tasks = [_run(suffix, label) for suffix, label in PERPLEXITY_QUERIES]
    raw = await asyncio.gather(*tasks, return_exceptions=True)

    items = []
    errors = []
    for entry in raw:
        if isinstance(entry, Exception):
            errors.append(str(entry))
            continue
        label, query, resp = entry
        if resp.error:
            logger.warning(f"[{name}] Query '{query}' failed: {resp.error}")
            errors.append(resp.error)
            continue
        if not resp.answer:
            continue

        citations = resp.citations or []
        # Render citations as "fake comments" so the existing frontend can show
        # them under the item without any schema/UI change.
        ai_comments = [
            {
                "author": (c.title or c.url)[:120],
                "text": (c.snippet or c.url),
                "sentiment": "neutro",
                "topics": ["perplexity-citation"],
                "url": c.url,
            }
            for c in citations
        ]

        # Build a compact summary from the first paragraph of the answer
        first_para = resp.answer.split("\n\n", 1)[0].strip()
        summary = first_para if len(first_para) <= 400 else first_para[:397] + "..."

        # Title shows which angle this query covered (e.g. "Rassegna recensioni — Fiat Grande Panda")
        title = f"{label} \u2014 {search_term}"

        items.append({
            "url": citations[0].url if citations else "",
            "title": title,
            "summary": summary,
            "content": resp.answer[:10000],
            "content_length": len(resp.answer),
            "ai_comments": ai_comments or None,
            "ai_comment_count": len(ai_comments),
            "scraped": True,
            "relevance_score": 100,
        })

    if not items:
        return SourceResult(
            source=name, source_type="perplexity", status="error",
            error=errors[0] if errors else "No Perplexity results",
            duration_ms=int((time.time() - start) * 1000),
        )

    return SourceResult(
        source=name, source_type="perplexity",
        status="ok" if not errors else "partial",
        result_count=len(items),
        credits_used=0,  # Perplexity billed separately from Firecrawl credits
        items=items,
        error=("; ".join(errors)[:500]) if errors else None,
        duration_ms=int((time.time() - start) * 1000),
    )
