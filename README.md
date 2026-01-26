# Pond Mobile CDR Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive toolkit for processing Call Detail Records (CDRs). This package provides tools for synchronization, alerting, searching, and managing CDR files.

## Tools

### CDR Notify

Automated notification service for Call Detail Records.

**Features:**
- Monitors CDR folder for new files
- Email and Telegram notifications
- Duplicate detection via file hashing
- Automatic deployment via GitHub Actions

**Location:** [cdr_notify/](cdr_notify/)

**Documentation:** See [cdr_notify/README.md](cdr_notify/README.md)

**Deployment:** Automatic via GitHub Actions on push to main branch

## Additional Features

- **CDR Synchronization**: Automated sync of CDR files from various sources
- **Alert System**: Email notifications for CDR-related events
- **Search Capabilities**: Efficient search within CDR content
- **File Management**: Rule-based copying and organization of CDR files

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, contact support@pondmobile.com

