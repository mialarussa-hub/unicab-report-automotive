# CLAUDE.md — Istruzioni per Claude Code in questo repo

Questo file viene caricato automaticamente da Claude Code quando lavori
nel repo UNICAB. Contiene le regole di ingaggio specifiche del progetto.

---

## 📋 Project Management — leggi prima `pm/`

Questo progetto ha un **sistema di project management coordinato** tra
due agenti AI:

| Agente | Ambiente | Ruolo | Cosa modifica |
|---|---|---|---|
| **PM AI** | Claude Cowork | Project manager. Mantiene visione, priorità, handoff. | **Solo `pm/`**. Non tocca codice. |
| **Claude Code (TU)** | CLI / IDE | Esecutore tecnico. Implementi, deployi, debugga. | Tutto il repo (`backend/`, `frontend/`, `scrapers/`, ecc.) + `pm/` solo come conseguenza di task tecnici. |

### Il TUO ruolo (Claude Code)

**Tu sei l'esecutore tecnico, NON il PM.**

#### ✅ Cosa modifichi liberamente
- `backend/`, `frontend/`, `scrapers/`, `n8n/`, `nginx/`, `scripts/`
- `Docs/`, root del repo
- `docker-compose*.yml`, `.env.example`
- File di configurazione, migrazioni DB, test

#### ⚠️ Cosa modifichi in `pm/` SOLO come conseguenza di task tecnici
- **`pm/SPRINT.md`** — segnare ✅ task completato (mai cambiare priorità!)
- **`pm/DONE.md`** — append in cima quando chiudi un task
- **`pm/ops/INCIDENTS.md`** — append dopo aver risolto un incident
- **`pm/ops/CREDENTIALS.md`** — quando integri un nuovo servizio (mai i secret, solo il "dove")
- **`pm/ops/DEPLOY.md`** — quando cambia la procedura di deploy
- **`pm/ops/COSTS.md`** — quando cambia un servizio a pagamento
- **`pm/decisions/ADR-NNN-*.md`** — solo se l'utente prende una decisione architetturale e ti chiede di scriverla
- **`pm/pm-agent/handoff-archive/`** — sposti qui gli handoff completati
- **`pm/pm-agent/FEEDBACK.md`** — scrivi qui se qualcosa nell'handoff non torna

#### ❌ Cosa NON fai mai di tua iniziativa
- Definire o riordinare priorità in `pm/SPRINT.md`
- Modificare `pm/ROADMAP.md` o `pm/BACKLOG.md`
- Scrivere nuovi ADR senza che l'utente l'abbia chiesto
- Toccare `pm/pm-agent/ROLE.md`, `ROUTINES.md`, `HANDOFF.md` (sono il manuale del PM)
- Improvvisare quando un handoff è ambiguo → scrivi in `pm/pm-agent/FEEDBACK.md`

### Workflow quando ricevi un handoff

Il PM ti passa lavoro in due modi:

1. **Inline:** una riga nella colonna Note di `pm/SPRINT.md` con prefisso `[handoff Code]`
2. **File dedicato:** `pm/pm-agent/handoff-YYYY-MM-DD-<x>-<topic>.md`

Procedura:

1. **Leggi l'handoff integralmente** (anche le sezioni "Vincoli" e "Note")
2. **Verifica i prerequisiti** (file citati esistono? servizio raggiungibile?)
3. **Se qualcosa non torna** → scrivi in `pm/pm-agent/FEEDBACK.md` (NON improvvisare)
4. **Esegui** il task
5. **Aggiorna `pm/SPRINT.md`** (✅) e **append in `pm/DONE.md`**
6. **Compila la sezione "Esito"** dell'handoff (se file dedicato)
7. **Sposta l'handoff** in `pm/pm-agent/handoff-archive/` (se file dedicato)

### Inizio sessione — ordine di lettura

Quando apri una nuova sessione, prima di lavorare leggi nell'ordine:

1. **`pm/pm-agent/FEEDBACK.md`** — eventuali messaggi dal PM
2. **`pm/SPRINT.md`** — task della settimana e priorità correnti
3. **Eventuali handoff** linkati nelle note di SPRINT (`pm/pm-agent/handoff-*.md`)

### Tabella riferimento veloce — file `pm/`

| File | Contiene | Quando lo leggi | Lo modifichi? |
|---|---|---|---|
| `pm/README.md` | Spiegazione del sistema PM | Solo se onboarding | No |
| `pm/SPRINT.md` | Task settimana, priorità | **Inizio sessione** | Solo per ✅ |
| `pm/ROADMAP.md` | Visione 3-6 mesi | Su richiesta | ❌ Mai di tua iniziativa |
| `pm/BACKLOG.md` | Idee non prioritizzate | Su richiesta | ❌ Mai di tua iniziativa |
| `pm/DONE.md` | Log task chiusi | Per contesto | ✅ Append a fine task |
| `pm/projects/*.md` | Feature grosse dettagliate | Quando lavori sul progetto | Su richiesta dell'utente |
| `pm/decisions/ADR-*.md` | Decisioni architetturali | Quando rilevante al task | Solo se l'utente decide |
| `pm/ops/CREDENTIALS.md` | Inventario "dove" sono i secret | Prima di integrare servizi | ✅ Quando aggiungi servizio |
| `pm/ops/DEPLOY.md` | Runbook deploy | Prima di deploy | ✅ Quando cambia procedura |
| `pm/ops/INCIDENTS.md` | Log incidenti prod | Per contesto storico | ✅ Append post-fix |
| `pm/ops/COSTS.md` | Stime costi mensili | Quando rilevante | ✅ Quando cambia |
| `pm/pm-agent/ROLE.md` | Manuale ruolo PM | Per capire chi è il PM | ❌ Mai |
| `pm/pm-agent/ROUTINES.md` | Playbook PM | Per capire come opera il PM | ❌ Mai |
| `pm/pm-agent/HANDOFF.md` | Convenzioni handoff | Quando ricevi handoff | ❌ Mai |
| `pm/pm-agent/FEEDBACK.md` | Canale Code ↔ PM | **Inizio sessione** | ✅ Per parlare al PM |
| `pm/pm-agent/handoff-*.md` | Handoff aperti | Quando ne ricevi uno | ✅ Sezione "Esito" + sposta in archive |

---

## Note tecniche del progetto

_(spazio per convenzioni di codice, comandi frequenti, gotcha specifici
del repo. Da popolare nel tempo.)_
