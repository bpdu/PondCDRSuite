# CDR Notify

CDR file notification service that monitors a folder for new CDR files and sends notifications via Email and/or Telegram.

## Features

- Monitors CDR folder for new files
- Sends notifications via Email (SMTP) and/or Telegram Bot
- SQLite database to track processed files
- Prevents duplicate notifications using file hash (filename + content)
- Retry logic with exponential backoff
- Configurable via config files

## Configuration

Edit `config/config.txt`:
- `CDR_FOLDER`: Path to folder containing CDR files
- `DB_NAME`: Path to SQLite database file
- `TELEGRAM_SEND`: Enable/disable Telegram notifications (True/False)
- `EMAIL_SEND`: Enable/disable Email notifications (True/False)
- Email settings: SMTP_HOST, SMTP_PORT, EMAIL_FROM, EMAIL_TO

Edit `secrets/telegram.env` (if using Telegram):
- `TELEGRAM_BOT_TOKEN`: Get from @BotFather
- `TELEGRAM_CHAT_ID`: Get from @userinfobot

Edit `secrets/smtp.env` (if SMTP requires auth):
- `SMTP_USER`: SMTP username
- `SMTP_PASSWORD`: SMTP password

## Manual Execution

Run manually for testing:
```bash
cd ~/PondCDRSuite/cdr_notify
source venv/bin/activate
python3 cdr_notify.py
```

## Deployment

Automatic deployment via GitHub Actions on push to main branch.

### GitHub Secrets Required

Configure these in GitHub repository settings (Settings → Secrets and variables → Actions):

- `SSH_HOST`: Server hostname or IP
- `SSH_PORT`: SSH port (usually 22)
- `SSH_USER`: SSH username (cdr_admin)
- `SSH_KEY`: Private SSH key for authentication

### Deployment Process

1. Push to main branch triggers GitHub Actions workflow
2. Workflow validates config exists on server
3. Creates database backup
4. Syncs files via rsync (preserves config/secrets/database)
5. Updates Python dependencies
6. Validates deployment

## Logs

View logs:
```bash
tail -f ~/PondCDRSuite/cdr_notify/log/cdr_notify.log
```

Check cron job status:
```bash
crontab -l  # View cron jobs
```

## Architecture

- `cdr_notify.py`: Main entry point
- `database.py`: SQLite database layer
- `utils.py`: Business logic and configuration
- `email_sender.py`: Email notification handler
- `telegram_sender.py`: Telegram notification handler
- `config/`: Configuration files
- `secrets/`: Secret credentials (excluded from git)
- `resources/`: Email and Telegram message templates

## Security

- Config files and secrets are never committed to git
- Database is excluded from deployment sync
- SSH keys are stored in GitHub Secrets
- Log files are rotated automatically

## Troubleshooting

### Check if cron job is running
```bash
grep CRON /var/log/syslog | grep cdr_notify
```

### View recent execution
```bash
tail -50 ~/PondCDRSuite/cdr_notify/log/cdr_notify.log
```

### Test configuration
```bash
cd ~/PondCDRSuite/cdr_notify
source venv/bin/activate
python3 -c "import utils; config = utils.load_config(); utils.validate_config(config)"
```

### Restore database from backup
```bash
cp ~/PondCDRSuite/cdr_notify_backups/cdr_files.db.YYYYMMDD_HHMMSS \
   ~/PondCDRSuite/cdr_notify/cdr_files.db
```
