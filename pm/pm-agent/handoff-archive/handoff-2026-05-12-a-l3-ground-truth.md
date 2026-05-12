# Handoff: L3 commenti — ground truth check

**Data:** 2026-05-12
**Da:** PM AI
**A:** Claude Code
**Priorità:** P0
**Stima rough:** S (<1h) — è una verifica, non implementazione
**Stato:** 🆕 Nuovo

---

## Contesto

Call con Paolo confermata **giovedì 14/5 alle 15:30**. Uno dei punti
all'OdG è lo stato del Layer 3 (commenti utenti). In `pm/SPRINT.md`
risulta P0 da chiudere ma con stima residua "~8h+" generica e nota
"era da chiudere entro 5 maggio, in realtà non è chiuso".

Il PM ha bisogno di sapere **con esattezza** cosa è già live di L3 e
cosa manca, per:
1. Dare ad Ale una risposta credibile a Paolo in call ("siamo a X%")
2. Stimare correttamente il residuo per riprogrammare la chiusura
3. Aggiornare `pm/SPRINT.md` e `pm/projects/release-0-0-prototipo.md`
   con la verità del codice

## Obiettivo

Mappare lo stato reale di L3 (ingest commenti + sentiment) confrontando
codice live, DB, e quanto pianificato/promesso.

## Acceptance Criteria

- [ ] Identificate le fonti commenti già integrate e funzionanti in
      produzione (YouTube? Reddit? Forum? altro?), con riferimenti a
      file/funzioni
- [ ] Identificate le fonti commenti pianificate ma **non** integrate
- [ ] Verificato lo stato della sentiment pipeline: cosa elabora oggi
      (quali tabelle/sorgenti), cosa no
- [ ] Conta righe attuali nelle tabelle commenti / sentiment (per dare
      ordine di grandezza ad Ale: "abbiamo già X commenti analizzati")
- [ ] Stima residua per chiudere L3 nello scope concordato con Paolo
      (vedi `pm/sources/2026-05-04-call-paolo.md` se rilevante e
      accessibile in lettura)
- [ ] Risultato riportato in `pm/pm-agent/FEEDBACK.md` come messaggio
      `[Code → PM]` con titolo "L3 ground truth — esito"

## File coinvolti (sospetti)

Il PM non conosce il codice nel dettaglio. Aree probabili:

- `scrapers/src/` — moduli ingest commenti (YouTube, Reddit, ev. forum)
- `backend/app/models/sentiment.py`
- Tabelle DB: commenti, sentiment (nomi da verificare)
- Eventuali script in `n8n/` per orchestrazione L3

## Vincoli / non-goals

- **Non implementare nulla.** Solo verifica + reporting al PM.
- Non toccare codice né schema DB.
- Se durante la verifica emergono bug evidenti → segnalali in FEEDBACK
  come follow-up, non fixarli in questo handoff.

## Note

- Output di riferimento per Paolo: "L3 commenti = X% pronto, manca Y,
  stima Z giorni". Punta a questa granularità.
- Se possibile, indicare 1-2 modelli auto su cui L3 è già visibile/
  testabile in UI — utile per la demo in call.

---

## 📤 Esito

**Esito:** ✅ (chiuso 2026-05-12) — andato oltre il ground-truth: ground-truth + implementazione completa + deploy in prod + test riuscito.

**Cosa è stato fatto:**

1. **Ground truth check** (richiesta originale dell'handoff): mappato lo stato L3 nel codice live.
   - **Ingest commenti**: forum (XenForo/IPS/AlVolante), YouTube user, Reddit (Arctic Shift) tutti funzionanti. Lo stub `scrapers/src/reddit.py` (`NotImplementedError`) è codice morto — il vero scraper Reddit vive in `_scrape_reddit_source` (test_scrape.py:848) e usa `RedditClient` direttamente.
   - **Sentiment per-comment**: funzionante via `SENTIMENT_PROMPT` + Claude in `content_cleaner.py`. Salvato in `scraping_results.ai_comments` JSONB.
   - **Report aggregato L3**: **NON esisteva**. Grep `l3_synthesis|analyze_l3` → 0 match. Confermato il bug che Ale aveva notato il 4/5 ("vedo commenti ma niente report").
   - Conclusione: L3 era ~50% pronto (ingest + sentiment OK, sintesi missing).

2. **Implementazione completa del minireport L3** (scope ampliato rispetto a "solo ground truth", su decisione Ale):
   - Modello DB: aggiunta colonna `ScrapingSession.l3_synthesis JSONB` (migrazione Alembic 003 + DDL psql diretto in prod come da convenzione).
   - Funzione `analyze_l3_user_synthesis()` in `content_cleaner.py` — 1 chiamata Claude Sonnet 4. Output JSON: `sentiment_globale` (dominante + distribuzione + descrizione), `apprezzamenti_utenti`, `critiche_problematiche`, `driver_acquisto` (pro/contro), `domande_ricorrenti`, `fonti_per_tipo`, `note_metodologiche`.
   - Aggregator in `test_scrape.py` con cross-import L2→L3 (i commenti dei video editoriali confluiscono in L3 senza essere riscrappati) e dedup per `video_id` YouTube (se un video appare sia in L2 che in L3, viene contato una volta sola).
   - Soglia minima 10 commenti totali per triggerare la chiamata Claude (evita sintesi inventate su dataset miseri).
   - **Filtro semantico target** nel prompt L3: sezione FILTRO TARGET istruisce Claude a estrarre SOLO materiale che riguarda il modello target. Filtri sessione (`alimentazione`, `cilindrata`) propagati al prompt. Aggiunto per risolvere il problema scoperto in test: con phase=L3 su Fiat Grande Panda lo scraping pesca anche commenti su altre Panda (4x4, Hybrid, Classic) e Claude le includeva nella sintesi. Filtro semantico (no esempi hardcoded) generalizza a qualsiasi modello.
   - API: save in `_run_scraping_background`, load in `get_session_results`.
   - Frontend: nuova card "💬 Minireport L3 — Sintesi voce utenti" con sentiment globale + distribuzione, sezioni apprezzamenti / critiche / driver (con badge pro/contro) / domande ricorrenti, pill fonti per tipo, note metodologiche. Stili dedicati (border-left verde L3, distrib pills, fonte pills colorate per tipo).

3. **Deploy in produzione**:
   - Pull codice su Hetzner CX33 in /opt/unicab
   - DDL applicata via psql diretto: `ALTER TABLE scraping_sessions ADD COLUMN l3_synthesis JSONB`
   - Container `scrapers` ricostruito (build) + ricreato. **Lezione operativa**: `force-recreate` da solo non basta per `scrapers` (no bind-mount), serve `build` prima. `api` invece usa bind-mount quindi force-recreate è sufficiente.
   - Nginx restartato dopo recreate (cache IP container Docker).
   - Documentato in DEPLOY.md.

4. **Test end-to-end** su Fiat Grande Panda (phase=L3, benzina, 1.2L):
   - 1° run senza filtro target: sintesi conteneva temi su Panda 4x4 / Hybrid (off-target).
   - 2° run con filtro target attivo: sintesi pulita — 3 apprezzamenti, 5 critiche, 3 driver, 2 domande su 1048 commenti / 47 thread. Ale conferma "molto meglio".

**File modificati:**
- `backend/app/models/scraping.py`
- `backend/alembic/versions/003_add_l3_synthesis_column.py` (nuovo)
- `backend/app/api/scraping_test.py`
- `scrapers/src/content_cleaner.py`
- `scrapers/src/test_scrape.py`
- `frontend/static/js/scraping_test.js`
- `frontend/static/js/scraping_render.js`
- `frontend/static/css/style.css`
- `pm/ops/DEPLOY.md` (nota build scrapers + nginx restart)

**Commit:**
- `03a39d8` — feat(l3): minireport sintesi voce utenti (backend + scrapers)
- `9113e02` — feat(l3): UI render minireport voce utenti
- `62ba086` — feat(l3): filtro semantico target nel prompt L3

**Note per il PM:**
- L3 è chiuso a livello di prototipo, **pronto per la call Paolo del 14/5**. Da segnalare in call come "Layer 3 ora produce un minireport user-voice aggregato + visibile in UI; il filtro semantico target rende la sintesi robusta a contaminazioni da altre versioni omonime".
- **Domani sono previsti altri test** (BMW Serie 3, Honda Jazz o altri modelli) per validare il filtro target su nomi diversi. Se emergono regressioni le segnalerò.
- Cross-link L2→L3 funziona: i commenti dei video editoriali L2 (Quattroruote, AlVolante, Motor1, DriveK) confluiscono nel report L3 con il loro contributo, senza essere riscrappati. Dedup per video_id evita doppio counting.
- Comportamento sui filtri fase: con "Solo L2" il report L3 NON viene generato (i commenti dei video editoriali finiscono dentro `tono_commenti_utenti` di L2 come prima). Con "Solo L3" il report L3 gira sui soli dati L3 nativi (cross-import vuoto). Con "Tutte" si ha sia L2 sia L3 senza sovrapposizioni.

**Follow-up emersi:**
- (Opzionale) Bottone "rigenera report L3" su sessione esistente per riprocessare la sintesi senza ri-scrappare. Utile per testare nuovi prompt su dataset già raccolti. Non implementato ora — scope creep.
- (Opzionale) Livello 2 filtro hard: skippare interi thread il cui titolo non contiene tutte le parole del modello target. Discusso con Ale, deciso di non implementarlo subito perché il Livello 1 (filtro semantico nel prompt) sembra sufficiente. Da rivalutare se nei test di domani emergono ancora contaminazioni.
