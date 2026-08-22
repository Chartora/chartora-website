#!/usr/bin/env python3
"""
CHARTORA.IN — Automated Database Backup & Verification Script
Backs up chartora.db with SQLite Online Backup API, checks file integrity,
and verifies restoration into a temporary test instance.
"""

import os
import sys
import sqlite3
import shutil
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("chartora.backup")

def backup_database(src_db_path: str = "chartora.db", backup_dir: str = "backups") -> str:
    if not os.path.exists(src_db_path):
        raise FileNotFoundError(f"Source database not found: {src_db_path}")

    os.makedirs(backup_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"chartora_backup_{ts}.db")

    logger.info(f"Initiating online backup: {src_db_path} -> {backup_file}")
    
    src_conn = sqlite3.connect(src_db_path)
    dst_conn = sqlite3.connect(backup_file)

    try:
        # SQLite Online Backup API
        src_conn.backup(dst_conn, pages=100, sleep=0.01)
        logger.info(f"Backup completed successfully: {backup_file} (Size: {os.path.getsize(backup_file)} bytes)")
    finally:
        dst_conn.close()
        src_conn.close()

    # Integrity verification
    verify_backup(backup_file)
    return backup_file

def verify_backup(backup_file: str):
    logger.info(f"Verifying backup integrity: {backup_file}")
    conn = sqlite3.connect(backup_file)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()[0]
        if res.lower() != "ok":
            raise RuntimeError(f"Integrity check failed: {res}")
        
        cursor.execute("SELECT count(*) FROM users;")
        user_count = cursor.fetchone()[0]
        logger.info(f"Integrity check OK. Verified {user_count} user records.")
    finally:
        conn.close()

def restore_test(backup_file: str, test_target: str = "data/restore_test.db") -> bool:
    logger.info(f"Performing test restore to: {test_target}")
    os.makedirs(os.path.dirname(test_target), exist_ok=True)
    shutil.copy2(backup_file, test_target)

    conn = sqlite3.connect(test_target)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA quick_check;")
        res = cursor.fetchone()[0]
        if res.lower() == "ok":
            logger.info("Restore test passed with zero corruption.")
            return True
        return False
    finally:
        conn.close()
        if os.path.exists(test_target):
            os.remove(test_target)

if __name__ == "__main__":
    bk = backup_database()
    restore_test(bk)
