#!/usr/bin/env python3
"""
Deploy QA test email Cloud Run job using YAML configuration.
"""

import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class JobDeployer:
    """Deploys Cloud Run Jobs based on YAML configuration."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.project_id = secrets_manager.project_id
        
    def build_common_secrets_string(self) -> str:
        """Build the --set-secrets parameter string for jobs context."""
        return self.manager.build_secrets_string(context="jobs")
    
    def deploy_job_by_name(self, job_name: str) -> bool:
        """Deploy a specific Cloud Run Job by name."""
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
        
        return self.deploy_job(job_def)
    
    def deploy_job(self, job_def: dict) -> bool:
        """Deploy a single Cloud Run Job."""
        import subprocess
        
        job_name = job_def['name']
        command = job_def['command']
        description = job_def['description']
        
        logging.info("Deploying %s (%s)...", job_name, description)
        
        # Build gcloud command
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
            result = subprocess.run(
                gcloud_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logging.info("  %s deployed successfully", job_name)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("  ERROR deploying %s: %s", job_name, e.stderr.strip())
            return False


def main():
    """Main function to deploy QA test email job."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and job deployer
        manager = SecretsManager()
        deployer = JobDeployer(manager)
        
        # Deploy the test email job specifically
        success = deployer.deploy_job_by_name("beryl3-qa-test-email")
        
        if success:
            logging.info("✅ Test email job deployed successfully!")
            logging.info("📧 Run the job to send test emails to mdubiel@gmail.com")
            logging.info("Execute with: ./workflows/bin/run_job.py beryl3-qa-test-email")
        else:
            logging.error("❌ Failed to deploy test email job")
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to deploy test email job: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()