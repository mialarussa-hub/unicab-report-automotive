#!/usr/bin/env bash
# UNICAB — ripristina un backup su un server pulito (o nuovo).
#
# Prerequisiti (PRIMA di lanciare questo script):
#   1. Docker + docker compose v2 installati
#   2. Repo clonata in /opt/unicab e cd /opt/unicab
#   3. Tarball del backup caricato in /tmp/ (es. /tmp/unicab-20260621-143000.tar.gz)
#
# Usage (sul server target, da /opt/unicab):
#   ./scripts/restore-prod.sh /tmp/unicab-<ts>.tar.gz

set -euo pipefail

[ $# -eq 1 ] || { echo "Usage: $0 <path-al-backup.tar.gz>"; exit 1; }
BACKUP="$1"
[ -f "${BACKUP}" ] || { echo "❌ File non trovato: ${BACKUP}"; exit 1; }

[ "$(pwd)" = "/opt/unicab" ] || { echo "❌ Eseguire da /opt/unicab"; exit 1; }

RESTORE_TMP=$(mktemp -d)
trap "rm -rf ${RESTORE_TMP}" EXIT

echo "[1/6] Estraggo tarball in ${RESTORE_TMP}..."
tar xzf "${BACKUP}" -C "${RESTORE_TMP}"
BKDIR=$(find "${RESTORE_TMP}" -maxdepth 1 -type d -name 'unicab-*' | head -1)
[ -d "${BKDIR}" ] || { echo "❌ Struttura backup inattesa"; exit 1; }
echo "    contenuto: $(ls ${BKDIR} | tr '\n' ' ')"

echo "[2/6] Ripristino .env..."
[ -f .env ] && cp .env ".env.pre-restore.$(date +%s).bak"
cp "${BKDIR}/dotenv" .env
chmod 600 .env

echo "[3/6] Ripristino certificati nginx (se presenti)..."
if [ -f "${BKDIR}/nginx-ssl.tar.gz" ]; then
  mkdir -p nginx
  tar xzf "${BKDIR}/nginx-ssl.tar.gz" -C nginx/
  echo "    nginx/ssl/ ripristinato"
else
  echo "    nessun certificato nel backup — andranno rigenerati con Let's Encrypt"
fi

echo "[4/6] Avvio solo il container db..."
docker compose up -d db

echo "    attendo healthcheck (max 60s)..."
set -a; source .env; set +a
for i in $(seq 1 30); do
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; then
    echo "    db pronto"
    break
  fi
  sleep 2
done

echo "[5/6] Drop+create DB e pg_restore..."
docker compose exec -T db dropdb -U "${POSTGRES_USER}" --if-exists "${POSTGRES_DB}"
docker compose exec -T db createdb -U "${POSTGRES_USER}" "${POSTGRES_DB}"
docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c \
  "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose cp "${BKDIR}/postgres.dump" db:/tmp/postgres.dump
docker compose exec -T db pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  --no-owner --no-acl --if-exists --clean /tmp/postgres.dump || \
  echo "    ⚠️  pg_restore ha segnalato warning (spesso normale: extension già esistente, ecc.)"

echo "[6/6] Avvio stack completo..."
# Nota: il container n8n parte vuoto (UNICAB non lo usa).
docker compose up -d
sleep 3
docker compose restart nginx

echo ""
echo "✅ Restore completato. Verifica:"
echo "   docker compose ps"
echo "   docker compose logs --tail=20 api scrapers"
echo "   curl -I https://unicab.automica.it    # se DNS già configurato"
echo ""
echo "Se i certificati TLS non sono stati ripristinati:"
echo "   ./scripts/issue-letsencrypt.sh   # (procedura certbot standard)"
