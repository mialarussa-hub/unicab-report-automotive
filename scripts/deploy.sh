#!/bin/bash
# UNICAB Report Automotive — Deploy script
# Usage: ssh into server, then run: bash scripts/deploy.sh

set -e

echo "=== UNICAB Deploy ==="

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Build and restart containers
echo "Building and restarting containers..."
docker compose -f docker-compose.yml up -d --build

# Run migrations
echo "Running database migrations..."
docker compose exec api alembic upgrade head

echo "=== Deploy complete ==="
docker compose ps
