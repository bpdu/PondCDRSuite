# Cron Deployment

Cron configuration files for PondCDRSuite automated processing.

## Files

- `telna_cdr` - CDR sync chain (runs hourly at :00)
- `telna_lu` - LU sync chain (runs hourly at :30)
- `cdr_backup` - Daily backup (runs at 23:50)
- `deploy.sh` - Deployment script

## Schedule

| Cron | Schedule | Chain |
|------|----------|-------|
| telna_cdr | `0 * * * *` | sync → transform → load |
| telna_lu | `30 * * * *` | sync → transform → load |
| cdr_backup | `50 23 * * *` | archive daily files |

## Deployment

### Option 1: Using deploy.sh (recommended)

```bash
cd deploy
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual deployment

```bash
# Copy files
sudo cp telna_cdr telna_lu cdr_backup /etc/cron.d/

# Set permissions
sudo chown root:root /etc/cron.d/telna_*
sudo chown root:root /etc/cron.d/cdr_backup
sudo chmod 644 /etc/cron.d/telna_*
sudo chmod 644 /etc/cron.d/cdr_backup

# Reload cron
sudo systemctl reload cron
```

### Option 3: One-liner

```bash
sudo cp telna_cdr telna_lu cdr_backup /etc/cron.d/ && sudo systemctl reload cron
```

## Verification

```bash
# Check cron files are deployed
sudo cat /etc/cron.d/telna_cdr
sudo cat /etc/cron.d/telna_lu
sudo cat /etc/cron_d/cdr_backup

# Watch cron execution
sudo tail -f /var/log/syslog | grep CRON

# Check individual logs
tail -f /home/cdr_admin/PondCDRSuite/cdr_sync/logs/*.json
tail -f /home/cdr_admin/PondCDRSuite/cdr_transform/logs/cdr_transform_*.log
tail -f /home/cdr_admin/PondCDRSuite/cdr_load/logs/cdr_load.log
tail -f /home/cdr_admin/PondCDRSuite/cdr_backup/logs/cdr_backup.log
```

## Troubleshooting

If cron jobs don't run:

1. **Check file permissions:**
   ```bash
   ls -la /etc/cron.d/telna_*
   # Should be root:root 644
   ```

2. **Check cron service:**
   ```bash
   sudo systemctl status cron
   ```

3. **Check cron logs:**
   ```bash
   sudo tail -50 /var/log/syslog | grep CRON
   ```

4. **Test manually:**
   ```bash
   # Test CDR chain
   /home/cdr_admin/PondCDRSuite/cdr_sync/cdr_sync.sh pull configs/telna_cdr.env
   python3 /home/cdr_admin/PondCDRSuite/cdr_transform/cdr_transform.py cdr
   python3 /home/cdr_admin/PondCDRSuite/cdr_load/cdr_load.py
```
