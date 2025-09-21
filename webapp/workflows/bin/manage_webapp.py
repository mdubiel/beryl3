#!/usr/bin/env python3
"""
Manage QA Cloud Run webapp (start/stop/restart/status).
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


class WebappManager:
    """Manages Cloud Run webapp operations."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.project_id = secrets_manager.project_id
        self.service_name = self.config['webapp']['service_name']
        self.region = self.config['webapp']['region']
        
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
    
    def get_service_info(self) -> dict:
        """Get service information."""
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "services", "describe",
            self.service_name,
            "--region", self.region,
            "--project", self.project_id,
            "--format", "json"
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            import json
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def update_service_traffic(self, percentage: int) -> bool:
        """Update service traffic allocation."""
        if percentage == 100:
            # Set all traffic to latest revision
            command = [
                "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "services", "update-traffic",
                self.service_name,
                "--to-latest",
                "--region", self.region,
                "--project", self.project_id
            ]
        elif percentage == 0:
            # Get current revision name and set traffic to 0
            service_info = self.get_service_info()
            if not service_info:
                return False
            
            # Get the current revision name from the status
            traffic_list = service_info.get('status', {}).get('traffic', [])
            if not traffic_list:
                logging.error("No traffic information found")
                return False
            
            revision_name = traffic_list[0].get('revisionName', '')
            if not revision_name:
                logging.error("No revision name found")
                return False
            
            command = [
                "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "services", "update-traffic",
                self.service_name,
                f"--to-revisions={revision_name}=0",
                "--region", self.region,
                "--project", self.project_id
            ]
        else:
            logging.error("Only 0 and 100 percent traffic allocation supported")
            return False
        
        success, output = self.run_gcloud_command(command)
        if not success:
            logging.error("Failed to update traffic: %s", output)
        return success
    
    def start_webapp(self) -> bool:
        """Start the webapp by setting traffic to 100%."""
        logging.info("Starting webapp service: %s", self.service_name)
        
        service_info = self.get_service_info()
        if not service_info:
            logging.error("Could not get service information")
            return False
        
        # Check current traffic allocation
        traffic = service_info.get('status', {}).get('traffic', [])
        if traffic and traffic[0].get('percent', 0) == 100:
            logging.info("Webapp is already running (100% traffic)")
            return True
        
        # Set traffic to 100%
        if self.update_service_traffic(100):
            logging.info("✅ Webapp started successfully")
            return True
        else:
            logging.error("❌ Failed to start webapp")
            return False
    
    def stop_webapp(self) -> bool:
        """Stop the webapp by setting traffic to 0%."""
        logging.info("Stopping webapp service: %s", self.service_name)
        
        service_info = self.get_service_info()
        if not service_info:
            logging.error("Could not get service information")
            return False
        
        # Check current traffic allocation
        traffic = service_info.get('status', {}).get('traffic', [])
        if traffic and traffic[0].get('percent', 0) == 0:
            logging.info("Webapp is already stopped (0% traffic)")
            return True
        
        # Set traffic to 0%
        if self.update_service_traffic(0):
            logging.info("✅ Webapp stopped successfully")
            return True
        else:
            logging.error("❌ Failed to stop webapp")
            return False
    
    def restart_webapp(self) -> bool:
        """Restart the webapp by deploying a new revision."""
        logging.info("Restarting webapp service: %s", self.service_name)
        
        # Force a new revision by updating an annotation
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "services", "update",
            self.service_name,
            f"--update-annotations", f"restart-timestamp={timestamp}",
            "--region", self.region,
            "--project", self.project_id
        ]
        
        success, output = self.run_gcloud_command(command)
        if success:
            logging.info("✅ Webapp restarted successfully")
            return True
        else:
            logging.error("❌ Failed to restart webapp: %s", output)
            return False
    
    def show_webapp_status(self) -> bool:
        """Show detailed webapp status."""
        logging.info("Webapp Status: %s", self.service_name)
        logging.info("=" * 50)
        
        service_info = self.get_service_info()
        if not service_info:
            logging.error("Could not retrieve service information")
            return False
        
        # Basic info
        metadata = service_info.get('metadata', {})
        status = service_info.get('status', {})
        
        logging.info("Service Name: %s", metadata.get('name', 'N/A'))
        logging.info("Region: %s", self.region)
        logging.info("Project: %s", self.project_id)
        
        # URL
        url = status.get('url', 'N/A')
        logging.info("URL: %s", url)
        
        # Traffic and conditions
        traffic = status.get('traffic', [])
        if traffic:
            latest_traffic = traffic[0].get('percent', 0)
            revision = traffic[0].get('revisionName', 'N/A')
            logging.info("Traffic: %d%% to %s", latest_traffic, revision)
            
            if latest_traffic == 0:
                logging.info("Status: 🔴 STOPPED (0% traffic)")
            else:
                logging.info("Status: 🟢 RUNNING (%d%% traffic)", latest_traffic)
        
        # Conditions
        conditions = status.get('conditions', [])
        for condition in conditions:
            condition_type = condition.get('type', 'Unknown')
            condition_status = condition.get('status', 'Unknown')
            if condition_type == 'Ready':
                status_emoji = "🟢" if condition_status == "True" else "🔴"
                logging.info("Ready Status: %s %s", status_emoji, condition_status)
        
        # Resource allocation
        spec = service_info.get('spec', {})
        template = spec.get('template', {})
        containers = template.get('spec', {}).get('containers', [])
        
        if containers:
            container = containers[0]
            resources = container.get('resources', {})
            limits = resources.get('limits', {})
            requests = resources.get('requests', {})
            
            logging.info("\nResource Allocation:")
            if limits:
                logging.info("  Limits: CPU=%s, Memory=%s", 
                           limits.get('cpu', 'N/A'), limits.get('memory', 'N/A'))
            if requests:
                logging.info("  Requests: CPU=%s, Memory=%s", 
                           requests.get('cpu', 'N/A'), requests.get('memory', 'N/A'))
        
        # Scaling configuration
        annotations = template.get('metadata', {}).get('annotations', {})
        max_scale = annotations.get('autoscaling.knative.dev/maxScale', 'N/A')
        min_scale = annotations.get('autoscaling.knative.dev/minScale', 'N/A')
        target = annotations.get('autoscaling.knative.dev/target', 'N/A')
        
        logging.info("\nScaling Configuration:")
        logging.info("  Min instances: %s", min_scale)
        logging.info("  Max instances: %s", max_scale)
        logging.info("  Target utilization: %s", target)
        
        # Latest image
        if containers:
            image = containers[0].get('image', 'N/A')
            logging.info("\nImage: %s", image)
        
        return True


def main():
    """Main function to manage webapp operations."""
    parser = argparse.ArgumentParser(
        description="Manage QA Cloud Run webapp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python workflows/bin/manage_webapp.py status
  uv run python workflows/bin/manage_webapp.py start
  uv run python workflows/bin/manage_webapp.py stop  
  uv run python workflows/bin/manage_webapp.py restart

Traffic Management:
  start  - Set traffic to 100% (webapp receives requests)
  stop   - Set traffic to 0% (webapp receives no requests, saves costs)
  restart - Force new revision deployment
        """
    )
    
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status'],
        help='Action to perform on the webapp'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and webapp manager
        manager = SecretsManager()
        webapp_manager = WebappManager(manager)
        
        success = False
        
        if args.action == 'start':
            success = webapp_manager.start_webapp()
        elif args.action == 'stop':
            success = webapp_manager.stop_webapp()
        elif args.action == 'restart':
            success = webapp_manager.restart_webapp()
        elif args.action == 'status':
            success = webapp_manager.show_webapp_status()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to manage webapp: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()