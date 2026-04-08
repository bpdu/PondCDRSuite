#!/bin/bash
# Deploy cron files to /etc/cron.d/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_TARGET="/etc/cron.d"

echo "=========================================="
echo "PondCDRSuite Cron Deployment"
echo "=========================================="
echo ""

# Deploy telna_cdr
echo "Deploying telna_cdr..."
sudo cp "$SCRIPT_DIR/telna_cdr" "$DEPLOY_TARGET/"
sudo chown root:root "$DEPLOY_TARGET/telna_cdr"
sudo chmod 644 "$DEPLOY_TARGET/telna_cdr"
echo "  ✓ telna_cdr deployed"

# Deploy telna_lu
echo "Deploying telna_lu..."
sudo cp "$SCRIPT_DIR/telna_lu" "$DEPLOY_TARGET/"
sudo chown root:root "$DEPLOY_TARGET/telna_lu"
sudo chmod 644 "$DEPLOY_TARGET/telna_lu"
echo "  ✓ telna_lu deployed"

# Deploy cdr_backup
echo "Deploying cdr_backup..."
sudo cp "$SCRIPT_DIR/cdr_backup" "$DEPLOY_TARGET/"
sudo chown root:root "$DEPLOY_TARGET/cdr_backup"
sudo chmod 644 "$DEPLOY_TARGET/cdr_backup"
echo "  ✓ cdr_backup deployed"

# Reload cron
echo ""
echo "Reloading cron..."
sudo systemctl reload cron 2>/dev/null || sudo service cron reload 2>/dev/null
echo "  ✓ cron reloaded"

echo ""
echo "=========================================="
echo "✅ Deployment complete!"
echo "=========================================="
echo ""
echo "Verify with:"
echo "  sudo cat /etc/cron.d/telna_cdr"
echo "  sudo cat /etc/cron.d/telna_lu"
echo "  sudo cat /etc/cron.d/cdr_backup"
echo ""
echo "Check cron logs:"
echo "  sudo tail -f /var/log/syslog | grep CRON"
