# ✅ DONE — log task completati

> **Append-only, newest first.** Non si modifica il passato. Quando un
> task viene marcato ✅ in `SPRINT.md`, qui si aggiunge una riga in
> testa.

---

## Formato

```
### YYYY-MM-DD — [Titolo task]
- **Sprint:** ref allo sprint (es. settimana 19)
- **Esecutore:** Claude Code / utente / PM AI
- **Outcome:** cosa è cambiato
- **Note / link:** commit, PR, handoff archiviato, ecc.
```

---

## Log

### 2026-05-14 — Call Paolo 15:30 — progetto in stand-by ~2 settimane + scope cut su L2/L3/L4

- **Sprint:** 19-20 (settimana 1, giovedì)
- **Esecutore:** Ale (call) + PM AI (sintesi/aggiornamenti)
- **Outcome:** Call di 33 min in clima cordiale. **Progetto in stand-by ~2 settimane** per ragioni personali di Paolo (riavvio fine maggio / inizio giugno). Ale resta operativo in background, Paolo accede via login se serve. Decisioni di scope chiave:
  - **L2/L3/L4 → YouTube + Google Ads only**. Tagliate: Reddit, testate scritte L2 (Quattroruote/AlVolante/Motor1/Corriere/Repubblica/etc.), Perplexity trade press, Facebook Ads Library. Razionale: YouTube concentra naturalmente i 4-5 editori auto italiani + applica selezione editoriale automatica + Reddit produce commenti viziati (esempio in call: Sandero confusa come competitor di Grande Panda, segmenti diversi).
  - **L4 scope ridotto**: solo (a) n. creatività ultimi 6 mesi, (b) continuità temporale, (c) timeline. Niente spend €, niente messaggio chiave, niente affissioni. Caveat: timeline da testare empiricamente, se troppo onerosa si rinegozia.
  - **L3 deve diventare quantitativo**: aggiungere conteggi commenti per categoria (es. "motore inaffidabile su 7/10 vs 1/10"). Senza conteggio, 1 commento sfortunato è equivalente a un pattern diffuso.
  - **L1 Prestazioni** compilazione condizionale **ratificata da Paolo** (scope ridotto deciso da Ale il 13/5 → confermato).
  - **Ibrido "a sola ricarica" / generatore termico** in stand-by (nomenclatura non standard tra costruttori).
  - **"Assenza di dati è un dato"**: se YouTube non trova editoriali su un modello (esempio call: DR Evo 5), è informazione valida ("auto editorialmente trascurata, vende solo sul prezzo"). Non un fallimento dello scraping.
  - **L2YT diventerà L2** (rename + archiviazione know-how testate scritte, non buttare il lavoro fatto). Da fare post-stand-by.
- **Fatturazione attivata**: Paolo manda via email l'intestazione "l'altra società"; Ale emette prima fattura con ore svolte finora; pagamento entro fine maggio 2026.
- **Pending Paolo**: numero auto prototipo (dataset immatricolazioni — "ultima cosa") + intestazione fatturazione + verifica nomenclatura ibridi su dataset Quattroruote.
- **Note / link:** meeting note completo in `pm/sources/UNICAB_meeting_2026-05-14.md`. Doc prep call (`pm/projects/2026-05-14-prep-call-paolo.docx`) usato come scaletta, scope L4 v1 disegnato in mattinata (FB Ads + Google + Perplexity trade press) **superato** dalla decisione di Paolo (solo Google Ads).

---

### 2026-05-13 — Fix: cap items_text L2/L3 alzato da 80k a 600k char (recupero punti di debolezza)

- **Sprint:** 19-20 (settimana 1, follow-up del deploy L2YT)
- **Esecutore:** Claude Code
- **Outcome:** Emerso durante i test L2YT di Ale: confronto L2 standard (60 risultati Grande Panda, 29/04) vs L2YT (16 risultati, oggi) → L2 standard produceva **0 punti di debolezza** mentre L2YT con MENO contenuti ne trovava 3. Diagnosi: cap a 80 000 char nell'`items_text` passato a Claude in `analyze_l2_media_synthesis` (e analogamente in `analyze_l3_user_synthesis`) tagliava il ~85% del pacchetto su sessioni grandi — gli ultimi 40+ items L2 venivano scartati prima di arrivare al modello. Le prove su strada con critiche, presenti nelle testate di settore per ordine di iterazione (Quattroruote/Motor1 dopo le news brand), non venivano mai analizzate.
- **Fix in 2 step:**
  - Primo bump 80k → 300k (commit `bcb716d`): 55% del contenuto su Grande Panda 60 items.
  - Secondo bump 300k → 600k (commit `4bcf66c`, dopo feedback Ale): 100% del contenuto sulla stessa sessione. Claude Sonnet 4 ha context 200k token (~800k char), 600k = ~150k token → ~43k token di margine per prompt skeleton + output (max 6k).
- **Logging aggiunto:** ogni chiamata L2/L3 ora logga la dimensione effettiva del pacchetto (`INFO L2 synthesis items_text size: N chars (X items)`). Quando si tronca: `WARNING L2 synthesis items_text truncated: N -> 600000`. Permette di vedere subito in `docker compose logs scrapers` se future sessioni mostre escono fuori cap.
- **Conferma in prod:** Ale ha rilanciato L2 standard dopo il fix, i punti di debolezza ora compaiono. 2 deploy successivi (build scrapers + force-recreate + restart nginx).
- **Note / link:** commit `bcb716d` + `4bcf66c` (entrambi su `main`). File modificato: `scrapers/src/content_cleaner.py`.

---

### 2026-05-13 — Scheda Prestazioni in L1: numeri-chiave come evidence nella card driver

- **Sprint:** 19-20 (settimana 1)
- **Esecutore:** Claude Code
- **Outcome:** La card driver L1 "Prestazioni & Piacere di guida" ora mostra, sotto le citazioni virgolettate del sito brand, un blocco "Numeri-chiave (dal sito brand)" con tabella per versione (CV, kW, Nm, 0-100, V.max) + extras (peso curb in kg, autonomia WLTP EV in km, rapporto peso/potenza in kg/CV calcolato). I dati provengono dai campi già estratti da `OFFICIAL_PROMPT` per ogni item L1 sito brand (`prestazioni_per_versione`, `consumi_per_versione`, `dimensioni.peso_kg`): nessun cambio backend, nessun cambio prompt. Aggregazione cross-item lato frontend con dedup per (versione, alimentazione, cilindrata_cc) per evitare doppioni quando più pagine del sito brand citano la stessa versione.
- **Decisione di scope (Ale 2026-05-13):** i 3 driver target dell'handoff (`prestazioni_guida`, `heritage_identita`, `lifestyle_emozione`) NON sono stati "promossi" a card sempre visibili. Ale ha chiarito: «la card prestazioni deve funzionare come le altre card quando le info scarseggiano». Tutte e 9 le categorie mantengono il comportamento standard: card quando peso > 0, riga "Driver non comunicati" in fondo quando peso = 0. Verifica preliminare ontologia: tutte e 9 le categorie sono già presenti in `DRIVER_TAXONOMY` (`scrapers/src/content_cleaner.py:582-592`) e nel prompt `DRIVER_ANALYSIS_PROMPT`, e i frontend (`scraping_render.js`, `scraping_test.js`) hanno già `DRIVER_LABELS` corrispondenti.
- **File modificati (3, solo frontend):** `frontend/static/js/scraping_render.js`, `frontend/static/js/scraping_test.js`, `frontend/static/css/style.css`. Aggiunti helper `_collectPerformanceEvidence(items)` e `_renderPerformanceEvidence(items)`; signature `renderDriverAnalysis(info, items=[])` estesa; call site `renderOfficialInfo(info, items)` aggiornata per propagare `restItems` (gli items L1 non driver-analysis della stessa source). CSS: classi `.driver-card-perf-evidence`, `.driver-card-perf-title`, `.driver-card-perf-table`, `.driver-card-perf-extras` coerenti con lo stile delle card driver esistenti.
- **Note / link:** commit `f907ba5` (branch `claude/flamboyant-bohr-cb95ff` → merged in `main`). Deploy 2026-05-13: solo `git pull` + `docker compose restart nginx` (frontend ha bind-mount via `./frontend:/app/frontend` su api, niente rebuild richiesto). Verifica: pagine `/frontend/scraping-test` e `/frontend/anteprime` rispondono HTTP 307, `_renderPerformanceEvidence` presente 2 volte nel JS servito da prod (definizione + call site). Handoff archiviato in `handoff-archive/handoff-2026-05-12-d-scheda-prestazioni-l1.md`.

---

### 2026-05-13 — L2YT: flusso parallelo a L2 (solo YouTube editoriali) implementato e deployato

- **Sprint:** 19-20 (settimana 1)
- **Esecutore:** Claude Code
- **Outcome:** Introdotta una seconda fase di scraping `L2YT` permanente, accanto a L2 standard. L2YT interroga solo i 4 canali YouTube editoriali (Quattroruote, AlVolante, Motor1 Italia, DriveK) e produce lo stesso schema di minireport L2 (`l2_synthesis` in DB). L2 standard (8 testate news + 4 YouTube ed.) resta intatto. Selezionabile da admin "Test Scraping" → dropdown Fase, oppure via API.
  - Backend `app/api/scraping_test.py`: aggiunta entry `"L2YT": {"youtube_editorial"}` in `PHASE_SOURCE_TYPES`, threshold `PHASE_MIN_MATCHES["L2YT"] = 1`, validazione phase estesa.
  - Scrapers `content_cleaner.py:analyze_l2_media_synthesis()`: nuovo parametro `sources_used`. Quando contiene solo `youtube_editorial`, l'introduzione del prompt cambia per parlare esplicitamente di "solo trascrizioni video editoriali + commenti utenti sotto i video", evitando menzioni di testate scritte assenti (regola di non-invenzione).
  - Scrapers `test_scrape.py`: aggregator L2 calcola `l2_sources_used` e lo passa alla synthesis.
  - Frontend: nuova `<option value="L2YT">` nel dropdown admin; `PHASE_BADGES.L2YT` con label "L2YT YouTube" e classe CSS `phase-l2yt` (rosso tenue); helper `_normalizePhaseForRender()` per trattare L2YT come L2 nel rendering risultati e banner motore — i source_type restano `youtube_editorial` e ricadono naturalmente nella sezione L2 via `getLevel()`, mentre il badge della sessione mostra distintamente `L2YT YouTube`.
- **Note / link:** commit `2cd74fc` (branch `claude/flamboyant-bohr-cb95ff` → merged in `main`). Deploy 2026-05-13: `git pull` + `docker compose build scrapers` + `docker compose up -d --force-recreate api scrapers` + `restart nginx`. Sanity check post-deploy: container Up, logs puliti, HTTP 307 sulle pagine admin (atteso), keyword `L2YT` e `sources_used` presenti dentro i container. Handoff archiviato in `handoff-archive/handoff-2026-05-12-b-test-solo-youtube.md`.

---

### 2026-05-12 — L3 commenti: minireport voce utenti implementato e deployato

- **Sprint:** 19-20 (settimana 1)
- **Esecutore:** Claude Code
- **Outcome:** Layer 3 finalmente produce un report aggregato — prima raccoglieva commenti e li classificava per-comment ma non c'era una sintesi. Aggiunto:
  - Modello DB: `ScrapingSession.l3_synthesis` JSONB + colonna applicata in prod via psql
  - Funzione `analyze_l3_user_synthesis()` in `content_cleaner.py`: 1 chiamata Claude Sonnet 4 con prompt focalizzato sulla voce utenti (sentiment globale + distribuzione, apprezzamenti, critiche, driver pro/contro, domande ricorrenti, fonti per tipo, note metodologiche)
  - Aggregator in `test_scrape.py` con dedup video_id (i commenti dei video editoriali L2 confluiscono in L3 senza essere riscrappati; se un video YouTube risulta sia in L2 sia in L3, lo skippiamo in L3 per evitare doppio conteggio)
  - Soglia minima 10 commenti totali per triggerare la chiamata Claude
  - **Filtro semantico target nel prompt L3**: sezione "FILTRO TARGET" istruisce Claude a estrarre SOLO materiale che riguarda il modello target (per evitare contaminazione da altre versioni omonime es. "Panda 4x4" quando il target è "Grande Panda"). Filtri sessione (alim, cilindrata) propagati al prompt
  - API save/load `l3_synthesis` come per `l2_synthesis`
  - Render frontend: card "💬 Minireport L3 — Sintesi voce utenti" in cima alla sezione L3 (sia in scraping_test live sia in Anteprime archiviate), con stili dedicati (verde, distrib pills sentiment, pill fonti per tipo, badge pro/contro per driver)
- **Note / link:**
  - Commit `03a39d8` (backend + scrapers), `9113e02` (UI), `62ba086` (filtro target)
  - Test riuscito su Fiat Grande Panda 1.2 benzina: 1048 commenti su 47 thread → 3 apprezzamenti, 5 critiche, 3 driver, 2 domande. Senza filtro target la sintesi conteneva riferimenti spuri a Panda 4x4/Hybrid; col filtro semantico questi sono spariti.
  - **Domani**: altri test su modelli diversi (BMW Serie 3, Honda Jazz o altri) per validare robustezza del filtro target su nomi diversi
  - Handoff archiviato → `pm/pm-agent/handoff-archive/handoff-2026-05-12-a-l3-ground-truth.md`
  - **Nota deploy**: trovato che `docker compose up -d --force-recreate scrapers` NON ribuilda l'immagine se `build: ./scrapers` è senza bind-mount. Serve sempre `docker compose build scrapers` PRIMA. Inoltre dopo `force-recreate` di api/scrapers, nginx va sempre restartato (cache IP container)
  - Tutti gli endpoint che servono session data (`/sessions/{id}/results`, etc.) ora ritornano anche `l3_synthesis`

### 2026-05-10 — Popolamento iniziale PM (sprint 19-20, scope Release 0.0)
- **Sprint:** kickoff sprint 19-20 (11-24 maggio)
- **Esecutore:** PM AI (su input Ale, prima sessione PM)
- **Outcome:** popolati `pm/SPRINT.md` (3 P0, 3 P1, 3 P2), `pm/BACKLOG.md` (4 desiderate post-prototipo), creato `pm/projects/release-0-0-prototipo.md` con scope distillato dalla call Paolo 4/5, aggiunta nota di de-prioritizzazione L1 in `pm/projects/00-stato-progetto.md`. Creata cartella `pm/sources/` con sintesi call 4/5 + README convenzioni; cartella da gitignore (handoff aperto per Code).
- **Note / link:** handoff `pm/pm-agent/handoff-2026-05-10-a-gitignore-pm-sources.md` da eseguire PRIMA del primo `git add pm/`. Modello PM ↔ Ale validato in pratica (proporre → confermare → scrivere → avvisare per push).

### 2026-05-10 — Setup struttura PM coordinata Cowork/Code
- **Sprint:** —
- **Esecutore:** Claude Code (su input utente)
- **Outcome:** creata `pm/` come single source of truth PM, scritto
  `CLAUDE.md` con mappa tecnica, codificato workflow di sync git
  (PM AI lavora locale, Code è l'unico operatore git), allargati
  permessi di lettura PM a `Docs/` e `CLAUDE.md`, popolato
  `pm/projects/00-stato-progetto.md` come brief operativo iniziale.
- **Note / link:** PR [#1](https://github.com/mialarussa-hub/unicab-report-automotive/pull/1)
  (struttura base) + PR [#2](https://github.com/mialarussa-hub/unicab-report-automotive/pull/2)
  (workflow sync git). Terza PR per popolamento contesto in arrivo.

_(i nuovi item vanno **in cima**, sopra questa riga)_
