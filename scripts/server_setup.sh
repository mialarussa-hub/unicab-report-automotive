#!/bin/bash
# =============================================================================
# UNICAB Report Automotive — Server Provisioning Script
# Run this ONCE on a fresh Hetzner CX41 (Ubuntu 22.04 LTS)
# Usage: ssh root@<IP> 'bash -s' < scripts/server_setup.sh
# =============================================================================

set -euo pipefail

DEPLOY_USER="unicab"
REPO_URL="https://github.com/mialarussa-hub/unicab-report-automotive.git"
APP_DIR="/opt/unicab"
SSH_PORT=2222

echo "=== UNICAB Server Setup ==="
echo "$(date)"

# --- 1. System update ---
echo "[1/8] Updating system..."
apt-get update && apt-get upgrade -y
apt-get install -y \
    curl git ufw fail2ban \
    apt-transport-https ca-certificates gnupg lsb-release

# --- 2. Create deploy user ---
echo "[2/8] Creating deploy user: ${DEPLOY_USER}..."
if ! id "${DEPLOY_USER}" &>/dev/null; then
    adduser --disabled-password --gecos "UNICAB Deploy" "${DEPLOY_USER}"
    usermod -aG sudo "${DEPLOY_USER}"
    # Allow sudo without password for deploy operations
    echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/${DEPLOY_USER}
fi

# Copy SSH keys from root to deploy user
mkdir -p /home/${DEPLOY_USER}/.ssh
cp /root/.ssh/authorized_keys /home/${DEPLOY_USER}/.ssh/
chown -R ${DEPLOY_USER}:${DEPLOY_USER} /home/${DEPLOY_USER}/.ssh
chmod 700 /home/${DEPLOY_USER}/.ssh
chmod 600 /home/${DEPLOY_USER}/.ssh/authorized_keys

# --- 3. SSH hardening ---
echo "[3/8] Hardening SSH..."
sed -i "s/#Port 22/Port ${SSH_PORT}/" /etc/ssh/sshd_config
sed -i "s/PermitRootLogin yes/PermitRootLogin no/" /etc/ssh/sshd_config
sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config
systemctl restart sshd

# --- 4. Firewall ---
echo "[4/8] Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ${SSH_PORT}/tcp    # SSH
ufw allow 80/tcp             # HTTP (redirect to HTTPS)
ufw allow 443/tcp            # HTTPS
ufw --force enable

# --- 5. Install Docker ---
echo "[5/8] Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add deploy user to docker group
usermod -aG docker ${DEPLOY_USER}

# Enable Docker on boot
systemctl enable docker
systemctl start docker

# --- 6. Clone repo ---
echo "[6/8] Cloning repository..."
mkdir -p ${APP_DIR}
git clone ${REPO_URL} ${APP_DIR}
chown -R ${DEPLOY_USER}:${DEPLOY_USER} ${APP_DIR}

# --- 7. Create .env from template ---
echo "[7/8] Creating .env..."
cp ${APP_DIR}/.env.example ${APP_DIR}/.env
echo ""
echo "!!! IMPORTANT: Edit ${APP_DIR}/.env with real values !!!"
echo "    nano ${APP_DIR}/.env"
echo ""

# --- 8. Fail2ban ---
echo "[8/8] Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'JAIL'
[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
JAIL
systemctl enable fail2ban
systemctl restart fail2ban

echo ""
echo "=== Setup complete ==="
echo ""
echo "NEXT STEPS:"
echo "  1. Edit .env:        nano ${APP_DIR}/.env"
echo "  2. Start services:   cd ${APP_DIR} && docker compose up -d"
echo "  3. Run migrations:   docker compose exec api alembic upgrade head"
echo "  4. Init admin user:  docker compose exec api python scripts/init_db.py"
echo "  5. Setup SSL:        bash ${APP_DIR}/scripts/setup_ssl.sh"
echo ""
echo "SSH access (after this session):"
echo "  ssh -p ${SSH_PORT} ${DEPLOY_USER}@<IP>"
echo ""
echo "WARNING: SSH port changed to ${SSH_PORT}. Root login disabled."
echo "         Make sure you can connect as '${DEPLOY_USER}' before closing this session!"
