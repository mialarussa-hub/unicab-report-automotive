# 🔐 CREDENTIALS — inventario

> **Qui dentro NON ci sono mai i secret.** Solo l'inventario di
> **dove** trovarli (file, secret manager, password manager, env del
> server, ecc.).

**Ultimo aggiornamento:** 2026-05-11

---

## Convenzione operativa di Ale

`Docs/Credentials.txt` è uno **scratchpad locale** di Ale per
condividere comodamente chiavi API e password con Claude Code durante
le sessioni di sviluppo. È **gitignored** (pattern `**/Credentials*`
in `.gitignore`) e non è mai stato committato in nessun branch.
**Convenzione confermata da Ale (2026-05-11): il file resta dov'è.**

Implicazioni:
- I valori reali delle chiavi non vivono in `pm/ops/` né in nessun
  altro file versionato — restano in `Docs/Credentials.txt` (locale) +
  `.env` (server prod + locale Ale, anch'essi gitignored).
- Questa tabella sotto contiene solo i puntatori "dove" — niente
  valori.

---

## Inventario corrente

### API esterne

| Servizio | Tipo credenziale | Dove si trova | Owner | Note |
|---|---|---|---|---|
| Firecrawl | API key | `Docs/Credentials.txt` (locale Ale) + `.env` server prod | Ale | usato negli scraper news (2-step search→scrape) |
| Anthropic Claude | API key | `Docs/Credentials.txt` (locale Ale) + `.env` server prod | Ale | sentiment + minireport L2 + aggregazione L1 |
| YouTube Data API v3 | API key | `Docs/Credentials.txt` (locale Ale) + `.env` server prod | Ale | commenti video, ricerca canali, metadati |
| Perplexity Sonar Pro | API key | `Docs/Credentials.txt` (locale Ale) + `.env` server prod | Ale | **attiva** in L1 Strato B (web ufficiale esteso) |
| OpenAI | API key | `Docs/Credentials.txt` (locale Ale) + `.env` server prod | Ale | Whisper API per trascrizione audio YouTube editoriale L2 |
| Webshare proxy | username + password | `Docs/Credentials.txt` (locale Ale) + `.env` server prod (`WEBSHARE_PROXY_URL`) | Ale | proxy residenziale per yt-dlp (ban YouTube datacenter) |

### Server e infrastruttura

| Servizio | Tipo credenziale | Dove si trova | Owner | Note |
|---|---|---|---|---|
| Hetzner Cloud (account) | login | gestito da UNICAB Italia | UNICAB | account intestato a UNICAB Italia SRL; Ale è "Member" del progetto, accesso revocabile |
| SSH server prod | chiave privata Ed25519 | macchina Ale (`~/.ssh/id_ed25519`) | Ale | chiave pubblica caricata su Hetzner; comando: `ssh -p 2222 unicab@46.225.147.176` |
| Postgres prod | password | `.env` server prod (`POSTGRES_PASSWORD`) | Ale | accesso via Docker container |
| n8n self-hosted | login | `.env` server prod (`N8N_BASIC_AUTH_*`) | Ale | accesso protetto via VPN WireGuard |

### Piattaforma unicab.automica.it (demo / produzione)

| Utente | Note | Stato |
|---|---|---|
| `p.brunetti@excellgo.com` | login demo Paolo, condivisa via mail in chiaro (2026-04-22 e 2026-04-29) | ancora attiva (2026-05-11). Bassa priorità: password debole + canale condivisione insicuro, ma scope limitato (solo dashboard demo). Valutare con Ale se ruotare/cambiare canale. |

### Dominio e DNS

| Servizio | Dove si trova | Owner |
|---|---|---|
| dominio `automica.it` + sottodominio `unicab.automica.it` | gestito da Automica | Ale |

---

## Procedure

### Aggiungere una nuova credenziale
1. Salvare il segreto **fuori dai file versionati** — opzioni:
   - `Docs/Credentials.txt` (locale Ale, gitignored) per scratchpad
     condiviso con Claude Code
   - `.env` (locale + server prod) per uso a runtime
2. Aggiungere una riga nella tabella sopra **descrivendo solo dove**.
3. Se è una env var: aggiornare `.env.example` con la chiave (senza valore).

### Rotazione
- Annotare data ultima rotazione nelle note.
- Per credenziali condivise, comunicare al team prima della rotazione.

---

## Riferimenti

- Pattern gitignore credenziali: `.gitignore` (linee `**/Credentials*`,
  `**/credentials*`, `*.secret`)
- Template variabili env: `.env.example`
