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

## 📤 Esito (da compilare da Claude Code a fine task)

**Esito:** ✅ / ❌
**Cosa è stato fatto:**
- ...

**File modificati:**
- ...

**Commit:** `<hash>` _o_ "non committato, vedi diff"

**Note per il PM:**
- ...

**Follow-up emersi:**
- ...
