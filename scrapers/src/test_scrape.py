"""Scraping test orchestrator — 3-step: search → scrape → clean with AI."""

import asyncio
import time
import logging
from dataclasses import dataclass, field, asdict

from src.firecrawl_client import FirecrawlClient
from src.youtube_client import YouTubeClient
from src.reddit_client import RedditClient
from src.content_cleaner import clean_and_extract

logger = logging.getLogger(__name__)

# Query templates per source type
QUERY_TEMPLATES = {
    "news": [
        "site:{domain} {search_term}",
        "site:{domain} {search_term} recensione",
    ],
    "forum": [
        "site:{domain} {search_term} opinioni",
        "site:{domain} {search_term} problemi difetti",
        "site:{domain} {search_term} proprietari esperienza",
    ],
    "social": [
        "site:{domain} {search_term}",
        "{source_name} {search_term} opinioni commenti",
    ],
}

# Max pages to scrape per source (controls credit usage)
MAX_SCRAPE_PER_SOURCE = 3


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
    """2-step web scraping: search for URLs, then scrape full content."""
    start = time.time()
    name = source.get("name", "Unknown")
    url = source.get("url", "")
    source_type = source.get("source_type", "news")
    domain = url.replace("https://", "").replace("http://", "").rstrip("/")
    search_term = f"{brand} {model}".strip()

    try:
        client = FirecrawlClient()
    except ValueError as e:
        return SourceResult(source=name, source_type=source_type, status="error", error=str(e))

    # --- STEP 1: Search for relevant URLs ---
    templates = QUERY_TEMPLATES.get(source_type, QUERY_TEMPLATES["news"])
    found_urls = {}  # url -> {title, snippet}
    search_credits = 0

    for template in templates:
        query = template.format(
            domain=domain, search_term=search_term, source_name=name,
        )
        resp = client.search(query, limit=5)
        search_credits += resp.credits_used

        if resp.error:
            logger.warning(f"[{name}] Search error for '{query}': {resp.error}")
            continue

        for r in resp.results:
            if r.url and r.url not in found_urls:
                found_urls[r.url] = {"title": r.title or "", "snippet": (r.content or "")[:300]}

    if not found_urls:
        return SourceResult(
            source=name, source_type=source_type, status="partial",
            credits_used=search_credits, error="No URLs found in search",
            duration_ms=int((time.time() - start) * 1000),
        )

    logger.warning(f"[{name}] STEP 1 done: found {len(found_urls)} URLs, scraping top {MAX_SCRAPE_PER_SOURCE}")
    for u in list(found_urls.keys())[:5]:
        logger.warning(f"  → {u}")

    # --- STEP 2: Scrape full content of top URLs ---
    urls_to_scrape = list(found_urls.keys())[:MAX_SCRAPE_PER_SOURCE]
    scrape_credits = 0
    items = []

    for page_url in urls_to_scrape:
        meta = found_urls[page_url]
        logger.warning(f"[{name}] STEP 2: scraping {page_url}")
        resp = client.scrape(page_url)
        scrape_credits += resp.credits_used

        if resp.error:
            logger.warning(f"[{name}] Scrape error for {page_url}: {resp.error}")
            items.append({
                "url": page_url,
                "title": meta["title"],
                "content": meta["snippet"],
                "content_length": len(meta["snippet"]),
                "scraped": False,
            })
            continue

        full_content = ""
        if resp.results:
            full_content = resp.results[0].content or ""
        logger.warning(f"[{name}] Scraped {page_url}: {len(full_content)} chars")

        # Use full content if we got it, otherwise fall back to snippet
        content = full_content if len(full_content) > len(meta["snippet"]) else meta["snippet"]

        items.append({
            "url": page_url,
            "title": resp.results[0].title if resp.results else meta["title"],
            "content": content[:5000],  # cap at 5k chars for display
            "content_length": len(full_content),
            "scraped": True,
        })

    # --- STEP 3: Clean with Claude AI ---
    logger.warning(f"[{name}] STEP 3: cleaning {len(items)} pages with Claude AI")
    for item in items:
        if item.get("scraped") and len(item.get("content", "")) > 200:
            cleaned = await clean_and_extract(item["content"], name, item["url"])
            if cleaned.get("cleaned") and cleaned.get("comments"):
                item["ai_comments"] = cleaned["comments"]
                item["ai_comment_count"] = cleaned["comment_count"]
                logger.warning(f"[{name}] AI extracted {cleaned['comment_count']} comments from {item['url']}")
            elif cleaned.get("error"):
                logger.warning(f"[{name}] AI cleaning error: {cleaned['error']}")

    total_credits = search_credits + scrape_credits
    duration = int((time.time() - start) * 1000)

    return SourceResult(
        source=name,
        source_type=source_type,
        status="ok" if items else "partial",
        result_count=len(items),
        credits_used=total_credits,
        items=items,
        duration_ms=duration,
    )


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
