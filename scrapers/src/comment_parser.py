"""Parse comments from forum markdown — extracts individual user comments before AI analysis."""

import re
import logging

logger = logging.getLogger(__name__)


def parse_comments(markdown: str, url: str = "") -> list[dict]:
    """Extract individual comments from forum markdown.

    Auto-detects forum type from URL/content and applies the right parser.
    Returns list of {"author": str, "text": str}.
    """
    if not markdown or len(markdown) < 50:
        return []

    # Try XenForo pattern first (forum.quattroruote.it)
    comments = _parse_xenforo(markdown)
    if len(comments) >= 2:
        logger.info(f"Parsed {len(comments)} comments (XenForo pattern) from {url}")
        return comments

    # Try IPS/Invision pattern (autopareri.com)
    comments = _parse_ips(markdown)
    if len(comments) >= 2:
        logger.info(f"Parsed {len(comments)} comments (IPS pattern) from {url}")
        return comments

    # Try generic pattern (any site with usernames + text blocks)
    comments = _parse_generic(markdown)
    if comments:
        logger.info(f"Parsed {len(comments)} comments (generic pattern) from {url}")
        return comments

    logger.info(f"No comment pattern detected for {url}, returning raw content")
    return []


def _parse_xenforo(markdown: str) -> list[dict]:
    """Parse XenForo forum markdown (forum.quattroruote.it).

    Pattern: #### [username](link) followed by comment text until next #### or end.
    """
    # Split on comment headers: #### [username](link)
    pattern = r'####\s+\[([^\]]+)\]\([^)]+\)'
    parts = re.split(pattern, markdown)

    # parts alternates: [before, username1, text1, username2, text2, ...]
    if len(parts) < 3:
        return []

    comments = []
    i = 1  # skip the first part (page header/nav)
    while i < len(parts) - 1:
        author = parts[i].strip()
        raw_text = parts[i + 1] if i + 1 < len(parts) else ""

        # Clean the comment text
        text = _clean_comment_text(raw_text)

        if text and len(text) > 15 and author:
            # Skip staff-only messages and very short noise
            comments.append({"author": author, "text": text})

        i += 2

    return comments


def _parse_ips(markdown: str) -> list[dict]:
    """Parse IPS/Invision Community markdown (autopareri.com).

    Pattern: posts separated by horizontal rules or author blocks with dates.
    """
    # IPS pattern: Look for date-like markers followed by content
    # Or look for "Posted X ago" / dates that separate posts

    # Try splitting on common IPS separators
    # Pattern: lines that look like dates or "Posted" markers
    post_pattern = r'(?:^|\n)(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,\s*\d{4})'
    parts = re.split(post_pattern, markdown)

    if len(parts) < 2:
        # Try Italian dates
        post_pattern = r'(?:^|\n)(?:(?:Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre)\s+\d+)'
        parts = re.split(post_pattern, markdown)

    if len(parts) < 2:
        return []

    comments = []
    for part in parts[1:]:  # skip header
        text = _clean_comment_text(part)
        if text and len(text) > 30:
            # Try to extract author from beginning of section
            author_match = re.search(r'\[([A-Za-z0-9_\-\.]+)\]', part[:200])
            author = author_match.group(1) if author_match else "anonimo"
            comments.append({"author": author, "text": text})

    return comments


def _parse_generic(markdown: str) -> list[dict]:
    """Generic comment parser — finds blocks of user-generated text.

    Looks for patterns like:
    - Username followed by text blocks
    - Quoted text with attribution
    - Numbered/bulleted user responses
    """
    comments = []

    # Pattern: **username** or [username] at start of paragraph followed by text
    blocks = re.split(r'\n\s*\n', markdown)

    current_author = "anonimo"
    current_text = []

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue

        # Check if this block starts with a username pattern
        author_match = re.match(r'^\*\*([^*]+)\*\*|^\[([^\]]+)\]\(', block)
        if author_match:
            # Save previous comment
            if current_text:
                text = _clean_comment_text("\n".join(current_text))
                if text and len(text) > 30:
                    comments.append({"author": current_author, "text": text})

            current_author = (author_match.group(1) or author_match.group(2) or "anonimo").strip()
            # Text after the author name
            remaining = re.sub(r'^\*\*[^*]+\*\*|^\[[^\]]+\]\([^)]+\)', '', block).strip()
            current_text = [remaining] if remaining else []
        else:
            # Skip navigation/UI lines
            if _is_noise(block):
                continue
            current_text.append(block)

    # Don't forget the last comment
    if current_text:
        text = _clean_comment_text("\n".join(current_text))
        if text and len(text) > 30:
            comments.append({"author": current_author, "text": text})

    return comments


def _clean_comment_text(raw: str) -> str:
    """Clean raw comment text — remove markdown noise, links, images, UI elements."""
    text = raw

    # Remove image markdown
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    # Remove links but keep link text
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Remove horizontal rules
    text = re.sub(r'^[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Remove heading markers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    # Remove "##### 0" type noise (reaction counts)
    text = re.sub(r'^#{1,6}\s*\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove "Membro dello Staff" type badges
    text = re.sub(r'^Membro dello Staff\s*$', '', text, flags=re.MULTILINE)
    # Remove "Ultima modifica:" lines
    text = re.sub(r'Ultima modifica:.*$', '', text, flags=re.MULTILINE)
    # Remove empty lines and normalize whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Filter out very short lines that are likely UI noise
    lines = [l for l in lines if len(l) > 5 or l.startswith('>')]
    text = '\n'.join(lines)

    return text.strip()


def _is_noise(text: str) -> bool:
    """Check if a text block is navigation/UI noise rather than user content."""
    noise_patterns = [
        r'^(Menu|Sign In|Registra|Install|Entra|Home|Forum|Marche)$',
        r'^(First page|Last page|Next|Prev|Page \d+)',
        r'^\* \* \*$',
        r'^(Thanks|I Like|Adoro|Haha)!?$',
        r'^(LISTINO|USATO|NEWS)$',
        r'^Go$',
        r'cookie',
        r'^Posted\s',
        r'^(Rispondi|Citazione|Condividi)',
    ]
    for pattern in noise_patterns:
        if re.match(pattern, text.strip(), re.IGNORECASE):
            return True
    return False
