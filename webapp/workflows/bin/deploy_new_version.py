#!/usr/bin/env python3
"""
Deploy a new version of the application - build, push, and deploy webapp and jobs.
"""

import logging
import subprocess
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class NewVersionDeployer:
    """Deploys a new version of the application with complete workflow."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.project_root = Path(__file__).parent.parent.parent
        
    def run_script(self, script_name: str) -> bool:
        """Run a workflow script and return success status."""
        script_path = self.project_root / "workflows/bin" / script_name
        
        logging.info("Running %s...", script_name)
        
        try:
            result = subprocess.run(
                ["uv", "run", "python", str(script_path)],
                cwd=self.project_root,
                check=True,
                text=True
            )
            logging.info("✅ %s completed successfully", script_name)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("❌ %s failed with exit code %d", script_name, e.returncode)
            return False
    
    def run_job(self, job_name: str) -> bool:
        """Run a specific Cloud Run Job."""
        logging.info("Executing job: %s", job_name)
        
        try:
            result = subprocess.run(
                ["uv", "run", "python", "workflows/bin/run_job.py", job_name],
                cwd=self.project_root,
                check=True,
                text=True
            )
            logging.info("✅ Job %s completed successfully", job_name)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("❌ Job %s failed with exit code %d", job_name, e.returncode)
            return False
    
    def deploy_new_version(self) -> bool:
        """Deploy a complete new version of the application."""
        logging.info("🚀 Starting new version deployment...")
        logging.info("=" * 60)
        
        # Step 1: Ensure database is running
        logging.info("📋 Step 1: Check database status")
        if not self.run_script("manage_database.py start"):
            logging.error("Failed to start database")
            return False
        
        # Step 2: Setup secrets
        logging.info("📋 Step 2: Setup secrets")
        if not self.run_script("setup_secrets.py"):
            logging.error("Failed to setup secrets")
            return False
        
        # Step 3: Build new images
        logging.info("📋 Step 3: Build new images")
        if not self.run_script("build_images.py"):
            logging.error("Failed to build images")
            return False
        
        # Step 4: Push images to registry
        logging.info("📋 Step 4: Push images to registry")
        if not self.run_script("push_images.py"):
            logging.error("Failed to push images")
            return False
        
        # Step 5: Deploy jobs
        logging.info("📋 Step 5: Deploy Cloud Run Jobs")
        if not self.run_script("deploy_jobs.py"):
            logging.error("Failed to deploy jobs")
            return False
        
        # Step 6: Run database migrations
        logging.info("📋 Step 6: Run database migrations")
        if not self.run_job("beryl3-qa-migrate"):
            logging.error("Failed to run migrations")
            return False
        
        # Step 7: Collect static files
        logging.info("📋 Step 7: Collect static files")
        if not self.run_job("beryl3-qa-collectstatic"):
            logging.error("Failed to collect static files")
            return False
        
        # Step 8: Deploy webapp
        logging.info("📋 Step 8: Deploy webapp")
        if not self.run_script("deploy_webapp.py"):
            logging.error("Failed to deploy webapp")
            return False
        
        # Step 9: Setup initial users (if needed)
        logging.info("📋 Step 9: Setup initial users")
        if not self.run_job("beryl3-qa-setup-initial-users"):
            logging.warning("⚠️  Initial users setup failed (may already exist)")
        
        # Step 10: Seed test data (optional)
        logging.info("📋 Step 10: Seed test data")
        if not self.run_job("beryl3-qa-seed"):
            logging.warning("⚠️  Test data seeding failed (may already exist)")
        
        logging.info("")
        logging.info("🎉 New version deployment completed successfully!")
        logging.info("=" * 60)
        
        # Show final status
        logging.info("📊 Deployment Summary:")
        if not self.run_script("status.py"):
            logging.warning("Could not retrieve deployment status")
        
        return True


def main():
    """Main function to deploy new version."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and deployer
        manager = SecretsManager()
        deployer = NewVersionDeployer(manager)
        
        success = deployer.deploy_new_version()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to deploy new version: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()