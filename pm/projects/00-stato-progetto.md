# 00 — Stato del progetto UNICAB

> **A cosa serve questo file:** brief operativo per orientare il PM AI
> alla prima sessione. Lo legge il PM, lo mantiene Claude Code (con
> aiuto dell'utente). Si aggiorna al cambio di stato grosso (nuova
> milestone, nuova fonte, nuovo ambiente, ecc.). **Non è SPRINT** —
> qui c'è il contesto, le priorità le scrivi in `pm/SPRINT.md`.

**Ultimo aggiornamento:** 2026-05-10
**Aggiornato da:** Claude Code

> **Nota 2026-05-10 (PM):** in call con Paolo del 2026-05-04, **L1 (siti case
> auto) è de-prioritizzato per la Release 0.0 prototipo**. L1 resta in
> produzione, ma il focus prototipo è **L2 + L3 + L4**. Lo scope completo
> della Release 0.0 (in/out, vincoli, pending Paolo, sensibilità) vive in
> [`release-0-0-prototipo.md`](release-0-0-prototipo.md). Il resto di questo
> file resta come fotografia tecnica di stato — non riscritto.

---

## In una riga

UNICAB è una piattaforma di **intelligence editoriale e social per il
mercato auto italiano**: per un dato modello, raccoglie news, video
YouTube (con trascrizione), Reddit, ads (Facebook/Google) e produce
report AI consultabili via dashboard.

---

## Stato attuale (settimana 8 dal go-live)

### ✅ Live in produzione
- **L1** (pipeline base ingest + report) — produttiva
- **L2 minireport AI per modello** — operativa con **8 fonti
  editoriali**:
  - News: AlVolante, Quattroruote, Corriere Motori, Repubblica, La
    Stampa, Gazzetta, Corriere della Sera Motori, Motor1.it
  - YouTube editoriali: AlVolante, Motor1 Italia, DriveK (trascrizione
    Whisper + scraping commenti)
- **Dashboard** consultabile su https://unicab.automica.it
- **Sentiment** (batch) attivo

### 🔄 In standby / nascosto
- **Perplexity (Sonar)** — codice in main, UI nascosta in attesa di
  `PERPLEXITY_API_KEY` cliente

### 🚧 Recentemente shippato (ultimi commit)
- Fix `_clean_items_with_ai` non sovrascrive più `ai_comments`
  preesistenti (`03ba38d`)
- L2 minireport include ora **trascrizioni video YouTube** + scraping
  commenti video (`579685f`)
- 3 canali YouTube editoriali aggiunti, ottimizzato bandwidth audio
  download (`48067a5`)
- yt-dlp via **proxy Webshare** per superare ban YouTube datacenter
  (`0f47f65`)
- Pilota L2 YouTube editoriale Quattroruote con Whisper (`8bb6433`)

---

## Infrastruttura

- **Server prod:** Hetzner CX33
- **Domain:** unicab.automica.it
- **Deploy:** `ssh -p 2222 unicab@46.225.147.176` (mai root, mai
  porta 22)
- **Stack:** Docker Compose (api FastAPI, db Postgres+pgvector, n8n,
  scrapers, nginx)
- **AI:** Anthropic Claude
- **Proxy YouTube:** Webshare

---

## Stakeholder noti

- **Ale Pagani** — AI Specialist freelance, lead developer, decisore
  tecnico
- **Paolo** — referente cliente / interlocutore principale lato
  business. C'è un file di lavoro `Sources/COMUNICAZIONI_PAOLO.md`
  nel filesystem dell'utente con i temi da portargli
  (decisioni aperte, aggiornamenti, prossimi step). Non è in `pm/`.

---

## Domande aperte tipiche (da portare all'utente)

Il PM dovrebbe verificare con l'utente, alla prima sessione:

1. **Sprint corrente — che goal vogliamo per i prossimi 7-14 giorni?**
2. **Backlog — ci sono richieste di Paolo non ancora prioritizzate?**
3. **Roadmap Q2/Q3 — milestone in vista? scadenze cliente?**
4. **Riattivazione Perplexity** — c'è una stima su quando arriva l'API
   key? Va in BACKLOG o in SPRINT con dipendenza esterna?
5. **Costi mensili** — chi paga cosa? (Hetzner, Anthropic API,
   Webshare proxy, dominio)
6. **Incidenti recenti** — c'è stato qualcosa in prod che vale la pena
   loggare in `pm/ops/INCIDENTS.md` per memoria storica?

---

## Cosa NON c'è ancora in `pm/`

Volutamente vuoti, vanno popolati con l'utente (o dal PM dopo
intervista):

- `pm/SPRINT.md` (priorità)
- `pm/ROADMAP.md` (milestone)
- `pm/BACKLOG.md` (idee da prioritizzare)
- `pm/ops/CREDENTIALS.md` (inventario "dove" sono i secret)
- `pm/ops/DEPLOY.md` (runbook completo)
- `pm/ops/COSTS.md` (numeri reali)
- `pm/decisions/` (ADR retroattivi se utili)

Non popolarli a vuoto. Se mancano dati, chiedere all'utente.

---

## Riferimenti

- **Mappa tecnica:** [`CLAUDE.md`](../../CLAUDE.md) (root del repo)
- **Documenti progetto:** `Docs/UNICAB_Kickoff_v2.pdf`,
  `Docs/UNICAB_Proposta_Infrastruttura.docx`,
  `Docs/Progetto Unicab - Report AI Automotive.pdf`
