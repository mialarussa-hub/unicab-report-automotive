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
