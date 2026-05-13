# Handoff: Scheda "Prestazioni & Piacere di guida" in L1 + verifica altre card driver

**Data:** 2026-05-12
**Da:** PM AI
**A:** Claude Code
**Priorità:** P1
**Stima rough:** M (1-4h)
**Stato:** ✅ Chiuso 2026-05-13 (con scope ridotto da decisione Ale — vedi Esito)

---

## Contesto

L1 oggi produce per ogni modello una serie di card-driver con
percentuale di "peso comunicativo" + citazioni dirette dal sito
brand (es. "Tecnologia & Innovazione 12%", "Sicurezza & ADAS 9%"
sulla Honda Jazz, con citazioni virgolettate sotto). In fondo alla
pagina compare una riga di testo **"Driver non comunicati:
Prestazioni & Piacere di guida, Heritage & Identità brand, Lifestyle
& Emozione..."** — quindi questi driver **esistono già nell'ontologia**
ma vengono mostrati come "non comunicati" relegati a una riga di
testo, non come card di pari dignità.

Paolo (in call 4/5 e re-confermato per la call 14/5 alle 15:30) ha
chiesto di **mettere a regime la scheda "Prestazioni"** in L1, dato
che è uno dei driver comunicativi più rilevanti per i modelli
sportivi/premium e per molti segmenti.

**Importante (framing):** L1 NON è "raccogli dati tecnici". L1 è
"leggi cosa il brand comunica del modello e classificalo per driver".
I numeri-chiave (0-100, potenza, peso, ecc.) servono come **evidenza
a corredo delle citazioni**, non come fine. Stessa logica delle card
esistenti (ADAS, Tecnologia): citazioni testuali dal sito brand +
attribuzione canale ("Canali: sito brand").

## Obiettivo

(1) La card **"Prestazioni & Piacere di guida"** è visibile in L1 con
la stessa estetica delle altre card-driver (percentuale + citazioni
+ canali), anche quando il brand non comunica quel driver (in tal
caso → card a 0% / "non comunicato" ma graficamente presente, non
relegata a una riga di testo in fondo).

(2) Quando il brand **sì** comunica le prestazioni, la card include
sotto le citazioni anche i **numeri-chiave prestazionali** del modello
presi dal sito ufficiale, come evidence di contesto.

(3) Stessa promozione "da riga di testo a card visibile" applicata
anche a **Heritage & Identità brand** e **Lifestyle & Emozione**
(verificare prima che siano effettivamente nell'ontologia driver e
non solo nella riga di testo).

## Acceptance Criteria

- [ ] La card "Prestazioni & Piacere di guida" è mostrata in L1 con
      lo stesso layout delle card driver attualmente comunicati
      (titolo, %, descrizione, citazioni virgolettate, "Canali: sito
      brand")
- [ ] Quando il driver è comunicato (es. modelli sportivi/premium) e
      ha % > 0, la card include in coda alle citazioni i **dati
      prestazionali estratti dal sito brand**: 0-100 km/h, velocità
      max, potenza (kW/CV), coppia, peso, rapporto peso/potenza,
      ripresa se disponibile. Per elettriche/ibride aggiungere
      autonomia WLTP e tempo di ricarica
- [ ] Quando il driver **non** è comunicato (% = 0), la card è
      comunque visibile con stato "non comunicato" — non più relegata
      alla riga di testo in fondo. Decidere se in quel caso mostrare
      comunque i numeri (utile per Paolo come benchmark) o lasciarla
      vuota: **proporre la scelta in FEEDBACK** prima di implementare
- [ ] Stesso trattamento applicato a **Heritage & Identità brand**
      e **Lifestyle & Emozione** (promozione a card visibile sempre)
- [ ] Verifica preliminare: queste 3 categorie sono effettivamente
      nell'ontologia driver oppure sono solo nomi in una stringa
      hard-coded? Se la seconda → segnalare in FEEDBACK come
      pre-requisito di disegno (allora va deciso con Ale)
- [ ] Test su **2 modelli pilota**: **Honda Jazz** (caso atteso: Honda
      non comunica prestazioni → card a 0% / "non comunicato") + **1
      premium o sportivo a scelta** (caso atteso: prestazioni
      comunicate → card valorizzata con citazioni + dati). Proporre
      il secondo modello in FEEDBACK se non ovvio da scelte
      precedenti
- [ ] Risultato accessibile in UI (sezione "Anteprima") al login Paolo

## File coinvolti (sospetti)

- Ontologia driver L1 (file da identificare — probabile in
  `scrapers/` o `backend/app/`)
- Pipeline analisi L1 sito brand (prompt AI che classifica le
  citazioni per driver — file da identificare)
- Template frontend che renderizza le card-driver (frontend/)
- Eventuale scraper dati tecnici (per i numeri prestazionali —
  potrebbe già esistere nel modulo "motore"/specs)

## Vincoli / non-goals

- **Non rifattorizzare** l'ontologia driver oltre la promozione delle
  3 categorie. Se si scopre che l'ontologia è messa male →
  segnalare in FEEDBACK come follow-up, non riscriverla qui
- **Non cambiare** il framing di L1 ("comunicazione brand", non
  "dati tecnici"). I numeri sono evidence sotto le citazioni, non
  l'oggetto principale della card
- **Non rifare** lo stile UI delle card esistenti — replicarlo
- Non aggiungere fonti diverse dal sito brand per questa card:
  l'attribuzione resta "Canali: sito brand"

## Note

- Esempio visivo del layout target: cfr. card "Tecnologia &
  Innovazione" e "Sicurezza & ADAS" già live su Honda Jazz. Stessa
  struttura per "Prestazioni" + le altre 2 promosse
- Se i dati prestazionali non sono tutti reperibili dal sito brand
  ufficiale (es. ripresa 80-120 spesso assente) → riportare solo
  quelli disponibili, non integrare da fonti terze in questo handoff
- Per il modello premium/sportivo del test, una scelta utile per
  Ale in call è qualcosa allineato col probabile prototipo (cfr.
  pending Paolo "numero modelli"): proporre 1-2 candidati e
  lasciare scegliere ad Ale in FEEDBACK se non ovvio

---

## 📤 Esito (compilato da Claude Code 2026-05-13)

**Esito:** ✅ con **scope ridotto** dalla decisione di Ale 2026-05-13.

### Decisione di Ale che ha modificato lo scope
- **Acceptance Criteria 1, 3, 4** (promozione di Prestazioni / Heritage / Lifestyle a card sempre visibili anche con peso=0) — **NON eseguiti**. Ale ha esplicitamente detto: «la card prestazioni deve funzionare come le altre card quando le info scarseggiano». Quindi tutte e 9 le categorie mantengono il comportamento standard: card quando peso > 0, riga "Driver non comunicati" in fondo quando peso = 0. Niente trattamento speciale per le 3 categorie target.
- **Acceptance Criterion 5** (verifica ontologia) — ✅ verificato preliminarmente: tutte e 9 le categorie target sono già in `DRIVER_TAXONOMY` (`scrapers/src/content_cleaner.py:582-592`) e nel prompt `DRIVER_ANALYSIS_PROMPT` che richiede esplicitamente tutti 9 i driver con peso=0 inclusi. Frontend `DRIVER_LABELS` allineati (`scraping_render.js:41-51`, `scraping_test.js:1305-1316`). Nessun refactor d'ontologia necessario.
- **Acceptance Criteria 2 + 6 + 7** (numeri-chiave nella card Prestazioni + test su modelli + visibilità in Anteprima) — ✅ eseguiti. La parte di test sui modelli la fa Ale direttamente in prod («i testi li faccio io! non t'interessa sapere su quali auto testerò»).

### Cosa è stato fatto
- **Card driver `prestazioni_guida`** arricchita: quando il driver ha peso > 0, sotto le citazioni e l'attribuzione canali appare un nuovo blocco **"Numeri-chiave (dal sito brand)"** con:
  - **Tabella per versione**: colonne Versione, CV, kW, Nm (coppia), 0-100 (s), V.max (km/h). Dedup per (versione, alimentazione, cilindrata_cc) per evitare doppioni cross-pagine.
  - **Extras** (riga sotto la tabella, separati da ·): Peso curb (kg), Autonomia WLTP EV (km, massimo cross-versione), Peso/potenza (kg/CV) calcolato sul CV massimo disponibile.
  - **Solo dati realmente estratti**: se un campo manca, non viene mostrato. Niente integrazione da fonti terze (come da vincolo handoff).
- I dati provengono dai campi **già estratti** da `OFFICIAL_PROMPT` in `content_cleaner.py` (`prestazioni_per_versione`, `consumi_per_versione`, `dimensioni.peso_kg`) presenti per-item negli items L1 sito brand. **Nessun cambio backend, nessun cambio prompt.**
- Aggregazione cross-item lato frontend: gli items L1 della stessa source-card (escluso quello con `is_driver_analysis=true`) vengono passati a `renderDriverAnalysis(info, items)` che li riusa solo per la card Prestazioni.
- Stile coerente con le card driver esistenti: sfondo grigio chiaro (`#f8fafc`), border 1px slate-200, font 0.82rem, table compatta.

### File modificati (3, solo frontend)
- `frontend/static/js/scraping_render.js` (usato da Anteprime + viewer sessioni)
- `frontend/static/js/scraping_test.js` (pagina admin Test Scraping)
- `frontend/static/css/style.css` (classi `.driver-card-perf-evidence`, `.driver-card-perf-title`, `.driver-card-perf-table`, `.driver-card-perf-extras`)

In entrambi i JS: nuovo helper `_collectPerformanceEvidence(items)` con dedup, helper di rendering `_renderPerformanceEvidence(items)`, signature estesa `renderDriverAnalysis(info, items=[])` e `renderOfficialInfo(info, items=[])`, call site della source-card L1 passa ora `restItems`.

### Commit
`f907ba5` (branch `claude/flamboyant-bohr-cb95ff` → merged in `main`).

### Deploy
2026-05-13. Solo `git pull` + `docker compose restart nginx` (frontend ha bind-mount `./frontend:/app/frontend` su api, niente rebuild necessario). Verifica: pagine admin/anteprime rispondono HTTP 307 (atteso), `_renderPerformanceEvidence` presente 2 volte nel JS servito da `https://unicab.automica.it/frontend/static/js/scraping_render.js`.

### Vincoli rispettati
- L1 framing invariato: "comunicazione brand" ≠ "dati tecnici". I numeri sono evidence sotto le citazioni, non l'oggetto principale della card.
- Stile UI delle card esistenti replicato, non rifatto.
- Nessuna fonte aggiunta oltre il sito brand (attribuzione "Canali: sito brand" invariata).
- Ontologia driver non rifattorizzata oltre la conferma di completezza.

### Note per il PM
- **La scelta di non promuovere le 3 categorie a card sempre visibili è di Ale, non un'omissione di Code.** L'handoff originale prevedeva la promozione (criteri 1, 3, 4); Ale ha ricalibrato ribattendo che il comportamento deve essere «come le altre». Se in call con Paolo si conferma invece che Prestazioni *deve* avere visibilità anche a 0%, l'estensione è banale (un branch nel filtro `inactive` nel rendering driver-details per i 3 driver target). Lo annoto come follow-up disponibile.
- Per il test in prod: bastano 2 modelli — uno che comunica le prestazioni (premium/sportivo) e uno che non le comunica (es. Honda Jazz, citato come esempio nell'handoff). Sul primo si vedrà la card popolata coi numeri-chiave, sul secondo la card non comparirà — ed è il comportamento "come le altre" voluto.
- Test sui modelli li esegue direttamente Ale come per L2YT.

### Follow-up emersi
- **Tempo di ricarica** per EV: non è oggi estratto da `OFFICIAL_PROMPT` (consumi_per_versione ha solo `autonomia_elettrica_km`, non `tempo_ricarica`). Se in call viene richiesto esplicitamente, è una piccola estensione del prompt.
- **Ripresa 80-120 km/h**: idem, non oggi estratto. L'handoff lo elencava come "se disponibile" → conforme.
- **Visibilità sempre-on per i 3 driver target** (proseguimento dell'handoff originale): se Paolo conferma la richiesta in call, è un'estensione di poche righe nel rendering — riservare un branch `if (['prestazioni_guida','heritage_identita','lifestyle_emozione'].includes(d.driver))` nel loop inactive per renderizzare comunque la card-shell.
