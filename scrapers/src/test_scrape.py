"""Scraping test orchestrator — 3-step: search → scrape → clean with AI."""

import asyncio
import re
import time
import logging
from dataclasses import dataclass, field, asdict

from src.firecrawl_client import FirecrawlClient
from src.youtube_client import YouTubeClient
from src.reddit_client import RedditClient
from src.content_cleaner import clean_and_extract
from src.auto_brands import build_model_context
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

# Max threads to scrape per source
MAX_SCRAPE_PER_SOURCE = 4
# Max extra pages to scrape for paginated forum threads
MAX_EXTRA_PAGES = 2


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


async def run_test_scrape(brand: str, model: str = "", sources: list[dict] = None) -> dict:
    """Run 2-step scrapers on configured sources."""
    start = time.time()

    if not sources:
        return asdict(TestScrapeResponse(brand=brand, model=model))

    tasks = [_scrape_source(brand, model, source) for source in sources]
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


async def _scrape_source(brand: str, model: str, source: dict) -> SourceResult:
    """Route to the right scraper based on source type and URL."""
    source_type = source.get("source_type", "news")
    url = source.get("url", "")

    if "reddit.com" in url:
        # Try native API first, fallback to Firecrawl search-only
        result = await _scrape_reddit_source(brand, model, source)
        if result.status == "error" and "403" in (result.error or ""):
            logger.warning(f"[{source.get('name')}] Reddit API blocked, using Firecrawl search fallback")
            return await _scrape_reddit_via_firecrawl(brand, model, source)
        return result
    elif source_type == "youtube":
        return await _scrape_youtube_source(brand, model, source)
    else:
        return await _scrape_web_source(brand, model, source)


async def _scrape_web_source(brand: str, model: str, source: dict) -> SourceResult:
    """Route to forum or news strategy based on source type."""
    source_type = source.get("source_type", "news")
    if source_type == "forum":
        return await _scrape_forum_source(brand, model, source)
    else:
        return await _scrape_news_source(brand, model, source)


async def _scrape_forum_source(brand: str, model: str, source: dict) -> SourceResult:
    """Forum strategy: MAP (1 credit) → relevance filter → scrape top N threads."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    search_term = f"{brand} {model}".strip()
    model_context = build_model_context(brand, model)
    search_terms = _build_search_terms(brand, model, model_context)

    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type="forum", status="error", error=str(e))

    # --- STEP 1: MAP the forum to discover thread URLs (1 credit per map call) ---
    found_urls = {}  # url -> {title, snippet}
    total_credits = 0

    for term in search_terms:
        logger.warning(f"[{name}] MAP: discovering URLs for '{term}'")
        map_resp = client.map(url, search=term, limit=20)
        total_credits += map_resp.credits_used

        if map_resp.error:
            logger.warning(f"[{name}] MAP error: {map_resp.error}")
            continue

        logger.warning(f"[{name}] MAP found {len(map_resp.urls)} URLs")

        for entry in map_resp.urls:
            raw_url = entry.get("url", "")
            if raw_url:
                clean_url = _normalize_forum_url(raw_url)
                if clean_url not in found_urls:
                    found_urls[clean_url] = {
                        "title": entry.get("title", ""),
                        "snippet": entry.get("description", "")[:300],
                    }

    # Fallback: if MAP returned nothing, try search
    if not found_urls:
        logger.warning(f"[{name}] MAP returned no URLs, falling back to search")
        for term in search_terms:
            for suffix in ["opinioni", "problemi", "proprietari"]:
                query = f"site:{url.replace('https://', '').replace('http://', '').rstrip('/')} {term} {suffix}"
                resp = client.search(query, limit=5)
                total_credits += resp.credits_used
                if resp.error:
                    continue
                for r in resp.results:
                    if r.url:
                        clean_url = _normalize_forum_url(r.url)
                        if clean_url not in found_urls:
                            found_urls[clean_url] = {"title": r.title or "", "snippet": (r.content or "")[:300]}

    if not found_urls:
        return SourceResult(
            source=name, source_type="forum", status="partial",
            credits_used=total_credits, error="No URLs found via MAP or search",
            duration_ms=int((time.time() - start) * 1000),
        )

    logger.warning(f"[{name}] Total unique URLs: {len(found_urls)}, scoring relevance...")

    # --- STEP 2: Relevance scoring and filtering ---
    ranked = filter_and_rank(found_urls, brand, model, model_context, max_results=MAX_SCRAPE_PER_SOURCE)

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
    ranked = filter_and_rank(found_urls, brand, model, model_context, max_results=MAX_SCRAPE_PER_SOURCE)

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
    """Scrape Reddit via native JSON API (free, no Firecrawl needed)."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")

    # Extract subreddit from URL (e.g. "reddit.com/r/ItalyMotori" -> "ItalyMotori")
    subreddit = "ItalyMotori"  # default
    if "/r/" in url:
        parts = url.split("/r/")
        if len(parts) > 1:
            subreddit = parts[1].strip("/").split("/")[0]

    client = RedditClient()
    try:
        search_term = f"{brand} {model}".strip()
        response = await client.collect(subreddit, search_term, max_posts=5, max_comments=20)

        if response.error:
            return SourceResult(
                source=name, source_type="forum", status="error",
                error=response.error, duration_ms=int((time.time() - start) * 1000),
            )

        items = []
        for post in response.posts:
            # Build content: post text + all comments
            content_parts = []
            if post.selftext:
                content_parts.append(post.selftext)

            if post.comments:
                content_parts.append(f"\n--- {len(post.comments)} commenti ---\n")
                for c in post.comments:
                    content_parts.append(f"[{c.author}] (score: {c.score}): {c.text}")

            full_content = "\n\n".join(content_parts)

            items.append({
                "url": post.url,
                "title": f"{post.title} (score: {post.score}, {post.num_comments} commenti)",
                "content": full_content[:5000],
                "content_length": len(full_content),
                "comments": [f"[{c.author}]: {c.text}" for c in post.comments[:15]],
                "scraped": True,
            })

        return SourceResult(
            source=name,
            source_type="forum",
            status="ok" if items else "partial",
            result_count=len(items),
            credits_used=0,  # Reddit API is free
            items=items,
            duration_ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return SourceResult(
            source=name, source_type="forum", status="error",
            error=str(e), duration_ms=int((time.time() - start) * 1000),
        )
    finally:
        await client.close()


async def _scrape_reddit_via_firecrawl(brand: str, model: str, source: dict) -> SourceResult:
    """Fallback: use Firecrawl search to find Reddit posts (no direct scrape needed)."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    search_term = f"{brand} {model}".strip()

    # Extract subreddit from URL
    subreddit = "ItalyMotori"
    if "/r/" in url:
        parts = url.split("/r/")
        if len(parts) > 1:
            subreddit = parts[1].strip("/").split("/")[0]

    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type="forum", status="error", error=str(e))

    queries = [
        f"site:reddit.com/r/{subreddit} {search_term}",
        f"reddit {subreddit} {search_term} opinioni",
    ]

    all_items = []
    total_credits = 0

    for query in queries:
        resp = client.search(query, limit=5)
        total_credits += resp.credits_used

        if resp.error:
            logger.warning(f"[{name}] Firecrawl Reddit search error: {resp.error}")
            continue

        for r in resp.results:
            if r.url and "reddit.com" in r.url and r.url not in [i["url"] for i in all_items]:
                all_items.append({
                    "url": r.url,
                    "title": r.title or "",
                    "content": (r.content or "")[:3000],
                    "content_length": len(r.content or ""),
                    "scraped": False,
                })

    # Run AI cleaning on the snippets
    if all_items:
        logger.warning(f"[{name}] Cleaning {len(all_items)} Reddit results with Claude AI")
        combined_content = "\n\n---\n\n".join(
            f"Post: {item['title']}\nURL: {item['url']}\n{item['content']}" for item in all_items
        )
        cleaned = await clean_and_extract(combined_content, name, f"reddit.com/r/{subreddit}")
        if cleaned.get("cleaned") and cleaned.get("comments"):
            # Add AI comments to the first item for display
            all_items[0]["ai_comments"] = cleaned["comments"]
            all_items[0]["ai_comment_count"] = cleaned["comment_count"]

    return SourceResult(
        source=name,
        source_type="forum",
        status="ok" if all_items else "partial",
        result_count=len(all_items),
        credits_used=total_credits,
        items=all_items,
        duration_ms=int((time.time() - start) * 1000),
    )


async def _scrape_youtube_source(brand: str, model: str, source: dict) -> SourceResult:
    """Scrape YouTube source with comments."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")

    client = YouTubeClient()
    try:
        search_term = f"{brand} {model}".strip()

        # Extract channel context from URL
        channel_name = ""
        if "youtube.com" in url:
            parts = url.rstrip("/").split("/")
            channel_name = parts[-1].replace("@", "") if parts else ""

        queries = [
            f"{channel_name} {search_term} recensione".strip(),
            f"{channel_name} {search_term} prova".strip(),
        ]

        all_videos = {}
        for query in queries:
            response = await client.collect(query, max_videos=3, max_comments=15)
            if response.error:
                logger.warning(f"[{name}] YouTube error for '{query}': {response.error}")
                continue
            for v in response.videos:
                if v.video_id not in all_videos:
                    all_videos[v.video_id] = v

        if not all_videos:
            return SourceResult(
                source=name, source_type="youtube", status="error",
                error="No YouTube results (API key may not be configured)",
                duration_ms=int((time.time() - start) * 1000),
            )

        items = [{
            "url": v.url,
            "title": v.title,
            "channel": v.channel,
            "view_count": v.view_count,
            "like_count": v.like_count,
            "content": v.description[:500],
            "comments": v.comments[:15],
            "content_length": len(v.description) + sum(len(c) for c in v.comments),
            "scraped": True,
        } for v in all_videos.values()]

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
