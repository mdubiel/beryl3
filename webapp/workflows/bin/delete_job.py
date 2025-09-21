#!/usr/bin/env python3
"""
Delete QA Cloud Run Jobs using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path
import argparse

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class JobDeleter:
    """Deletes Cloud Run Jobs based on YAML configuration."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.project_id = secrets_manager.project_id
        
    def show_available_jobs(self):
        """Show available Cloud Run Jobs."""
        logging.info("Available Cloud Run Jobs:")
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "table(metadata.name,metadata.labels.environment)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                logging.info("  %s", line)
        except subprocess.CalledProcessError:
            logging.warning("Could not retrieve job list")
        
        logging.info("")
        logging.info("Available job names:")
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "value(metadata.name)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    logging.info("  - %s", line.strip())
        except subprocess.CalledProcessError:
            logging.warning("Could not retrieve job names")
    
    def job_exists(self, job_name: str) -> bool:
        """Check if a job exists."""
        try:
            subprocess.run([
                "gcloud", "run", "jobs", "describe", job_name,
                "--region", self.config['jobs']['region'],
                "--project", self.project_id
            ], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def delete_job(self, job_name: str) -> bool:
        """Delete a Cloud Run Job."""
        logging.info("Deleting Cloud Run Job: %s", job_name)
        
        try:
            subprocess.run([
                "gcloud", "run", "jobs", "delete", job_name,
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--quiet"
            ], check=True)
            
            logging.info("Job %s deleted successfully!", job_name)
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error("Failed to delete job %s: %s", job_name, e.stderr.strip())
            return False
    
    def confirm_deletion(self, job_name: str) -> bool:
        """Confirm deletion with user."""
        try:
            response = input(f"WARNING: Are you sure you want to delete job '{job_name}'? [y/N]: ")
            return response.lower().strip() in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            logging.info("\nDeletion cancelled.")
            return False


def main():
    """Main function to delete QA jobs."""
    parser = argparse.ArgumentParser(description="Delete QA Cloud Run Jobs")
    parser.add_argument("job_name", nargs='?', help="Name of the job to delete")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and job deleter
        manager = SecretsManager()
        deleter = JobDeleter(manager)
        
        if not args.job_name:
            # Show usage and available jobs
            logging.info("Cloud Run Job Deletion Tool")
            logging.info("")
            deleter.show_available_jobs()
            logging.info("")
            logging.info("Usage: %s <job-name>", sys.argv[0])
            logging.info("Example: %s beryl3-qa-collectstatic", sys.argv[0])
            sys.exit(1)
        
        # Check if job exists
        if not deleter.job_exists(args.job_name):
            logging.error("Job '%s' not found!", args.job_name)
            logging.info("")
            deleter.show_available_jobs()
            sys.exit(1)
        
        # Confirm deletion unless -y flag is used
        if not args.yes:
            if not deleter.confirm_deletion(args.job_name):
                logging.info("Deletion cancelled.")
                sys.exit(1)
        
        # Delete the job
        success = deleter.delete_job(args.job_name)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to delete job: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()