# cdr_load

Load CDR/LU files for HTTP access with three different views.

## Directory Structure

```
/srv/cdr_load/
├── cdr/
│   ├── raw/                    # All files mixed in root
│   ├── by_date/                # Organized by date (YYYY-MM-DD/)
│   └── by_company/             # Only company subdirectories
└── lu/
    ├── raw/
    ├── by_date/
    └── by_company/
```

## Usage

```bash
# Create all three structures (default)
python3 cdr_load.py

# Create specific structure only
python3 cdr_load.py --mode raw
python3 cdr_load.py --mode by_date
python3 cdr_load.py --mode by_company
```

## Integration

Run after cdr_transform in cron:
```bash
cdr_sync.sh pull configs/client1_cdr.env && \
cdr_transform.py {CDR_BASE_DIR}/inbound/client1_cdr /home/cdr_admin/outbound && \
cdr_load.py
```

## Logging

Logs: `logs/cdr_load.log`

Format:
```
2025-04-08 10:00:00 - RAW - COPIED - LIVE_Company1_CDR_20260406.csv
2025-04-08 10:00:01 - BY_DATE - COPIED - LIVE_Company1_CDR_20260406.csv -> 2026-04-06/
2025-04-08 10:00:02 - RUN SUMMARY [raw]: copied=150 skipped=0 overwritten=0 errors=0
```
