# Handoff: Indagine anomalia L2 vs L2YT — temi YT "scompaiono" nel L2 aggregato

**Data:** 2026-05-14
**Da:** PM AI
**A:** Claude Code
**Priorità:** P0
**Stima rough:** S (<1h, prevalentemente lettura codice + diff prompt)
**Stato:** 🆕 Nuovo

---

## Contesto

Confronto tra i due minireport prodotti oggi su **Fiat Grande Panda**:

- **L2 standard** (8 testate + 4 canali YT editoriali) → 1850 commenti, top-3 forza: design, spaziosità, comfort di marcia; top-3 debolezza: consumi urbani, qualità costruttiva, affidabilità PureTech.
- **L2YT** (solo 4 canali YT editoriali) → 330 commenti, top-4 forza: design, spaziosità, **sistema multimediale**, **posizione di guida**; top-3 debolezza: **problemi sterzo/maneggevolezza** (da test stabilità), consumi urbani, qualità materiali.

**Anomalia osservata da Ale:** L2 ⊇ L2YT come fonti, quindi L2 dovrebbe essere un *superset* dei temi di L2YT. Invece **temi tecnici puntuali emergono solo in L2YT e scompaiono in L2** (sterzo/maneggevolezza, infotainment, posizione di guida). Lo scenario inverso (L2YT "più diluito" perché meno fonti) sarebbe quello atteso.

Il sospetto è che il problema sia di **pipeline di sintesi**, non di scraping (gli items YT sono nel pool L2 come confermato dall'handoff L2YT del 12/5). Il cap items_text è già stato portato a 600k il 13/5 (commit `4bcf66c`), quindi *non* dovrebbe essere troncamento. Ma il fix è recente: la sessione L2 Grande Panda usata per il confronto potrebbe essere pre-fix oppure post-fix, va verificato.

**Obiettivo strategico (Ale):** stiamo testando i due flussi per decidere quale tenere. Senza capire la causa di questa anomalia, il confronto qualitativo dei due minireport non è interpretabile.

## Obiettivo

Capire **perché temi presenti nel pool YT vengono persi nel minireport L2 aggregato** ma sopravvivono nel minireport L2YT, e rispondere alle 4 domande diagnostiche sotto.

## Acceptance Criteria

- [ ] Risposta verificata alla domanda **1 — Inclusione**: i contenuti dei 4 canali YouTube editoriali (trascrizioni + commenti video) entrano effettivamente nel pacchetto `items_text` passato a Claude per la sintesi L2 nella sessione Grande Panda usata per il confronto? (sì/no con evidenza dal codice e/o dai log della sessione specifica)
- [ ] Risposta verificata alla domanda **2 — Prompt**: il prompt di sintesi usato da L2 e L2YT è lo **stesso** o sono **due prompt diversi**? (diff testuale, oppure stesso prompt con variabile dinamica come `sources_used` notata in handoff L2YT del 13/5)
- [ ] Risposta verificata alla domanda **3 — Pipeline**: tra raw scrape e sintesi finale c'è un passaggio intermedio (es. chunking, summary-of-summaries, dedup tematica, weighting per fonte) che in L2 esiste e in L2YT no, o che si comporta in modo diverso al variare del numero di fonti? (descrivere il flusso)
- [ ] Risposta verificata alla domanda **4 — Selezione top-N**: con quale criterio il modello/codice estrae i "top-3 punti di forza/debolezza"? È prompt-driven (judge call del modello) o c'è un post-processing che conteggia/ordina? Se è judge call, com'è formulata la richiesta?
- [ ] Indicazione **causa probabile** dell'anomalia (una o più tra: diluizione per voto di maggioranza implicita nel prompt, prompt divergenti, sommarizzazione intermedia distruttiva, clustering tematico che assorbe segnali minoritari, bug di inclusione fonti, sessione L2 confrontata pre-fix cap 600k)
- [ ] Indicazione delle **leve d'azione possibili** per riallineare i due flussi (es. modifica prompt per richiedere copertura per-tipo-fonte, weighting esplicito, top-N esteso, ecc.) — solo elenco di opzioni, **non implementare nulla**

## File coinvolti (sospetti)

Il PM non conosce i path esatti, Code verifica. Probabili:

- `scrapers/src/content_cleaner.py` — funzione `analyze_l2_media_synthesis()` citata nell'handoff L2YT (gestisce il prompt L2 con `sources_used` dinamico)
- Eventuale modulo dedicato alla sintesi/aggregazione cross-source (cerca per `synthesis`, `synthesize`, `aggregate`, `media_summary`)
- Prompt template L2 / L2YT (string constants nel modulo sintesi)
- Log delle 2 sessioni Grande Panda confrontate (sessione L2 standard usata per il minireport "1850 commenti" e sessione L2YT "330 commenti"). Da `docker compose logs scrapers | grep "synthesis items_text"` si ricava la size effettiva per ciascuna sessione (logging aggiunto da Code il 13/5).

## Vincoli / non-goals

- **NON modificare il prompt o la pipeline** in questo handoff. È solo **diagnosi**. Le eventuali modifiche le decidiamo dopo, in un secondo handoff, una volta capita la causa.
- **NON rilanciare scrape** se non strettamente necessario per la diagnosi. Le 2 sessioni Grande Panda usate per il confronto esistono già (Ale le ha lanciate oggi).
- Non serve verificare la "qualità giornalistica" dei due minireport, è già stata fatta dal PM lato testo.
- Non serve confrontare con altri modelli (BMW, Honda, ecc.) in questo handoff: l'anomalia è osservata sul Grande Panda, partiamo da lì.

## Note

- Le 2 sessioni Grande Panda da confrontare sono quelle che hanno generato i minireport mostrati in chat dal PM oggi. Se Code ha bisogno degli ID sessione o degli scraping_session_id, **chiedere ad Ale prima di indagare** (probabilmente recuperabili dalla UI admin "Test Scraping" o da una query semplice sul DB ordinando per timestamp recente brand="Fiat" modello="Grande Panda").
- Ipotesi PM (in ordine di probabilità soggettiva, non vincolanti per Code):
  1. **Diluizione per voto di maggioranza**: il prompt chiede "top-N temi più ricorrenti" e con 12 fonti vs 4 i temi citati da pochi item perdono il ranking.
  2. Prompt divergenti tra L2 e L2YT (oltre alla variabile `sources_used`).
  3. Truncation/sommarizzazione intermedia che in L2 si attiva e in L2YT no.
  4. Bug di inclusione (YT non entra davvero nel pool L2 — sembra escluso dall'handoff L2YT 13/5 ma vale verifica veloce).
  5. Clustering tematico che fonde temi simili (es. "sterzo" assorbito in "comfort di marcia").
- Output atteso dal PM: messaggio in `FEEDBACK.md` con risposta puntuale alle 4 domande + diagnosi probabile + opzioni di intervento. Non serve scrivere codice né aprire altri handoff in questa fase.
- Riferimento storico utile: handoff L2YT archiviato `pm/pm-agent/handoff-archive/handoff-2026-05-12-b-test-solo-youtube.md` + messaggio `FEEDBACK.md` del 13/5 su bug fix cap items_text 80k → 600k (commit `bcb716d` + `4bcf66c`).

---

## 📤 Esito (da compilare da Claude Code a fine task)

**Esito:** ✅ / ❌
**Cosa è stato fatto:**
-

**File modificati:**
-

**Commit:** `<hash>` _o_ "nessuno (solo diagnosi, no codice toccato)"

**Risposte alle 4 domande:**
1. Inclusione: …
2. Prompt: …
3. Pipeline: …
4. Selezione top-N: …

**Causa probabile:**
-

**Leve d'azione possibili (opzioni, non implementare):**
-

**Note per il PM:**
-

**Follow-up emersi:**
-
