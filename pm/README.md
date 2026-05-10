# 📋 pm/ — Project Management UNICAB

Questa cartella è la **single source of truth** per il project
management del progetto UNICAB. Tutto ciò che riguarda priorità,
roadmap, decisioni, task in corso, runbook operativi e log
incidenti vive qui dentro.

---

## Chi gestisce cosa

Il PM ha due "agenti":

| Agente | Ambiente | Ruolo | Cosa modifica |
|---|---|---|---|
| **PM AI** | Claude Cowork | Project manager. Mantiene visione, priorità, coordina sessioni, prepara handoff. | **Solo `pm/`**. Non tocca codice, mai. |
| **Claude Code** | CLI / IDE | Esecutore tecnico. Implementa, debugga, deploya, scrive codice. | `src/`, `backend/`, `frontend/`, `scrapers/`, `n8n/`, `nginx/`, `scripts/`, `Docs/`, root del repo. Modifica `pm/` **solo come conseguenza** di task tecnici (✅ in SPRINT, append in DONE/INCIDENTS, ADR su richiesta). |

Il PM non scrive codice. Claude Code non decide priorità.

---

## File in questa cartella

### Root `pm/`
- **[SPRINT.md](SPRINT.md)** — Task della settimana (P0/P1/P2). È il file più "caldo".
- **[ROADMAP.md](ROADMAP.md)** — Visione 3-6 mesi, milestone strategiche.
- **[BACKLOG.md](BACKLOG.md)** — Idee non ancora prioritizzate, parking lot.
- **[DONE.md](DONE.md)** — Log append-only di task completati, newest-first.

### `pm/projects/`
Un file `.md` per ogni progetto/feature grossa (es. `L3-perplexity.md`,
`onboarding-flow.md`). Vuota all'inizio.

### `pm/decisions/`
Architecture Decision Records (ADR) numerati: `ADR-001-xxx.md`,
`ADR-002-xxx.md`. Vuota all'inizio. Si aggiungono solo quando l'utente
prende una decisione architetturale esplicita.

### `pm/ops/`
- **[CREDENTIALS.md](ops/CREDENTIALS.md)** — Inventario di **dove** sono i secret. Mai i secret stessi.
- **[DEPLOY.md](ops/DEPLOY.md)** — Runbook deploy + procedure di rollback.
- **[INCIDENTS.md](ops/INCIDENTS.md)** — Log problemi prod + risoluzione (append-only).
- **[COSTS.md](ops/COSTS.md)** — Stime costi mensili dei servizi.

### `pm/pm-agent/`
- **[ROLE.md](pm-agent/ROLE.md)** — Manuale di ruolo del PM AI.
- **[ROUTINES.md](pm-agent/ROUTINES.md)** — Cosa fa il PM in quali circostanze.
- **[HANDOFF.md](pm-agent/HANDOFF.md)** — Convenzioni handoff PM → Code + template.
- **[FEEDBACK.md](pm-agent/FEEDBACK.md)** — Canale bidirezionale Code ↔ PM.
- **[handoff-archive/](pm-agent/handoff-archive/)** — Handoff completati, archiviati.

---

## Regole d'oro

1. **PM AI tocca solo `pm/`**. Non legge né scrive nulla fuori. Se ha
   bisogno di info dal codice, chiede a Claude Code via handoff.
2. **Claude Code non riscrive priorità**. Aggiorna `pm/` solo per
   marcare ✅ task fatti, appendere in `DONE.md`/`INCIDENTS.md`,
   scrivere ADR/CREDENTIALS quando l'utente lo chiede esplicitamente.
3. **L'utente è il decisore finale**. PM AI propone, l'utente approva.
4. **Gli handoff complessi vivono in file dedicati**. Riferimento da
   `SPRINT.md`. A completamento → `pm/pm-agent/handoff-archive/`.
5. **`FEEDBACK.md` è bidirezionale**. Si legge a inizio sessione, sia
   dal PM che da Claude Code.

---

## Ordine di lettura a inizio sessione

### Per PM AI (in Cowork)
1. `pm/pm-agent/ROLE.md` — chi sono, cosa posso/non posso fare
2. `pm/pm-agent/ROUTINES.md` — come opero
3. `pm/pm-agent/FEEDBACK.md` — messaggi da Code
4. `pm/SPRINT.md` — sprint corrente
5. Top 10 di `pm/DONE.md` — contesto recente
6. Eventuali handoff aperti in `pm/pm-agent/handoff-*.md`

### Per Claude Code (in CLI)
1. `pm/pm-agent/FEEDBACK.md` — messaggi dal PM
2. `pm/SPRINT.md` — task della settimana
3. Eventuali handoff linkati nelle note di SPRINT

---

## Workflow tipico

```
Utente
  │
  ├─► PM AI (Cowork): "ho un'idea X"
  │       │
  │       ├─► PM struttura: BACKLOG / SPRINT / nuovo project
  │       └─► Se serve esecuzione → handoff in pm/pm-agent/
  │
  ├─► Claude Code (CLI): legge handoff + esegue
  │       │
  │       ├─► aggiorna SPRINT (✅) + DONE
  │       └─► archivia handoff
  │
  └─► PM AI: ground truth check periodico
```
