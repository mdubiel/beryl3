#!/usr/bin/env python3
"""
Show comprehensive status of QA environment - images, database, webapp, and jobs.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class QAStatusReporter:
    """Reports comprehensive status of QA environment."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.docker_config = secrets_manager.get_docker_config()
        self.project_id = secrets_manager.project_id
        
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
    
    def get_version_info(self) -> Dict[str, str]:
        """Get current version information."""
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if not version_file.exists():
            return {"current": "unknown", "format": "0.1-build123"}
        
        version_data = {}
        with open(version_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    version_data[key] = int(value)
        
        major = version_data.get('MAJOR', 0)
        minor = version_data.get('MINOR', 1)
        build = version_data.get('BUILD', 0)
        
        return {
            "current": f"{major}.{minor}-build{build}",
            "next": f"{major}.{minor}-build{build + 1}"
        }
    
    def show_image_status(self) -> bool:
        """Show status of images in Google Artifact Registry."""
        logging.info("📦 Docker Images in Google Artifact Registry")
        logging.info("=" * 60)
        
        registry_parts = self.docker_config['registry'].split('/')
        location = registry_parts[0].split('-')[0] + '-' + registry_parts[0].split('-')[1]  # e.g., europe-west6
        repository = registry_parts[2]  # e.g., beryl3
        
        image_name = self.docker_config['images']['webapp']
        
        # Get image list
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "artifacts", "docker", "images", "list",
            f"{self.docker_config['registry']}/{image_name}",
            "--project", self.project_id,
            "--format", "json"
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            logging.error("❌ Failed to get image list: %s", output)
            return False
        
        try:
            images = json.loads(output)
        except json.JSONDecodeError:
            logging.error("❌ Failed to parse image list")
            return False
        
        if not images:
            logging.warning("⚠️  No images found in registry")
            return True
        
        # Show version info
        version_info = self.get_version_info()
        logging.info("Current Version: %s", version_info['current'])
        logging.info("Next Version: %s", version_info['next'])
        logging.info("")
        
        # Show latest images
        logging.info("Latest Images:")
        for image in images[:5]:  # Show latest 5 images
            uri = image.get('uri', '')
            created = image.get('createTime', 'Unknown')
            size_mb = round(image.get('sizeBytes', 0) / (1024 * 1024), 1) if image.get('sizeBytes') else 0
            
            # Extract tag from URI
            tag = uri.split(':')[-1] if ':' in uri else 'latest'
            
            logging.info("  %s (Size: %sMB, Created: %s)", tag, size_mb, created[:19] if created != 'Unknown' else 'Unknown')
        
        return True
    
    def show_database_status(self) -> bool:
        """Show Cloud SQL database status."""
        logging.info("🗄️  Cloud SQL Database Status")
        logging.info("=" * 60)
        
        instance_name = "beryl3-qa"
        
        # Get instance details
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "sql", "instances", "describe",
            instance_name,
            "--project", self.project_id,
            "--format", "json"
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            logging.error("❌ Failed to get database status: %s", output)
            return False
        
        try:
            instance_info = json.loads(output)
        except json.JSONDecodeError:
            logging.error("❌ Failed to parse database info")
            return False
        
        # Extract key information
        state = instance_info.get('state', 'Unknown')
        version = instance_info.get('databaseVersion', 'Unknown')
        region = instance_info.get('region', 'Unknown')
        
        settings = instance_info.get('settings', {})
        tier = settings.get('tier', 'Unknown')
        
        # Parse tier for vCPU and memory info
        vcpu_info = "Unknown"
        memory_info = "Unknown"
        
        if tier.startswith('db-'):
            if 'f1-micro' in tier:
                vcpu_info = "Shared vCPU"
                memory_info = "0.6GB"
            elif 'g1-small' in tier:
                vcpu_info = "Shared vCPU"
                memory_info = "1.7GB"
            # Add more tier mappings as needed
        
        # IP addresses
        ip_addresses = instance_info.get('ipAddresses', [])
        private_ip = None
        public_ip = None
        
        for ip_addr in ip_addresses:
            if ip_addr.get('type') == 'PRIVATE':
                private_ip = ip_addr.get('ipAddress')
            elif ip_addr.get('type') == 'PRIMARY':
                public_ip = ip_addr.get('ipAddress')
        
        # Status icon
        status_icon = "🟢" if state == "RUNNABLE" else "🔴" if state == "STOPPED" else "🟡"
        
        logging.info("Instance: %s", instance_name)
        logging.info("Status: %s %s", status_icon, state)
        logging.info("Version: %s", version)
        logging.info("Region: %s", region)
        logging.info("Tier: %s", tier)
        logging.info("vCPU: %s", vcpu_info)
        logging.info("Memory: %s", memory_info)
        
        if public_ip:
            logging.info("Public IP: %s", public_ip)
        if private_ip:
            logging.info("Private IP: %s", private_ip)
        
        # Connection info
        connection_name = instance_info.get('connectionName', 'Unknown')
        logging.info("Connection Name: %s", connection_name)
        
        # Cost optimization note
        if state == "RUNNABLE":
            logging.info("\n💡 Cost Note: Database is running and incurring charges")
        elif state == "STOPPED":
            logging.info("\n💰 Cost Optimized: Database is stopped (storage costs only)")
        
        return True
    
    def show_webapp_status(self) -> bool:
        """Show Cloud Run webapp status."""
        logging.info("🌐 Cloud Run Webapp Status")
        logging.info("=" * 60)
        
        service_name = self.config['webapp']['service_name']
        region = self.config['webapp']['region']
        
        # Get service details
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "services", "describe",
            service_name,
            "--region", region,
            "--project", self.project_id,
            "--format", "json"
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            logging.error("❌ Failed to get webapp status: %s", output)
            return False
        
        try:
            service_info = json.loads(output)
        except json.JSONDecodeError:
            logging.error("❌ Failed to parse webapp info")
            return False
        
        # Extract information
        metadata = service_info.get('metadata', {})
        status = service_info.get('status', {})
        
        url = status.get('url', 'N/A')
        
        # Traffic info
        traffic = status.get('traffic', [])
        traffic_percent = 0
        current_revision = "N/A"
        
        if traffic:
            traffic_percent = traffic[0].get('percent', 0)
            current_revision = traffic[0].get('revisionName', 'N/A')
        
        # Ready condition
        conditions = status.get('conditions', [])
        ready_status = "Unknown"
        for condition in conditions:
            if condition.get('type') == 'Ready':
                ready_status = condition.get('status', 'Unknown')
                break
        
        # Status icons
        traffic_icon = "🟢" if traffic_percent > 0 else "🔴"
        ready_icon = "🟢" if ready_status == "True" else "🔴"
        
        logging.info("Service: %s", service_name)
        logging.info("Region: %s", region)
        logging.info("URL: %s", url)
        logging.info("Traffic: %s %d%% to %s", traffic_icon, traffic_percent, current_revision)
        logging.info("Ready: %s %s", ready_icon, ready_status)
        
        # Current image
        spec = service_info.get('spec', {})
        template = spec.get('template', {})
        containers = template.get('spec', {}).get('containers', [])
        
        if containers:
            image = containers[0].get('image', 'N/A')
            # Extract version from image
            image_tag = image.split(':')[-1] if ':' in image else 'latest'
            logging.info("Image Tag: %s", image_tag)
        
        return True
    
    def show_jobs_status(self) -> bool:
        """Show Cloud Run Jobs status."""
        logging.info("⚙️  Cloud Run Jobs Status")
        logging.info("=" * 60)
        
        region = self.config['jobs']['region']
        
        # Get jobs list
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "jobs", "list",
            "--region", region,
            "--project", self.project_id,
            "--filter", "metadata.name~beryl3-qa-",
            "--format", "json"
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            logging.error("❌ Failed to get jobs list: %s", output)
            return False
        
        try:
            jobs = json.loads(output)
        except json.JSONDecodeError:
            logging.error("❌ Failed to parse jobs info")
            return False
        
        if not jobs:
            logging.warning("⚠️  No jobs found")
            return True
        
        logging.info("Deployed Jobs:")
        for job in jobs:
            name = job.get('metadata', {}).get('name', 'Unknown')
            status = job.get('status', {})
            
            # Get the latest condition
            conditions = status.get('conditions', [])
            job_status = "Unknown"
            for condition in conditions:
                if condition.get('type') == 'Ready':
                    job_status = condition.get('status', 'Unknown')
                    break
            
            status_icon = "🟢" if job_status == "True" else "🔴" if job_status == "False" else "🟡"
            logging.info("  %s %s", status_icon, name)
        
        # Show recent job executions
        logging.info("\nRecent Job Executions:")
        
        for job in jobs:
            job_name = job.get('metadata', {}).get('name', 'Unknown')
            
            # Get recent executions
            exec_command = [
                "/home/mdubiel/google-cloud-sdk/bin/gcloud", "run", "jobs", "executions", "list",
                "--job", job_name,
                "--region", region,
                "--project", self.project_id,
                "--limit", "1",
                "--format", "json"
            ]
            
            exec_success, exec_output = self.run_gcloud_command(exec_command)
            if exec_success:
                try:
                    executions = json.loads(exec_output)
                    if executions:
                        execution = executions[0]
                        exec_name = execution.get('metadata', {}).get('name', 'Unknown')
                        exec_status = execution.get('status', {})
                        
                        # Get completion status
                        exec_conditions = exec_status.get('conditions', [])
                        completion_status = "Unknown"
                        for condition in exec_conditions:
                            if condition.get('type') == 'Completed':
                                completion_status = condition.get('status', 'Unknown')
                                break
                        
                        exec_icon = "✅" if completion_status == "True" else "❌" if completion_status == "False" else "⏳"
                        start_time = execution.get('metadata', {}).get('creationTimestamp', 'Unknown')
                        
                        logging.info("  %s %s - %s (%s)", exec_icon, job_name, exec_name, start_time[:19] if start_time != 'Unknown' else 'Unknown')
                    else:
                        logging.info("  ⚪ %s - No recent executions", job_name)
                except json.JSONDecodeError:
                    logging.info("  ❓ %s - Could not parse execution info", job_name)
            else:
                logging.info("  ❓ %s - Could not get execution info", job_name)
        
        return True
    
    def show_comprehensive_status(self) -> bool:
        """Show comprehensive status of all components."""
        logging.info("🔍 Beryl3 QA Environment Status Report")
        logging.info("=" * 70)
        logging.info("Project: %s", self.project_id)
        logging.info("Generated: %s", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        logging.info("")
        
        success = True
        
        # Images status
        if not self.show_image_status():
            success = False
        logging.info("")
        
        # Database status
        if not self.show_database_status():
            success = False
        logging.info("")
        
        # Webapp status
        if not self.show_webapp_status():
            success = False
        logging.info("")
        
        # Jobs status
        if not self.show_jobs_status():
            success = False
        logging.info("")
        
        # Summary
        logging.info("📋 Quick Actions")
        logging.info("=" * 30)
        logging.info("Database:  uv run python workflows/bin/manage_database.py [start|stop|restart]")
        logging.info("Webapp:    uv run python workflows/bin/manage_webapp.py [start|stop|restart]")
        logging.info("Deploy:    uv run python workflows/bin/deploy_new_version.py")
        logging.info("Jobs:      uv run python workflows/bin/run_job.py <job-name>")
        
        return success


def main():
    """Main function to show comprehensive status."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and status reporter
        manager = SecretsManager()
        reporter = QAStatusReporter(manager)
        
        success = reporter.show_comprehensive_status()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to generate status report: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()