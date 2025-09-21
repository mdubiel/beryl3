#!/usr/bin/env python3
"""
Manage QA Cloud SQL database instance (start/stop/restart/status).
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class DatabaseManager:
    """Manages Cloud SQL database instance operations."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.project_id = secrets_manager.project_id
        self.instance_name = "beryl3-qa"  # From our Cloud SQL setup
        
    def run_gcloud_command(self, command: list) -> tuple[bool, str]:
        """Run a gcloud command and return success status and output."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
    
    def get_instance_state(self) -> str:
        """Get current state of the database instance."""
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "instances", "describe",
            self.instance_name,
            "--project", self.project_id,
            "--format", "value(state)"
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            return output.strip()
        else:
            logging.error("Failed to get instance state: %s", output)
            return "UNKNOWN"
    
    def wait_for_operation(self, operation_timeout: int = 300) -> bool:
        """Wait for database operation to complete."""
        logging.info("Waiting for operation to complete...")
        start_time = time.time()
        
        while time.time() - start_time < operation_timeout:
            state = self.get_instance_state()
            if state == "RUNNABLE":
                logging.info("Database is now running")
                return True
            elif state == "STOPPED":
                logging.info("Database is now stopped")
                return True
            elif state in ["PENDING_CREATE", "PENDING_DELETE", "MAINTENANCE"]:
                logging.info("Operation in progress (state: %s)...", state)
                time.sleep(10)
            else:
                logging.warning("Unexpected state: %s", state)
                time.sleep(5)
        
        logging.error("Operation timed out after %d seconds", operation_timeout)
        return False
    
    def start_database(self) -> bool:
        """Start the database instance."""
        current_state = self.get_instance_state()
        
        if current_state == "RUNNABLE":
            logging.info("Database is already running")
            return True
        elif current_state == "STOPPED":
            logging.info("Starting database instance: %s", self.instance_name)
            
            command = [
                "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "instances", "patch",
                self.instance_name,
                "--project", self.project_id,
                "--activation-policy", "ALWAYS",
                "--quiet"
            ]
            
            success, output = self.run_gcloud_command(command)
            if success:
                logging.info("Start command issued successfully")
                return self.wait_for_operation()
            else:
                logging.error("Failed to start database: %s", output)
                return False
        else:
            logging.error("Cannot start database in state: %s", current_state)
            return False
    
    def stop_database(self) -> bool:
        """Stop the database instance."""
        current_state = self.get_instance_state()
        
        if current_state == "STOPPED":
            logging.info("Database is already stopped")
            return True
        elif current_state == "RUNNABLE":
            logging.info("Stopping database instance: %s", self.instance_name)
            
            command = [
                "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "instances", "patch",
                self.instance_name,
                "--project", self.project_id,
                "--activation-policy", "NEVER",
                "--quiet"
            ]
            
            success, output = self.run_gcloud_command(command)
            if success:
                logging.info("Stop command issued successfully")
                return self.wait_for_operation()
            else:
                logging.error("Failed to stop database: %s", output)
                return False
        else:
            logging.error("Cannot stop database in state: %s", current_state)
            return False
    
    def restart_database(self) -> bool:
        """Restart the database instance."""
        logging.info("Restarting database instance: %s", self.instance_name)
        
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "instances", "restart",
            self.instance_name,
            "--project", self.project_id,
            "--quiet"
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            logging.info("Restart command issued successfully")
            return self.wait_for_operation()
        else:
            logging.error("Failed to restart database: %s", output)
            return False
    
    def show_database_status(self) -> bool:
        """Show detailed database status information."""
        logging.info("Database Status for %s", self.instance_name)
        logging.info("=" * 50)
        
        # Get detailed instance information
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "instances", "describe",
            self.instance_name,
            "--project", self.project_id,
            "--format", "table(name,state,databaseVersion,settings.tier,region,ipAddresses[0].ipAddress)"
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            for line in output.split('\n'):
                logging.info("%s", line)
        else:
            logging.error("Failed to get database status: %s", output)
            return False
        
        # Get database list
        logging.info("\nDatabases:")
        logging.info("-" * 20)
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "databases", "list",
            "--instance", self.instance_name,
            "--project", self.project_id,
            "--format", "table(name,charset,collation)"
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            for line in output.split('\n'):
                logging.info("%s", line)
        else:
            logging.warning("Could not retrieve database list")
        
        # Get user list
        logging.info("\nUsers:")
        logging.info("-" * 10)
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "users", "list",
            "--instance", self.instance_name,
            "--project", self.project_id,
            "--format", "table(name,type)"
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            for line in output.split('\n'):
                logging.info("%s", line)
        else:
            logging.warning("Could not retrieve user list")
        
        # Cost optimization tip
        current_state = self.get_instance_state()
        if current_state == "RUNNABLE":
            logging.info("\n💡 Cost Optimization:")
            logging.info("Database is currently running and incurring charges.")
            logging.info("To save costs when not in use, run:")
            logging.info("  uv run python workflows/bin/manage_database.py stop")
        elif current_state == "STOPPED":
            logging.info("\n💰 Cost Optimized:")
            logging.info("Database is stopped and not incurring compute charges.")
            logging.info("To start for testing, run:")
            logging.info("  uv run python workflows/bin/manage_database.py start")
        
        return True


def main():
    """Main function to manage database operations."""
    parser = argparse.ArgumentParser(
        description="Manage QA Cloud SQL database instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python workflows/bin/manage_database.py status
  uv run python workflows/bin/manage_database.py start
  uv run python workflows/bin/manage_database.py stop
  uv run python workflows/bin/manage_database.py restart

Cost Optimization:
  Stop the database when not in use to reduce costs.
  Only storage costs apply when stopped.
        """
    )
    
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status'],
        help='Action to perform on the database'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and database manager
        manager = SecretsManager()
        db_manager = DatabaseManager(manager)
        
        success = False
        
        if args.action == 'start':
            success = db_manager.start_database()
        elif args.action == 'stop':
            success = db_manager.stop_database()
        elif args.action == 'restart':
            success = db_manager.restart_database()
        elif args.action == 'status':
            success = db_manager.show_database_status()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to manage database: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()