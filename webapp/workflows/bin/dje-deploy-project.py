#!/usr/bin/env python3
"""
Django Europe - Git-Based Project Deployment Script

This script deploys the beryl3 project to Django Europe hosting directly from git,
using a simplified structure that serves static files from GCS.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
import os


class DjangoEuropeProjectDeploy:
    """Manages git-based project deployment for Django Europe hosting."""
    
    def __init__(self, environment='preprod', host_config=None, git_config=None):
        # Environment-specific configurations
        self.environment = environment
        
        # Default configurations based on environment
        env_configs = {
            'preprod': {
                'project_path': '~/beryl3-preprod',
                'venv_path': '~/.virtualenvs/beryl3-preprod',
                'url': 'http://beryl3-preprod.mdubiel.org',
                'dev_url': 'http://dev.beryl3-preprod.mdubiel.org'
            },
            'production': {
                'project_path': '~/beryl3',
                'venv_path': '~/.virtualenvs/beryl3',
                'url': 'http://beryl3.mdubiel.org',
                'dev_url': 'http://dev.beryl3.mdubiel.org',
                'port': '62079'
            }
        }
        
        env_config = env_configs.get(environment, env_configs['preprod'])
        
        # Default Django Europe configuration
        self.host_config = host_config or {
            'host': '148.251.140.153',
            'user': 'mdubiel',
            'project_path': env_config['project_path'],
            'venv_path': env_config['venv_path'],
            'url': env_config['url'],
            'dev_url': env_config['dev_url']
        }
        
        # Git repository configuration
        self.git_config = git_config or {
            'repo_url': 'https://github.com/mdubiel/beryl3.git',
            'branch': 'main',
            'commit': 'HEAD'  # Can be specific commit hash or release tag
        }
    
    def clone_from_git(self) -> bool:
        """Clone/update project from git repository on remote host."""
        print(f"📦 Cloning beryl3 from git ({self.git_config['commit']})...")
        
        # First, backup existing .env file if it exists
        env_backup_path = f"{self.host_config['project_path']}/.env.backup"
        env_file_path = f"{self.host_config['project_path']}/.env"
        
        backup_commands = [
            f'cd {self.host_config["project_path"]}',
            f'if [ -f .env ]; then cp .env .env.backup && echo "✅ Backed up existing .env file"; else echo "ℹ️ No existing .env file to backup"; fi'
        ]
        
        backup_command = ' && '.join(backup_commands)
        backup_result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            backup_command
        ], capture_output=True, text=True)
        
        if backup_result.returncode != 0:
            print(f"⚠️ Warning: Could not backup .env file: {backup_result.stderr}")
        else:
            print(backup_result.stdout.strip())
        
        # Commands to clone or update git repository
        commands = [
            f'cd ~',
            f'rm -rf beryl3-tmp',  # Clean any existing temp clone
            f'git clone {self.git_config["repo_url"]} beryl3-tmp',
            f'cd beryl3-tmp',
            f'git checkout {self.git_config["commit"]}',  # Checkout specific commit
            f'cd ~',
            f'rm -rf {self.host_config["project_path"]}/webapp',  # Remove old webapp
            f'mkdir -p {self.host_config["project_path"]}',
            f'cp -r beryl3-tmp/webapp/* {self.host_config["project_path"]}/',  # Copy webapp contents
            f'rm -rf beryl3-tmp'  # Clean up temp clone
        ]
        
        command = ' && '.join(commands)
        
        result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            command
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error cloning project from git: {result.stderr}")
            return False
        
        print("✅ Project cloned from git successfully")
        
        # Restore .env file if backup exists
        restore_commands = [
            f'cd {self.host_config["project_path"]}',
            f'if [ -f .env.backup ]; then cp .env.backup .env && echo "✅ Restored .env file from backup"; else echo "ℹ️ No .env backup found, using fresh environment"; fi'
        ]
        
        restore_command = ' && '.join(restore_commands)
        restore_result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            restore_command
        ], capture_output=True, text=True)
        
        if restore_result.returncode != 0:
            print(f"⚠️ Warning: Could not restore .env file: {restore_result.stderr}")
        else:
            print(restore_result.stdout.strip())
        
        return True
    
    def create_production_settings(self) -> bool:
        """Create production settings file on remote host."""
        print("📝 Creating production settings file...")
        
        # Create production settings that extends webapp.settings with environment overrides
        project_path = self.host_config['project_path'].replace('~', '/home/mdubiel')
        
        production_settings_content = f"""\"\"\"Production settings for Django Europe hosting.
Extends the main webapp.settings with environment-specific overrides.
\"\"\"
import os
from pathlib import Path
import environ

# Import base settings from webapp.settings
from webapp.settings import *

# Build paths - Django Europe project directory
BASE_DIR = Path('{project_path}')

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    USE_GCS_STORAGE=(bool, True),
    CONTENT_MODERATION_ENABLED=(bool, True),
    ALLOW_USER_REGISTRATION=(bool, False),
)

# Read environment variables from .env file
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

# Override settings with environment-specific values
DEBUG = env.bool('DEBUG', default=False)
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['beryl3-preprod.mdubiel.org'])

# Database configuration (individual postgres settings)
DATABASES = {{
    'default': {{
        'ENGINE': env('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': env('PG_DB'),
        'USER': env('PG_USER'),
        'PASSWORD': env('PG_PASSWORD'),
        'HOST': env('PG_HOST', default='localhost'),
        'PORT': env('PG_PORT', default='5432'),
    }}
}}

# Email settings
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Feature flags
ALLOW_USER_REGISTRATION = env.bool('ALLOW_USER_REGISTRATION', default=False)
CONTENT_MODERATION_ENABLED = env.bool('CONTENT_MODERATION_ENABLED', default=True)
APPLICATION_ACTIVITY_LOGGING = env.bool('APPLICATION_ACTIVITY_LOGGING', default=True)

# Google Cloud Storage settings
USE_GCS_STORAGE = env.bool('USE_GCS_STORAGE', default=True)
if USE_GCS_STORAGE:
    GCS_BUCKET_NAME = env('GCS_BUCKET_NAME')
    GCS_PROJECT_ID = env('GCS_PROJECT_ID')
    GCS_CREDENTIALS_PATH = env('GCS_CREDENTIALS_PATH')
    
    # Override static and media settings for GCS using Django 4+ STORAGES
    GS_BUCKET_NAME = GCS_BUCKET_NAME
    GS_PROJECT_ID = GCS_PROJECT_ID
    GS_CREDENTIALS_FILE = GCS_CREDENTIALS_PATH
    GS_LOCATION = env('GCS_LOCATION', default='media')
    
    # Configure STORAGES for Django 4+
    STORAGES = {{
        "default": {{
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        }},
        "staticfiles": {{
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        }},
    }}
    
    STATIC_URL = f'https://storage.googleapis.com/{{GCS_BUCKET_NAME}}/static/'
    MEDIA_URL = f'https://storage.googleapis.com/{{GCS_BUCKET_NAME}}/{{GS_LOCATION}}/'

# Security settings (Django Europe handles SSL)
SECURE_SSL_REDIRECT = False

# Note: Logging configuration is now handled automatically by 
# webapp/logging_configs/preprod.py and loaded dynamically by settings.py
"""
        
        # Create temp file and upload production settings
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(production_settings_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload via SCP
            result = subprocess.run([
                'scp', temp_file_path,
                f"{self.host_config['user']}@{self.host_config['host']}:{self.host_config['project_path']}/production_settings.py"
            ], capture_output=True, text=True)
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
        
        if result.returncode != 0:
            print(f"❌ Error creating production settings: {result.stderr}")
            return False
        
        print("✅ Production settings created")
        return True
    
    def create_run_script(self) -> bool:
        """Create the RUN script for Django Europe using gunicorn."""
        print("📝 Creating RUN script with gunicorn...")
        
        # Determine port based on environment
        port = self.host_config.get('port', '62059')  # Default to preprod port
        if self.environment == 'production':
            port = '62079'
        
        run_content = f'''#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
source {self.host_config["venv_path"]}/bin/activate
cd {self.host_config["project_path"]}
export DJANGO_SETTINGS_MODULE=production_settings
gunicorn webapp.wsgi:application --bind 127.0.0.1:{port} --workers 2 --timeout 120
'''
        
        # Create temp file and upload RUN script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            temp_file.write(run_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload via SCP
            result = subprocess.run([
                'scp', temp_file_path,
                f"{self.host_config['user']}@{self.host_config['host']}:{self.host_config['project_path']}/RUN"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Make executable
                subprocess.run([
                    'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
                    f'chmod +x {self.host_config["project_path"]}/RUN'
                ], capture_output=True, text=True)
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
        
        if result.returncode != 0:
            print(f"❌ Error creating RUN script: {result.stderr}")
            return False
        
        print("✅ RUN script created with gunicorn")
        
        # Also copy the service script for service management
        service_script_local = Path(__file__).parent / 'beryl3-service.sh'
        if service_script_local.exists():
            try:
                result = subprocess.run([
                    'scp', str(service_script_local),
                    f"{self.host_config['user']}@{self.host_config['host']}:{self.host_config['project_path']}/beryl3-service.sh"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Make it executable
                    subprocess.run([
                        'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
                        f'chmod +x {self.host_config["project_path"]}/beryl3-service.sh'
                    ], capture_output=True, text=True)
                    print("✅ Service script deployed")
            except Exception:
                print("⚠️  Service script deployment failed (optional)")
        
        return True
    
    def run_migrations(self) -> bool:
        """Run Django migrations on the remote host."""
        print("🔄 Running Django migrations...")
        
        commands = [
            f'cd {self.host_config["project_path"]}',
            f'source {self.host_config["venv_path"]}/bin/activate',
            'export DJANGO_SETTINGS_MODULE=production_settings',
            'python manage.py migrate'
        ]
        
        command = ' && '.join(commands)
        
        result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            command
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error running migrations: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return False
        
        print("✅ Migrations completed successfully")
        print(f"Output: {result.stdout}")
        return True
    
    def collect_static(self) -> bool:
        """Collect static files to GCS (if enabled)."""
        print("📦 Collecting static files to GCS...")
        
        commands = [
            f'cd {self.host_config["project_path"]}',
            f'source {self.host_config["venv_path"]}/bin/activate',
            'export DJANGO_SETTINGS_MODULE=production_settings',
            'python manage.py collectstatic --noinput'
        ]
        
        command = ' && '.join(commands)
        
        result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            command
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Check if it's a GCS credentials error
            if "DefaultCredentialsError" in result.stderr or "credentials were not found" in result.stderr:
                print("⚠️  GCS credentials not found - skipping static file collection")
                print("   Static files will be served from local static directory")
                return True
            else:
                print(f"❌ Error collecting static files: {result.stderr}")
                print(f"Stdout: {result.stdout}")
                return False
        
        print("✅ Static files collected to GCS successfully")
        return True
    
    def deploy_all(self) -> bool:
        """Run the complete git-based deployment process."""
        print(f"🚀 Starting Django Europe git-based deployment to {self.environment.upper()} environment...")
        
        # Step 1: Clone/update from git
        if not self.clone_from_git():
            return False
        
        # Step 2: Create production settings
        if not self.create_production_settings():
            return False
        
        # Step 3: Create RUN script with gunicorn
        if not self.create_run_script():
            return False
        
        # Step 4: Run migrations
        if not self.run_migrations():
            return False
        
        # Step 5: Collect static files to GCS
        if not self.collect_static():
            return False
        
        print(f"🎉 Git-based deployment to {self.environment.upper()} completed successfully!")
        print(f"🌐 Your application should be available at: {self.host_config['url']}/")
        print(f"🛠️  Development URL: {self.host_config['dev_url']}/")
        
        # Check final .env file status
        check_env_commands = [
            f'cd {self.host_config["project_path"]}',
            f'if [ -f .env ]; then echo "📄 Environment file: .env exists (restored from backup or fresh)"; else echo "⚠️ Environment file: No .env file found"; fi',
            f'if [ -f .env.backup ]; then echo "💾 Backup file: .env.backup preserved for reference"; else echo "ℹ️ Backup file: No backup file created (no original .env existed)"; fi'
        ]
        
        check_env_command = ' && '.join(check_env_commands)
        env_status_result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            check_env_command
        ], capture_output=True, text=True)
        
        if env_status_result.returncode == 0:
            print("\n📋 Environment File Status:")
            for line in env_status_result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"   {line.strip()}")
        else:
            print("⚠️ Could not check environment file status")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Deploy beryl3 project to Django Europe hosting from git")
    parser.add_argument('--environment', '--env', default='preprod', choices=['preprod', 'production'], 
                       help='Target environment (default: preprod)')
    parser.add_argument('--host', default='148.251.140.153', help='Django Europe host IP')
    parser.add_argument('--user', default='mdubiel', help='SSH username')
    parser.add_argument('--project-path', help='Remote project path (overrides environment default)')
    parser.add_argument('--venv-path', help='Remote virtual environment path (overrides environment default)')
    parser.add_argument('--repo-url', default='https://github.com/mdubiel/beryl3.git', help='Git repository URL')
    parser.add_argument('--branch', default='main', help='Git branch to deploy')
    parser.add_argument('--commit', default='HEAD', help='Git commit/tag/release to deploy (e.g., v0.2.1)')
    parser.add_argument('--migrations-only', action='store_true', help='Only run migrations')
    parser.add_argument('--static-only', action='store_true', help='Only collect static files')
    parser.add_argument('--git-only', action='store_true', help='Only clone/update from git')
    
    args = parser.parse_args()
    
    # Build host config, allowing overrides
    host_config = {
        'host': args.host,
        'user': args.user,
    }
    
    # Only override paths if explicitly provided
    if args.project_path:
        host_config['project_path'] = args.project_path
    if args.venv_path:
        host_config['venv_path'] = args.venv_path
    
    git_config = {
        'repo_url': args.repo_url,
        'branch': args.branch,
        'commit': args.commit
    }
    
    deploy = DjangoEuropeProjectDeploy(
        environment=args.environment,
        host_config=host_config if any([args.project_path, args.venv_path]) else None,
        git_config=git_config
    )
    
    if args.git_only:
        success = deploy.clone_from_git()
    elif args.migrations_only:
        success = deploy.run_migrations()
    elif args.static_only:
        success = deploy.collect_static()
    else:
        success = deploy.deploy_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()