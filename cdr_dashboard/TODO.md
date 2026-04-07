# cdr_dashboard - Technical Specification

## Overview

Web-based monitoring dashboard for CDR/LU file processing system. Provides real-time visibility into sync tasks, file counts, errors, and system metrics.

## Requirements

### Functional Requirements

1. **Task Status Monitoring** - Show last run info for telna_cdr, telna_lu, plintron_fraud
2. **File Counts** - Display total processed files and breakdown by client
3. **Error Tracking** - Show recent and unresolved errors
4. **System Metrics** - Display disk usage (df -H), memory (free -m), CPU load (/proc/loadavg)
5. **Search Integration** - Interface with cdr_search module for record lookup
6. **Auto-refresh** - Update dashboard every 30 seconds

### Data Sources

- cdr_sync logs: `../cdr_sync/logs/<config>_<YYYYMMDD>.json`
- cdr_organize logs: `../cdr_organize/logs/{cdr,lu}_process.log`
- System commands: `df -H`, `free -m`, `cat /proc/loadavg`
- cdr_search module: `../cdr_search/cdr_search.py`

## Implementation Tasks

### Phase 1: Project Structure
- [ ] Create FastAPI project structure
  - [ ] `cdr_dashboard/` - Main package
  - [ ] `main.py` - FastAPI app entry point
  - [ ] `config.py` - Configuration via .env
  - [ ] `database.py` - SQLite operations
  - [ ] `models.py` - Pydantic models
- [ ] Create subdirectories
  - [ ] `parsers/` - Log parsers
  - [ ] `routes/` - API and page routes
  - [ ] `services/` - Background jobs
  - [ ] `templates/` - HTML templates
- [ ] Create static files
  - [ ] `static/css/main.css`
  - [ ] `static/js/dashboard.js`
- [ ] Create deployment files
  - [ ] `requirements.txt`
  - [ ] `cdr_dashboard.service`
  - [ ] `README.md`

### Phase 2: Database Setup
- [ ] Create SQLite database schema
  - [ ] `cdr_sync_runs` table
  - [ ] `cdr_organize_runs` table
  - [ ] `errors` table
- [ ] Create database.py module
  - [ ] Database connection management
  - [ ] CRUD operations for each table
  - [ ] Database initialization/migration

### Phase 3: Log Parsers
- [ ] Create parsers/cdr_sync.py
  - [ ] Parse JSON log format
  - [ ] Extract: timestamp, status, duration, files_count, error
  - [ ] Handle multiple config files
- [ ] Create parsers/cdr_organize.py
  - [ ] Parse text log format
  - [ ] Extract RUN SUMMARY lines
  - [ ] Extract error lines
- [ ] Migrate existing log data to database

### Phase 4: API Endpoints
- [ ] Create routes/api.py
  - [ ] `GET /api/tasks/status` - Last run info, next run time
  - [ ] `GET /api/files/stats` - File counts by client
  - [ ] `GET /api/errors` - Recent errors, unresolved
  - [ ] `GET /api/system` - Disk, memory, CPU metrics
  - [ ] `POST /api/search` - Call cdr_search module

### Phase 5: Background Processing
- [ ] Create services/scheduler.py
  - [ ] Setup APScheduler
  - [ ] Incremental log parsing job (every 1 min)
  - [ ] Cache latest run data in memory
- [ ] Create services/aggregator.py
  - [ ] Aggregate file counts by client
  - [ ] Calculate system health metrics

### Phase 6: Frontend
- [ ] Create templates/dashboard.html
  - [ ] Task status cards
  - [ ] File counts display
  - [ ] System metrics section
  - [ ] Error list
  - [ ] Search form
- [ ] Create static/css/main.css
  - [ ] Responsive layout
  - [ ] Status indicator colors
- [ ] Create static/js/dashboard.js
  - [ ] API calls for each section
  - [ ] 30-second auto-refresh
  - [ ] Search form handling
  - [ ] Results display

### Phase 7: Configuration
- [ ] Create config.py
  - [ ] Environment variables via .env
  - [ ] Database path
  - [ ] Log paths (relative to project)
  - [ ] CDR/LU outbound paths
- [ ] Create .env.example

### Phase 8: Deployment
- [ ] Create systemd service file
  - [ ] User: cdr_admin
  - [ ] Auto-restart on failure
  - [ ] Log to syslog
- [ ] Create logrotate config
- [ ] Testing and validation

## API Endpoints Specification

### GET /api/tasks/status

Response:
```json
{
  "tasks": [
    {
      "name": "telna_cdr",
      "last_run": "2025-04-07T22:30:00Z",
      "status": "success" | "failed" | "pending",
      "duration_sec": 45,
      "next_run": "2025-04-07T23:00:00Z",
      "files_count": 150
    }
  ]
}
```

### GET /api/files/stats

Response:
```json
{
  "total_files": 72455,
  "cdr_files": 22186,
  "lu_files": 50269,
  "by_client": {
    "edata": 8234,
    "silver": 6521
  }
}
```

### GET /api/errors

Response:
```json
{
  "errors": [
    {
      "id": 1,
      "source": "cdr_sync",
      "timestamp": "2025-04-07T16:35:00Z",
      "error": "SSH timeout",
      "resolved": false
    }
  ]
}
```

### GET /api/system

Response:
```json
{
  "disk": {
    "used": "45G",
    "total": "100G",
    "percent": 45
  },
  "memory": {
    "used": "1.2G",
    "total": "16G",
    "percent": 7.5
  },
  "cpu": {
    "load_1min": 0.75,
    "load_5min": 0.82,
    "load_15min": 0.65,
    "cores": 4,
    "percent": 18.75
  }
}
```

### POST /api/search

Request:
```json
{
  "query_type": "cdr_id" | "iccid",
  "query_value": "1234567890"
}
```

Response (from cdr_search):
```json
{
  "query_type": "cdr_id",
  "query_value": "1234567890",
  "results": [...],
  "total_found": 1,
  "truncated": false
}
```

## Database Schema

```sql
CREATE TABLE cdr_sync_runs (
    id INTEGER PRIMARY KEY,
    config TEXT NOT NULL,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_sec INTEGER,
    files_count INTEGER,
    error TEXT
);

CREATE TABLE cdr_organize_runs (
    id INTEGER PRIMARY KEY,
    source_dir TEXT NOT NULL,
    copied INTEGER,
    skipped INTEGER,
    overwritten INTEGER,
    errors INTEGER,
    timestamp TEXT NOT NULL
);

CREATE TABLE errors (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    run_id INTEGER,
    timestamp TEXT NOT NULL,
    error TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE
);
```

## Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
apscheduler==3.10.4
jinja2==3.1.2
python-dotenv==1.0.0
```

## Success Criteria

1. ✅ Dashboard loads at http://localhost:8000
2. ✅ Task status shows correct last run times
3. ✅ File counts match actual data
4. ✅ Errors are captured and displayed
5. ✅ System metrics update correctly
6. ✅ Search returns matching records
7. ✅ Auto-refresh works every 30 seconds
8. ✅ Runs as systemd service

## Security Considerations

- Run behind firewall or SSH tunnel
- Add Basic Auth for remote access
- Validate all user inputs
- Sanitize log output
- No sensitive data in error messages

## Performance Targets

- Initial page load: < 2 seconds
- API response time: < 500ms
- Search response time: < 5 seconds (depends on file count)
- Memory usage: < 200MB
- CPU usage: < 5% when idle
