# Implementation of cdr_copy module

**Date:** 2026-04-10
**Status:** ✅ Done

## Brief description

Created a new module `cdr_copy` for copying CDR/LU files from source folder to destination folder based on configuration rules.

## Requirements

### Functional requirements
- Copy files from source to destination
- Configuration tasks in .env format
- Filtering by company, dates
- Structure flags: `-by_company`, `-by_date`, `-flat`
- Convenience flags: `-yesterday`, `-today`
- Dry-run mode for preview
- Skip existing files
- Atomic copying

### Non-functional requirements
- Follow project patterns
- Logging with rotation
- Error handling
- Configuration validation

## Implementation

### Module structure

```
cdr_copy/
├── cdr_copy.py              # Main script (390 lines)
├── config.py                # Configuration class (165 lines)
├── requirements.txt         # python-dotenv==1.0.0
├── README.md                # Documentation
├── .gitignore
├── cdr_copy.logrotate       # Log rotation configuration
├── logs/                    # Log files
└── config/                  # Task configurations
    └── example.env          # Example configuration
```

### Key components

#### 1. Configuration (config.py)

**CDRCopyConfig class:**
- Loading .env via `python-dotenv`
- Validation of required parameters (from, to)
- Parsing flags (parameter presence = True)
- Validation of date formats
- Checking incompatible flags

**Important fix:**
Flags are handled correctly - a flag is considered set if the key is present in the .env file, regardless of value.

#### 2. Main script (cdr_copy.py)

**Utility functions (reused from existing modules):**
- `extract_date_from_filename()` - from `cdr_load/cdr_load.py:50-65`
- `extract_company()` - from `cdr_organize/cdr_organize.py:50-63` + replace _ with spaces
- `get_file_type()` - from `cdr_organize/cdr_organize.py:42-47`
- `copy_atomically()` - from `cdr_organize/cdr_organize.py:82-96` + dry-run support

**Processing logic:**
- `should_process_file()` - filtering by type, company, dates
- `build_dest_path()` - path building considering flags
- `should_copy()` - inverted logic (skip existing)
- `process_file()` - single file processing
- `scan_directory()` - scanning with -flat support

**Logging system:**
- Log file: `cdr_copy/logs/cdr_copy.log`
- Format: `YYYY-MM-DD HH:MM:SS - MESSAGE`
- Dry-run mode: duplication to stdout
- Levels: INFO, WARNING, ERROR

### Supported functions

✅ **Basic copying:**
```bash
python3 cdr_copy/cdr_copy.py task_name
```

✅ **Dry-run mode:**
```bash
python3 cdr_copy/cdr_copy.py task_name --dry-run
```

✅ **-by_company flag:**
Organizes files into company folders with underscores replaced by spaces.
Example: `LIVE_Telna_Corp_CDR_...` → `Telna Corp/file.csv`

✅ **-by_date flag:**
Organizes files into date folders in YYYY-MM-DD format.
Example: `2026-04-10/file.csv`

✅ **Flag combination:**
`-by_company -by_date` → `Telna Corp/2026-04-10/file.csv`

✅ **-flat flag:**
Recursive file search with flat destination structure.

✅ **Company filtering:**
```ini
company="Telna"
```
Copies only files with "Telna" in company name.

✅ **Date filtering:**
```ini
from_date="20260101"
to_date="20261231"
```

✅ **Convenience flags:**
```ini
-yesterday  # Only yesterday's files
-today      # Only today's files
```

✅ **Skip existing files:**
Files that already exist in destination are skipped.

✅ **Atomic copying:**
Uses temporary files (.tmp) to prevent partial writes.

## Test results

### Test 1: Basic copying
✅ Files are copied from source to destination

### Test 2: Dry-run mode
✅ Shows what will be copied without actual copying

### Test 3: -by_company flag
✅ Files organized into company folders with _ replaced by spaces
```
dest/
├── Telna Corp/
│   └── file.csv
└── eData Online/
    └── file.csv
```

### Test 4: -by_date flag
✅ Files organized into date folders
```
dest/
└── 2026-04-10/
    ├── file1.csv
    └── file2.csv
```

### Test 5: Combination -by_company -by_date
✅ Files organized by companies and dates
```
dest/
├── Telna Corp/
│   └── 2026-04-10/
│       └── file.csv
└── eData Online/
    └── 2026-04-10/
        └── file.csv
```

### Test 6: -flat flag
✅ Files from subfolders copied to flat structure

### Test 7: Company filtering
✅ Only files with "Telna" in name were copied

### Test 8: Date filtering (from_date)
✅ Files before specified date were skipped

### Test 9: Skip existing files
✅ Repeated run skips existing files

## Problems and solutions

### Problem 1: AttributeError in _is_flag_set
**Description:** `dotenv_values()` returns `None` for flags without values, causing AttributeError.

**Solution:** Changed check logic - flag is considered set if key is present in dictionary, regardless of value.

**Code:**
```python
def _is_flag_set(env_values: dict, flag_name: str) -> bool:
    return flag_name in env_values
```

### Problem 2: Installing dependencies
**Description:** User requested using same installation method as cdr_sync.

**Solution:** Used `pip3 install python-dotenv==1.0.0` (same as other modules).

## Integration with existing system

### Following project patterns
✅ Logging like `cdr_organize` (separate log file)
✅ Atomic copying from `cdr_organize`
✅ Date extraction from `cdr_load`
✅ Company extraction from `cdr_organize`
✅ Loading .env via `python-dotenv` (like `cdr_sync`)

### Compatibility
✅ Works independently from other modules
✅ Can be used in chains: `cdr_sync` → `cdr_copy` → `cdr_organize`
✅ Does not conflict with `cdr_load`, `cdr_publish`, `cdr_backup`

## Documentation

Created documentation in `README.md`:
- Detailed description of all parameters
- Configuration examples
- Usage examples
- Log format description
- Rotation setup instructions

## Status: ✅ Done

Module is fully implemented, tested and ready to use.

All requirements completed:
- ✅ Configuration tasks in .env format
- ✅ All structure flags work
- ✅ Filtering by company and dates
- ✅ Dry-run mode
- ✅ Atomic copying
- ✅ Logging with rotation
- ✅ Error handling
- ✅ Following project patterns
- ✅ Full documentation
