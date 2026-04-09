# Wrapper Scripts for Cron

Python scripts that chain CDR operations with proper logging and error handling.

## Files

- `telna_cdr_sync.sh` - Telna CDR sync chain (sync → organize → publish)
- `telna_lu_sync.sh` - Telna LU sync chain (sync → organize → publish)
- `telna_cdr.cron` - Cron config for CDR (runs at :00)
- `telna_lu.cron` - Cron config for LU (runs at :30)

## Deployment

```bash
# Create logs directory
mkdir -p /home/cdr_admin/PondCDRSuite/logs

# Deploy scripts
cp scripts/*.sh /home/cdr_admin/PondCDRSuite/scripts/
chmod +x /home/cdr_admin/PondCDRSuite/scripts/*.sh

# Update cron
sudo cp scripts/telna_*.cron /etc/cron.d/
sudo systemctl reload cron
```

## Logs

Chain logs: `/home/cdr_admin/PondCDRSuite/logs/telna_{cdr,lu}_chain.log`

Module logs remain in their respective directories.
