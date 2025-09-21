#!/usr/bin/env python3
"""
Deploy QA Cloud Run Jobs using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

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
    
    def deploy_job(self, job_def: Dict[str, any]) -> bool:
        """Deploy a single Cloud Run Job."""
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
    
    def deploy_all_jobs(self) -> bool:
        """Deploy all Cloud Run Jobs."""
        logging.info("Deploying beryl3-qa-* Cloud Run Jobs")
        logging.info("Using image: %s", self.config['jobs']['image'])
        
        job_definitions = self.config['jobs']['job_definitions']
        success_count = 0
        
        logging.info("Deploying Cloud Run Jobs...")
        
        for job_def in job_definitions:
            if self.deploy_job(job_def):
                success_count += 1
        
        logging.info("All beryl3-qa-* jobs deployed successfully!")
        
        # Show deployed jobs
        logging.info("Deployed jobs:")
        self.show_job_status()
        
        # Show usage examples
        logging.info("Execute jobs with:")
        for job_def in job_definitions:
            logging.info("  ./workflows/bin/run_job.py %s", job_def['name'])
        
        return success_count == len(job_definitions)
    
    def show_job_status(self):
        """Show status of deployed jobs."""
        try:
            result = subprocess.run([
                "gcloud", "run", "jobs", "list",
                "--region", self.config['jobs']['region'],
                "--project", self.project_id,
                "--format", "table(metadata.name,status.conditions[0].status)",
                "--filter", "metadata.name~beryl3-qa-"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                logging.info("  %s", line)
        except subprocess.CalledProcessError:
            logging.warning("Could not retrieve job status")


def main():
    """Main function to deploy QA jobs."""
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
        
        success = deployer.deploy_all_jobs()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to deploy jobs: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()