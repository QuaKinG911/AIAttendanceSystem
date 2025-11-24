#!/usr/bin/env python3
"""
Database Backup Script for AI Attendance System
Creates automated backups of the SQLite database with rotation
"""

import os
import shutil
import datetime
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self, db_path='data/attendance.db', backup_dir='backups'):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, suffix=None):
        """Create a backup of the database"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        # Generate backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if suffix:
            backup_name = f"attendance_backup_{timestamp}_{suffix}.db"
        else:
            backup_name = f"attendance_backup_{timestamp}.db"

        backup_path = self.backup_dir / backup_name

        try:
            # Create backup by copying the file
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")

            # Set appropriate permissions (readable/writable by owner only)
            backup_path.chmod(0o600)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def rotate_backups(self, max_backups=7):
        """Rotate old backups, keeping only the most recent ones"""
        try:
            # Get all backup files sorted by modification time (newest first)
            backup_files = sorted(
                self.backup_dir.glob('attendance_backup_*.db'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            # Remove old backups beyond the limit
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")

        except Exception as e:
            logger.error(f"Failed to rotate backups: {e}")
            raise

    def get_backup_info(self):
        """Get information about existing backups"""
        backups = []
        try:
            for backup_file in self.backup_dir.glob('attendance_backup_*.db'):
                stat = backup_file.stat()
                backups.append({
                    'path': backup_file,
                    'size': stat.st_size,
                    'created': datetime.datetime.fromtimestamp(stat.st_mtime),
                    'name': backup_file.name
                })

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")

        return backups

    def restore_backup(self, backup_path):
        """Restore database from a backup"""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        try:
            # Create a backup of current database before restore
            current_backup = self.create_backup('before_restore')

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from: {backup_path}")
            logger.info(f"Current database backed up to: {current_backup}")

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Database backup utility for AI Attendance System')
    parser.add_argument('--db-path', default='data/attendance.db', help='Path to database file')
    parser.add_argument('--backup-dir', default='backups', help='Directory to store backups')
    parser.add_argument('--max-backups', type=int, default=7, help='Maximum number of backups to keep')
    parser.add_argument('--action', choices=['backup', 'rotate', 'info', 'restore'],
                       default='backup', help='Action to perform')
    parser.add_argument('--backup-file', help='Backup file to restore from (for restore action)')
    parser.add_argument('--suffix', help='Suffix for backup filename')

    args = parser.parse_args()

    backup_manager = DatabaseBackup(args.db_path, args.backup_dir)

    try:
        if args.action == 'backup':
            backup_path = backup_manager.create_backup(args.suffix)
            print(f"Backup created: {backup_path}")

            # Auto-rotate after creating backup
            backup_manager.rotate_backups(args.max_backups)
            print(f"Rotated backups, keeping max {args.max_backups}")

        elif args.action == 'rotate':
            backup_manager.rotate_backups(args.max_backups)
            print(f"Rotated backups, keeping max {args.max_backups}")

        elif args.action == 'info':
            backups = backup_manager.get_backup_info()
            if backups:
                print(f"Found {len(backups)} backups:")
                for backup in backups:
                    print(f"  {backup['name']} - {backup['created']} - {backup['size']} bytes")
            else:
                print("No backups found")

        elif args.action == 'restore':
            if not args.backup_file:
                parser.error("--backup-file is required for restore action")
            backup_manager.restore_backup(args.backup_file)
            print(f"Database restored from: {args.backup_file}")

    except Exception as e:
        logger.error(f"Operation failed: {e}")
        exit(1)

if __name__ == '__main__':
    main()