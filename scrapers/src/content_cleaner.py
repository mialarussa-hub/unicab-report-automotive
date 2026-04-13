"""Claude-powered sentiment analyzer — classifies pre-extracted comments."""

import os
import logging
import json

import httpx

from src.comment_parser import parse_comments

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

SENTIMENT_PROMPT = """Analizza questi commenti di utenti da un forum automotive italiano.
Per OGNI commento restituisci sentiment e topics. Non aggiungere e non rimuovere commenti.

Topics possibili: prezzo, motore, design, affidabilità, consumi, cambio, comfort, qualità, spazio, tecnologia, assistenza, valore, guida, rumorosità, sicurezza, batteria, autonomia, ricarica

Restituisci un JSON array con UN oggetto per OGNI commento, nello stesso ordine:
[{{"sentiment": "positivo|negativo|neutro|misto", "topics": ["topic1", "topic2"]}}]

SOLO il JSON array, nessuna spiegazione.

Commenti da analizzare:

{comments_text}"""


async def clean_and_extract(content: str, source_name: str, url: str) -> dict:
    """Parse comments from markdown, then use Claude for sentiment analysis only.

    Step 1: Parse comments from markdown (regex, no AI)
    Step 2: Send extracted comments to Claude for sentiment classification
    """
    # Step 1: Parse comments from markdown
    parsed = parse_comments(content, url)

    if not parsed:
        logger.warning(f"[{source_name}] No comments parsed from {url}")
        return {"comments": [], "comment_count": 0, "error": "No comments found by parser", "cleaned": False}

    logger.warning(f"[{source_name}] Parsed {len(parsed)} comments from {url}")

    # Step 2: Claude sentiment analysis
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Return parsed comments without sentiment
        comments = [{"author": c["author"], "text": c["text"], "sentiment": "neutro", "topics": []} for c in parsed]
        return {"comments": comments, "comment_count": len(comments), "error": "No API key — sentiment skipped", "cleaned": True}

    # Build compact text for Claude — just numbered comments
    comments_text = "\n\n".join(
        f"[{i+1}] {c['author']}: {c['text'][:500]}"
        for i, c in enumerate(parsed)
    )

    # Cap at 30k chars for the prompt
    if len(comments_text) > 30000:
        comments_text = comments_text[:30000] + "\n\n[... altri commenti troncati]"

    prompt = SENTIMENT_PROMPT.format(comments_text=comments_text)

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
                logger.error(f"Claude API {resp.status_code}: {error_body}")
                # Return comments without sentiment
                comments = [{"author": c["author"], "text": c["text"], "sentiment": "neutro", "topics": []} for c in parsed]
                return {"comments": comments, "comment_count": len(comments), "error": f"API {resp.status_code}", "cleaned": True}

            data = resp.json()

        # Extract response text
        response_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                response_text += block.get("text", "")

        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

        sentiments = json.loads(response_text)

        # Merge parsed comments with sentiment analysis
        comments = []
        for i, c in enumerate(parsed):
            sentiment_data = sentiments[i] if i < len(sentiments) else {}
            comments.append({
                "author": c["author"],
                "text": c["text"],
                "sentiment": sentiment_data.get("sentiment", "neutro"),
                "topics": sentiment_data.get("topics", []),
            })

        logger.warning(f"[{source_name}] AI analyzed {len(comments)} comments with sentiment")
        return {"comments": comments, "comment_count": len(comments), "error": None, "cleaned": True}

    except json.JSONDecodeError as e:
        logger.warning(f"Claude JSON error for {source_name}: {e}")
        comments = [{"author": c["author"], "text": c["text"], "sentiment": "neutro", "topics": []} for c in parsed]
        return {"comments": comments, "comment_count": len(comments), "error": f"JSON parse error", "cleaned": True}
    except Exception as e:
        logger.error(f"Claude error for {source_name}: {e}")
        comments = [{"author": c["author"], "text": c["text"], "sentiment": "neutro", "topics": []} for c in parsed]
        return {"comments": comments, "comment_count": len(comments), "error": str(e), "cleaned": True}


# ---------------------------------------------------------------------------
# L1: Official communication information extraction
# ---------------------------------------------------------------------------

OFFICIAL_PROMPT = """Sei un analista marketing automotive. Analizza i seguenti contenuti dal sito ufficiale di {brand} riguardante il modello {model}.

Estrai le informazioni di comunicazione ufficiale del brand. NON esprimere opinioni personali — riporta SOLO ciò che il brand comunica.

Per ogni contenuto restituisci un oggetto JSON con questa struttura:

{{
  "tipo_contenuto": "pagina_prodotto|promozione|comunicato_stampa|video|configuratore|listino",
  "posizionamento": "come il brand presenta e posiziona questo modello (1-2 frasi)",
  "claim_principale": "tagline, slogan o messaggio chiave della comunicazione",
  "punti_di_forza_comunicati": ["elenco dei selling points principali comunicati dal brand"],
  "prezzo": {{
    "da": null,
    "a": null,
    "valuta": "EUR",
    "note": "eventuali note (con incentivi, IPT esclusa, etc.)"
  }},
  "versioni_disponibili": ["lista delle versioni/allestimenti menzionati"],
  "promozioni_attive": [
    {{
      "tipo": "finanziamento|sconto|rottamazione|noleggio|altro",
      "descrizione": "dettaglio della promozione",
      "rata_mensile": null,
      "durata_mesi": null,
      "anticipo": null
    }}
  ],
  "motorizzazioni_citate": ["elenco motori/alimentazioni menzionati"],
  "target_comunicato": "pubblico target del messaggio (famiglie, giovani, professionisti, etc.)",
  "tono_comunicazione": "sportivo|premium|accessibile|tecnologico|ecologico|familiare|altro",
  "caratteristiche_evidenziate": ["feature tecniche/di design su cui il brand insiste"]
}}

Se un'informazione non è presente nel contenuto, usa null o lista vuota.
Restituisci un JSON array con UN oggetto per OGNI contenuto analizzato, nello stesso ordine.
SOLO il JSON array, nessuna spiegazione.

Contenuti da analizzare:

{items_text}"""


async def analyze_official_content(items: list[dict], brand: str, model: str) -> list[dict] | None:
    """Analyze official manufacturer content with Claude — information extraction, NOT sentiment.

    Returns a list of dicts with structured marketing/positioning data, one per item.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No API key — official content analysis skipped")
        return None

    # Build items text for the prompt
    items_text_parts = []
    for i, item in enumerate(items):
        title = item.get("title", "Senza titolo")
        url = item.get("url", "")
        content = item.get("content", "")[:5000]  # Cap per-item content
        items_text_parts.append(f"[{i+1}] Titolo: {title}\nURL: {url}\n\n{content}")

    items_text = "\n\n---\n\n".join(items_text_parts)

    # Cap total at 30k chars
    if len(items_text) > 30000:
        items_text = items_text[:30000] + "\n\n[... contenuti troncati]"

    prompt = OFFICIAL_PROMPT.format(brand=brand, model=model, items_text=items_text)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
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
                logger.error(f"Claude API {resp.status_code} (official analysis): {error_body}")
                return None

            data = resp.json()

        response_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                response_text += block.get("text", "")

        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

        results = json.loads(response_text)
        logger.warning(f"AI analyzed {len(results)} official content items for {brand} {model}")
        return results

    except json.JSONDecodeError as e:
        logger.warning(f"Claude JSON error (official analysis): {e}")
        return None
    except Exception as e:
        logger.error(f"Claude error (official analysis): {e}")
        return None
