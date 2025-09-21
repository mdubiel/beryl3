#!/usr/bin/env python3
"""
Deploy QA scheduled email queue processing Cloud Run job using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class ScheduledJobDeployer:
    """Deploys scheduled Cloud Run Jobs based on YAML configuration."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.project_id = secrets_manager.project_id
        
    def build_common_secrets_string(self) -> str:
        """Build the --set-secrets parameter string for jobs context."""
        return self.manager.build_secrets_string(context="jobs")
    
    def deploy_scheduled_job(self, job_name: str) -> bool:
        """Deploy a scheduled Cloud Run Job."""
        # Find the job definition
        job_definitions = self.config['jobs']['job_definitions']
        job_def = None
        
        for jd in job_definitions:
            if jd['name'] == job_name:
                job_def = jd
                break
        
        if not job_def:
            logging.error("Job definition not found: %s", job_name)
            return False
        
        if 'schedule' not in job_def:
            logging.error("Job %s does not have a schedule defined", job_name)
            return False
        
        command = job_def['command']
        description = job_def['description']
        schedule = job_def['schedule']
        
        logging.info("Deploying scheduled job %s (%s)...", job_name, description)
        logging.info("Schedule: %s (every 5 minutes)", schedule)
        
        # Build gcloud command for scheduled job
        gcloud_cmd = [
            "gcloud", "run", "jobs", "deploy", job_name,
            "--image", self.config['jobs']['image'],
            "--command", ",".join(command),
            "--region", self.config['jobs']['region'],
            "--service-account", self.manager.service_account,
            "--set-secrets", self.build_common_secrets_string(),
            "--set-cloudsql-instances", self.config['jobs']['cloudsql_instances'],
            "--project", self.project_id
        ]
        
        try:
            # Deploy the job first
            result = subprocess.run(
                gcloud_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logging.info("  %s deployed successfully", job_name)
            
            # Create Cloud Scheduler job for the schedule
            # Cloud Scheduler has different available regions, use europe-west6 (closest to europe-west4)
            scheduler_region = "europe-west6"
            scheduler_name = f"{job_name}-scheduler"
            schedule_cmd = [
                "gcloud", "scheduler", "jobs", "create", "http", scheduler_name,
                "--location", scheduler_region,
                "--schedule", schedule,
                "--uri", f"https://{self.config['jobs']['region']}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{self.project_id}/jobs/{job_name}:run",
                "--http-method", "POST",
                "--oauth-service-account-email", self.manager.service_account,
                "--project", self.project_id,
                "--description", f"Scheduler for {description}",
                "--quiet"
            ]
            
            try:
                result = subprocess.run(
                    schedule_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                logging.info("  ✅ Scheduler %s created successfully", scheduler_name)
                logging.info("  📅 Will run every 5 minutes to process email queue")
                return True
            except subprocess.CalledProcessError as e:
                if "already exists" in e.stderr:
                    logging.info("  📅 Scheduler already exists, updating...")
                    # Try to update the existing scheduler
                    update_cmd = [
                        "gcloud", "scheduler", "jobs", "update", "http", scheduler_name,
                        "--location", scheduler_region,
                        "--schedule", schedule,
                        "--project", self.project_id,
                        "--quiet"
                    ]
                    subprocess.run(update_cmd, capture_output=True, text=True, check=True)
                    logging.info("  ✅ Scheduler updated successfully")
                    return True
                else:
                    logging.error("  ERROR creating scheduler: %s", e.stderr.strip())
                    return False
                    
        except subprocess.CalledProcessError as e:
            logging.error("  ERROR deploying %s: %s", job_name, e.stderr.strip())
            return False


def main():
    """Main function to deploy scheduled email queue job."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and job deployer
        manager = SecretsManager()
        deployer = ScheduledJobDeployer(manager)
        
        # Deploy the scheduled email queue processing job
        success = deployer.deploy_scheduled_job("beryl3-qa-send-queued-mail")
        
        if success:
            logging.info("✅ Scheduled email queue job deployed successfully!")
            logging.info("📧 The job will automatically process email queue every 5 minutes")
        else:
            logging.error("❌ Failed to deploy scheduled email queue job")
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to deploy scheduled email queue job: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()