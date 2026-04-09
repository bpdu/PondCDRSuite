#!/usr/bin/env python3
"""
Telna CDR sync chain - pull, organize, publish
Run via cron: 0 * * * *
"""

import subprocess
import sys
import logging
from datetime import datetime

LOG_FILE = "/home/cdr_admin/PondCDRSuite/logs/telna_cdr_chain.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('telna_cdr_chain')

def run_command(cmd_name, cmd):
    """Run command and return success status."""
    logger.info(f"=== Starting {cmd_name} ===")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )
        if result.returncode == 0:
            logger.info(f"✓ {cmd_name} completed successfully")
            if result.stdout:
                for line in result.stdout.strip().split('\n')[-10:]:  # Last 10 lines
                    logger.info(f"  {line}")
            return True
        else:
            logger.error(f"✗ {cmd_name} failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"  stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {cmd_name} timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"✗ {cmd_name} exception: {e}")
        return False

def main():
    start_time = datetime.now()
    logger.info(f"========== Telna CDR Chain Started at {start_time} ==========")

    base_dir = "/home/cdr_admin/PondCDRSuite"

    commands = [
        ("CDR Sync", f"{base_dir}/cdr_sync/cdr_sync.sh pull configs/telna_cdr.env"),
        ("CDR Transform", f"python3 {base_dir}/cdr_transform/cdr_transform.py cdr"),
        ("CDR Load", f"python3 {base_dir}/cdr_load/cdr_load.py --mode all"),
    ]

    results = {}
    for name, cmd in commands:
        success = run_command(name, cmd)
        results[name] = success
        if not success:
            logger.error(f"Chain stopped due to {name} failure")
            break

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"========== Chain Completed in {duration:.0f}s ==========")
    logger.info(f"Results: {', '.join(f'{k}={\"✓\" if v else \"✗\"}' for k, v in results.items())}")

    # Exit with error if any step failed
    if not all(results.values()):
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
