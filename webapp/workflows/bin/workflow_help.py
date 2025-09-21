#!/usr/bin/env python3
"""
Show help and available commands for the Beryl3 QA workflow system.
"""

import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


def main():
    """Show workflow help and available commands."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Load configuration to show current settings
        manager = SecretsManager()
        
        logging.info("Beryl3 QA Workflow System")
        logging.info("=" * 50)
        logging.info("Project: %s", manager.project_id)
        logging.info("Service Account: %s", manager.service_account)
        logging.info("Total secrets: %d", len(manager.secrets))
        logging.info("Config file: %s", manager.config_path)
        logging.info("")
        
        logging.info("Available Commands:")
        logging.info("-" * 30)
        logging.info("")
        
        logging.info("🔧 Setup & Configuration:")
        logging.info("  uv run python workflows/bin/setup_secrets.py")
        logging.info("    - Setup all secrets in Google Cloud Secret Manager")
        logging.info("    - Grant IAM permissions to service account")
        logging.info("    - Intelligent versioning (only updates if values changed)")
        logging.info("")
        
        logging.info("🐳 Docker Image Management:")
        logging.info("  uv run python workflows/bin/build_images.py")
        logging.info("    - Build webapp and jobs Docker images")
        logging.info("    - Auto-increment version numbers")
        logging.info("    - Tag for local and registry use")
        logging.info("")
        logging.info("  uv run python workflows/bin/push_images.py")
        logging.info("    - Push images to Google Artifact Registry")
        logging.info("    - Configure Docker authentication")
        logging.info("    - Push both versioned and latest tags")
        logging.info("")
        
        logging.info("☁️  Cloud Run Deployment:")
        logging.info("  uv run python workflows/bin/deploy_webapp.py")
        logging.info("    - Deploy QA webapp to Cloud Run")
        logging.info("    - Generate YAML with secret references")
        logging.info("    - Show deployment status and URL")
        logging.info("")
        logging.info("  uv run python workflows/bin/deploy_jobs.py")
        logging.info("    - Deploy all Cloud Run Jobs (migrate, collectstatic, etc.)")
        logging.info("    - Configure jobs with database and storage access")
        logging.info("    - Show job deployment status")
        logging.info("")
        
        logging.info("🚀 Job Execution:")
        logging.info("  uv run python workflows/bin/run_job.py <job-name>")
        logging.info("    - Execute specific Cloud Run Job")
        logging.info("    - Available jobs: beryl3-qa-migrate, beryl3-qa-collectstatic,")
        logging.info("                      beryl3-qa-seed (creates user@mdubiel.org + test data),")
        logging.info("                      beryl3-qa-setup-initial-users")
        logging.info("")
        
        logging.info("🗄️  Database Management:")
        logging.info("  uv run python workflows/bin/manage_database.py status")
        logging.info("    - Show database status and connection info")
        logging.info("    - Display cost optimization recommendations")
        logging.info("")
        logging.info("  uv run python workflows/bin/manage_database.py start")
        logging.info("    - Start the Cloud SQL database instance")
        logging.info("    - Wait for operation to complete")
        logging.info("")
        logging.info("  uv run python workflows/bin/manage_database.py stop")
        logging.info("    - Stop the database to save costs")
        logging.info("    - Only storage costs apply when stopped")
        logging.info("")
        logging.info("  uv run python workflows/bin/manage_database.py restart")
        logging.info("    - Restart the database instance")
        logging.info("    - Useful for troubleshooting")
        logging.info("")
        
        logging.info("📱 Application Management:")
        logging.info("  uv run python workflows/bin/manage_webapp.py status")
        logging.info("    - Show webapp deployment status and traffic allocation")
        logging.info("    - Display resource usage and scaling configuration")
        logging.info("")
        logging.info("  uv run python workflows/bin/manage_webapp.py start")
        logging.info("    - Start webapp by setting traffic to 100%")
        logging.info("")
        logging.info("  uv run python workflows/bin/manage_webapp.py stop")
        logging.info("    - Stop webapp by setting traffic to 0% (cost optimization)")
        logging.info("")
        logging.info("  uv run python workflows/bin/manage_webapp.py restart")
        logging.info("    - Restart webapp by forcing new revision deployment")
        logging.info("")
        
        logging.info("🚀 Complete Deployment:")
        logging.info("  uv run python workflows/bin/deploy_new_version.py")
        logging.info("    - Complete new version deployment workflow")
        logging.info("    - Build → Push → Deploy → Migrate → Setup")
        logging.info("    - Includes database startup and status reporting")
        logging.info("")
        
        logging.info("📊 Status & Monitoring:")
        logging.info("  uv run python workflows/bin/status.py")
        logging.info("    - Comprehensive status report of entire QA environment")
        logging.info("    - Images in GAR, database status, webapp, and jobs")
        logging.info("    - Recent job executions and resource allocation")
        logging.info("")
        
        logging.info("🔍 Testing & Validation:")
        logging.info("  uv run python test_secrets_manager.py")
        logging.info("    - Test SecretsManager functionality")
        logging.info("    - Validate YAML configuration")
        logging.info("    - Show environment variable mappings")
        logging.info("")
        
        logging.info("📁 Configuration Files:")
        logging.info("  workflows/envs/qa/secrets.yaml - Main configuration (YAML)")
        logging.info("  workflows/envs/qa/secrets.yaml.template - Template for setup")
        logging.info("  workflows/bin/ - Python workflow scripts")
        logging.info("")
        
        logging.info("🔗 Deployment Workflows:")
        logging.info("")
        logging.info("🎯 Quick Deploy (Recommended):")
        logging.info("  uv run python workflows/bin/deploy_new_version.py")
        logging.info("    - Complete automated deployment of new version")
        logging.info("")
        logging.info("🔧 Manual Step-by-Step:")
        logging.info("  1. uv run python workflows/bin/manage_database.py start")
        logging.info("  2. uv run python workflows/bin/setup_secrets.py")
        logging.info("  3. uv run python workflows/bin/build_images.py")
        logging.info("  4. uv run python workflows/bin/push_images.py")
        logging.info("  5. uv run python workflows/bin/deploy_jobs.py")
        logging.info("  6. uv run python workflows/bin/run_job.py beryl3-qa-migrate")
        logging.info("  7. uv run python workflows/bin/run_job.py beryl3-qa-collectstatic")
        logging.info("  8. uv run python workflows/bin/deploy_webapp.py")
        logging.info("  9. uv run python workflows/bin/run_job.py beryl3-qa-setup-initial-users")
        logging.info(" 10. uv run python workflows/bin/run_job.py beryl3-qa-seed")
        logging.info("")
        logging.info("💰 Cost Optimization:")
        logging.info("  After testing: uv run python workflows/bin/manage_database.py stop")
        logging.info("  Before testing: uv run python workflows/bin/manage_database.py start")
        logging.info("  Stop webapp: uv run python workflows/bin/manage_webapp.py stop")
        
    except Exception as e:
        logging.error("Failed to load configuration: %s", e)
        logging.info("")
        logging.info("Make sure you have:")
        logging.info("- workflows/envs/qa/secrets.yaml configuration file")
        logging.info("- PyYAML installed (uv sync)")
        sys.exit(1)


if __name__ == "__main__":
    main()