#!/usr/bin/env python3
"""
Environment Backup and Migration Workflow

Creates timestamped backups of environment files and provides migration utilities.

Usage:
    uv run python workflows/bin/backup-envs.py backup              # Backup all generated files
    uv run python workflows/bin/backup-envs.py restore TIMESTAMP   # Restore from backup
    uv run python workflows/bin/backup-envs.py list                # List available backups
    uv run python workflows/bin/backup-envs.py clean --days 30     # Clean old backups
"""

import argparse
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


class EnvironmentBackupManager:
    """Manages backup and restoration of environment files."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.generated_dir = self.project_root / "envs" / "generated"
        self.backup_dir = self.project_root / "envs" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> str:
        """Create a timestamped backup of all generated environment files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        
        if not self.generated_dir.exists():
            raise FileNotFoundError(f"Generated directory not found: {self.generated_dir}")
        
        print(f"Creating backup: {timestamp}")
        
        # Copy all files from generated directory
        shutil.copytree(self.generated_dir, backup_path)
        
        # Create manifest file
        manifest = backup_path / "MANIFEST.txt"
        with open(manifest, 'w') as f:
            f.write(f"Backup created: {datetime.now().isoformat()}\n")
            f.write(f"Source: {self.generated_dir}\n")
            f.write(f"Files included:\n")
            
            for file_path in sorted(backup_path.glob("*")):
                if file_path.name != "MANIFEST.txt":
                    f.write(f"  - {file_path.name}\n")
        
        print(f"✅ Backup created: {backup_path}")
        return timestamp
    
    def list_backups(self) -> List[str]:
        """List all available backups with details."""
        backups = []
        
        print("Available backups:")
        print("=" * 50)
        
        for backup_path in sorted(self.backup_dir.glob("*"), reverse=True):
            if backup_path.is_dir():
                timestamp = backup_path.name
                
                # Read manifest if available
                manifest_path = backup_path / "MANIFEST.txt"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        lines = f.readlines()
                        creation_time = lines[0].split(": ", 1)[1].strip() if lines else "Unknown"
                else:
                    creation_time = "Unknown"
                
                # Count files
                file_count = len(list(backup_path.glob("*"))) - 1  # Exclude manifest
                
                print(f"📅 {timestamp}")
                print(f"   Created: {creation_time}")
                print(f"   Files: {file_count}")
                print()
                
                backups.append(timestamp)
        
        if not backups:
            print("No backups found.")
        
        return backups
    
    def restore_backup(self, timestamp: str) -> bool:
        """Restore environment files from a backup."""
        backup_path = self.backup_dir / timestamp
        
        if not backup_path.exists():
            print(f"❌ Backup not found: {timestamp}")
            return False
        
        print(f"Restoring backup: {timestamp}")
        
        # Create backup of current state first
        current_backup = self.create_backup()
        print(f"Current state backed up as: {current_backup}")
        
        # Clear generated directory
        if self.generated_dir.exists():
            shutil.rmtree(self.generated_dir)
        
        # Restore files (excluding manifest)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in backup_path.glob("*"):
            if file_path.name != "MANIFEST.txt":
                shutil.copy2(file_path, self.generated_dir)
                print(f"  Restored: {file_path.name}")
        
        print(f"✅ Backup restored: {timestamp}")
        return True
    
    def clean_old_backups(self, days: int = 30) -> int:
        """Remove backups older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        print(f"Cleaning backups older than {days} days...")
        
        for backup_path in self.backup_dir.glob("*"):
            if backup_path.is_dir():
                try:
                    # Parse timestamp from directory name
                    timestamp_str = backup_path.name
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if backup_date < cutoff_date:
                        print(f"  Removing: {timestamp_str}")
                        shutil.rmtree(backup_path)
                        removed_count += 1
                        
                except ValueError:
                    # Skip directories that don't match timestamp format
                    continue
        
        print(f"✅ Removed {removed_count} old backups")
        return removed_count
    
    def migrate_environment(self, from_env: str, to_env: str) -> bool:
        """Migrate configuration from one environment to another."""
        from_file = self.generated_dir / f"{from_env}.env"
        to_file = self.generated_dir / f"{to_env}.env"
        
        if not from_file.exists():
            print(f"❌ Source environment file not found: {from_file}")
            return False
        
        # Create backup first
        backup_timestamp = self.create_backup()
        
        print(f"Migrating configuration: {from_env} → {to_env}")
        
        # Copy file with timestamp comment
        with open(from_file, 'r') as src:
            content = src.read()
        
        # Add migration header
        migration_header = f"""# =============================================================================
# MIGRATED FROM {from_env.upper()} ENVIRONMENT on {datetime.now().isoformat()}
# Original backup: {backup_timestamp}
# =============================================================================

"""
        
        with open(to_file, 'w') as dst:
            dst.write(migration_header + content)
        
        print(f"✅ Environment migrated: {to_file}")
        print(f"🔄 Original backed up as: {backup_timestamp}")
        return True


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Environment backup and migration utilities",
        epilog="""
Examples:
  uv run python workflows/bin/backup-envs.py backup
  uv run python workflows/bin/backup-envs.py restore 20240921_143000
  uv run python workflows/bin/backup-envs.py list
  uv run python workflows/bin/backup-envs.py clean --days 30
  uv run python workflows/bin/backup-envs.py migrate qa prod
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create backup of generated files')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('timestamp', help='Timestamp of backup to restore')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Remove old backups')
    clean_parser.add_argument('--days', type=int, default=30, 
                             help='Remove backups older than N days (default: 30)')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate environment configuration')
    migrate_parser.add_argument('from_env', help='Source environment (e.g., qa)')
    migrate_parser.add_argument('to_env', help='Target environment (e.g., prod)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = EnvironmentBackupManager()
    
    try:
        if args.command == 'backup':
            manager.create_backup()
        
        elif args.command == 'restore':
            if not manager.restore_backup(args.timestamp):
                return 1
        
        elif args.command == 'list':
            manager.list_backups()
        
        elif args.command == 'clean':
            manager.clean_old_backups(args.days)
        
        elif args.command == 'migrate':
            if not manager.migrate_environment(args.from_env, args.to_env):
                return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())