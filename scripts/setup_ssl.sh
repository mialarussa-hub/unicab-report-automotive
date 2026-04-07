#!/bin/bash
# =============================================================================
# UNICAB — SSL Setup with Let's Encrypt
# Run AFTER DNS is pointing to this server and docker compose is running
# Usage: sudo bash scripts/setup_ssl.sh
# =============================================================================

set -euo pipefail

DOMAIN="unicab.automica.it"
EMAIL="a.pagani@automica.it"
APP_DIR="/opt/unicab"

echo "=== SSL Setup for ${DOMAIN} ==="

# Install certbot
apt-get install -y certbot

# Stop nginx temporarily to free port 80
cd ${APP_DIR}
docker compose stop nginx

# Get certificate
certbot certonly --standalone \
    -d ${DOMAIN} \
    --email ${EMAIL} \
    --agree-tos \
    --non-interactive

# Copy certs to nginx ssl directory
mkdir -p ${APP_DIR}/nginx/ssl
cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ${APP_DIR}/nginx/ssl/
cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem ${APP_DIR}/nginx/ssl/

# Set permissions
chown -R unicab:unicab ${APP_DIR}/nginx/ssl
chmod 600 ${APP_DIR}/nginx/ssl/*.pem

# Restart nginx
docker compose up -d nginx

# Setup auto-renewal cron
cat > /etc/cron.d/certbot-unicab << CRON
# Renew SSL certificate — runs twice daily, restarts nginx on renewal
0 3,15 * * * root certbot renew --quiet --deploy-hook "cd ${APP_DIR} && cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem nginx/ssl/ && cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem nginx/ssl/ && docker compose restart nginx"
CRON

echo ""
echo "=== SSL Setup Complete ==="
echo "  Certificate: /etc/letsencrypt/live/${DOMAIN}/"
echo "  Auto-renewal: configured via cron (twice daily)"
echo "  Test: https://${DOMAIN}"
