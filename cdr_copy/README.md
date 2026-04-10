# cdr_copy

Module for copying CDR/LU files from source folder to destination folder based on configuration rules.

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic usage

```bash
# Direct Python call
python3 cdr_copy/cdr_copy.py <task_name>

# With dry-run mode
python3 cdr_copy/cdr_copy.py <task_name> --dry-run

# Examples
python3 cdr_copy/cdr_copy.py telna_cdr
python3 cdr_copy/cdr_copy.py telna_cdr --dry-run
```

### Configuration files

Configuration tasks are stored in `cdr_copy/config/<task_name>.env`

To create a new task:
1. Copy the template `cdr_copy/config/task.env.example`
2. Rename to `<task_name>.env`
3. Fill in the parameters

#### Example configuration

```ini
# Required parameters
from="/source/folder"
to="/target/folder"

# Optional filters
company="ClientName"

# Structure flags (yes/no)
by_company=no
flat=no
by_date=no

# Convenient flags for quick filtering (yes/no)
yesterday=no
today=no

# Date ranges (YYYYMMDD format)
from_date="20260101"
to_date="20261231"
```

## Parameter description

### Required parameters

- **from** - Source folder with files
  - Must exist
  - Checked at startup

- **to** - Destination folder for copying
  - Created automatically if doesn't exist
  - Must be writable

### Optional filters

- **company** - Filter by company name
  - Searches for substring in company name
  - Example: `company="eData"` will find files with `LIVE_eData_Online_CDR_...`

### Structure flags

Flags accept values `yes` or `no` and can be combined:

- **by_company** - Organize files into company folders
  - Extracts company from filename
  - Replaces underscores with spaces
  - Example: `LIVE_Telna_Corp_CDR_...` → `Telna Corp/`
  - Value: `yes` or `no`

- **by_date** - Organize files into date folders
  - Extracts date from filename
  - Folder format: YYYY-MM-DD
  - Example: `2026-04-10/`
  - Value: `yes` or `no`

- **flat** - Flat structure from subfolders
  - Recursively scans source folder
  - Copies all files to destination folder without preserving structure
  - Value: `yes` or `no`

**Combination examples:**

| Flags | Result |
|-------|-----------|
| All `no` | `to/filename.csv` |
| `by_company=yes` | `to/Telna Corp/filename.csv` |
| `by_date=yes` | `to/2026-04-10/filename.csv` |
| `by_company=yes by_date=yes` | `to/Telna Corp/2026-04-10/filename.csv` |
| `flat=yes` | `to/filename.csv` (from all subfolders) |

### Date filtering flags

Flags accept values `yes` or `no`:

- **yesterday** - Only yesterday's files
  - Sets from_date and to_date to yesterday
  - Value: `yes` or `no`

- **today** - Only today's files
  - Sets from_date and to_date to today
  - Value: `yes` or `no`

**Important:** Cannot use `yesterday=yes` and `today=yes` simultaneously.

### Date ranges

- **from_date** - Ignore files before this date (YYYYMMDD format)
- **to_date** - Ignore files after this date (YYYYMMDD format)

## Usage examples

### Example 1: Simple copy

Configuration `config/telna_cdr.env`:

```ini
from="/home/cdr_admin/incoming/telna"
to="/home/cdr_admin/outbound/telna"
```

Run:

```bash
python3 cdr_copy/cdr_copy.py telna_cdr
```

### Example 2: Sort by companies

Configuration `config/all_clients.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/processed"
by_company=yes
```

Result:

```
/home/cdr_admin/processed/
├── Telna Corp/
│   └── file1.csv
├── Client X/
│   └── file2.csv
```

### Example 3: Sort by dates

Configuration `config/daily_cdr.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/archive"
by_date=yes
```

Result:

```
/home/cdr_admin/archive/
├── 2026-04-10/
│   └── file1.csv
├── 2026-04-11/
│   └── file2.csv
```

### Example 4: Combined sorting

Configuration `config/organized.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/organized"
by_company=yes
by_date=yes
```

Result:

```
/home/cdr_admin/organized/
├── Telna Corp/
│   ├── 2026-04-10/
│   │   └── file1.csv
│   └── 2026-04-11/
│       └── file2.csv
└── Client X/
    └── 2026-04-10/
        └── file3.csv
```

### Example 5: Flat structure

Configuration `config/flat.env`:

```ini
from="/home/cdr_admin/incoming/telna"
to="/home/cdr_admin/flat"
flat=yes
```

Result:

```
/home/cdr_admin/flat/
├── file1.csv (from /incoming/telna/subdir1/)
├── file2.csv (from /incoming/telna/subdir2/)
└── file3.csv (from /incoming/telna/)
```

### Example 6: Filter by company

Configuration `config/edata_only.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/edata"
company="eData"
```

Will copy only files with `eData` in company name.

### Example 7: Yesterday's files

Configuration `config/yesterday.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/yesterday"
yesterday=yes
```

Will copy only files from yesterday.

### Example 8: Date range

Configuration `config/q1_2026.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/q1_2026"
from_date="20260101"
to_date="20260331"
```

Will copy only files from Q1 2026.

## Dry-run mode

Preview mode without actual copying:

```bash
python3 cdr_copy/cdr_copy.py telna_cdr --dry-run
```

Output:

```
2026-04-10 15:30:45 - DRY RUN MODE - no files will be copied
2026-04-10 15:30:46 - DRY RUN: Would copy /src/file.csv -> /dst/file.csv
2026-04-10 15:30:47 - DRY RUN: Would copy /src/file2.csv -> /dst/file2.csv
2026-04-10 15:30:48 - RUN SUMMARY: copied=0 skipped=0 errors=0 dry_run_skipped=2
```

## Logging

Log files are stored in `cdr_copy/logs/cdr_copy.log`.

### Log format

```
2026-04-10 15:30:45 - COPIED LIVE_Telna_CDR_20260410...
2026-04-10 15:30:46 - SKIPPED LIVE_Client_LU_... (exists)
2026-04-10 15:30:47 - ERROR LIVE_... : Permission denied
2026-04-10 15:30:48 - RUN SUMMARY: copied=10 skipped=5 errors=0
```

### Log rotation

To configure rotation, use logrotate:

```bash
# Install logrotate configuration
sudo cp cdr_copy.logrotate /etc/logrotate.d/cdr_copy
```

Configuration stores 7 days of logs with compression.

## Error handling

### Configuration validation

Module checks:

- Required parameters (from, to)
- Source folder existence
- Ability to create destination folder
- Write permissions to destination folder
- Date format (YYYYMMDD)
- Date range logic (from_date <= to_date)
- Incompatible flags (yesterday=yes and today=yes)

### Return codes

- **0** - Successful execution
- **1** - Validation error or copy errors

## Features

- **Atomic copying** - uses temporary files to prevent partial writes
- **Skip existing files** - does not overwrite files that already exist
- **Metadata extraction** - uses filename patterns to get date and company
- **Flexible filtering** - flag combinations for various use cases

## Filename format

Module expects files in format:

```
LIVE_{Company}_{Type}_{DateTime}_{N}_{EndDateTime}.csv
```

Examples:

- `LIVE_eData_Online_CDR_20260323090000_1_20260323101228.csv`
- `LIVE_Telna_Corp_LU_20260407120000_1_20260407123456.csv`

## Integration

Module can be used in chains:

```
cdr_sync → cdr_copy → cdr_organize → cdr_load → cdr_publish
```

## Dependencies

- Python 3.8+
- python-dotenv==1.0.0
