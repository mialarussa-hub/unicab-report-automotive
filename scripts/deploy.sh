#!/bin/bash
# =============================================================================
# UNICAB Report Automotive — Deploy script
# Usage from local machine: ssh -p 2222 unicab@<IP> 'cd /opt/unicab && bash scripts/deploy.sh'
# Or SSH into server first, then: cd /opt/unicab && bash scripts/deploy.sh
# =============================================================================

set -euo pipefail

APP_DIR="/opt/unicab"
cd "${APP_DIR}"

echo "=== UNICAB Deploy — $(date) ==="

# Pull latest code
echo "[1/4] Pulling latest code..."
git pull origin main

# Build and restart containers
echo "[2/4] Building and restarting containers..."
docker compose up -d --build

# Run migrations
echo "[3/4] Running database migrations..."
docker compose exec -T api alembic upgrade head

# Health check
echo "[4/4] Health check..."
sleep 3
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "  API: OK"
else
    echo "  API: FAILED — check logs with: docker compose logs api"
fi

echo ""
echo "=== Deploy complete ==="
docker compose ps
