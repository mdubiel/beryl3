#!/usr/bin/env python3
"""
Django Europe - Environment Synchronization Script

This script synchronizes environment variables from env.gold to Django Europe
hosting environment, creating the appropriate .env file for beryl3-preprod.
"""

import argparse
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, Set
from datetime import datetime
import re


class DjangoEuropeEnvSync:
    """Manages environment variable synchronization for Django Europe hosting."""
    
    def __init__(self, host_config=None):
        self.project_root = Path(__file__).parent.parent
        self.golden_file = self.project_root / "envs" / "env.gold"
        
        # Default Django Europe configuration
        self.host_config = host_config or {
            'host': '148.251.140.153',
            'user': 'mdubiel',
            'project_path': '~/beryl3-preprod',
            'env_file_path': '~/beryl3-preprod/config/settings/.env'
        }
    
    def parse_golden_file(self) -> Dict[str, str]:
        """Parse the golden file and extract environment variables for beryl3-preprod."""
        print("📖 Parsing env.gold file...")
        
        if not self.golden_file.exists():
            print(f"❌ Golden file not found: {self.golden_file}")
            return {}
        
        variables = {}
        
        with open(self.golden_file, 'r') as f:
            content = f.read()
        
        # Split by variable assignments
        variable_blocks = re.split(r'\n([A-Z_][A-Z0-9_]*=)', content)
        
        for i in range(1, len(variable_blocks), 2):
            if i + 1 >= len(variable_blocks):
                break
                
            var_name = variable_blocks[i][:-1]  # Remove =
            rest = variable_blocks[i + 1]
            
            # Extract the default value (first line after variable name)
            lines = rest.split('\n')
            value = lines[0] if lines else ""
            
            # Look for environment-specific values in comments
            env_specific_value = None
            for line in lines:
                # Look for 🧪 QA or preprod specific values
                if '🧪' in line and 'preprod' in line.lower():
                    # Extract value after colon
                    if ':' in line:
                        env_specific_value = line.split(':', 1)[1].strip()
                        break
                elif '🧪' in line and 'QA' in line:
                    # Use QA values for preprod if no specific preprod value
                    if ':' in line and not env_specific_value:
                        env_specific_value = line.split(':', 1)[1].strip()
            
            # Use environment-specific value if available, otherwise use default
            final_value = env_specific_value if env_specific_value else value
            variables[var_name] = final_value
        
        print(f"✅ Parsed {len(variables)} variables from golden file")
        return variables
    
    def generate_django_europe_env(self, variables: Dict[str, str]) -> str:
        """Generate .env file content for Django Europe hosting."""
        print("🔧 Generating Django Europe .env file...")
        
        # Django Europe specific mappings and overrides
        django_europe_vars = {}
        
        # Core Django settings
        django_europe_vars['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
        django_europe_vars['DJANGO_SECRET_KEY'] = variables.get('SECRET_KEY', 'CHANGE-THIS-SECRET-KEY')
        django_europe_vars['DJANGO_ALLOWED_HOSTS'] = '.beryl3-preprod.mdubiel.org,.dev.beryl3-preprod.mdubiel.org'
        
        # Database - use existing beryl3-preprod database
        django_europe_vars['DATABASE_URL'] = 'postgres://mdubiel:rgCP9p0SFGHpwUmK@localhost/mdubiel_beryl3-preprod'
        
        # Email settings
        django_europe_vars['DEFAULT_FROM_EMAIL'] = variables.get('DEFAULT_FROM_EMAIL', 'mdubiel@gmail.com')
        django_europe_vars['DJANGO_SERVER_EMAIL'] = variables.get('DEFAULT_FROM_EMAIL', 'mdubiel@gmail.com')
        
        # Security settings for Django Europe
        django_europe_vars['DJANGO_SECURE_SSL_REDIRECT'] = 'False'  # Handled by nginx
        
        # Debug settings
        django_europe_vars['DEBUG'] = variables.get('DEBUG', 'False')
        
        # Beryl3-specific feature flags and settings
        beryl3_specific = [
            'ALLOW_USER_REGISTRATION',
            'CONTENT_MODERATION_ENABLED',
            'CONTENT_MODERATION_ACTION',
            'CONTENT_MODERATION_SOFT_BAN_THRESHOLD',
            'MARKETING_EMAIL_DEFAULT_OPT_IN',
            'APPLICATION_ACTIVITY_LOGGING',
            'LOKI_ENABLED',
            'USE_GOOGLE_CLOUD_LOGGING',
            'USE_GCS_STORAGE',
            'USE_INBUCKET'
        ]
        
        for var in beryl3_specific:
            if var in variables:
                django_europe_vars[var] = variables[var]
        
        # Email provider settings (if using external services)
        email_vars = [
            'RESEND_API_KEY',
            'RESEND_MARKETING_AUDIENCE_ID',
            'RESEND_SYNC_TIMEOUT_MINUTES'
        ]
        
        for var in email_vars:
            if var in variables and variables[var]:
                django_europe_vars[var] = variables[var]
        
        # Generate the .env file content
        env_content = f"""# Django Europe Environment Configuration for Beryl3 PRE-PROD
# Generated from env.gold on {datetime.now().isoformat()}
# ⚠️  DO NOT EDIT MANUALLY - Use dje-sync-env.py to update

# ==============================================================================
# CORE DJANGO SETTINGS
# ==============================================================================
"""
        
        for key, value in django_europe_vars.items():
            env_content += f'{key}="{value}"\n'
        
        env_content += "\n# ==============================================================================\n"
        env_content += "# END OF CONFIGURATION\n"
        env_content += "# ==============================================================================\n"
        
        print("✅ Django Europe .env file generated")
        return env_content
    
    def upload_env_file(self, env_content: str) -> bool:
        """Upload .env file to Django Europe host."""
        print("📤 Uploading .env file to Django Europe host...")
        
        # Create temporary file with env content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_file:
            temp_file.write(env_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload via SCP
            result = subprocess.run([
                'scp', temp_file_path,
                f"{self.host_config['user']}@{self.host_config['host']}:{self.host_config['env_file_path']}"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error uploading .env file: {result.stderr}")
                return False
            
            print("✅ .env file uploaded successfully")
            return True
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def verify_env_file(self) -> bool:
        """Verify that the .env file was uploaded correctly."""
        print("🔍 Verifying .env file on remote host...")
        
        result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            f'ls -la {self.host_config["env_file_path"]} && head -5 {self.host_config["env_file_path"]}'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error verifying .env file: {result.stderr}")
            return False
        
        print("✅ .env file verified:")
        print(result.stdout)
        return True
    
    def sync_all(self) -> bool:
        """Run the complete environment synchronization process."""
        print("🚀 Starting Django Europe environment synchronization...")
        
        # Step 1: Parse golden file
        variables = self.parse_golden_file()
        if not variables:
            print("❌ No variables found in golden file")
            return False
        
        # Step 2: Generate Django Europe .env content
        env_content = self.generate_django_europe_env(variables)
        if not env_content:
            return False
        
        # Step 3: Upload to host
        if not self.upload_env_file(env_content):
            return False
        
        # Step 4: Verify upload
        if not self.verify_env_file():
            return False
        
        print("🎉 Environment synchronization completed successfully!")
        return True


def main():
    parser = argparse.ArgumentParser(description="Sync environment variables to Django Europe hosting")
    parser.add_argument('--host', default='148.251.140.153', help='Django Europe host IP')
    parser.add_argument('--user', default='mdubiel', help='SSH username')
    parser.add_argument('--project-path', default='~/beryl3-preprod', help='Remote project path')
    parser.add_argument('--env-file-path', default='~/beryl3-preprod/config/settings/.env', help='Remote .env file path')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing .env file')
    
    args = parser.parse_args()
    
    host_config = {
        'host': args.host,
        'user': args.user,
        'project_path': args.project_path,
        'env_file_path': args.env_file_path
    }
    
    sync = DjangoEuropeEnvSync(host_config)
    
    if args.verify_only:
        success = sync.verify_env_file()
    else:
        success = sync.sync_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()