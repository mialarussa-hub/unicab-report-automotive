"""Parse comments from forum/editorial markdown — extracts individual user comments before AI analysis.

Each platform has its own parser:
- XenForo (forum.quattroruote.it): #### [username](link) headers
- IPS/Invision (autopareri.com): date-separated blocks with profile links
- AlVolante (alvolante.it): [username](utente/xxx) + date + text + "segnala abuso" separator
- Generic: fallback for unknown formats
"""

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

    # Route to platform-specific parser based on URL
    if "quattroruote.it" in url and "forum." in url:
        comments = _parse_xenforo(markdown)
        if comments:
            logger.info(f"Parsed {len(comments)} comments (XenForo) from {url}")
            return comments

    if "autopareri.com" in url:
        comments = _parse_ips(markdown)
        if comments:
            logger.info(f"Parsed {len(comments)} comments (IPS/Autopareri) from {url}")
            return comments

    if "alvolante.it" in url:
        comments = _parse_alvolante(markdown)
        if comments:
            logger.info(f"Parsed {len(comments)} comments (AlVolante) from {url}")
            return comments

    # Fallback: try XenForo then IPS then generic
    comments = _parse_xenforo(markdown)
    if len(comments) >= 2:
        logger.info(f"Parsed {len(comments)} comments (XenForo pattern) from {url}")
        return comments

    comments = _parse_ips(markdown)
    if len(comments) >= 2:
        logger.info(f"Parsed {len(comments)} comments (IPS pattern) from {url}")
        return comments

    comments = _parse_generic(markdown)
    if comments:
        logger.info(f"Parsed {len(comments)} comments (generic pattern) from {url}")
        return comments

    logger.info(f"No comment pattern detected for {url}")
    return []


# =============================================================================
# XenForo parser (forum.quattroruote.it)
# =============================================================================

def _parse_xenforo(markdown: str) -> list[dict]:
    """Parse XenForo forum markdown.

    Pattern: #### [username](link) followed by comment text until next #### or end.
    """
    pattern = r'####\s+\[([^\]]+)\]\([^)]+\)'
    parts = re.split(pattern, markdown)

    if len(parts) < 3:
        return []

    # Find where "Discussioni popolari" section starts — everything after is footer noise
    footer_idx = markdown.lower().find("discussioni popolari")

    comments = []
    pos = 0  # track position in original markdown
    i = 1
    while i < len(parts) - 1:
        author = parts[i].strip()
        raw_text = parts[i + 1] if i + 1 < len(parts) else ""

        # Track position to skip footer
        pos += len(parts[i - 1]) + len(author) + 10  # approximate
        if footer_idx > 0 and pos > footer_idx:
            break

        text = _clean_comment_text(raw_text)

        if text and len(text) > 10 and author:
            # Skip sidebar noise: long "author" names
            if len(author) > 50 or "..." in author:
                i += 2
                continue
            # Skip known footer items
            if author in ("Avvistamenti", "Discussioni popolari"):
                i += 2
                continue
            comments.append({"author": author, "text": text})

        i += 2

    return comments


# =============================================================================
# IPS/Invision parser (autopareri.com)
# =============================================================================

# IPS date pattern — the weird format where year and relative time merge:
# "September 28, 20223 yr" or "January 15, 2025" or "Marzo 5, 20241 yr"
_MONTHS_EN = "January|February|March|April|May|June|July|August|September|October|November|December"
_MONTHS_IT = "Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre"
_IPS_DATE_RE = re.compile(
    rf'(?:^|\n)\s*(?:{_MONTHS_EN}|{_MONTHS_IT})\s+\d{{1,2}},?\s*\d{{4}}',
    re.IGNORECASE,
)

# IPS noise patterns to remove from comment text
_IPS_NOISE = re.compile(
    r'(?:^|\n)\s*(?:'
    r'!\[(?:I Like|Thanks|Haha|Adoro|Sad|Confused|Like)!?\].*|'  # reaction images
    r'Toggle Quote.*|'
    r'Edited\s.*|'
    r'\d+\s*$|'  # standalone numbers (reaction counts)
    r'Share this (?:post|comment).*|'
    r'Link to (?:post|comment).*|'
    r'Posted\s.*|'
    r'Report\s*(?:post)?.*'
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# IPS username patterns — look in order of specificity
_IPS_AUTHOR_PATTERNS = [
    # Profile link: [username](https://...autopareri.com/profile/...)
    re.compile(r'\[([A-Za-z0-9_\-\.\ ]+)\]\(https?://[^)]*(?:profile|members?)[^)]*\)'),
    # Quote attribution: [username](https://...autopareri.com/...) said:
    re.compile(r'\[([A-Za-z0-9_\-\.\ ]+)\]\([^)]*\)\s*said:'),
    # Standalone link at start of block
    re.compile(r'^\s*\[([A-Za-z0-9_\-\.\ ]{2,30})\]\('),
]


def _parse_ips(markdown: str) -> list[dict]:
    """Parse IPS/Invision Community markdown (autopareri.com).

    Each comment block starts with a date line. Comments may contain:
    - Quoted text (> blocks)
    - Reaction images (![Like!], ![Thanks!])
    - Profile links [username](profile_url)
    """
    parts = _IPS_DATE_RE.split(markdown)

    if len(parts) < 3:
        return []

    # Find pagination/footer boundary
    footer_markers = ["First page", "Last page", "Next", "Prev", "Page 1 of"]

    comments = []
    for part in parts[1:]:  # skip header/nav before first comment
        # Stop at pagination footer
        if any(marker in part for marker in footer_markers):
            # Still extract text before the footer marker
            for marker in footer_markers:
                idx = part.find(marker)
                if idx > 0:
                    part = part[:idx]
                    break

        # Clean IPS noise
        text = _IPS_NOISE.sub('', part)
        text = _clean_comment_text(text)

        if not text or len(text) < 10:
            continue

        # Find author
        author = "anonimo"
        for pattern in _IPS_AUTHOR_PATTERNS:
            match = pattern.search(part[:500])
            if match:
                author = match.group(1).strip()
                break

        # Remove the author name/link from the comment text to avoid duplication
        if author != "anonimo":
            text = text.replace(f"{author} said:", "").strip()

        # Skip pure reaction/UI blocks
        if len(text) < 10:
            continue
        if all(w in text.lower() for w in ["like", "thanks"]) and len(text) < 50:
            continue

        comments.append({"author": author, "text": text})

    return comments


# =============================================================================
# =============================================================================
# AlVolante parser (alvolante.it)
# =============================================================================

# AlVolante comment pattern:
# [username](https://www.alvolante.it/utente/xxx)
# 6 aprile 2026 - 14:15
# [optional score number]
# comment text
# - Accedi o registrati per inserire commenti.
# - segnala abuso
_ALVOLANTE_COMMENT_RE = re.compile(
    r'\[([^\]]+)\]\(https://www\.alvolante\.it/utente/[^)]+\)\s*\n+'
    r'(\d{1,2}\s+\w+\s+\d{4}\s*-\s*\d{1,2}:\d{2})\s*\n*'
    r'(\d+\s*\n)?'  # optional score
    r'(.*?)'
    r'(?=\[(?:[^\]]+)\]\(https://www\.alvolante\.it/utente/|\Z|- segnala abuso)',
    re.DOTALL,
)


def _parse_alvolante(markdown: str) -> list[dict]:
    """Parse alVolante.it article comments.

    Pattern: [username](utente/xxx) + date + optional score + text, separated by "segnala abuso".
    All comments on one page (no pagination needed).
    """
    # Find the comments section (starts after "Aggiungi un commento" or user voting section)
    comments_start = markdown.find("Aggiungi un commento")
    if comments_start == -1:
        comments_start = markdown.find("segnala abuso")
    if comments_start == -1:
        return []

    comments_section = markdown[comments_start:]

    # Split on "segnala abuso" — each block is one comment
    blocks = re.split(r'-\s*segnala abuso', comments_section)

    comments = []
    for block in blocks:
        # Find username from profile link
        author_match = re.search(
            r'\[([^\]]+)\]\(https://www\.alvolante\.it/utente/',
            block,
        )
        if not author_match:
            continue

        author = author_match.group(1).strip()

        # Find date
        date_match = re.search(
            r'(\d{1,2}\s+\w+\s+\d{4}\s*-\s*\d{1,2}:\d{2})',
            block,
        )

        # Extract text: everything after the date (and optional score number)
        if date_match:
            text_start = date_match.end()
            raw_text = block[text_start:]
        else:
            # Fallback: everything after the author link
            text_start = author_match.end()
            raw_text = block[text_start:]

        # Clean: remove score numbers at start, login prompts, images
        raw_text = re.sub(r'^\s*\d+\s*\n', '', raw_text)  # leading score
        raw_text = re.sub(r'-\s*\[Accedi\].*', '', raw_text, flags=re.DOTALL)  # login prompt
        text = _clean_comment_text(raw_text)

        if text and len(text) > 5 and author:
            # Skip "Visualizza il profilo" noise
            if "Visualizza il profilo" in text:
                continue
            comments.append({"author": author, "text": text})

    return comments


# =============================================================================
# Generic parser (fallback)
# =============================================================================

def _parse_generic(markdown: str) -> list[dict]:
    """Generic comment parser — finds blocks of user-generated text."""
    comments = []
    blocks = re.split(r'\n\s*\n', markdown)

    current_author = "anonimo"
    current_text = []

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue

        author_match = re.match(r'^\*\*([^*]+)\*\*|^\[([^\]]+)\]\(', block)
        if author_match:
            if current_text:
                text = _clean_comment_text("\n".join(current_text))
                if text and len(text) > 30:
                    comments.append({"author": current_author, "text": text})

            current_author = (author_match.group(1) or author_match.group(2) or "anonimo").strip()
            remaining = re.sub(r'^\*\*[^*]+\*\*|^\[[^\]]+\]\([^)]+\)', '', block).strip()
            current_text = [remaining] if remaining else []
        else:
            if _is_noise(block):
                continue
            current_text.append(block)

    if current_text:
        text = _clean_comment_text("\n".join(current_text))
        if text and len(text) > 30:
            comments.append({"author": current_author, "text": text})

    return comments


# =============================================================================
# Shared utilities
# =============================================================================

def _strip_quotes(text: str) -> str:
    """Remove quoted reply blocks (lines starting with >) from comment text.

    On forums, replies often quote the parent comment. Including quotes means
    the same text appears multiple times — once as the original comment and
    once in every reply that quotes it. Stripping quotes gives us only the
    user's OWN words.
    """
    lines = text.split('\n')
    result = []
    in_quote = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('>'):
            in_quote = True
            continue
        if in_quote and not stripped:
            # Blank line after quote block — end of quote
            in_quote = False
            continue
        in_quote = False
        # Also skip "XXX said:" and "Clicca per allargare" quote markers
        if re.match(r'.*\bsaid:\s*$', stripped, re.IGNORECASE):
            continue
        if re.match(r'.*\bha scritto:\s*$', stripped, re.IGNORECASE):
            continue
        if 'Clicca per allargare' in stripped or 'Toggle Quote' in stripped:
            continue
        result.append(line)
    return '\n'.join(result)


def _clean_comment_text(raw: str) -> str:
    """Clean raw comment text — remove markdown noise, links, images, UI elements."""
    text = raw

    # Strip quoted reply blocks FIRST (before other cleaning)
    text = _strip_quotes(text)

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
    # Remove "Clicca per allargare..." lines
    text = re.sub(r'Clicca per allargare\.{0,3}\s*$', '', text, flags=re.MULTILINE)
    # Remove standalone relative time ("3 yr", "1 yr", "2 mo")
    text = re.sub(r'^\d+\s*(?:yr|mo|wk|hr|min|sec)\s*$', '', text, flags=re.MULTILINE)
    # Remove empty lines and normalize whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Filter out very short noise lines
    lines = [l for l in lines if len(l) > 5]
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
        r'^Discussioni popolari',
        r'^(Skip to content|View in the app|A better way)',
        r'^(Customizer|Sign In)$',
        r'^(Home Page|Messaggi non Letti|Discussioni Seguite)',
    ]
    for pattern in noise_patterns:
        if re.match(pattern, text.strip(), re.IGNORECASE):
            return True
    return False
