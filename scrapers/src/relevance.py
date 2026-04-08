"""Relevance scoring for search results — filters off-topic URLs before scraping.

Pure string-based scoring, no API calls. Runs on search result metadata
(title, URL, snippet) to decide whether a URL is worth scraping.
"""

import re
import logging
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Minimum score to proceed to scraping
RELEVANCE_THRESHOLD = 30

# URL patterns that indicate real discussion threads vs. index pages
FORUM_THREAD_PATTERNS = {
    "forum.quattroruote.it": {
        "good": [r"/threads?\."],
        "bad": [r"/forums/", r"/categories/", r"^/$"],
    },
    "autopareri.com": {
        "good": [r"/topic/"],
        "bad": [r"/forum/\d+-[^/]+/?$"],
    },
    "clubalfa.it": {
        "good": [r"/threads?/", r"/topic/"],
        "bad": [r"/forums?/$"],
    },
}

# Generic patterns for unknown forums
GENERIC_THREAD_PATTERNS = {
    "good": [r"/threads?[./]", r"/topic/", r"/discussion/", r"/post/"],
    "bad": [r"/forums?/?$", r"/categories?/?$", r"/members/", r"/login", r"/register", r"/tags?/"],
}

# Current year for recency scoring
CURRENT_YEAR = datetime.now().year
RECENT_YEARS = {str(y) for y in range(CURRENT_YEAR - 1, CURRENT_YEAR + 1)}  # last year + this year
OLD_YEARS = {str(y) for y in range(2000, CURRENT_YEAR - 3)}  # anything older than 3 years

# Classifieds / listing domains to penalize
LISTING_SIGNALS = [
    "autoscout24", "subito.it", "automobile.it", "annunci",
    "usato", "vendita", "prezzo-", "/listino/",
]


def score_result(
    title: str,
    url: str,
    snippet: str,
    brand: str,
    model: str,
    model_context: dict,
) -> tuple[int, list[str]]:
    """Score a search result for relevance to the target brand+model.

    Returns:
        (score, reasons) — score is an int, reasons is a list of human-readable strings
        explaining the scoring breakdown.
    """
    score = 0
    reasons = []

    title_lower = (title or "").lower()
    url_lower = (url or "").lower()
    snippet_lower = (snippet or "").lower()
    brand_lower = brand.lower()
    model_lower = model.lower()

    # Build match terms
    brand_terms = [brand_lower] + [a.lower() for a in model_context.get("brand_aliases", [])]
    model_terms = [model_lower] + [v.lower() for v in model_context.get("model_variants", [])]
    exclude_models = [m.lower() for m in model_context.get("exclude_models", [])]

    # === TITLE MATCHING (0-40 pts) ===
    title_has_brand = any(t in title_lower for t in brand_terms)
    title_has_model = any(t in title_lower for t in model_terms)

    if title_has_brand and title_has_model:
        score += 40
        reasons.append("+40 title: brand+model match")
    elif title_has_model:
        score += 30
        reasons.append("+30 title: model match")
    elif title_has_brand:
        score += 15
        reasons.append("+15 title: brand only")

    # === URL PATTERN MATCHING (0-20 pts) ===
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    # Check forum-specific patterns
    patterns = FORUM_THREAD_PATTERNS.get(domain, GENERIC_THREAD_PATTERNS)

    for p in patterns.get("good", []):
        if re.search(p, path):
            score += 15
            reasons.append(f"+15 url: thread pattern '{p}'")
            break

    for p in patterns.get("bad", []):
        if re.search(p, path):
            score -= 20
            reasons.append(f"-20 url: index/category pattern '{p}'")
            break

    # Model name in URL slug is a good sign
    if model_lower.replace(" ", "-") in path or model_lower.replace(" ", "") in path:
        score += 5
        reasons.append("+5 url: model in path")

    # === SNIPPET MATCHING (0-25 pts) ===
    snippet_has_brand = any(t in snippet_lower for t in brand_terms)
    snippet_has_model = any(t in snippet_lower for t in model_terms)

    if snippet_has_brand and snippet_has_model:
        score += 25
        reasons.append("+25 snippet: brand+model match")
    elif snippet_has_model:
        score += 15
        reasons.append("+15 snippet: model match")
    elif snippet_has_brand:
        score += 5
        reasons.append("+5 snippet: brand only")

    # === NEGATIVE SIGNALS ===

    # Different model from same brand in title (strong negative)
    all_text = f"{title_lower} {snippet_lower}"
    for exclude in exclude_models:
        exclude_low = exclude.lower()
        # Only penalize if the excluded model appears but the target model does NOT
        if exclude_low in all_text and not any(t in all_text for t in model_terms):
            score -= 30
            reasons.append(f"-30 wrong model: '{exclude}' found, target '{model}' absent")
            break

    # Classifieds / listing pages
    for signal in LISTING_SIGNALS:
        if signal in url_lower or signal in title_lower:
            score -= 15
            reasons.append(f"-15 listing/classifieds signal: '{signal}'")
            break

    # === RECENCY SIGNALS (heavily weighted — recent content is critical) ===

    # Check for years in title/snippet
    found_recent = any(y in f"{title_lower} {snippet_lower}" for y in RECENT_YEARS)
    found_old = [y for y in OLD_YEARS if y in f"{title_lower} {snippet_lower}"]

    if found_recent:
        score += 25
        reasons.append("+25 recency: recent year found")
    elif found_old:
        oldest = min(int(y) for y in found_old)
        age = CURRENT_YEAR - oldest
        penalty = min(age * 5, 40)  # -5 per year, max -40
        score -= penalty
        reasons.append(f"-{penalty} recency: year {oldest} found ({age}y old)")

    # Forum topic ID heuristic — heavily weighted
    # IPS (autopareri): /topic/2633 (2006) → /topic/83225 (2025)
    # XenForo (QR): .1334 (old) → .147540 (2024)
    topic_match = re.search(r'/topic/(\d+)', path) or re.search(r'\.(\d{3,6})/?$', path)
    if topic_match:
        topic_id = int(topic_match.group(1))
        if topic_id < 30000:
            score -= 35
            reasons.append(f"-35 recency: topic ID {topic_id} (very old)")
        elif topic_id < 50000:
            score -= 20
            reasons.append(f"-20 recency: topic ID {topic_id} (old)")
        elif topic_id < 65000:
            score -= 10
            reasons.append(f"-10 recency: topic ID {topic_id} (somewhat old)")
        elif topic_id > 78000:
            score += 20
            reasons.append(f"+20 recency: topic ID {topic_id} (recent)")
        elif topic_id > 65000:
            score += 5
            reasons.append(f"+5 recency: topic ID {topic_id} (moderate)")

    return score, reasons


def filter_and_rank(
    found_urls: dict[str, dict],
    brand: str,
    model: str,
    model_context: dict,
    max_results: int = 3,
) -> list[tuple[str, dict]]:
    """Score, filter, and rank search results.

    Args:
        found_urls: {url: {"title": ..., "snippet": ...}} dict from search step
        brand, model: target car
        model_context: from build_model_context()
        max_results: max URLs to return for scraping

    Returns:
        List of (url, meta_with_score) tuples, sorted by score descending,
        filtered by RELEVANCE_THRESHOLD.
    """
    scored = []

    for url, meta in found_urls.items():
        points, reasons = score_result(
            title=meta.get("title", ""),
            url=url,
            snippet=meta.get("snippet", ""),
            brand=brand,
            model=model,
            model_context=model_context,
        )

        meta_with_score = {**meta, "score": points, "reasons": reasons}

        if points >= RELEVANCE_THRESHOLD:
            scored.append((url, meta_with_score))
            logger.warning(f"  [PASS] score={points:+d} {url}")
            for r in reasons:
                logger.warning(f"         {r}")
        else:
            logger.warning(f"  [SKIP] score={points:+d} {url}")
            for r in reasons:
                logger.warning(f"         {r}")

    # Sort by score descending
    scored.sort(key=lambda x: x[1]["score"], reverse=True)

    return scored[:max_results]
