"""Claude-powered content cleaner — extracts user comments and sentiment from raw scraped content."""

import os
import logging
import json

import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

EXTRACTION_PROMPT = """Sei un analista di contenuti automotive. Analizza il testo scrappato da una pagina web e estrai TUTTI i commenti/opinioni degli utenti.

REGOLE:
- Estrai OGNI commento di utente reale, non saltarne nessuno
- IGNORA: navigazione, pubblicità, UI, testo articolo originale
- RIASSUMI ogni commento in 1-2 frasi (NON copiare il testo integrale)
- Cattura il SENSO del commento, non le parole esatte

Per ogni commento restituisci:
{{"author": "nome_utente", "text": "riassunto 1-2 frasi del commento", "sentiment": "positivo|negativo|neutro|misto", "topics": ["topic1", "topic2"]}}

Topics possibili: prezzo, motore, design, affidabilità, consumi, cambio, comfort, qualità, spazio, tecnologia, assistenza, valore, guida, rumorosità, sicurezza

Restituisci SOLO un JSON array. Se non trovi commenti: [].

Fonte: {source_name} | URL: {url}

{content}"""


async def clean_and_extract(content: str, source_name: str, url: str) -> dict:
    """Use Claude to extract clean comments and sentiment from raw scraped content."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"comments": [], "comment_count": 0, "error": "ANTHROPIC_API_KEY not set", "cleaned": False}

    # Claude 3 Haiku context: 200k tokens. Safe limit: 50k chars (~12k tokens)
    max_chars = 50000
    truncated = content[:max_chars]
    if len(content) > max_chars:
        truncated += f"\n\n[... troncato, {len(content) - max_chars} caratteri rimanenti]"

    prompt = EXTRACTION_PROMPT.format(
        source_name=source_name,
        url=url,
        content=truncated,
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
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
                error_body = resp.text[:300]
                logger.error(f"Claude API {resp.status_code} for {source_name}: {error_body}")
                return {"comments": [], "comment_count": 0, "error": f"API {resp.status_code}: {error_body}", "cleaned": False}
            data = resp.json()

        # Extract the text response
        response_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                response_text += block.get("text", "")

        # Parse JSON from response
        response_text = response_text.strip()
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
