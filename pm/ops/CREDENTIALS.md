# 🔐 CREDENTIALS — inventario

> **Qui dentro NON ci sono mai i secret.** Solo l'inventario di
> **dove** trovarli (file, secret manager, password manager, env del
> server, ecc.).

**Ultimo aggiornamento:** 2026-05-11

---

## ⚠️ ALLERTA IN CORSO — credentials leak nel repo

Al 2026-05-10 è stato individuato che **`Docs/Credentials.txt` contiene 6 secret in chiaro committati nel repo git** (anche se privato). Vedi handoff aperto P0:
`pm/pm-agent/handoff-2026-05-10-b-rotate-credentials.md`

Le chiavi compromesse (DA RUOTARE) sono:
1. Firecrawl API
2. Anthropic Claude API
3. YouTube Data API v3
4. **Perplexity API** (con buona pace della nota "in attesa API key cliente" — la key c'è ed è in uso in L1 Strato B)
5. OpenAI API
6. Webshare proxy (username + password)

Dopo rotazione lato Code, questa tabella va popolata con i nuovi "dove".

---

## Convenzione

| Servizio | Tipo credenziale | Dove si trova | Owner | Note |
|---|---|---|---|---|
| _esempio_ | API key | `.env` server prod (`/home/unicab/...`) | Ale | rotazione manuale |
| _esempio_ | DB password | 1Password / vault | Ale | — |

---

## Inventario corrente (post-rotazione, da compilare da Code)

### API esterne

| Servizio | Tipo credenziale | Dove si trova (target) | Owner | Note |
|---|---|---|---|---|
| Firecrawl | API key | _da definire post-rotazione_ | Ale | usato negli scraper news (2-step search→scrape) |
| Anthropic Claude | API key | _da definire post-rotazione_ | Ale | sentiment + minireport L2 + aggregazione L1 |
| YouTube Data API v3 | API key | _da definire post-rotazione_ | Ale | commenti video, ricerca canali, metadati |
| Perplexity Sonar Pro | API key | _da definire post-rotazione_ | Ale | L1 Strato B (web esteso) |
| OpenAI | API key | _da definire post-rotazione_ | Ale | uso da chiarire (Whisper? altro?) — verificare con Code |
| Webshare proxy | username + password | _da definire post-rotazione_ | Ale | proxy residenziale per yt-dlp (ban YouTube datacenter) |

### Server e infrastruttura

| Servizio | Tipo credenziale | Dove si trova | Owner | Note |
|---|---|---|---|---|
| Hetzner Cloud (account) | login | gestito da UNICAB Italia | UNICAB | account intestato a UNICAB Italia SRL; Ale è "Member" del progetto, accesso revocabile |
| SSH server prod | chiave privata Ed25519 | macchina Ale (`~/.ssh/id_ed25519`) | Ale | chiave pubblica caricata su Hetzner; comando: `ssh -p 2222 unicab@46.225.147.176` |
| Postgres prod | password | _da chiarire con Code_ | Ale | accesso via Docker container/env |
| n8n self-hosted | login | _da chiarire con Code_ | Ale | accesso protetto via VPN WireGuard |

### Piattaforma unicab.automica.it (demo / produzione)

| Utente | Password | Note | Stato |
|---|---|---|---|
| `p.brunetti@excellgo.com` | `Unicab` | login demo Paolo, condivisa via mail in chiaro (2026-04-22 e 2026-04-29) | **DA RIVALUTARE**: password debole, condivisa via canale insicuro. Ale ha confermato è ancora attiva (2026-05-11). Considerare rotazione a una password forte + canale sicuro (1Password share, signal, ecc.). |

### Dominio e DNS

| Servizio | Dove si trova | Owner |
|---|---|---|
| dominio `automica.it` + sottodominio `unicab.automica.it` | gestito da Automica | Ale |

---

## Procedure

### Aggiungere una nuova credenziale
1. Salvare il segreto **fuori dal repo** (env server, secret manager, password manager).
2. Aggiungere una riga nella tabella sopra **descrivendo solo dove**.
3. Se è una env var: aggiornare `.env.example` con la chiave (senza valore).

### Rotazione
- Annotare data ultima rotazione nelle note.
- Per credenziali condivise, comunicare al team prima della rotazione.

### Mai mettere in `Docs/` o in altro file versionato
Tutto il segreto va in `.env` (con `.env` in `.gitignore`) o in un secret manager esterno. Il file `Docs/Credentials.txt` è stato la causa dell'incidente del 2026-05-10 e non deve ricomparire.

---

## Riferimenti

- Handoff rotazione: `pm/pm-agent/handoff-2026-05-10-b-rotate-credentials.md`
- Promessa contrattuale violata: `pm/sources/2026-03-27-doc-proposta-infrastruttura.md` (sezione Sicurezza: *"Tutte le API key gestite come variabili d'ambiente cifrate. Nessuna credenziale in chiaro su filesystem o nei repository."*)
- Checklist infra (Hetzner setup): `pm/sources/2026-04-doc-checklist-hetzner.md`
