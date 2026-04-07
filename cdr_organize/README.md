# cdr_organize

Console utility for organizing incoming CSV files into client folders.

## Directory Structure

```
/home/cdr_admin/CDRs/
├── inbound/              # Source files from SFTP downloads
│   ├── telna_cdr/
│   ├── telna_lu/
│   └── pintron_fraud/
└── outbound/             # Processed files organized by client
    ├── cdr/
    │   └── <client>/
    └── lu/
        └── <client>/
```

## Project Structure

```
cdr_organize/
├── cdr_organize.py         # Main utility
├── cdr_organize.logrotate  # Logrotate configuration
├── cdr_organize.cron       # Cron jobs example
├── logs/                   # Log directory
│   └── cdr_process.log     # Log file
└── README.md               # This file
```

## Installation

1. Copy utility to server:
```bash
mkdir -p {PROJECT_DIR}/cdr_organize
cp cdr_organize.py {PROJECT_DIR}/cdr_organize/
chmod +x {PROJECT_DIR}/cdr_organize/cdr_organize.py
```

2. Setup logrotate:
```bash
sudo cp cdr_organize.logrotate {LOGROTATE_DIR}/cdr_organize
```

3. Setup cron (optional):
```bash
sudo cp cdr_organize.cron {CRON_DIR}/cdr_organize
```

## Usage

Manual run:
```bash
python3 cdr_organize.py <SOURCE_DIR> <DEST_DIR>
```

Examples:
```bash
python3 cdr_organize.py /home/cdr_admin/CDRs/inbound/telna_cdr /home/cdr_admin/CDRs/outbound
python3 cdr_organize.py /home/cdr_admin/CDRs/inbound/telna_lu /home/cdr_admin/CDRs/outbound
```

## Verification

Check the log:
```bash
tail -f {PROJECT_DIR}/cdr_organize/logs/cdr_process.log
```

Check destination:
```bash
ls -la /home/cdr_admin/CDRs/outbound/cdr/
ls -la /home/cdr_admin/CDRs/outbound/lu/
```

Test run (dry run - just check what would be processed):
```bash
ls /home/cdr_admin/CDRs/inbound/telna_cdr/*.csv | head -5
```

## File Processing Rules

1. Only `.csv` files from SOURCE_DIR root (no recursion)
2. Type detection: `_CDR_` → cdr, `_LU_` → lu
3. Client name extracted from `LIVE_<CLIENT>_<TYPE>_...` pattern
4. Target directories created automatically
5. Existing files with same size are skipped
6. Existing files with different size are overwritten
7. Atomic copy via temporary file
8. Errors on individual files don't stop processing
