"""Claude-powered content cleaner — extracts user comments and sentiment from raw scraped content."""

import os
import logging
import json

import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

EXTRACTION_PROMPT = """Sei un analista di contenuti automotive. Ti viene fornito il testo raw scrappato da una pagina web di un forum o sito automotive.

Il tuo compito è estrarre SOLO i commenti/opinioni degli utenti reali, ignorando:
- Navigazione del sito, header, footer, sidebar
- Pubblicità e banner
- Link di paginazione
- Quote di articoli giornalistici (tieni solo le reazioni degli utenti)
- Testo UI (pulsanti, menu, cookie banner)

Per ogni commento trovato, restituisci un oggetto JSON con:
- "author": nome utente (se disponibile, altrimenti "anonimo")
- "text": il testo del commento pulito
- "sentiment": "positivo", "negativo", "neutro" o "misto"
- "topics": lista di argomenti trattati (es. ["prezzo", "motore", "design", "affidabilità"])

Restituisci SOLO un JSON array. Se non trovi commenti utente, restituisci [].
NON includere spiegazioni, solo il JSON.

Testo da analizzare (fonte: {source_name}, URL: {url}):

{content}"""


async def clean_and_extract(content: str, source_name: str, url: str) -> dict:
    """Use Claude to extract clean comments and sentiment from raw scraped content.

    Returns:
        dict with keys:
        - "comments": list of extracted comments with sentiment
        - "comment_count": number of comments found
        - "error": error message if any
        - "cleaned": True if cleaning was applied
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"comments": [], "comment_count": 0, "error": "ANTHROPIC_API_KEY not set", "cleaned": False}

    # Truncate content to avoid token limits (Claude Haiku handles ~100k tokens)
    max_chars = 15000
    truncated = content[:max_chars]
    if len(content) > max_chars:
        truncated += f"\n\n[... troncato, {len(content) - max_chars} caratteri rimanenti]"

    prompt = EXTRACTION_PROMPT.format(
        source_name=source_name,
        url=url,
        content=truncated,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-20250414",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract the text response
        response_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                response_text += block.get("text", "")

        # Parse JSON from response
        response_text = response_text.strip()
        # Handle markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

        comments = json.loads(response_text)

        if not isinstance(comments, list):
            comments = []

        return {
            "comments": comments,
            "comment_count": len(comments),
            "error": None,
            "cleaned": True,
        }

    except json.JSONDecodeError as e:
        logger.warning(f"Claude response not valid JSON for {source_name}: {e}")
        return {"comments": [], "comment_count": 0, "error": f"Invalid JSON response: {e}", "cleaned": False}
    except Exception as e:
        logger.error(f"Claude cleaning error for {source_name}: {e}")
        return {"comments": [], "comment_count": 0, "error": str(e), "cleaned": False}
