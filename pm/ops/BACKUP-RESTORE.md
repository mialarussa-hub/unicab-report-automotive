# 💾 BACKUP & RESTORE — runbook

Procedura per fare un **backup completo** della piattaforma UNICAB su
filesystem locale (Windows) e per **ripristinarla in futuro** su un
nuovo server (o sullo stesso server riformattato).

Caso d'uso primario: **progetto in stand-by lungo, server liberato per
altro uso, possibile ripresa fra mesi**.

---

## Cosa viene salvato

| Cosa | Origine | Note |
|---|---|---|
| Database Postgres | volume `postgres_data` | Tutti i dati: report, sentiment, scraping sessions, embeddings pgvector. Schema delle tabelle n8n presente ma vuoto (UNICAB non usa n8n) |
| `.env` di produzione | `/opt/unicab/.env` | Tutti i secret: DB password, API keys (Anthropic, Firecrawl, Perplexity), Webshare proxy |
| Certificati TLS Let's Encrypt | `/opt/unicab/nginx/ssl/` | Opzionali, regenerabili al restore con certbot |
| Manifest ambiente | runtime | Git SHA del commit attivo, versioni Docker, size DB live, size dump |

**Cosa NON viene salvato** (ridondante o regenerabile):
- Codice → su GitHub (`origin/main`)
- Cartella `pm/` → su GitHub (è parte della repo)
- Immagini Docker → ricostruite con `docker compose build`
- File temporanei (audio Whisper, ecc.) → rigenerabili dallo scraping
- **Volume n8n_data** → nello stack c'è il container n8n, ma non è mai stato usato in produzione (verificato 2026-06-21: 0 workflow, 0 credentials, 0 executions). Se in futuro qualcuno crea workflow in n8n, ri-aggiungere il backup del volume `n8n_data` (e gestire la chiave di encryption — vedi git history dello script `backup-prod.sh`)

---

## Procedura BACKUP (3 step)

### Step 1 — Sincronizza GitHub

Da locale, assicurati che `main` non abbia modifiche pendenti:

```bash
cd D:/PROGETTI/UNICAB/Piattaforma
git status            # niente untracked critico (Docs/SQL ok ignorarli)
git pull --ff-only
git push              # se hai commit locali pendenti
```

Il backup include il **git SHA corrente** del server nel `MANIFEST.txt`,
quindi al restore puoi tornare bit-perfect al commit giusto.

### Step 2 — Lancia il backup sul server

Esegui lo script via SSH senza copiarlo sul server (stream diretto):

```powershell
ssh -p 2222 unicab@46.225.147.176 'bash -s' < D:/PROGETTI/UNICAB/Piattaforma/scripts/backup-prod.sh
```

Output sul server: `/opt/unicab/backups/unicab-YYYYMMDD-HHMMSS.tar.gz`
+ relativo `.sha256`.

### Step 3 — Scarica e verifica su Windows

Da PowerShell:

```powershell
D:\PROGETTI\UNICAB\Piattaforma\scripts\download-backup.ps1
```

Default: scarica in `D:\PROGETTI\UNICAB\backups\`, verifica SHA256,
conferma con `✅`. Per cambiare destinazione:

```powershell
.\download-backup.ps1 -DestDir "E:\Backups\UNICAB"
```

> ⚠️ **Salvare anche in un secondo posto** (Google Drive personale,
> NAS, HDD esterno). È l'unica copia del lavoro: non bruciarla.

### Verifica rapida contenuto

```powershell
# Lista file dentro il tarball
tar -tzf "D:\PROGETTI\UNICAB\backups\unicab-YYYYMMDD-HHMMSS.tar.gz" | findstr /v "/$"

# Leggi solo il MANIFEST (senza estrarre tutto)
tar -xzOf "D:\PROGETTI\UNICAB\backups\unicab-YYYYMMDD-HHMMSS.tar.gz" --wildcards "*/MANIFEST.txt"
```

---

## Pulizia server post-backup

**Prima di smontare lo stack:** controlla due volte che il backup sia
scaricato in locale, checksum OK, e idealmente già copiato anche in un
secondo posto.

```bash
ssh -p 2222 unicab@46.225.147.176
cd /opt/unicab

# 1. Stop di tutti i container
docker compose down

# 2. Rimozione volumi (⚠️ DATI: irrecuperabili dopo questo)
docker volume ls                # vedi cosa c'è
docker volume rm $(docker volume ls -q | grep -E 'postgres_data|n8n_data')
# (il volume n8n_data è vuoto nel caso UNICAB, ma rimuoviamolo per pulizia)

# 3. Rimozione immagini progetto (opzionale, libera spazio)
docker compose down --rmi local

# 4. Rimozione codice e backup obsoleti
sudo rm -rf /opt/unicab
```

A questo punto il server è pulito e libero per altri progetti.
L'utente unix `unicab`, l'SSH config sulla porta 2222, e gli eventuali
strumenti di sistema (docker, fail2ban, ecc.) restano installati.

> 💡 Se vuoi tenere il dominio `unicab.automica.it` puntato a un
> placeholder, abbassa il TTL del record A prima della pulizia. Se lo
> liberi del tutto, alla riattivazione la propagazione DNS richiede
> 24-48h.

---

## Procedura RESTORE

### Prerequisiti

- Server con **Docker + docker-compose v2** installati
- DNS `unicab.automica.it` puntato al nuovo IP (se diverso)
- Accesso SSH (riusiamo `unicab@<IP>:2222` come convenzione)
- Tarball del backup caricato in `/tmp/` sul server target

### Passi

```bash
# 1. SSH sul server target
ssh -p 2222 unicab@<NEW_IP>

# 2. Clona la repo nel path canonico
sudo mkdir -p /opt/unicab && sudo chown unicab:unicab /opt/unicab
git clone https://github.com/<owner>/<repo>.git /opt/unicab
cd /opt/unicab

# 3. (opzionale, bit-perfect) torna al commit del backup
#    Lo trovi in MANIFEST.txt → campo "git_commit:"
git checkout <commit-from-MANIFEST>

# 4. Carica il tarball del backup (da Windows)
#    Da PowerShell locale:
#    scp -P 2222 D:/PROGETTI/UNICAB/backups/unicab-<ts>.tar.gz unicab@<NEW_IP>:/tmp/

# 5. Lancia restore
chmod +x scripts/restore-prod.sh
./scripts/restore-prod.sh /tmp/unicab-<ts>.tar.gz

# 6. Verifica
docker compose ps
docker compose logs --tail=20 api scrapers
```

### Certificati TLS

Se il backup includeva `nginx-ssl.tar.gz`, sono già a posto. Altrimenti
rigenera con certbot (procedura standard, dipende dal setup esistente).

### Tempi stimati

| Step | Tempo |
|---|---|
| Provisioning server + Docker + clone | 15-30 min |
| Upload tarball (dipende dalla size DB e dalla banda) | 5-15 min |
| `pg_restore` | 10-30 min |
| Start stack | 5 min |
| Cert Let's Encrypt + smoke test | 15 min |
| **TOTALE** | **1-2 ore** |

---

## Quirks e gotchas

- **pgvector**: lo script restore crea l'extension `vector` **prima**
  del `pg_restore`. Se rifatto manualmente: `CREATE EXTENSION IF NOT
  EXISTS vector;` come superuser nel DB target.

- **n8n**: predisposto nello stack ma mai usato in produzione. Al
  restore il container parte vuoto, non c'è nulla da ripristinare. Se
  un domani UNICAB inizia davvero a usare n8n, il backup va esteso al
  volume `n8n_data` (contiene la chiave di encryption delle credentials
  n8n — irrecuperabili senza).

- **DNS TTL**: se rilasci `unicab.automica.it`, alla riattivazione la
  propagazione DNS richiede 24-48h. Per ridurre downtime, abbassa il
  TTL a 300s prima del rilascio.

- **Hetzner CX33**: il server attuale resta in piedi per altro progetto.
  Se in futuro ricreiamo un'istanza nuova, scegliere stessa size (CX33,
  4 GB RAM) o superiore. La piattaforma UNICAB non è particolarmente
  CPU-bound; il collo di bottiglia in passato è stato I/O su disco
  durante restore + first scraping cycle.

- **Backup ricorrenti**: questo runbook è pensato per backup *una
  tantum* (stand-by progetto). Se in futuro UNICAB torna in produzione
  con carico reale, valutare backup giornalieri automatici (cron su
  server + offload S3/B2).

---

## Riferimenti

- Script backup: `scripts/backup-prod.sh`
- Script download: `scripts/download-backup.ps1`
- Script restore: `scripts/restore-prod.sh`
- Deploy/operativo prod: `pm/ops/DEPLOY.md`
- Credenziali (dove sono): `pm/ops/CREDENTIALS.md`
