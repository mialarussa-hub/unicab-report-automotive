#!/usr/bin/env bash
# UNICAB — backup completo della produzione.
# Eseguito sul server prod. Output: /opt/unicab/backups/unicab-<ts>.tar.gz
#
# Usage (da locale, via SSH, senza copiare lo script sul server):
#   ssh -p 2222 unicab@46.225.147.176 'bash -s' < scripts/backup-prod.sh
#
# Contenuto del tarball:
#   - postgres.dump        (pg_dump -Fc dell'intero DB unicab)
#   - dotenv               (copia di /opt/unicab/.env)
#   - nginx-ssl.tar.gz     (certificati TLS, se presenti)
#   - MANIFEST.txt         (metadata: git SHA, versioni, size DB, ecc.)
#
# NOTA su n8n: il container n8n è nello stack ma in UNICAB non è mai stato
# usato (0 workflow, 0 credentials al check del 2026-06-21). Il volume
# n8n_data NON viene salvato. Se in futuro qualcuno crea workflow in n8n,
# riaggiungere lo step di tar del volume (vedi git history).

set -euo pipefail

cd /opt/unicab

TS=$(date +%Y%m%d-%H%M%S)
BKDIR="/opt/unicab/backups/unicab-${TS}"
mkdir -p "${BKDIR}"

set -a; source .env; set +a

echo "[1/4] pg_dump del DB ${POSTGRES_DB}..."
docker compose exec -T db pg_dump -U "${POSTGRES_USER}" -Fc -d "${POSTGRES_DB}" \
  < /dev/null > "${BKDIR}/postgres.dump"
DB_DUMP_SIZE=$(du -h "${BKDIR}/postgres.dump" | cut -f1)
echo "    dump: ${DB_DUMP_SIZE}"

echo "[2/4] copia .env e certificati nginx..."
cp .env "${BKDIR}/dotenv"
chmod 600 "${BKDIR}/dotenv"
if [ -d nginx/ssl ] && [ -n "$(ls -A nginx/ssl 2>/dev/null)" ]; then
  tar czf "${BKDIR}/nginx-ssl.tar.gz" -C nginx ssl/
  echo "    nginx/ssl/ inclusi"
else
  echo "    nginx/ssl/ vuoto o assente — skip"
fi

echo "[3/4] manifest..."
DB_SIZE=$(docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc \
  "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'));" </dev/null 2>/dev/null || echo "n/a")
{
  echo "# UNICAB backup ${TS}"
  echo ""
  echo "host: $(hostname)"
  echo "uname: $(uname -a)"
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "git_commit: $(git rev-parse HEAD)"
  echo "git_branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "git_status_clean: $([ -z "$(git status --porcelain)" ] && echo yes || echo no)"
  echo ""
  echo "docker: $(docker --version)"
  echo "compose: $(docker compose version --short 2>/dev/null || echo n/a)"
  echo ""
  echo "db_name: ${POSTGRES_DB}"
  echo "db_user: ${POSTGRES_USER}"
  echo "db_live_size: ${DB_SIZE}"
  echo "db_dump_size: ${DB_DUMP_SIZE}"
  echo ""
  echo "## Container snapshot"
  docker compose ps --format 'table {{.Service}}\t{{.Image}}\t{{.Status}}' </dev/null 2>/dev/null || true
} > "${BKDIR}/MANIFEST.txt"

echo "[4/4] tarball finale + checksum..."
cd /opt/unicab/backups
tar czf "unicab-${TS}.tar.gz" "unicab-${TS}/"
sha256sum "unicab-${TS}.tar.gz" > "unicab-${TS}.tar.gz.sha256"
rm -rf "unicab-${TS}/"

FINAL_SIZE=$(du -h "unicab-${TS}.tar.gz" | cut -f1)
echo ""
echo "✅ Backup pronto:"
echo "   /opt/unicab/backups/unicab-${TS}.tar.gz  (${FINAL_SIZE})"
echo "   /opt/unicab/backups/unicab-${TS}.tar.gz.sha256"
echo ""
echo "Per scaricare in locale:"
echo "   scp -P 2222 unicab@46.225.147.176:/opt/unicab/backups/unicab-${TS}.tar.gz* D:/PROGETTI/UNICAB/backups/"
