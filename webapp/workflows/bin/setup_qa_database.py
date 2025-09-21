#!/usr/bin/env python3
"""
Setup QA Database Environment - Python replacement for ansible qa-db-setup.yml
Creates beryl3-qa database in existing GCP cluster and manages configuration.
"""

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class QADatabaseSetup:
    """Sets up QA database environment in Google Cloud SQL."""
    
    def __init__(self):
        self.manager = SecretsManager()
        self.project_id = self.manager.project_id
        
        # Configuration from ansible inventory
        self.config = {
            'gcp_project': 'beryl3',
            'gcp_region': 'europe-west6', 
            'gcp_zone': 'europe-west6-a',
            'db_instance_name': 'beryl3-qa',
            'db_name': 'beryl3-qa',
            'db_user': 'beryl3-qa',
            'db_password': 'Qa-Pass123!',
            'env_name': 'qa',
            'deployment_environment': 'qa',
            'app_name': 'beryl3',
            'app_image': 'europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp'
        }
        
    def run_gcloud_command(self, command: list) -> Tuple[bool, str]:
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
    
    def check_gcloud_auth(self) -> bool:
        """Check if gcloud CLI is installed and authenticated."""
        # Check if gcloud is available
        try:
            subprocess.run(['gcloud', '--version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.error("gcloud CLI not found. Please install Google Cloud SDK.")
            return False
        
        # Check authentication
        success, output = self.run_gcloud_command([
            'gcloud', 'auth', 'list', 
            '--filter=status:ACTIVE', 
            '--format=value(account)'
        ])
        
        if not success or not output:
            logging.error("No active gcloud authentication found. Run 'gcloud auth login'")
            return False
            
        logging.info(f"Using gcloud account: {output}")
        return True
    
    def check_instance_exists(self) -> bool:
        """Check if database instance exists."""
        command = [
            'gcloud', 'sql', 'instances', 'describe',
            self.config['db_instance_name'],
            '--project', self.config['gcp_project'],
            '--format', 'value(name)'
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            logging.error(f"Database instance '{self.config['db_instance_name']}' not found in project '{self.config['gcp_project']}'")
            return False
            
        logging.info(f"Found database instance: {self.config['db_instance_name']}")
        return True
    
    def get_instance_info(self) -> Dict[str, str]:
        """Get database instance status and connection information."""
        command = [
            'gcloud', 'sql', 'instances', 'describe',
            self.config['db_instance_name'],
            '--project', self.config['gcp_project'],
            '--format', 'value(state,connectionName,ipAddresses[0].ipAddress)'
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            raise Exception(f"Failed to get instance info: {output}")
        
        parts = output.split('\t')
        return {
            'state': parts[0] if len(parts) > 0 else 'UNKNOWN',
            'connection_name': parts[1] if len(parts) > 1 else '',
            'ip_address': parts[2] if len(parts) > 2 else ''
        }
    
    def start_instance_if_stopped(self, instance_info: Dict[str, str]) -> str:
        """Start database instance if it's stopped."""
        if instance_info['state'] == 'STOPPED':
            logging.info("Starting database instance...")
            command = [
                'gcloud', 'sql', 'instances', 'patch',
                self.config['db_instance_name'],
                '--project', self.config['gcp_project'],
                '--activation-policy', 'ALWAYS',
                '--quiet'
            ]
            
            success, output = self.run_gcloud_command(command)
            if not success:
                raise Exception(f"Failed to start instance: {output}")
            
            # Wait for instance to start
            logging.info("Waiting for instance to start...")
            for i in range(10):
                info = self.get_instance_info()
                if info['state'] == 'RUNNABLE':
                    logging.info("Database instance started successfully")
                    return 'RUNNABLE'
                logging.info(f"Instance state: {info['state']}, waiting...")
                subprocess.run(['sleep', '30'])
            
            raise Exception("Instance failed to start within timeout")
        
        return instance_info['state']
    
    def ensure_database_exists(self) -> bool:
        """Create QA database if it doesn't exist."""
        command = [
            'gcloud', 'sql', 'databases', 'list',
            '--instance', self.config['db_instance_name'],
            '--project', self.config['gcp_project'],
            '--filter', f"name={self.config['db_name']}",
            '--format', 'value(name)'
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            raise Exception(f"Failed to check database existence: {output}")
        
        if not output:
            logging.info(f"Creating database: {self.config['db_name']}")
            create_command = [
                'gcloud', 'sql', 'databases', 'create',
                self.config['db_name'],
                '--instance', self.config['db_instance_name'],
                '--project', self.config['gcp_project']
            ]
            
            success, create_output = self.run_gcloud_command(create_command)
            if not success:
                raise Exception(f"Failed to create database: {create_output}")
            
            logging.info(f"Database '{self.config['db_name']}' created successfully")
            return True
        else:
            logging.info(f"Database '{self.config['db_name']}' already exists")
            return False
    
    def ensure_database_user(self) -> bool:
        """Create or update QA database user."""
        command = [
            'gcloud', 'sql', 'users', 'list',
            '--instance', self.config['db_instance_name'],
            '--project', self.config['gcp_project'],
            '--filter', f"name={self.config['db_user']}",
            '--format', 'value(name)'
        ]
        
        success, output = self.run_gcloud_command(command)
        if not success:
            raise Exception(f"Failed to check user existence: {output}")
        
        if not output:
            logging.info(f"Creating database user: {self.config['db_user']}")
            create_command = [
                'gcloud', 'sql', 'users', 'create',
                self.config['db_user'],
                '--instance', self.config['db_instance_name'],
                '--project', self.config['gcp_project'],
                '--password', self.config['db_password']
            ]
            
            success, create_output = self.run_gcloud_command(create_command)
            if not success:
                raise Exception(f"Failed to create user: {create_output}")
            
            logging.info(f"User '{self.config['db_user']}' created successfully")
            return True
        else:
            logging.info(f"Updating password for user: {self.config['db_user']}")
            update_command = [
                'gcloud', 'sql', 'users', 'set-password',
                self.config['db_user'],
                '--instance', self.config['db_instance_name'],
                '--project', self.config['gcp_project'],
                '--password', self.config['db_password']
            ]
            
            success, update_output = self.run_gcloud_command(update_command)
            if not success:
                raise Exception(f"Failed to update user password: {update_output}")
            
            logging.info(f"User '{self.config['db_user']}' password updated")
            return False
    
    def generate_qa_env_file(self, instance_info: Dict[str, str]) -> str:
        """Generate qa.env file with database configuration."""
        connection_string = (
            f"postgresql://{self.config['db_user']}:"
            f"{self.config['db_password']}@"
            f"{instance_info['ip_address']}:5432/"
            f"{self.config['db_name']}"
        )
        
        env_content = f"""# ==============================================================================
# BERYL3 QA ENVIRONMENT CONFIGURATION
# ==============================================================================
# Generated automatically by QA database setup script
# ==============================================================================

# ==============================================================================
# CRITICAL SETTINGS - REQUIRED
# ==============================================================================

# Django Secret Key - Generate new for QA
SECRET_KEY=qa-secret-key-change-this-in-production

# Debug Mode - Set to False for QA
DEBUG=False

# Site Domain - QA environment domain
SITE_DOMAIN=beryl3-qa.example.com

# Allowed Hosts - Update with actual QA domain
ALLOWED_HOSTS=beryl3-qa.example.com,localhost

# ==============================================================================
# DATABASE CONFIGURATION - QA
# ==============================================================================

# Database Engine
DB_ENGINE=django.db.backends.postgresql

# PostgreSQL QA Database Settings - Generated from GCP
PG_DB={self.config['db_name']}
PG_USER={self.config['db_user']}
PG_PASSWORD={self.config['db_password']}
PG_HOST={instance_info['ip_address']}
PG_PORT=5432

# Full connection string for reference
DATABASE_URL={connection_string}

# ==============================================================================
# GOOGLE CLOUD CONFIGURATION
# ==============================================================================

# GCP Project Information
GCP_PROJECT_ID={self.config['gcp_project']}
GCP_REGION={self.config['gcp_region']}
GCP_ZONE={self.config['gcp_zone']}

# Database Instance Information  
DB_INSTANCE_NAME={self.config['db_instance_name']}
DB_CONNECTION_NAME={instance_info['connection_name']}

# ==============================================================================
# EMAIL CONFIGURATION - QA
# ==============================================================================

# Use Resend for QA environment
USE_INBUCKET=False
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=your-resend-api-key-here
DEFAULT_FROM_EMAIL=Beryl3 QA <qa@beryl3-qa.example.com>

# ==============================================================================
# MEDIA STORAGE CONFIGURATION - QA
# ==============================================================================

# Use Google Cloud Storage for QA
USE_GCS_STORAGE=True
GCS_BUCKET_NAME=beryl3-qa-media
GCS_PROJECT_ID={self.config['gcp_project']}
GCS_LOCATION=media
GCS_CREDENTIALS_PATH=/app/gcs-key.json

# ==============================================================================
# APPLICATION FEATURES - QA
# ==============================================================================

# Application Activity Logging
APPLICATION_ACTIVITY_LOGGING=True

# ==============================================================================
# QA ENVIRONMENT INFO
# ==============================================================================

# Environment identification
ENVIRONMENT=qa
DEPLOYMENT_ENVIRONMENT=qa

# Database connection details for reference
# Instance: {self.config['db_instance_name']}
# Database: {self.config['db_name']}
# User: {self.config['db_user']}
# Connection Name: {instance_info['connection_name']}
# IP Address: {instance_info['ip_address']}
"""
        
        qa_env_path = Path(__file__).parent.parent.parent / "qa" / "qa.env"
        qa_env_path.parent.mkdir(exist_ok=True)
        
        with open(qa_env_path, 'w') as f:
            f.write(env_content)
        
        # Set restrictive permissions
        qa_env_path.chmod(0o600)
        
        return str(qa_env_path)
    
    def setup_qa_database(self) -> bool:
        """Main function to setup QA database environment."""
        logging.info("Setting up QA database environment...")
        
        # Check prerequisites
        if not self.check_gcloud_auth():
            return False
        
        if not self.check_instance_exists():
            return False
        
        # Get instance info and start if needed
        instance_info = self.get_instance_info()
        logging.info(f"Database Instance: {self.config['db_instance_name']}")
        logging.info(f"Status: {instance_info['state']}")
        logging.info(f"Connection Name: {instance_info['connection_name']}")
        logging.info(f"IP Address: {instance_info['ip_address']}")
        
        # Start instance if stopped
        final_state = self.start_instance_if_stopped(instance_info)
        if final_state != 'RUNNABLE':
            logging.error("Database instance is not in RUNNABLE state")
            return False
        
        # Update instance info after potential startup
        if instance_info['state'] == 'STOPPED':
            instance_info = self.get_instance_info()
        
        # Create database and user
        self.ensure_database_exists()
        self.ensure_database_user()
        
        # Generate configuration file
        connection_string = (
            f"postgresql://{self.config['db_user']}:"
            f"{self.config['db_password']}@"
            f"{instance_info['ip_address']}:5432/"
            f"{self.config['db_name']}"
        )
        
        qa_env_path = self.generate_qa_env_file(instance_info)
        
        logging.info("=== QA DATABASE SETUP COMPLETE ===")
        logging.info(f"Database: {self.config['db_name']}")
        logging.info(f"User: {self.config['db_user']}")
        logging.info(f"Instance: {self.config['db_instance_name']}")
        logging.info(f"Connection Name: {instance_info['connection_name']}")
        logging.info(f"IP Address: {instance_info['ip_address']}")
        logging.info(f"Connection String: {connection_string}")
        logging.info(f"Configuration saved to: {qa_env_path}")
        logging.info("")
        logging.info("Next steps:")
        logging.info("1. Use 'make qa-deploy' to deploy the application")
        logging.info("2. Access QA environment once deployed")
        
        return True


def main():
    """Main function to setup QA database."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        setup = QADatabaseSetup()
        success = setup.setup_qa_database()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Failed to setup QA database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()