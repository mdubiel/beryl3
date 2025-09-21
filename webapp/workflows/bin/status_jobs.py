#!/usr/bin/env python3
"""
Show status of QA Cloud Run Jobs using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class JobStatusChecker:
    """Shows status of Cloud Run Jobs based on YAML configuration."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.project_id = secrets_manager.project_id
        
    def show_job_status(self):
        """Show status of all QA jobs."""
        logging.info("QA Jobs Status Report")
        logging.info("=" * 20)
        logging.info("")
        
        # Show all beryl3-qa-* jobs with their status
        logging.info("Cloud Run Jobs:")
        logging.info("-" * 15)
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "table(metadata.name,status.conditions[0].type,status.conditions[0].status,metadata.creationTimestamp)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                logging.info("%s", line)
        except subprocess.CalledProcessError:
            logging.info("No beryl3-qa-* jobs found.")
        
        logging.info("")
        
        # Show recent executions for each job
        self.show_recent_executions()
        
        # Show recent logs
        self.show_recent_logs()
        
        # Show summary
        self.show_summary()
    
    def show_recent_executions(self):
        """Show recent executions for each job."""
        logging.info("Recent Job Executions:")
        logging.info("-" * 21)
        
        # Get list of jobs
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "value(metadata.name)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            jobs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            if not jobs:
                logging.info("No beryl3-qa-* jobs found.")
                return
            
            for job in jobs:
                logging.info("")
                logging.info("Job: %s", job)
                logging.info("-" * 40)
                
                # Get recent executions for this job
                try:
                    exec_result = subprocess.run([
                        "gcloud", "run", "jobs", "executions", "list",
                        "--region", self.config['jobs']['region'],
                        "--project", self.project_id,
                        "--job", job,
                        "--limit", "3",
                        "--format", "table(metadata.name,status.conditions[0].type,status.conditions[0].status,metadata.creationTimestamp)"
                    ], capture_output=True, text=True, check=True)
                    
                    for line in exec_result.stdout.strip().split('\n'):
                        logging.info("%s", line)
                except subprocess.CalledProcessError:
                    logging.info("No executions found for %s", job)
                    
        except subprocess.CalledProcessError:
            logging.info("Could not retrieve job list")
    
    def show_recent_logs(self):
        """Show recent log activity."""
        logging.info("")
        logging.info("Recent Log Activity (last 10 entries):")
        logging.info("-" * 38)
        try:
            result = subprocess.run([
                "gcloud", "logging", "read",
                'resource.type=cloud_run_job AND resource.labels.job_name~beryl3-qa-',
                "--project", self.project_id,
                "--limit", "10",
                "--format", "table(timestamp,resource.labels.job_name,severity,jsonPayload.message,textPayload)"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                logging.info("%s", line)
        except subprocess.CalledProcessError:
            logging.info("No recent log entries found.")
    
    def show_summary(self):
        """Show summary statistics."""
        logging.info("")
        logging.info("Summary:")
        logging.info("-" * 8)
        
        # Count total jobs
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "value(metadata.name)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            jobs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            job_count = len(jobs)
        except subprocess.CalledProcessError:
            job_count = 0
        
        # Count running executions
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "executions", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "value(status.conditions[0].status)",
                "--filter", "metadata.labels.run.googleapis.com/job~beryl3-qa- AND status.conditions[0].status=True"
            ], capture_output=True, text=True, check=True)
            
            running_count = len([line for line in result.stdout.strip().split('\n') if line.strip()])
        except subprocess.CalledProcessError:
            running_count = 0
        
        logging.info("Total beryl3-qa-* jobs: %d", job_count)
        logging.info("Currently running executions: %d", running_count)
        
        logging.info("")
        logging.info("Commands:")
        logging.info("-" * 9)
        logging.info("View specific job:     gcloud run jobs describe <job-name> --region=%s --project=%s", 
                    self.config['jobs']['region'], self.project_id)
        logging.info("Execute job:           ./workflows/bin/run_job.py <job-name>")
        logging.info("Delete job:            ./workflows/bin/delete_job.py <job-name>")
        logging.info("Deploy all jobs:       ./workflows/bin/deploy_jobs.py")


def main():
    """Main function to show job status."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and status checker
        manager = SecretsManager()
        checker = JobStatusChecker(manager)
        
        checker.show_job_status()
        
    except Exception as e:
        logging.error("Failed to show job status: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()