#!/usr/bin/env python3
"""
Deploy QA Cloud Run webapp using YAML configuration.
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class WebappDeployer:
    """Deploys Cloud Run webapp based on YAML configuration."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.config = secrets_manager.get_cloud_run_config()
        self.project_id = secrets_manager.project_id
        
    def build_env_variables_yaml(self) -> str:
        """Build environment variables section for Cloud Run YAML."""
        env_mapping = self.manager.get_env_var_mapping(context="webapp")
        
        env_vars = []
        for env_var, secret_ref in env_mapping.items():
            secret_name, version = secret_ref.split(':', 1)
            env_vars.append(f"""        - name: {env_var}
          valueFrom:
            secretKeyRef:
              name: {secret_name}
              key: {version}""")
        
        return "\n".join(env_vars)
    
    def generate_cloudrun_yaml(self) -> str:
        """Generate Cloud Run service YAML configuration."""
        webapp_config = self.config['webapp']
        service_name = webapp_config['service_name']
        image = webapp_config['image']
        region = webapp_config['region']
        
        env_variables = self.build_env_variables_yaml()
        
        yaml_content = f"""apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: {service_name}
  labels:
    cloud.googleapis.com/location: {region}
  annotations:
    run.googleapis.com/ingress: all
    environment: qa
spec:
  template:
    metadata:
      labels:
        environment: qa
        app: beryl3-webapp
      annotations:
        autoscaling.knative.dev/maxScale: "1"
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/target: "80"
        run.googleapis.com/cpu: "2000m"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/service-account: {self.manager.service_account}
        run.googleapis.com/cloudsql-instances: beryl3:europe-west6:beryl3-qa
    spec:
      containerConcurrency: 1
      timeoutSeconds: 600
      serviceAccountName: {self.manager.service_account}
      containers:
      - name: beryl3-webapp
        image: {image}
        ports:
        - name: http1
          containerPort: 8000
        env:
{env_variables}
        
        # Resource limits
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "1000m"
            memory: "1Gi"

  traffic:
  - percent: 100
    latestRevision: true
"""
        return yaml_content
    
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
    
    def deploy_webapp(self) -> bool:
        """Deploy the QA webapp service."""
        webapp_config = self.config['webapp']
        service_name = webapp_config['service_name']
        region = webapp_config['region']
        image = webapp_config['image']
        
        logging.info("Deploying QA webapp service: %s", service_name)
        logging.info("Using image: %s", image)
        logging.info("Region: %s", region)
        
        # Generate YAML configuration
        yaml_content = self.generate_cloudrun_yaml()
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_yaml_path = f.name
        
        try:
            # Deploy using gcloud
            deploy_cmd = [
                "gcloud", "run", "services", "replace", temp_yaml_path,
                "--region", region,
                "--project", self.project_id
            ]
            
            success, output = self.run_gcloud_command(deploy_cmd)
            if not success:
                logging.error("Failed to deploy webapp: %s", output)
                return False
            
            logging.info("QA webapp deployed successfully!")
            
            # Set public access
            public_cmd = [
                "gcloud", "run", "services", "add-iam-policy-binding", service_name,
                "--member", "allUsers",
                "--role", "roles/run.invoker",
                "--region", region,
                "--project", self.project_id
            ]
            
            success, output = self.run_gcloud_command(public_cmd)
            if success:
                logging.info("✅ Public access configured")
            else:
                logging.warning("⚠️  Could not set public access: %s", output)
            
            # Get service URL
            describe_cmd = [
                "gcloud", "run", "services", "describe", service_name,
                "--region", region,
                "--project", self.project_id,
                "--format", "value(status.url)"
            ]
            
            success, service_url = self.run_gcloud_command(describe_cmd)
            if success and service_url:
                logging.info("Service URL: %s", service_url)
            else:
                logging.warning("Could not retrieve service URL")
            
            return True
            
        finally:
            # Clean up temporary file
            Path(temp_yaml_path).unlink(missing_ok=True)
    
    def show_webapp_status(self):
        """Show status of deployed webapp."""
        webapp_config = self.config['webapp']
        service_name = webapp_config['service_name']
        region = webapp_config['region']
        
        try:
            result = subprocess.run([
                "gcloud", "run", "services", "describe", service_name,
                "--region", region,
                "--project", self.project_id,
                "--format", "table(metadata.name,status.url,status.conditions[0].status)"
            ], capture_output=True, text=True, check=True)
            
            logging.info("Webapp Status:")
            for line in result.stdout.strip().split('\\n'):
                logging.info("  %s", line)
        except subprocess.CalledProcessError:
            logging.warning("Could not retrieve webapp status")


def main():
    """Main function to deploy QA webapp."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and webapp deployer
        manager = SecretsManager()
        deployer = WebappDeployer(manager)
        
        success = deployer.deploy_webapp()
        
        if success:
            # Show status
            deployer.show_webapp_status()
        else:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to deploy webapp: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()