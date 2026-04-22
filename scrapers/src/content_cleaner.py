"""Claude-powered sentiment analyzer — classifies pre-extracted comments."""

import os
import logging
import json

import httpx

from src.comment_parser import parse_comments
from src.motore import prompt_enum_description, normalize_cilindrata, normalize_alimentazione

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

SENTIMENT_PROMPT = """Analizza questi commenti di utenti da un forum automotive italiano.
Per OGNI commento restituisci sentiment, topics e (se menzionata) la motorizzazione. Non aggiungere e non rimuovere commenti.

Topics possibili: prezzo, motore, design, affidabilità, consumi, cambio, comfort, qualità, spazio, tecnologia, assistenza, valore, guida, rumorosità, sicurezza, batteria, autonomia, ricarica

`motore_menzionato` deve essere null se il commento NON cita alcuna motorizzazione/alimentazione.
Se lo cita: {{"alimentazione": "{alim_enum}", "cilindrata": 1.0}} (cilindrata decimale in litri, null se elettrico puro o non citata).

Restituisci un JSON array con UN oggetto per OGNI commento, nello stesso ordine:
[{{"sentiment": "positivo|negativo|neutro|misto", "topics": ["topic1"], "motore_menzionato": null}}]

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

    prompt = SENTIMENT_PROMPT.format(
        comments_text=comments_text,
        alim_enum=prompt_enum_description(),
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
            mm = sentiment_data.get("motore_menzionato")
            if isinstance(mm, dict):
                a = normalize_alimentazione(mm.get("alimentazione"))
                cc = normalize_cilindrata(mm.get("cilindrata"))
                motore_menzionato = (
                    {"alimentazione": a, "cilindrata": cc}
                    if (a or cc is not None) else None
                )
            else:
                motore_menzionato = None
            comments.append({
                "author": c["author"],
                "text": c["text"],
                "sentiment": sentiment_data.get("sentiment", "neutro"),
                "topics": sentiment_data.get("topics", []),
                "motore_menzionato": motore_menzionato,
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
  "motorizzazioni_citate": ["elenco motori/alimentazioni menzionati, stringhe libere"],
  "motore_info": {{
    "versioni": [
      {{
        "alimentazione": "{alim_enum}",
        "cilindrata": 1.0,
        "descrizione": "breve descrizione (es. 1.0 TSI 110cv)"
      }}
    ]
  }},
  "prestazioni_per_versione": [
    {{
      "versione": "nome/allestimento",
      "alimentazione": "{alim_enum}",
      "cilindrata_cc": 1499,
      "cv": 127,
      "kw": 93,
      "coppia_nm": 225,
      "cilindri": 4,
      "cambio": "manuale 6 rapporti | automatico 8 rapporti | DCT 7 rapporti | e-CVT | etc.",
      "trazione": "anteriore|posteriore|integrale",
      "posti": 5,
      "zero_cento_s": 10.5,
      "velocita_max_kmh": 190
    }}
  ],
  "consumi_per_versione": [
    {{
      "versione": "nome/allestimento",
      "wltp_combinato_l_100km": 7.2,
      "wltp_combinato_kwh_100km": null,
      "emissioni_co2_gkm": 174,
      "classe_emissioni": "Euro 6D",
      "autonomia_elettrica_km": null
    }}
  ],
  "dimensioni": {{
    "lunghezza_mm": 4325,
    "larghezza_mm": 1815,
    "altezza_mm": 1640,
    "passo_mm": 2570,
    "peso_kg": 1325,
    "serbatoio_l": 46,
    "bagagliaio_min_l": 375,
    "bagagliaio_max_l": 1000
  }},
  "garanzia": {{
    "anni": 5,
    "km": 100000,
    "note": "chilometraggio illimitato per i primi 2 anni"
  }},
  "dotazione_dettagliata": ["ABS", "ESP", "TPMS", "airbag", "cerchi lega 17", "infotainment touch 8\"", "telecamera posteriore", "..."],
  "target_comunicato": "pubblico target del messaggio (famiglie, giovani, professionisti, etc.)",
  "tono_comunicazione": "sportivo|premium|accessibile|tecnologico|ecologico|familiare|altro",
  "caratteristiche_evidenziate": ["feature tecniche/di design su cui il brand insiste"]
}}

REGOLE per i campi tecnici:
- Riempi SOLO i campi per cui hai un dato ESPLICITO nel contenuto. NON inventare.
- `prestazioni_per_versione` e `consumi_per_versione`: un oggetto per versione distinta citata.
- `dimensioni`, `garanzia`: un solo oggetto (il modello base o la versione dominante).
- Se un singolo valore manca usa null; se un intero oggetto manca usa null o oggetto vuoto.
- `dotazione_dettagliata`: lista piatta di stringhe ESATTAMENTE come citate.

REGOLE per motore_info.versioni:
- Un oggetto per OGNI motorizzazione/versione menzionata nel contenuto.
- `alimentazione`: UNO dei valori canonici: {alim_enum}.
- `cilindrata`: numero decimale in litri (es. 1.0, 1.5, 2.0). Usa null SOLO se elettrico puro o se la cilindrata non è indicata.
- Se il contenuto non cita motorizzazioni specifiche, restituisci "motore_info": {{"versioni": []}}.

Se un'altra informazione non è presente nel contenuto, usa null o lista vuota.
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

    prompt = OFFICIAL_PROMPT.format(
        brand=brand, model=model, items_text=items_text,
        alim_enum=prompt_enum_description(),
    )

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

        # Normalize motore_info to canonical values
        for r in results:
            mi = r.get("motore_info") or {}
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
            r["motore_info"] = {"versioni": clean}

        logger.warning(f"AI analyzed {len(results)} official content items for {brand} {model}")
        return results

    except json.JSONDecodeError as e:
        logger.warning(f"Claude JSON error (official analysis): {e}")
        return None
    except Exception as e:
        logger.error(f"Claude error (official analysis): {e}")
        return None


# ---------------------------------------------------------------------------
# L1: Aggregated extraction — one rich consolidated JSON across all L1 items
# ---------------------------------------------------------------------------

AGGREGATE_PROMPT = """Sei un analista dati ufficiali automotive. Ricevi un "pacchetto" di fonti ufficiali (pagine del sito del costruttore, schede tecniche, scheda comparativa PDF, sintesi Perplexity con citazioni dealer-network) su {brand} {model}{variant_suffix}.

Il tuo compito: produrre UN SOLO oggetto JSON consolidato, aggregando TUTTI i dati ufficiali presenti nelle fonti. Non una sintesi per fonte — UNA fotografia completa.

REGOLE DI AGGREGAZIONE (fondamentali):
1. Ogni allestimento, motorizzazione, colore, optional citato in UNA QUALSIASI fonte DEVE comparire nell'output. Non scartare allestimenti solo perché una fonte non li elenca tutti.
2. Unisci le informazioni: se la fonte A dice "Pop: cerchi 16\"" e la fonte B dice "Pop: ABS ESP", il risultato è "Pop: cerchi 16\", ABS, ESP".
3. NON inventare numeri (prezzi, CV, Nm, mm, WLTP). Se una fonte dice "da X€" e nessuna dichiara il massimo, metti `min_eur=X` e `max_eur=null` con nota esplicita.
4. Se le fonti sono in contrasto, privilegia il sito ufficiale del brand; riporta la divergenza in `note_discrepanze`.
5. Usa null (o lista vuota) per dati NON esplicitamente presenti nelle fonti — non dedurre.

SCHEMA OUTPUT (restituisci ESATTAMENTE questa struttura):

{{
  "is_aggregate": true,
  "allestimenti": [
    {{
      "nome": "Pop",
      "posizionamento": "entry|intermedio|top|sportivo|business|altro",
      "prezzo_eur": 18900,
      "prezzo_note": "IVA inclusa, IPT esclusa",
      "disponibile_su": ["benzina", "ibrido_mild"]
    }}
  ],
  "motorizzazioni": [
    {{
      "nome_commerciale": "1.2 Hybrid 100 CV",
      "alimentazione": "{alim_enum}",
      "cilindrata_cc": 1199,
      "cilindrata_l": 1.2,
      "cv": 100,
      "kw": 74,
      "coppia_nm": 205,
      "cilindri": 3,
      "trasmissione": {{
        "tipo": "manuale|automatico|automatico_dct|e_cvt|automatico_cvt|altro",
        "marce": 6,
        "trazione": "anteriore|posteriore|integrale"
      }}
    }}
  ],
  "consumi_emissioni": [
    {{
      "motorizzazione": "1.2 Hybrid",
      "wltp_combinato_l_100km": 5.4,
      "wltp_combinato_kwh_100km": null,
      "emissioni_co2_gkm": 122,
      "classe_emissioni": "Euro 6D-ISC-FCM",
      "autonomia_elettrica_km": null,
      "autonomia_totale_km": null
    }}
  ],
  "prezzi_finanziamenti": {{
    "fascia_prezzo": {{ "min_eur": 18900, "max_eur": 24900, "note": "listino base" }},
    "promozioni": [
      {{
        "tipo": "rateizzato|leasing|NLT|rottamazione|sconto|altro",
        "descrizione": "Finanziamento Be-Hybrid: TAN 0%",
        "anticipo_eur": 3000,
        "rata_mensile_eur": 189,
        "durata_mesi": 48,
        "tan_percent": 0,
        "taeg_percent": 5.99,
        "scadenza": "2026-03-31"
      }}
    ]
  }},
  "dimensioni": {{
    "lunghezza_mm": 3990,
    "larghezza_mm": 1760,
    "altezza_mm": 1580,
    "passo_mm": 2540,
    "peso_kg": 1150,
    "serbatoio_l": 40,
    "bagagliaio_min_l": 361,
    "bagagliaio_max_l": 1249
  }},
  "dotazione_per_allestimento": {{
    "Pop": ["ABS", "ESP", "cerchi acciaio 16\\""],
    "Icon": ["cerchi lega 17\\"", "telecamera posteriore"]
  }},
  "optionals_disponibili": [
    {{
      "nome": "Pack Winter",
      "categoria": "comfort|sicurezza|estetica|audio|tecnologia|altro",
      "prezzo_eur": 450,
      "disponibile_su": ["Icon", "La Prima"],
      "descrizione": "sedili riscaldati, volante riscaldato"
    }}
  ],
  "sicurezza_adas": {{
    "di_serie": ["AEB", "Lane Keep Assist", "Traffic Sign Recognition"],
    "opzionali": ["Adaptive Cruise Control", "Blind Spot Detection"],
    "note": "NCAP rating se dichiarato, Level 2 autonomy, etc."
  }},
  "colori_disponibili": [
    {{ "nome": "Blu Lago", "tipo": "pastello|metallizzato|tri_strato|opaco|altro", "prezzo_eur": 0 }},
    {{ "nome": "Grigio Vulcano", "tipo": "metallizzato", "prezzo_eur": 700 }}
  ],
  "materiali_costruttivi": {{
    "carrozzeria": ["acciaio alto resistenziale", "alluminio su porte"],
    "interni": ["bioplastica riciclata", "tessuto Seaqual Yarn"],
    "sostenibilita": ["98% materiali riciclabili a fine vita"]
  }},
  "peculiarita": [
    "Nicchia porta-oggetti ereditata dalla Panda storica",
    "Tappo serbatoio senza chiusura manuale"
  ],
  "posizionamento_marketing": "Come il costruttore presenta il modello nel segmento (1-2 frasi)",
  "claim_principale": "slogan o tagline ufficiale",
  "tono_comunicazione": "sportivo|premium|accessibile|tecnologico|ecologico|familiare|altro",
  "target_comunicato": "famiglie|giovani|professionisti|urbani|altro",
  "note_discrepanze": "eventuali contraddizioni tra fonti, es. Fiat.it dichiara X€ mentre un dealer riporta Y€"
}}

VINCOLI TECNICI:
- `alimentazione` DEVE essere uno di: {alim_enum}.
- `cilindrata_l` è decimale in litri (es. 1.0, 1.2, 1.5); se elettrico puro o non dichiarata, null.
- Numeri sono numeri JSON, NON stringhe.
- Restituisci SOLO il JSON, nessuna spiegazione.

PACCHETTO FONTI:

{items_text}"""


async def aggregate_official_content(
    items: list[dict], brand: str, model: str,
    alimentazione: str | None = None, cilindrata: float | None = None,
) -> dict | None:
    """Run ONE consolidated analysis across all L1 items, producing a rich contract JSON.

    This replaces per-item analysis for the consolidated view: instead of 6 partial
    JSONs it returns 1 complete structured dossier with all allestimenti, motorizzazioni,
    consumi, prezzi, dotazione, ADAS, colori, materiali, peculiarità.
    """
    from src.motore import prompt_enum_description, normalize_alimentazione, normalize_cilindrata

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not items:
        return None

    # Build items pack — wide budget, this is the aggregate
    parts = []
    for i, item in enumerate(items):
        title = item.get("title", "Senza titolo")
        url = item.get("url", "")
        content = item.get("content", "")[:6000]
        origin = "Perplexity (consolidato)" if item.get("perplexity_consolidated") else "Sito ufficiale"
        parts.append(f"[{i+1}] ({origin}) Titolo: {title}\nURL: {url}\n\n{content}")
    items_text = "\n\n===\n\n".join(parts)
    if len(items_text) > 60000:
        items_text = items_text[:60000] + "\n\n[... troncato]"

    variant_suffix = ""
    if alimentazione or cilindrata is not None:
        bits = []
        if cilindrata is not None:
            bits.append(f"{cilindrata:.1f}".rstrip("0").rstrip("."))
        if alimentazione:
            bits.append(alimentazione)
        variant_suffix = f" ({' '.join(bits)})"

    prompt = AGGREGATE_PROMPT.format(
        brand=brand, model=model, variant_suffix=variant_suffix,
        items_text=items_text, alim_enum=prompt_enum_description(),
    )

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
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
                logger.error(f"Claude aggregate API {resp.status_code}: {resp.text[:300]}")
                return None

            data = resp.json()
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        result = json.loads(text)

        # Normalize alimentazione + cilindrata in motorizzazioni
        motori = result.get("motorizzazioni") or []
        for m in motori:
            if isinstance(m, dict):
                a = normalize_alimentazione(m.get("alimentazione"))
                c = normalize_cilindrata(m.get("cilindrata_l") or m.get("cilindrata_cc"))
                m["alimentazione"] = a
                if c is not None:
                    m["cilindrata_l"] = c

        logger.warning(
            f"Aggregated L1 for {brand} {model}: "
            f"{len(result.get('allestimenti') or [])} allestimenti, "
            f"{len(result.get('motorizzazioni') or [])} motorizzazioni, "
            f"{len(result.get('colori_disponibili') or [])} colori"
        )
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"Claude aggregate JSON error: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude aggregate error: {e}")
        return None
