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

1. **`git pull --ff-only`** — sincronizza con il remoto (vedi sezione "Sync git" sotto)
2. **`pm/pm-agent/FEEDBACK.md`** — eventuali messaggi dal PM
3. **`pm/SPRINT.md`** — task della settimana e priorità correnti
4. **Eventuali handoff** linkati nelle note di SPRINT (`pm/pm-agent/handoff-*.md`)

---

### 🔄 Sync git con il PM AI (CRITICO)

**Il PM AI in Cowork lavora sul filesystem locale ma NON sa usare git.**
Modifica i file in `pm/` direttamente. Tu sei l'unico che committa e
sincronizza con il remoto. Questo significa che **il git diventa
responsabilità tua** anche per le modifiche del PM.

#### Quando l'utente dice "pusha le modifiche del PM"

Il PM ha appena modificato qualcosa in `pm/` (in Cowork) e l'utente
vuole che il cambiamento finisca su GitHub.

```bash
git status                    # vedi cosa il PM ha toccato
git add pm/                   # SOLO pm/, mai aggiungere file fuori
git diff --cached             # rileggi prima di committare
git commit -m "pm: <descrizione di cosa ha fatto il PM>"
git push
```

**Convenzione commit message:**
- Modifiche fatte dal PM AI → prefisso **`pm:`** (es. `pm: aggiungi 3 task P0 per sprint settimana 19`)
- Modifiche fatte da te (Claude Code) come conseguenza tecnica → prefisso **`chore(pm):`** (es. `chore(pm): mark task 'fix login' as done`)

In entrambi i casi, **se hai toccato anche codice nello stesso ciclo
di lavoro, fai due commit separati**: uno `pm:` e uno per il codice.
Non mischiare.

#### Quando stai per scrivere in `pm/` (specie `FEEDBACK.md`)

Prima di modificare qualunque file in `pm/`, **fai sempre `git pull
--ff-only`** per non sovrascrivere modifiche del PM avvenute nel
frattempo (es. da un'altra sessione su un altro device, o se il PM
sta lavorando in parallelo).

```bash
git pull --ff-only            # se fallisce, c'è conflitto: chiedi all'utente
# ...modifichi pm/...
git add pm/
git commit -m "chore(pm): <cosa hai fatto>"
git push
```

#### Riassunto del flusso

| Scenario | Chi modifica | Tu fai |
|---|---|---|
| PM in Cowork modifica `pm/SPRINT.md` | PM AI (in locale) | Su richiesta utente: `add` + commit `pm: ...` + push |
| PM scrive nuovo handoff `pm/pm-agent/handoff-*.md` | PM AI | Idem |
| Tu chiudi un task tecnico → ✅ in SPRINT, append in DONE | Tu | `pull` → modifica → commit `chore(pm): ...` → push |
| Tu rispondi al PM in `pm/pm-agent/FEEDBACK.md` | Tu | `pull` → modifica → commit `chore(pm): feedback to PM about X` → push |
| Tu sposti handoff completato in archive | Tu | `pull` → `git mv` → commit `chore(pm): archive handoff X` → push |
| Tu modifichi codice (`backend/`, `src/`, ecc.) | Tu | flusso normale, mai mischiato con commit `pm:` |

#### Gotcha
- **Mai `git add .` o `git add -A`** quando il PM ha modificato `pm/`: rischi di trascinare file di codice non pronti. Usa sempre `git add pm/`.
- **Se `git pull --ff-only` fallisce**: c'è un commit divergente. Non fare `git pull` senza flag (rebase/merge). Fermati e chiedi all'utente.
- **Cowork non vede commit/branch**: per Cowork esistono solo i file nel filesystem locale. Se hai pushato qualcosa di rilevante per il PM, l'utente deve dirgli "rileggi `pm/...`" — non c'è notifica automatica.

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

### Cosa fa UNICAB

Piattaforma di **intelligence editoriale e social per il mercato
automotive italiano**. Per un dato modello di auto, raccoglie e
analizza:

- **News editoriali** (testate auto + generaliste con sezione motori)
- **Video editoriali YouTube** (canali professional, con trascrizione
  audio via Whisper e scraping commenti)
- **Conversazioni social** (Reddit principalmente, con cliente per
  Arctic Shift)
- **Advertising** (Facebook Ads Library, Google Ads)
- **Specifiche modello** (scraper "motore")

Output: **report e minireport AI** (sintesi per modello, sintesi
media/giornalisti, analisi sentiment) consultabili in dashboard via
unicab.automica.it.

### Architettura — vista a volo d'uccello

| Componente | Path | Stack | Ruolo |
|---|---|---|---|
| API + report engine | `backend/` | Python (FastAPI), pydantic-settings, SQLAlchemy + Alembic | Endpoint REST, orchestrazione report, sentiment, adv, sources, timesheet |
| Scrapers | `scrapers/` | Python | Reddit, YouTube (yt-dlp + Whisper + commenti), news (Firecrawl 2-step search→scrape), Facebook/Google Ads, Perplexity client (standby), motore (specs auto) |
| Frontend | `frontend/` | Templates + static (server-side render via API) | Dashboard report viewer + admin (Test Scraping, timesheet) |
| Workflow automation | `n8n/` | n8n | Orchestrazione job ricorrenti, schedulazione scraping/report |
| Reverse proxy | `nginx/` | nginx | TLS, routing API/n8n |
| DB | container `db` | Postgres 15 + **pgvector** | Persistenza, embeddings sentiment |
| AI | — | Anthropic Claude | Sintesi report/minireport, sentiment classification, content cleaning |

Tutto orchestrato via **Docker Compose** (`docker-compose.yml`).

### Modelli DB (alto livello)

In `backend/app/models/`: `user`, `source`, `scraping`, `report`,
`sentiment`, `adv`, `activity`. Migrazioni Alembic in
`backend/alembic/`.

> **Attenzione (da memoria):** Alembic in produzione **non** è
> affidabile. Per modifiche schema in prod, usare **psql diretto** per
> DDL. Vedi `pm/ops/DEPLOY.md`.

### Pipeline L1 / L2

- **L1** (produttivo) — pipeline base di ingest + report standard.
- **L2** (in espansione) — minireport AI per modello con sintesi
  media/giornalisti per sessione. Fonti L2 attive (al 2026-05-10):
  - **News editoriali (8):** AlVolante, Quattroruote, Corriere
    Motori, Repubblica, La Stampa, Gazzetta, Corriere della Sera
    Motori, Motor1.it
  - **YouTube editoriali (3):** AlVolante, Motor1 Italia, DriveK
    (trascrizione Whisper + scraping commenti video)
- **Perplexity (Sonar)** — implementato in main, **UI nascosta** in
  attesa di API key. Per riattivarlo: aggiungere `PERPLEXITY_API_KEY`
  + reinserire l'option nel dropdown.

### Infrastruttura

- **Server prod:** Hetzner CX33
- **URL pubblico:** https://unicab.automica.it
- **Deploy SSH:** `ssh -p 2222 unicab@46.225.147.176`
  - ⚠️ **MAI** usare `root`, porta `22`, hostname o IP `49.13.11.137`
- **Proxy yt-dlp:** Webshare (per superare ban YouTube datacenter)

### Convenzioni / gotchas noti

- **Filtro temporale ricerche Google:** `tbs=qdr:y` (ultimo anno)
- **Reddit:** preferire **Arctic Shift** all'API ufficiale per
  storico
- **News scrapers:** strategia **2-step (search → scrape)**, non
  scrape diretto
- **Rilevanza:** fallback **brand-only** se modello non matcha;
  `versioni=[]` → considerato pertinente; `cilindrata=null` tollerata
- **Sentiment:** elaborazione **batch**, no item-by-item
- **YouTube:** canali senza prefisso `@channel`
- **AI cleaning:** `_clean_items_with_ai` **non** deve sovrascrivere
  `ai_comments` preesistenti (fix recente, vedi commit `03ba38d`)
- **Container env:** per cambi env vars usare **force-recreate**, non
  semplice restart

### Comandi frequenti (locali)

```bash
# Avvio stack dev
docker compose -f docker-compose.dev.yml up -d

# Log API
docker compose logs -f api

# Migrazione (solo in dev — in prod psql diretto)
docker compose exec api alembic upgrade head
```

### Riferimenti

- **Documenti progetto:** `Docs/UNICAB_Kickoff_v2.pdf`,
  `Docs/UNICAB_Proposta_Infrastruttura.docx`,
  `Docs/Progetto Unicab - Report AI Automotive.pdf`
- **PM:** vedi `pm/` (entry point: `pm/README.md`)
