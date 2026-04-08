# cdr_search - Technical Specification

## Overview

Standalone CLI utility for searching CDR/LU records by cdr_id or iccid. Provides JSON output for integration with web dashboard.

## Requirements

### Functional Requirements

1. **Search by cdr_id** - Find exact matches in CDR files
2. **Search by iccid** - Find exact matches in LU files
3. **JSON output** - Return results in structured JSON format
4. **Limit results** - Maximum 100 results per search
5. **CLI interface** - Command-line interface with argparse

### Data Sources

- CDR files: `{OUTBOUND_DIR}/cdr/*/*.csv`
- LU files: `{OUTBOUND_DIR}/lu/*/*.csv`

Where `{OUTBOUND_DIR}` is the base output directory (configured in deployment)

### Output Format

```json
{
  "query_type": "cdr_id" | "iccid",
  "query_value": "search_value",
  "results": [
    {
      "file": "/path/to/file.csv",
      "line_number": 123,
      "client": "client_name",
      "data": "full,csv,row,contents"
    }
  ],
  "total_found": 1,
  "truncated": false
}
```

## Implementation Tasks

### Phase 1: Core Structure
- [ ] Create project structure
  - [ ] `cdr_search.py` - Main CLI entry point
  - [ ] `config.py` - Configuration for search paths
  - [ ] `requirements.txt` - Dependencies
  - [ ] `README.md` - Usage documentation

### Phase 2: CLI Interface
- [ ] Implement argparse for CLI arguments
  - [ ] `--cdr-id <value>` - Search by CDR ID
  - [ ] `--iccid <value>` - Search by ICCID
  - [ ] `--output json` - JSON output format (default)
  - [ ] `--limit <n>` - Override default 100 result limit
- [ ] Validate mutually exclusive arguments (cdr-id vs iccid)
- [ ] Add help text and examples

### Phase 3: Search Logic
- [ ] Implement file discovery (walk through outbound directories)
- [ ] Implement CSV parsing for each file type
  - [ ] CDR files: extract cdr_id column
  - [ ] LU files: extract iccid column
- [ ] Implement exact match search
- [ ] Implement result limiting (100 results)
- [ ] Extract client name from file path

### Phase 4: Output Formatting
- [ ] Implement JSON output structure
- [ ] Add truncation flag when limit is reached
- [ ] Add total_found count
- [ ] Handle empty results gracefully

### Phase 5: Error Handling
- [ ] Handle missing directories gracefully
- [ ] Handle malformed CSV files
- [ ] Handle permission errors
- [ ] Add logging for debugging

### Phase 6: Testing
- [ ] Test with sample CDR files
- [ ] Test with sample LU files
- [ ] Test exact match functionality
- [ ] Test result limiting
- [ ] Test edge cases (empty results, malformed files)

## Configuration

### Search Paths (config.py)

```python
# Base path for CDR/LU files
BASE_PATH = "{OUTBOUND_DIR}"  # Configure in deployment

# Subdirectories
CDR_SUBDIR = "cdr"
LU_SUBDIR = "lu"

# File patterns
CDR_FILE_PATTERN = "*.csv"
LU_FILE_PATTERN = "*.csv"
```

## CLI Usage Examples

```bash
# Search by CDR ID
python3 cdr_search.py --cdr-id 1234567890

# Search by ICCID
python3 cdr_search.py --iccid 8991000000000000001

# Custom limit
python3 cdr_search.py --cdr-id 1234567890 --limit 50

# Help
python3 cdr_search.py --help
```

## Dependencies

```
# Minimal dependencies
argparse  # CLI arguments (standard library)
csv       # CSV parsing (standard library)
json      # JSON output (standard library)
pathlib   # Path operations (standard library)
```

## Success Criteria

1. ✅ Successfully finds CDR records by cdr_id
2. ✅ Successfully finds LU records by iccid
3. ✅ Returns valid JSON output
4. ✅ Limits results to 100 by default
5. ✅ Extracts correct client names from file paths
6. ✅ Handles edge cases gracefully
7. ✅ CLI works independently without dashboard

## Notes

- CDR ID column position: Determine from actual file format
- ICCID column position: Determine from actual file format
- Client extraction: From directory structure `/cdr/<client>/file.csv`
- Performance: For large datasets, consider future optimization with indexing
