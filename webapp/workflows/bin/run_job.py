#!/usr/bin/env python3
"""
Execute QA Cloud Run Jobs using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path
import argparse
import re

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class JobRunner:
    """Executes Cloud Run Jobs based on YAML configuration."""
    
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
                "--format", "table(metadata.name,status.conditions[0].type,status.conditions[0].status)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                logging.info("  %s", line)
        except subprocess.CalledProcessError:
            logging.warning("Could not retrieve job list")
        
        logging.info("")
        logging.info("Available job names:")
        for job_def in self.config['jobs']['job_definitions']:
            logging.info("  - %s", job_def['name'])
    
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
    
    def execute_job(self, job_name: str) -> bool:
        """Execute a Cloud Run Job."""
        logging.info("Executing Cloud Run Job: %s", job_name)
        
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "execute", job_name,
                "--region", self.config['jobs']['region'],
                "--project", self.project_id
            ], capture_output=True, text=True, check=True)
            
            # Extract execution name from output
            execution_name = None
            for line in result.stdout.split('\n'):
                if 'Execution' in line and 'started running' in line:
                    # Extract execution name using regex
                    match = re.search(r'beryl3-qa-[a-z-]*-[a-z0-9]+', line)
                    if match:
                        execution_name = match.group()
                        break
            
            logging.info("Job execution started successfully!")
            if execution_name:
                logging.info("Execution name: %s", execution_name)
            
            logging.info("")
            logging.info("Monitor execution:")
            logging.info("   gcloud run jobs executions describe %s --region=%s --project=%s", 
                        execution_name or "<execution-name>", 
                        self.config['jobs']['region'], 
                        self.project_id)
            
            logging.info("")
            logging.info("View logs:")
            logging.info('   gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=%s" --project=%s --limit=20', 
                        job_name, self.project_id)
            
            logging.info("")
            logging.info("Console URL:")
            if execution_name:
                logging.info("   https://console.cloud.google.com/run/jobs/executions/details/%s/%s?project=%s", 
                            self.config['jobs']['region'], execution_name, self.project_id)
            
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error("Failed to execute job %s: %s", job_name, e.stderr.strip())
            return False


def main():
    """Main function to execute QA jobs."""
    parser = argparse.ArgumentParser(description="Execute QA Cloud Run Jobs")
    parser.add_argument("job_name", nargs='?', help="Name of the job to execute")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and job runner
        manager = SecretsManager()
        runner = JobRunner(manager)
        
        if not args.job_name:
            # Show usage and available jobs
            logging.info("Cloud Run Job Execution Tool")
            logging.info("")
            runner.show_available_jobs()
            logging.info("")
            logging.info("Usage: %s <job-name>", sys.argv[0])
            logging.info("Example: %s beryl3-qa-collectstatic", sys.argv[0])
            sys.exit(1)
        
        # Check if job exists
        if not runner.job_exists(args.job_name):
            logging.error("Job '%s' not found!", args.job_name)
            logging.info("")
            runner.show_available_jobs()
            sys.exit(1)
        
        # Execute the job
        success = runner.execute_job(args.job_name)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to execute job: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()