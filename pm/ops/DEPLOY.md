# 🚀 DEPLOY — runbook

Procedure di deploy e rollback per la piattaforma UNICAB.

---

## Ambiente

- **Server prod:** Hetzner CX33
- **URL pubblico:** https://unicab.automica.it
- **SSH:** `ssh -p 2222 unicab@46.225.147.176` (⚠️ MAI usare root, porta 22, hostname o IP 49.13.11.137)
- **Repo path su server:** `/opt/unicab`
- **Stack:** Docker Compose con servizi `api`, `scrapers`, `db` (Postgres+pgvector), `nginx`, `n8n`

---

## Deploy standard

### Pre-check
- [ ] Branch `main` aggiornato e pushato
- [ ] `python -c "import ast; ast.parse(...)"` passa su file Python modificati
- [ ] `node --check` passa su file JS modificati
- [ ] Migrazione Alembic preparata se schema DB cambia (003 esiste, prossima sarà 004)

### Procedura per push su main

```bash
# 1. SSH al server
ssh -p 2222 unicab@46.225.147.176

# 2. Pull codice
cd /opt/unicab && git pull --ff-only

# 3. Se il commit cambia lo schema DB → DDL via psql diretto (Alembic
#    in prod non è affidabile; mai usare alembic upgrade in prod)
docker compose exec -T db psql -U unicab -d unicab \
  -c "ALTER TABLE scraping_sessions ADD COLUMN <nome> <type>;"

# 4. Rebuild + recreate dei container che hanno cambiato codice.
#    ⚠️ ATTENZIONE — distinzione critica:
#    - `api` ha bind-mount del codice → docker compose up -d --force-recreate api
#      è sufficiente, NON serve build
#    - `scrapers` NON ha bind-mount, il codice è dentro l'immagine → SERVE BUILD:
#      docker compose build scrapers
#      docker compose up -d --force-recreate scrapers
docker compose build scrapers          # SOLO se scrapers/ è cambiato
docker compose up -d --force-recreate api scrapers

# 5. SEMPRE: restart nginx dopo force-recreate di api o scrapers
#    Motivo: force-recreate cambia l'IP interno del container, nginx
#    ha cachato l'IP vecchio e va in 502 Bad Gateway finché non
#    rifresca il DNS interno
docker compose restart nginx

# 6. Verifica
docker compose ps                       # tutti i container up
docker compose logs api --tail=20       # nessun error/exception
docker compose logs scrapers --tail=20  # idem
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://unicab.automica.it/frontend/scraping-test
# atteso: HTTP 307 (redirect login). Se 502 → problema nginx routing
```

### Verifica codice nuovo arrivato nel container

Per essere sicuri che la build abbia preso il codice giusto (utile per debug
quando "ho pushato ma vedo ancora il comportamento vecchio"):

```bash
# Cerca una keyword del codice nuovo dentro al container
docker compose exec -T scrapers grep -c '<funzione_nuova>' /app/src/<file>.py
docker compose exec -T scrapers stat /app/src/<file>.py | grep Modify
```

Se il count è 0 o la data Modify è vecchia, hai dimenticato il `build`.

### Post-deploy
- [ ] Verificare URL pubblico risponde (HTTP 200/307)
- [ ] Controllare log prime 5 minuti (no Traceback, no 5xx persistenti)
- [ ] Annotare in `pm/DONE.md` se era un task tracciato

---

## Rollback

### Quando rollbackare
- Errori 5xx persistenti dopo 5 min
- Funzione critica rotta (login, ingest, dashboard, scraping test)
- Performance degradata in modo evidente

### Procedura

```bash
# 1. SSH al server
ssh -p 2222 unicab@46.225.147.176
cd /opt/unicab

# 2. Identifica il commit precedente buono
git log --oneline -10

# 3. Reset al commit buono (no force-push — solo locale sul server)
git reset --hard <commit-good>

# 4. Rebuild + recreate
docker compose build scrapers           # se serve
docker compose up -d --force-recreate api scrapers
docker compose restart nginx

# 5. Se il rollback include uno schema DB rollback, applicare il
#    downgrade DDL via psql (mirror dell'ALTER originale)
```

⚠️ **Non fare `git push --force` su origin/main**: il rollback è solo locale
sul server. Per ripristinare anche origin, fare un `git revert <commit>` da
locale dev → commit → push (operazione safe).

---

## Note operative (quirks e lezioni dal campo)

- **`scrapers` NO bind-mount, `api` SÌ.** Vedi sezione "Procedura". Il
  `docker-compose.yml` ha `build: ./scrapers` senza volume override, quindi
  `force-recreate` da solo non aggiorna il codice. Imparato 2026-05-12 con
  il deploy L3 — l'aggregator L3 nuovo non girava perché il container era
  ancora con codice del 29 aprile pur dopo recreate.

- **`nginx` cache IP container dopo `force-recreate`.** Docker assegna un
  nuovo IP interno al container ricreato, nginx ha cachato il vecchio e
  manda 502 Connection refused finché non viene restartato. Restart è
  istantaneo, lo facciamo sempre dopo force-recreate api/scrapers.

- **Alembic in prod non è affidabile.** Schema divergente tra dev e prod
  (es. `l2_synthesis` mai applicato via Alembic in prod). Per ogni DDL su
  prod usare **psql diretto**, non `alembic upgrade`. Tenere comunque la
  migrazione Alembic per dev e per tracciabilità schema.

- **Container env: cambio env vars richiede `--force-recreate`**, non basta
  `restart`.

- **`docker compose exec -T <service>` da SSH non interattivo:** sempre
  `-T` per evitare il "the input device is not a TTY" su exec via SSH
  one-shot.

- **Credentials DB**: `POSTGRES_USER=unicab`, `POSTGRES_DB=unicab`. Password
  in `/opt/unicab/.env` (gitignored). Per psql one-shot da SSH:
  `docker compose exec -T db psql -U unicab -d unicab -c "..."`

- **Porte legate a loopback (security, dal 2026-07-02).** In prod `db` (5432),
  `api` (8000) e `n8n` (5678) sono pubblicate solo su `127.0.0.1`, non su
  `0.0.0.0` (vedi INCIDENTS 2026-07-02: erano esposte su Internet, segnalate
  da BSI/CERT-Bund). Le uniche porte pubbliche restano **80/443** su nginx.
  - Il DDL via `docker compose exec -T db psql ...` **non è impattato** (gira
    dentro il container, non usa la porta pubblicata).
  - Per accedere al DB/api/n8n con un client sull'host o dal proprio PC usare
    un **SSH tunnel**, es.:
    `ssh -p 2222 -L 5432:127.0.0.1:5432 unicab@46.225.147.176`
    (poi il client si connette a `localhost:5432`). Analogo per 8000/5678.
  - ⚠️ Non ripristinare mai il mapping `"5432:5432"` (o 8000/5678 su `0.0.0.0`):
    Docker bypassa UFW, quindi la porta tornerebbe pubblica anche col firewall.
