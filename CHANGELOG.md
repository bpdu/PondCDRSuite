# Changelog

All notable changes to the PondCDRSuite project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `logrotate.template` — single repository-level logrotate configuration template
  with `__LOG_DIR__` and `__DEPLOY_USER__` placeholders, automatically rendered
  and installed to `/etc/logrotate.d/cdr_copy` and `/etc/logrotate.d/cdr_sync`
  during deployment.
- `--verbose` flag for `cdr_copy.py` to log every skipped file individually
  (for one-off diagnostics).
- Aggregated skip-reason reporting: `RUN SUMMARY` now includes
  `SKIP REASONS: <count>x <reason>` lines instead of per-file entries.
- Disk usage output (`df -h /`) at the end of the deploy pipeline.
- `DEPLOY_USER` variable in deploy pipeline sourced from
  `CDR_SYNC_SERVER_USER` secret.

### Changed

- `cdr_copy.py` no longer logs a `SKIPPED` line per file by default.
  Previously, every cron run logged each foreign file in the shared source
  directory (e.g. `company mismatch`), producing 300–850 MB daily logs.
  Skip reasons are now aggregated into counters; daily logs shrink to a
  few kilobytes.
- Logrotate policy: retention set to 3 days, `maxsize 1G` (rotation
  triggers on size before the daily limit), `delaycompress` removed
  (archives are compressed immediately).
- Deploy pipeline: obsolete per-project logrotate configs
  (`cdr_copy/cdr_copy.logrotate`, `cdr_sync/logrotate.conf`) removed in
  favor of the shared template.
- Documentation: READMEs of `cdr_copy` and `cdr_sync` updated with the new
  logrotate template workflow and logging behavior.

### Fixed

- Deploy pipeline `mkdir` bug: the script exited unconditionally after
  `mkdir -p "$DEPLOY_DIR"` regardless of the command result. Failure is now
  handled explicitly with a clear error message.
- Deploy pipeline no longer aborts when `chmod +x` fails due to file
  ownership mismatch — a warning is logged instead.
- Credential task configs (`cdr_copy/config/*.env`, `cdr_sync/config/*.env`)
  are now backed up before any git operation and automatically restored on
  both success and failure. The previous `git stash push/pop` approach
  failed silently when no files matched its pathspecs and never covered
  `cdr_copy/config`.
- Fresh-clone path no longer moves credential configs away together with
  the rest of the directory contents; configs are restored after cloning.

## [2026-10] — 2026-10-30

### Added

- Deploy pipeline now clones the repository into `DEPLOY_DIR` if it does not
  exist, and creates the directory when missing.
- `TARGET_DIR` added to Git safe directories to resolve "dubious ownership"
  errors during deployment.

### Changed

- Deploy pipeline updated to use the configured target directory.
- Inactive PondCDRSuite projects removed from the repository.
- `cdr_sync` config directory renamed from `configs` to `config`.
- `cdr_copy` accepts either a task name or a direct path to a `.env`
  configuration file.

## [2026-07] — 2026-07-28

### Changed

- CI/CD pipeline updated with a new `logrotate.conf` for `cdr_sync`;
  logrotate installation moved out of the pipeline (manual setup).
- `cdr_copy` logrotate retention reduced to 3 days.

### Fixed

- `cdr_copy` timestamp extraction for fraud report filenames, including
  additional filename checks and alternative timestamp formats.
- File structure check skipped for tasks that do not require it.
- `config.py` added for correct file extension processing.
- Inactive projects removed from the public repository.

## [2026-04] — 2026-04-10

### Added

- `cdr_copy` module for flexible CDR/LU file copying with per-task `.env`
  configurations (`by_company`, `by_date`, `flat`, `yesterday`, `today` flags).
- Context-aware company name normalization to avoid duplicate destination
  folders.
- Dated log filenames (`<task>_<YYYYMMDD>.log`) for `cdr_copy`.
- `cdr_publish` and `cdr_backup` modules.
- `cdr_search` and `cdr_dashboard` module specifications (TODO).
- Cron deployment files; console output for `cdr_backup --dry-run`.
- UTC timestamps for `cdr_copy` logs.

### Changed

- Configuration flags switched to a `yes/no` format.
- Project restructured to an ETL architecture.
- Log files renamed to use module names; logging split into
  `cdr_process.log` and `lu_process.log`.
- Documentation translated to English; real paths and data replaced with
  placeholders.

### Fixed

- Telna CSV files missing a dot before the extension are now handled.
- `deploy/telna_sync.sh` preserved during CI/CD deployment.
- Logrotate paths corrected; `su` directive added to logrotate configs.
- Deploy workflow: diverged branches handled; stashed files restored
  after `git reset`.
