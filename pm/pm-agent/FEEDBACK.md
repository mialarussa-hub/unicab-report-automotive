# 💬 FEEDBACK — canale Code ↔ PM

Questo file è il **canale bidirezionale** tra **Claude Code** (CLI) e
**PM AI** (Cowork).

---

## A cosa serve

Si scrive qui quando:

- **Code → PM:** "il tuo handoff non è chiaro su X", "ho trovato un
  drift tra `pm/SPRINT.md` e la realtà", "una convenzione di HANDOFF
  va aggiornata", "ho fatto Y ma fuori scope, valuta tu se promuoverlo
  in SPRINT", "manca un dato per chiudere il task"
- **PM → Code:** "ho aggiornato HANDOFF.md, leggi le nuove regole",
  "richiedi ground truth check su X", risposte a messaggi di Code
- **Entrambi:** segnalazioni di drift, richieste di chiarimento,
  proposte di miglioramento del workflow PM stesso

---

## Quando si legge

A **inizio sessione**, sia per Code che per PM AI. È nella checklist
di entrambi (vedi `pm/pm-agent/ROUTINES.md` e la sezione PM in
`CLAUDE.md`).

---

## Convenzione di scrittura

Ogni messaggio è una sezione con:

```
## YYYY-MM-DD — [Code → PM] o [PM → Code] — Titolo breve

[corpo del messaggio]

**Stato:** 🆕 Aperto / ✅ Risolto / 📦 Archiviato
```

Quando un messaggio è **risolto**, si lascia nel file e si marca
`✅ Risolto`. Periodicamente i messaggi `✅` o `📦` vecchi (>30
giorni) si archiviano (taglia/incolla in fondo, sotto `## Archivio`).

---

## Messaggi attivi

### 2026-05-11 — [PM → Code] — Discrepanze tra `00-stato-progetto.md` e fonti documentali

Dopo aver letto i 9 documenti in `pm/sources/` (call Paolo, mail, PDF flussi, proposte, checklist Hetzner), il PM ha trovato **3 discrepanze** tra `pm/projects/00-stato-progetto.md` (scritto da Code il 2026-05-10) e i documenti fonte. Il PM **non corregge** `00-stato-progetto.md` di sua iniziativa perché la verità tecnica autorevole è nel codice live, che solo tu vedi. Verifica e correggi se conferma:

1. **Perplexity NON è "in standby in attesa di API key cliente"**, è **attiva** e usata in **L1 Strato B** (Perplexity Sonar Pro, 1 query con prompt restrittivo). Fonti:
   - `pm/sources/doc-flusso-l1.md` (descrive esplicitamente Perplexity in Strato B)
   - `Docs/Credentials.txt` contiene una `PERPLEXITY API KEY` (`pplx-B075...`) — questo è anche un problema di sicurezza separato, vedi handoff P0 `handoff-2026-05-10-b-rotate-credentials.md`
   - Verifica con `grep -r "perplexity\|PERPLEXITY\|sonar\|pplx-" backend/scrapers/` per confermare uso live
   - Se confermato → aggiorna `pm/projects/00-stato-progetto.md` (sezione "Standby/nascosto") e `CLAUDE.md` (sezione "Pipeline L1/L2")

2. **L2 fonti scritte: il PDF dice "Corriere dello Sport Motori"**, non "Corriere della Sera Motori" come in `00-stato-progetto.md`.
   - Fonte: `pm/sources/doc-flusso-l2.md` (tabella fonti)
   - Verifica nel codice quale dei due è effettivamente integrato (probabile Corriere dello Sport, ma non escludo che entrambi/altro)
   - Se Corriere dello Sport → correggi `00-stato-progetto.md`. Se invece è davvero "Corriere della Sera" (cosa diversa dal PDF) → correggi il PDF in `Docs/` o nota la discrepanza

3. **L2 canali YouTube editoriali: sono 4, non 3.**
   - Il PDF L2 elenca: Quattroruote + AlVolante + Motor1 Italia + DriveK
   - `00-stato-progetto.md` elenca: AlVolante + Motor1 Italia + DriveK (manca **Quattroruote YouTube**)
   - Verifica nel codice quali canali sono ingeriti come "editoriali" in L2. Se anche Quattroruote → correggi `00-stato-progetto.md`.

**Esito atteso:** 3 correzioni in `pm/projects/00-stato-progetto.md` (e magari `CLAUDE.md`), riportate in questo file come reply quando chiuse.

**Stato:** 🆕 Aperto

---

## Archivio

_(vuoto)_
