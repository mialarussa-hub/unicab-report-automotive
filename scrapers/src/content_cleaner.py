"""Claude-powered sentiment analyzer — classifies pre-extracted comments."""

import os
import logging
import json
import re

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


# ---------------------------------------------------------------------------
# L1: Communication drivers analysis — positioning / messaging, NOT technical specs
# ---------------------------------------------------------------------------

DRIVER_TAXONOMY = {
    "design_linea": "Design & Linea",
    "prezzo_accessibilita": "Prezzo & Accessibilità",
    "tecnologia_innovazione": "Tecnologia & Innovazione",
    "sicurezza_adas": "Sicurezza & ADAS",
    "consumi_sostenibilita": "Consumi & Sostenibilità",
    "prestazioni_guida": "Prestazioni & Piacere di guida",
    "spazio_praticita": "Spazio & Praticità",
    "heritage_identita": "Heritage & Identità brand",
    "lifestyle_emozione": "Lifestyle & Emozione",
}

DRIVER_ANALYSIS_PROMPT = """Sei un analista di comunicazione di marketing automotive.

Ricevi un pacchetto di contenuti UFFICIALI (sito del costruttore, canale YouTube ufficiale, sintesi consolidata Perplexity con citazioni dealer/listini) su {brand} {model}.

COMPITO: identificare su quali DRIVER COMUNICATIVI il brand punta per questo modello.
NON estrarre specifiche tecniche (prezzi, motorizzazioni, dimensioni, dotazione): quelle sono trattate separatamente.
Focalizzati su COSA IL BRAND ENFATIZZA nella sua narrazione: messaggi, claim, tagline, angolo emotivo, target comunicato.

TASSONOMIA DRIVER (usa ESATTAMENTE questi 9 codici, nessun altro):
- design_linea: estetica, stile esterno/interno, linguaggio formale, personalizzazione estetica
- prezzo_accessibilita: pricing, finanziamenti, promo, accessibilità economica, value for money
- tecnologia_innovazione: infotainment, connettività, feature tech distintive, soluzioni proprietarie
- sicurezza_adas: sistemi di assistenza alla guida, protezione, crash rating
- consumi_sostenibilita: efficienza, emissioni, elettrificazione, materiali sostenibili, eco
- prestazioni_guida: dinamica, potenza, handling, piacere di guida
- spazio_praticita: abitabilità, baule, modularità, famiglia/quotidiano
- heritage_identita: storia, DNA del brand, tradizione, Made in, appartenenza
- lifestyle_emozione: target aspirazionale, stile di vita, emozioni evocate, narrazione lifestyle

OUTPUT (restituisci ESATTAMENTE questa struttura, UN solo oggetto JSON):

{{
  "is_driver_analysis": true,
  "brand": "{brand}",
  "model": "{model}",
  "ranking_driver": [
    {{
      "driver": "design_linea",
      "peso": 28,
      "claim_esemplificativi": ["quote testuale 1 dal contenuto", "quote testuale 2"],
      "canali": ["sito_brand", "youtube", "perplexity"],
      "evidenze": "1-2 frasi di sintesi che spiegano cosa il brand enfatizza su questo driver"
    }}
  ],
  "tagline_campagna": "payoff/slogan ufficiale se identificabile, null altrimenti",
  "target_comunicato": "es. famiglie urbane, giovani, professionisti — null se non chiaro",
  "note_metodologiche": "limitazioni relative ai contenuti PRESENTI nel pacchetto (es. 'sito brand con molte schede tecniche e poco storytelling') — NON menzionare canali non presenti come mancanze"
}}

REGOLE FONDAMENTALI:
1. I `peso` sono numeri interi e DEVONO sommare esattamente a 100 complessivamente.
2. Includi TUTTI i 9 driver nel ranking, anche con peso=0: in tal caso `claim_esemplificativi=[]`, `canali=[]`, `evidenze="non presente nella comunicazione analizzata"`.
3. `claim_esemplificativi`: quote TESTUALI dal contenuto, MAI parafrasate o inventate. Max 5 per driver. Se non ci sono quote appropriate, lista vuota.
4. `canali`: metti SOLO i canali in cui il driver emerge davvero (sito_brand, youtube, perplexity). Lista vuota se peso=0.
5. NON estrarre né strutturare dati tecnici (prezzi, CV, dimensioni, dotazione). Anche se il contenuto ne parla, il tuo output è puramente sul POSIZIONAMENTO comunicativo.
6. Se il pacchetto è povero di contenuto sostanziale, segnalalo in `note_metodologiche` e distribuisci i pesi con cautela. NON parlare di canali/fonti non presenti nel pacchetto come fossero "mancanze": le fonti sono quelle che trovi qui, non commentare l'assenza di altri canali (YouTube, social, ecc.) se non sono tra gli item forniti.
7. Restituisci SOLO il JSON, nessuna spiegazione, nessun markdown.

REGOLE JSON (molto importanti — evitano output non parseabile):
- Le claim_esemplificativi sono citazioni dal sito. Quando una citazione ha virgolette interne al testo originale, NON usare mai la virgoletta doppia ("): sostituisci con le virgolette italiane «...» oppure con l'apostrofo tipografico '. Esempio giusto: "Il SUV «compatto» per eccellenza". Esempio sbagliato: "Il SUV "compatto" per eccellenza" — questo rompe il JSON.
- Non inserire mai caratteri di controllo (newline, tab) dentro una stringa JSON senza escape.
- Prima di restituire, verifica mentalmente che ogni virgoletta doppia sia bilanciata e che il JSON sia un documento singolo valido.

PACCHETTO CONTENUTI:

{items_text}"""


async def analyze_communication_drivers(
    items: list[dict], brand: str, model: str,
) -> dict | None:
    """Classify which communication drivers the brand emphasizes for the model.

    Replaces the technical-specs aggregate: runs ONE call across all L1 items and
    returns the 9-driver ranking with exemplary quotes, tagline and target — the
    positioning-focused L1 output requested for the UNICAB pilot.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not items:
        return None

    parts = []
    for i, item in enumerate(items):
        title = item.get("title", "Senza titolo")
        url = item.get("url", "")
        content = item.get("content", "")[:6000]
        if item.get("perplexity_consolidated"):
            origin = "Perplexity (consolidato)"
        elif "youtube.com" in (url or "") or item.get("video_id"):
            origin = "YouTube ufficiale"
        else:
            origin = "Sito ufficiale"
        parts.append(f"[{i+1}] ({origin}) Titolo: {title}\nURL: {url}\n\n{content}")
    items_text = "\n\n===\n\n".join(parts)
    if len(items_text) > 60000:
        items_text = items_text[:60000] + "\n\n[... troncato]"

    base_prompt = DRIVER_ANALYSIS_PROMPT.format(
        brand=brand, model=model, items_text=items_text,
    )

    async def _call_and_parse(prompt_text: str, attempt_label: str) -> tuple[dict | None, str]:
        """Call Claude + try to parse JSON. Returns (parsed_dict_or_None, raw_text)."""
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
                    "messages": [{"role": "user", "content": prompt_text}],
                },
            )
            if resp.status_code != 200:
                logger.error(
                    f"Claude driver-analysis [{attempt_label}] API {resp.status_code}: "
                    f"{resp.text[:300]}"
                )
                return None, ""
            data = resp.json()
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text), text
        except json.JSONDecodeError as e:
            logger.warning(
                f"Claude driver-analysis [{attempt_label}] JSON error: {e} "
                f"| raw[0:400]={text[:400]!r}"
            )
            return None, text

    try:
        # Attempt 1 — base prompt
        result, raw = await _call_and_parse(base_prompt, "attempt-1")

        # Attempt 2 — retry with a reinforced instruction after a JSON failure.
        # Commonly the model injects unescaped inner " quotes. We tell it to
        # replace them with «...» or ' and re-emit the JSON.
        if result is None:
            retry_prompt = (
                base_prompt
                + "\n\n---\nRITENTATIVO: il tentativo precedente ha prodotto JSON malformato. "
                "Rigenera l'output assicurandoti che NESSUNA stringa contenga virgolette doppie "
                "non escapate. Dentro le claim_esemplificativi usa SEMPRE le virgolette italiane "
                "«...» o l'apostrofo ' al posto della virgoletta doppia \"."
                " Verifica che il JSON sia perfettamente parseabile prima di restituirlo."
            )
            result, raw = await _call_and_parse(retry_prompt, "attempt-2-retry")

        if result is None:
            logger.error(
                f"Driver analysis failed for {brand} {model} after 2 attempts. "
                f"Last raw response (truncated): {raw[:600]!r}"
            )
            return None

        ranking = result.get("ranking_driver") or []
        ranking = [d for d in ranking if isinstance(d, dict) and d.get("driver") in DRIVER_TAXONOMY]
        for d in ranking:
            try:
                d["peso"] = max(0, int(d.get("peso") or 0))
            except (TypeError, ValueError):
                d["peso"] = 0

        # Renormalize pesi to exactly 100 when the model drifts
        total = sum(d["peso"] for d in ranking)
        if total > 0 and total != 100:
            for d in ranking:
                d["peso"] = round((d["peso"] / total) * 100)
            # correct rounding drift on the largest bucket
            drift = 100 - sum(d["peso"] for d in ranking)
            if drift != 0 and ranking:
                ranking.sort(key=lambda d: -d["peso"])
                ranking[0]["peso"] += drift

        ranking.sort(key=lambda d: -d["peso"])
        result["ranking_driver"] = ranking

        top = ranking[0]["driver"] if ranking else "N/A"
        logger.warning(
            f"Driver analysis L1 for {brand} {model}: "
            f"{len(ranking)} driver classificati, top={top}"
        )
        return result

    except Exception as e:
        logger.error(f"Claude driver-analysis error: {e}")
        return None


# ---------------------------------------------------------------------------
# L2 minireport — sintesi narrativa di articoli e commenti delle testate media
# ---------------------------------------------------------------------------

L2_MEDIA_SYNTHESIS_PROMPT = """Sei un analista che sintetizza la copertura editoriale media di un modello automobilistico.

Ricevi un pacchetto di contenuti editoriali pubblicati da testate giornalistiche italiane (riviste motori, rubriche motori dei quotidiani, canali YouTube ufficiali delle testate) su {brand} {model}. Ogni elemento include il testo del contenuto editoriale (articolo scritto OPPURE trascrizione automatica del parlato di un video editoriale, riconoscibile dall'URL youtube.com) e, quando disponibili, i commenti utenti pubblicati sotto l'articolo o sotto il video.

COMPITO: produrre un minireport sintetico con tre sezioni distinte.

OUTPUT (restituisci ESATTAMENTE questa struttura, UN solo oggetto JSON):

{{
  "is_l2_synthesis": true,
  "brand": "{brand}",
  "model": "{model}",
  "tono_commenti_utenti": {{
    "sentiment_dominante": "positivo | neutro | misto | critico",
    "n_commenti_analizzati": 0,
    "descrizione": "1-2 frasi che sintetizzano il tono complessivo dei commenti utenti riscontrati"
  }},
  "giornalisti_punti_forza": [
    {{
      "tema": "etichetta breve del tema (es. Design e identità, Rapporto qualità/prezzo, Comfort di marcia)",
      "descrizione": "1-2 frasi che riassumono ciò che i giornalisti apprezzano",
      "fonti": ["url_articolo_1", "url_articolo_2"]
    }}
  ],
  "giornalisti_punti_debolezza": [
    {{
      "tema": "etichetta breve",
      "descrizione": "1-2 frasi che riassumono la criticità segnalata dai giornalisti",
      "fonti": ["url_articolo"]
    }}
  ],
  "note_metodologiche": "limitazioni dell'analisi rispetto al pacchetto fornito (es. 'pochi articoli con prove su strada, prevalenza di news di prodotto'). NON menzionare fonti non presenti nel pacchetto come mancanze."
}}

REGOLE FONDAMENTALI:
1. **Punti di forza/debolezza**: identifica i temi RICORRENTI tra più contenuti editoriali (articoli + video, trattati uniformemente). Includi MASSIMO 5 temi per sezione, MINIMO 0 (lista vuota se non emergono temi solidi). Scarta i temi citati una sola volta.
2. **fonti**: SOLO URL effettivamente presenti nel pacchetto, MAI inventati. Se un tema emerge da un solo contenuto NON lo includere (regola di ricorrenza).
3. **descrizione**: parafrasa, NON riportare quote testuali letterali. Sintesi, non traduzione. Le trascrizioni dei video possono contenere errori di riconoscimento vocale o intercalari del parlato: estrai il senso, non i dettagli letterali.
4. **tono_commenti_utenti.n_commenti_analizzati**: conteggio totale dei commenti utenti nei contenuti forniti (somma di tutti i blocchi "Commenti utenti", inclusi quelli sotto i video YouTube).
5. **sentiment_dominante**: scegli il valore che meglio rappresenta la maggioranza dei commenti utenti analizzati. Se i commenti sono troppo pochi (<5) o assenti, usa "neutro" e segnalalo in `descrizione`.
6. NON confondere la voce dei giornalisti con quella degli utenti: i punti di forza/debolezza vanno estratti SOLO dal corpo dei contenuti editoriali (articoli scritti e trascrizioni di video di giornalisti), non dai commenti del pubblico.
7. Se il pacchetto è povero, lascia liste vuote con onestà — è preferibile a contenuto inventato.
8. Restituisci SOLO il JSON, nessuna spiegazione, nessun markdown.

REGOLE JSON (importanti — evitano output non parseabile):
- Nelle stringhe non usare mai virgolette doppie (") nidificate. Usa le virgolette italiane «...» o l'apostrofo tipografico '.
- Non inserire newline o tab grezzi dentro le stringhe.
- Verifica che il JSON sia un documento singolo valido prima di restituirlo.

PACCHETTO ARTICOLI:

{items_text}"""


async def analyze_l2_media_synthesis(
    items: list[dict], brand: str, model: str,
) -> dict | None:
    """Generate a synthetic L2 minireport from media articles + user comments.

    Single Claude call across all L2 items in the session. Returns a dict with
    `tono_commenti_utenti`, `giornalisti_punti_forza`, `giornalisti_punti_debolezza`.
    None on failure (caller falls back gracefully).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not items:
        return None

    parts = []
    total_user_comments = 0
    for i, item in enumerate(items):
        title = item.get("title", "Senza titolo")
        url = item.get("url", "")
        content = (item.get("content") or "")[:5000]
        ai_comments = item.get("ai_comments") or []
        total_user_comments += len(ai_comments)

        # Format embedded user comments compactly so the LLM can extract sentiment.
        comments_block = ""
        if ai_comments:
            sample = ai_comments[:30]  # cap per article to keep prompt manageable
            comment_lines = []
            for c in sample:
                if isinstance(c, dict):
                    txt = (c.get("text") or "").strip().replace("\n", " ")[:300]
                    if txt:
                        comment_lines.append(f"- {txt}")
            if comment_lines:
                more = f" (+{len(ai_comments) - len(sample)} ulteriori)" if len(ai_comments) > len(sample) else ""
                comments_block = (
                    f"\n\nCommenti utenti ({len(ai_comments)} totali{more}):\n"
                    + "\n".join(comment_lines)
                )

        parts.append(
            f"[{i+1}] Testata: derivata dall'URL\nTitolo: {title}\nURL: {url}\n\n{content}{comments_block}"
        )

    items_text = "\n\n===\n\n".join(parts)
    if len(items_text) > 80000:
        items_text = items_text[:80000] + "\n\n[... troncato]"

    base_prompt = L2_MEDIA_SYNTHESIS_PROMPT.format(
        brand=brand, model=model, items_text=items_text,
    )

    async def _call_and_parse(prompt_text: str, attempt_label: str) -> tuple[dict | None, str]:
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
                    "max_tokens": 6000,
                    "messages": [{"role": "user", "content": prompt_text}],
                },
            )
            if resp.status_code != 200:
                logger.error(
                    f"Claude L2-synthesis [{attempt_label}] API {resp.status_code}: "
                    f"{resp.text[:300]}"
                )
                return None, ""
            data = resp.json()
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text), text
        except json.JSONDecodeError as e:
            logger.warning(
                f"Claude L2-synthesis [{attempt_label}] JSON error: {e} "
                f"| raw[0:400]={text[:400]!r}"
            )
            return None, text

    try:
        result, raw = await _call_and_parse(base_prompt, "attempt-1")

        if result is None:
            retry_prompt = (
                base_prompt
                + "\n\n---\nRITENTATIVO: il tentativo precedente ha prodotto JSON malformato. "
                "Rigenera l'output assicurandoti che NESSUNA stringa contenga virgolette doppie "
                "non escapate. Usa SEMPRE «...» o l'apostrofo ' al posto della virgoletta doppia \". "
                "Verifica che il JSON sia perfettamente parseabile prima di restituirlo."
            )
            result, raw = await _call_and_parse(retry_prompt, "attempt-2-retry")

        if result is None:
            logger.error(
                f"L2 synthesis failed for {brand} {model} after 2 attempts. "
                f"Last raw response (truncated): {raw[:600]!r}"
            )
            return None

        # Sanity: ensure the section keys exist as lists/dicts; trim to max 5 each.
        result.setdefault("is_l2_synthesis", True)
        forza = result.get("giornalisti_punti_forza") or []
        debolezza = result.get("giornalisti_punti_debolezza") or []
        result["giornalisti_punti_forza"] = [
            f for f in forza if isinstance(f, dict) and f.get("tema")
        ][:5]
        result["giornalisti_punti_debolezza"] = [
            d for d in debolezza if isinstance(d, dict) and d.get("tema")
        ][:5]

        # Use the actual count we observed if model omitted/wrong-counted
        tono = result.get("tono_commenti_utenti")
        if isinstance(tono, dict):
            try:
                if not tono.get("n_commenti_analizzati"):
                    tono["n_commenti_analizzati"] = total_user_comments
            except Exception:
                tono["n_commenti_analizzati"] = total_user_comments

        logger.warning(
            f"L2 synthesis for {brand} {model}: "
            f"{len(result['giornalisti_punti_forza'])} plus, "
            f"{len(result['giornalisti_punti_debolezza'])} minus, "
            f"{total_user_comments} commenti utenti"
        )
        return result

    except Exception as e:
        logger.error(f"Claude L2-synthesis error: {e}")
        return None


# ---------------------------------------------------------------------------
# L3 minireport — sintesi della voce degli utenti, aggrega commenti utente da
# forum + youtube (user) + reddit/social + cross-import dai video editoriali L2.
# Dedup video_id è responsabilità del caller (in test_scrape.py).
# ---------------------------------------------------------------------------

L3_USER_SYNTHESIS_PROMPT = """Sei un analista che sintetizza la VOCE DEGLI UTENTI su un modello automobilistico.

Ricevi un pacchetto di commenti scritti dal pubblico (NON dai giornalisti) su {brand} {model}, raccolti da forum specialistici auto, thread Reddit, video YouTube di utenti e commenti pubblicati sotto video editoriali (recensioni di canali professionali). Ogni elemento è un singolo thread/video con il suo elenco di commenti utenti.

COMPITO: produrre un minireport sintetico che dia voce agli UTENTI, NON ai giornalisti. Il contenuto editoriale (articolo o trascrizione del giornalista) NON è incluso nel pacchetto — leggi e analizza solo i commenti.

OUTPUT (restituisci ESATTAMENTE questa struttura, UN solo oggetto JSON):

{{
  "is_l3_synthesis": true,
  "brand": "{brand}",
  "model": "{model}",
  "sentiment_globale": {{
    "dominante": "positivo | neutro | misto | critico",
    "n_commenti_analizzati": 0,
    "distribuzione": {{ "positivi": 0, "neutri": 0, "critici": 0 }},
    "descrizione": "1-2 frasi che sintetizzano l'umore complessivo del pubblico"
  }},
  "apprezzamenti_utenti": [
    {{
      "tema": "etichetta breve (es. Consumi reali, Comfort lunghe percorrenze, Design)",
      "descrizione": "1-2 frasi che riassumono cosa gli utenti apprezzano",
      "fonti": ["url_thread_1", "url_thread_2"]
    }}
  ],
  "critiche_problematiche": [
    {{
      "tema": "etichetta breve",
      "descrizione": "1-2 frasi sulla criticita segnalata dagli utenti",
      "fonti": ["url_thread"]
    }}
  ],
  "driver_acquisto": [
    {{
      "driver": "etichetta breve",
      "direzione": "pro | contro",
      "descrizione": "1-2 frasi: motivo emerso per cui gli utenti comprerebbero o NON comprerebbero"
    }}
  ],
  "domande_ricorrenti": [
    {{
      "tema": "etichetta breve della domanda (es. Compatibilita seggiolini, Autonomia reale invernale)",
      "esempi": ["parafrasi domanda 1", "parafrasi domanda 2"]
    }}
  ],
  "note_metodologiche": "limitazioni dell'analisi (es. 'pochi commenti reddit, prevalenza forum'). NON menzionare fonti non presenti nel pacchetto come mancanze."
}}

REGOLE FONDAMENTALI:
1. **Voce degli utenti**: l'analisi deve riflettere SOLO cio che gli utenti dicono nei commenti. Anche quando il thread origina da un articolo o video di un giornalista, qui ricevi unicamente i commenti — non confonderti con la voce editoriale.
2. **Temi ricorrenti**: includi un tema in `apprezzamenti_utenti` / `critiche_problematiche` / `driver_acquisto` SOLO se emerge da almeno 2 commenti distinti (preferibilmente in thread diversi). Scarta i temi citati una sola volta.
3. **MASSIMO 5** elementi per sezione (apprezzamenti, critiche, driver, domande), MINIMO 0 (lista vuota se non emergono pattern solidi).
4. **fonti**: SOLO URL effettivamente presenti nel pacchetto, MAI inventati.
5. **descrizione**: parafrasi sintetica, NON quote testuali letterali.
6. **sentiment_globale.distribuzione**: stima approssimativa (positivi + neutri + critici devono sommare circa a `n_commenti_analizzati`).
7. **sentiment_globale.dominante**: scegli il valore che meglio rappresenta la maggioranza dei commenti analizzati.
8. **domande_ricorrenti**: identifica solo domande GENUINE poste dagli utenti (con punto di domanda o forma "qualcuno sa se...", "chi ha esperienza con..."). MASSIMO 5.
9. Se il pacchetto e povero (<10 commenti totali), restituisci comunque la struttura ma quasi vuota, segnalando la scarsita in `note_metodologiche`.
10. Restituisci SOLO il JSON, nessuna spiegazione, nessun markdown.

REGOLE JSON (importanti — evitano output non parseabile):
- Nelle stringhe non usare mai virgolette doppie (") nidificate. Usa le virgolette italiane «...» o l'apostrofo tipografico '.
- Non inserire newline o tab grezzi dentro le stringhe.
- Verifica che il JSON sia un documento singolo valido prima di restituirlo.

PACCHETTO COMMENTI UTENTI:

{items_text}"""


async def analyze_l3_user_synthesis(
    items: list[dict], brand: str, model: str,
) -> dict | None:
    """Generate a synthetic L3 minireport from user comments aggregated across
    forum + youtube (user) + reddit/social + cross-imported comments from L2
    youtube_editorial items.

    Each `items[i]` is expected to expose `ai_comments` (list of {text,...}),
    `url`, `title` and `_source_type` (annotation set by the caller). Items
    without comments are silently skipped — L3 analysis is comments-only.

    Single Claude call. Returns a dict with the keys defined in
    L3_USER_SYNTHESIS_PROMPT, plus a `fonti_per_tipo` map computed
    server-side from observed `_source_type` (more reliable than letting
    the model count). None on failure (caller falls back gracefully).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not items:
        return None

    parts = []
    total_user_comments = 0
    per_type_threads: dict[str, int] = {}
    for i, item in enumerate(items):
        ai_comments = item.get("ai_comments") or []
        if not ai_comments:
            continue
        title = item.get("title", "Senza titolo")
        url = item.get("url", "")
        src_type = item.get("_source_type") or "unknown"

        sample = ai_comments[:60]
        comment_lines = []
        for c in sample:
            if isinstance(c, dict):
                txt = (c.get("text") or "").strip().replace("\n", " ")[:300]
                if txt:
                    comment_lines.append(f"- {txt}")
        if not comment_lines:
            continue

        per_type_threads[src_type] = per_type_threads.get(src_type, 0) + 1
        total_user_comments += len(ai_comments)
        more = (
            f" (+{len(ai_comments) - len(sample)} ulteriori)"
            if len(ai_comments) > len(sample) else ""
        )
        parts.append(
            f"[{i+1}] Tipo fonte: {src_type}\nTitolo thread: {title}\nURL: {url}\n"
            f"Commenti utenti ({len(ai_comments)} totali{more}):\n"
            + "\n".join(comment_lines)
        )

    if not parts:
        return None

    items_text = "\n\n===\n\n".join(parts)
    if len(items_text) > 80000:
        items_text = items_text[:80000] + "\n\n[... troncato]"

    base_prompt = L3_USER_SYNTHESIS_PROMPT.format(
        brand=brand, model=model, items_text=items_text,
    )

    async def _call_and_parse(prompt_text: str, attempt_label: str) -> tuple[dict | None, str]:
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
                    "max_tokens": 6000,
                    "messages": [{"role": "user", "content": prompt_text}],
                },
            )
            if resp.status_code != 200:
                logger.error(
                    f"Claude L3-synthesis [{attempt_label}] API {resp.status_code}: "
                    f"{resp.text[:300]}"
                )
                return None, ""
            data = resp.json()
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text), text
        except json.JSONDecodeError as e:
            logger.warning(
                f"Claude L3-synthesis [{attempt_label}] JSON error: {e} "
                f"| raw[0:400]={text[:400]!r}"
            )
            return None, text

    try:
        result, raw = await _call_and_parse(base_prompt, "attempt-1")

        if result is None:
            retry_prompt = (
                base_prompt
                + "\n\n---\nRITENTATIVO: il tentativo precedente ha prodotto JSON malformato. "
                "Rigenera l'output assicurandoti che NESSUNA stringa contenga virgolette doppie "
                "non escapate. Usa SEMPRE «...» o l'apostrofo ' al posto della virgoletta doppia \". "
                "Verifica che il JSON sia perfettamente parseabile prima di restituirlo."
            )
            result, raw = await _call_and_parse(retry_prompt, "attempt-2-retry")

        if result is None:
            logger.error(
                f"L3 synthesis failed for {brand} {model} after 2 attempts. "
                f"Last raw response (truncated): {raw[:600]!r}"
            )
            return None

        result.setdefault("is_l3_synthesis", True)
        for key in ("apprezzamenti_utenti", "critiche_problematiche",
                    "driver_acquisto", "domande_ricorrenti"):
            v = result.get(key) or []
            if key == "driver_acquisto":
                v = [d for d in v if isinstance(d, dict) and d.get("driver")]
            else:
                v = [d for d in v if isinstance(d, dict) and d.get("tema")]
            result[key] = v[:5]

        sent = result.get("sentiment_globale")
        if isinstance(sent, dict) and not sent.get("n_commenti_analizzati"):
            sent["n_commenti_analizzati"] = total_user_comments

        # Server-computed: more reliable than letting the model count thread types.
        result["fonti_per_tipo"] = per_type_threads

        logger.warning(
            f"L3 synthesis for {brand} {model}: "
            f"{len(result['apprezzamenti_utenti'])} plus, "
            f"{len(result['critiche_problematiche'])} minus, "
            f"{len(result['driver_acquisto'])} driver, "
            f"{len(result['domande_ricorrenti'])} questions, "
            f"{total_user_comments} commenti su {sum(per_type_threads.values())} thread"
        )
        return result

    except Exception as e:
        logger.error(f"Claude L3-synthesis error: {e}")
        return None


async def discover_trim_slugs(content: str, brand: str, model: str) -> list[str]:
    """Mini-call to Claude Haiku: identify trim/allestimento slugs from the model page.

    Takes the scraped text of the main model page and returns a lowercase list of
    URL-friendly slugs (e.g. ['pop', 'icon', 'la-prima', 'red']). These are then used
    to boost per-trim subpages in the URL ranker so we scrape them too.

    Returns empty list on any failure — caller should fall back to no-boost ranking.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not content:
        return []

    snippet = content[:8000]

    prompt = f"""Leggi questo contenuto estratto dalla pagina ufficiale {brand} {model}.
Identifica gli ALLESTIMENTI / VERSIONI commerciali citati (es. Pop, Icon, La Prima, RED, Cross, Sport, M-Sport, R-Line, GTI, Abarth).

NON includere:
- Motorizzazioni (benzina, diesel, ibrido, plug-in, elettrico, hybrid)
- Tagli di cilindrata (1.0, 1.5 TSI, 2.0 TDI)
- Nomi di modello o marca

REGOLE DI FORMATO (fondamentali):
- La tua risposta DEVE essere esclusivamente un JSON array di stringhe lowercase URL-friendly (trattini al posto degli spazi).
- NESSUN testo prima o dopo l'array. Nessuna spiegazione. Nessun commento.
- Esempio output valido: ["pop", "icon", "la-prima", "red"]
- Se nessun allestimento e' chiaramente identificabile, rispondi con: []

CONTENUTO:

{snippet}"""

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
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 256,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Haiku trim-slug API {resp.status_code}: {resp.text[:200]}")
                return []
            data = resp.json()
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        # Robust JSON array extraction — Haiku sometimes appends explanatory text
        # after the array (e.g. "[]\n\nNessun allestimento trovato.") which breaks
        # json.loads with "Extra data" error. We extract the first top-level array.
        arr = _extract_first_json_array(text)
        if arr is None:
            logger.warning(f"Trim slug: no JSON array parseable from response: {text[:200]!r}")
            return []
        if not isinstance(arr, list):
            return []
        # Normalize: lowercase, strip, hyphenate spaces, drop empties and duplicates
        seen = set()
        out = []
        for s in arr:
            if not isinstance(s, str):
                continue
            slug = s.strip().lower().replace(" ", "-")
            if slug and slug not in seen:
                seen.add(slug)
                out.append(slug)
        logger.warning(f"Discovered trim slugs for {brand} {model}: {out}")
        return out
    except Exception as e:
        logger.warning(f"Trim slug discovery failed for {brand} {model}: {e}")
        return []


def _extract_first_json_array(text: str):
    """Extract the first top-level JSON array from text, tolerating trailing content.

    Scans for '[' and walks characters tracking bracket depth + string/escape state
    so nested arrays and bracket-like chars inside strings are handled correctly.
    Returns parsed Python list, or None if not found / not parseable.
    """
    if not text:
        return None
    start = text.find("[")
    if start < 0:
        return None

    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
    return None
