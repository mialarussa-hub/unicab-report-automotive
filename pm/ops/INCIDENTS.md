# 🚨 INCIDENTS — log incidenti prod

> **Append-only, newest first.** Ogni incidente si aggiunge in cima.
> Non si cancella il passato.

---

## Formato

```
### YYYY-MM-DD HH:MM — [Titolo breve incidente]
- **Severità:** SEV1 (down) / SEV2 (degrado) / SEV3 (minore)
- **Durata:** dall'ora X all'ora Y
- **Sintomo:** cosa hanno visto gli utenti / il monitoring
- **Causa root:** cosa è effettivamente successo
- **Fix:** cosa è stato fatto per risolvere
- **Follow-up:** azioni preventive (link a SPRINT/BACKLOG se aperte)
```

---

## Log

### 2026-07-02 — Postgres (5432) esposto su Internet
- **Severità:** SEV2 (esposizione di sicurezza, nessuna compromissione nota)
- **Durata:** rilevato dal BSI/CERT-Bund il 2026-06-30 17:54 UTC (segnalazione inoltrata da Hetzner); chiuso il 2026-07-02
- **Sintomo:** notifica BSI/CERT-Bund via Hetzner Abuse Team — porta PostgreSQL 5432 aperta e raggiungibile da Internet sull'IP prod 46.225.147.176
- **Causa root:** in `docker-compose.yml` il servizio `db` pubblicava `"5432:5432"`, cioè su `0.0.0.0` (IPv4+IPv6). Il mapping non serve: api/n8n/scrapers raggiungono il DB via rete Docker interna (host `db`). Nota: Docker inserisce regole iptables che bypassano UFW, quindi un firewall non avrebbe protetto la porta.
- **Fix:** bind della porta al loopback → `"127.0.0.1:5432:5432"`. Applicato nel repo (commit `8f6f172`) e in-place sul server (`/opt/unicab`, backup `docker-compose.yml.bak-5432`), poi `docker compose up -d db` (ricreato solo `db`, dati su volume persistente, ~35s). Verificato: `ss -tlnp` mostra solo `127.0.0.1:5432`; db `healthy`; sito HTTP 307 OK. Per accesso host al DB usare SSH tunnel: `ssh -p 2222 -L 5432:127.0.0.1:5432 unicab@46.225.147.176`.
- **Follow-up:**
  - Il git del server (`/opt/unicab`) è **divergente**: fermo a `dc276a6` (dietro il remoto), con `nginx/nginx.conf` modificato non committato e `backups/` untracked. Al prossimo deploy pulito, `git pull` andrà riconciliato (il fix compose è già nel repo, quindi non regredisce). La patch in-place lascia `docker-compose.yml` modificato rispetto a HEAD sul server.
  - **Da valutare (esposizione secondaria):** `api` pubblica `0.0.0.0:8000` e `n8n` è raggiungibile su `5678` — verificare se debbano restare pubblici o passare solo dietro nginx/loopback.

_(vuoto — i nuovi incidenti vanno **in cima**, sopra questa riga)_
