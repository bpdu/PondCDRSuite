# cdr_transform

Console utility for transforming incoming CSV files with flat structure (no client subdirectories).

## Directory Structure

```
/home/cdr_admin/
├── inbound/              # Source files from SFTP downloads
│   ├── telna_cdr/
│   └── telna_lu/
└── outbound/             # Processed files with flat structure
    ├── cdr/
    └── lu/
```

## Project Structure

```
cdr_transform/
├── cdr_transform.py         # Main utility
├── cdr_transform.logrotate  # Logrotate configuration
├── cdr_transform.cron       # Cron jobs example
├── logs/                    # Log directory
│   ├── cdr_transform_cdr.log  # CDR log file
│   └── cdr_transform_lu.log   # LU log file
└── README.md               # This file
```

## Installation

1. Copy utility to server:
```bash
mkdir -p /opt/cdr_tools/cdr_transform
cp cdr_transform.py /opt/cdr_tools/cdr_transform/
chmod +x /opt/cdr_tools/cdr_transform/cdr_transform.py
```

2. Setup logrotate:
```bash
sudo cp cdr_transform.logrotate /etc/logrotate.d/cdr_transform
```

3. Setup cron (optional):
```bash
sudo cp cdr_transform.cron /etc/cron.d/cdr_transform
```

## Usage

Manual run:
```bash
python3 cdr_transform.py <cdr|lu>
```

Examples:
```bash
# Process CDR files
python3 cdr_transform.py cdr

# Process LU files
python3 cdr_transform.py lu
```

## Verification

Check the logs:
```bash
tail -f /opt/cdr_tools/cdr_transform/logs/cdr_transform_cdr.log
tail -f /opt/cdr_tools/cdr_transform/logs/cdr_transform_lu.log
```

Check destination:
```bash
ls -la /home/cdr_admin/outbound/cdr/
ls -la /home/cdr_admin/outbound/lu/
```

## File Processing Rules

1. Only `.csv` files from inbound directory
2. Type detection: `_CDR_` → cdr, `_LU_` → lu
3. Flat structure - files placed directly in cdr/ or lu/ directories (no client subdirectories)
4. Target directories created automatically
5. Duplicate detection via SHA256 hash (not file size)
6. Existing files with different hash are overwritten
7. Source files are NOT deleted from inbound (copy-only operation)
8. Atomic copy via temporary file
9. Errors on individual files don't stop processing

## Differences from cdr_organize

- **Flat structure**: No client subdirectories in outbound
- **Hardcoded paths**: INBOUND_BASE and OUTBOUND_BASE are built-in
- **Simplified CLI**: Single argument (cdr|lu) instead of two path arguments
- **SHA256 duplicates**: Uses hash instead of file size for duplicate detection
- **No source deletion**: Files are copied, not moved from inbound
