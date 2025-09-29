#!/usr/bin/env python3
"""
Django Europe - Sync Dependencies Script

This script synchronizes Python dependencies from local pyproject.toml to the
Django Europe hosting environment using UV package manager.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import tempfile
import os


class DjangoEuropeDependencySync:
    """Manages dependency synchronization for Django Europe hosting."""
    
    def __init__(self, host_config=None):
        self.workflows_root = Path(__file__).parent.parent
        self.project_root = self.workflows_root.parent  # Go up one more level to webapp root
        self.pyproject_path = self.project_root / "pyproject.toml"
        
        # Default Django Europe configuration
        self.host_config = host_config or {
            'host': '148.251.140.153',
            'user': 'mdubiel', 
            'project_path': '~/beryl3-preprod',
            'venv_path': '~/.virtualenvs/beryl3-preprod',
            'python_version': '3.11'
        }
    
    def generate_requirements_txt(self) -> str:
        """Generate requirements.txt from pyproject.toml using UV."""
        print("📦 Generating requirements.txt from pyproject.toml...")
        
        # Create temporary directory for UV operations
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy pyproject.toml to temp directory
            temp_pyproject = temp_path / "pyproject.toml"
            temp_pyproject.write_text(self.pyproject_path.read_text())
            
            # Use UV to generate requirements
            try:
                result = subprocess.run([
                    'uv', 'pip', 'compile', 
                    str(temp_pyproject), 
                    '--output-file', str(temp_path / 'requirements.txt'),
                    '--python-version', self.host_config['python_version']
                ], capture_output=True, text=True, cwd=temp_dir)
                
                if result.returncode != 0:
                    print(f"❌ Error generating requirements: {result.stderr}")
                    return None
                
                requirements_content = (temp_path / 'requirements.txt').read_text()
                print("✅ Requirements.txt generated successfully")
                return requirements_content
                
            except FileNotFoundError:
                print("❌ UV not found. Please install UV first: curl -LsSf https://astral.sh/uv/install.sh | sh")
                return None
    
    def upload_requirements(self, requirements_content: str) -> bool:
        """Upload requirements.txt to Django Europe host."""
        print("📤 Uploading requirements.txt to Django Europe host...")
        
        # Create temporary file with requirements
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(requirements_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload via SCP
            result = subprocess.run([
                'scp', temp_file_path,
                f"{self.host_config['user']}@{self.host_config['host']}:{self.host_config['project_path']}/requirements.txt"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error uploading requirements.txt: {result.stderr}")
                return False
            
            print("✅ Requirements.txt uploaded successfully")
            return True
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def install_dependencies_remote(self) -> bool:
        """Install dependencies on the remote host using UV."""
        print("🔧 Installing dependencies on Django Europe host...")
        
        # Commands to run on remote host
        commands = [
            # Ensure UV is in PATH
            'export PATH=$HOME/.local/bin:$PATH',
            # Navigate to project directory
            f'cd {self.host_config["project_path"]}',
            # Install dependencies using UV
            f'$HOME/.local/bin/uv pip sync requirements.txt --python {self.host_config["venv_path"]}/bin/python'
        ]
        
        command = ' && '.join(commands)
        
        result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            command
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error installing dependencies: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return False
        
        print("✅ Dependencies installed successfully")
        print(f"Output: {result.stdout}")
        return True
    
    def verify_installation(self) -> bool:
        """Verify that key dependencies are installed correctly."""
        print("🔍 Verifying dependency installation...")
        
        # Key packages to verify
        key_packages = [
            'django',
            'django-allauth', 
            'django-htmx',
            'psycopg2-binary',
            'gunicorn'
        ]
        
        commands = [
            'export PATH=$HOME/.local/bin:$PATH',
            f'source {self.host_config["venv_path"]}/bin/activate',
            'pip list | grep -E "(' + '|'.join(key_packages) + ')"'
        ]
        
        command = ' && '.join(commands)
        
        result = subprocess.run([
            'ssh', f"{self.host_config['user']}@{self.host_config['host']}", 
            command
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error verifying installation: {result.stderr}")
            return False
        
        print("✅ Key dependencies verified:")
        print(result.stdout)
        return True
    
    def sync_all(self) -> bool:
        """Run the complete dependency sync process."""
        print("🚀 Starting Django Europe dependency synchronization...")
        
        # Step 1: Generate requirements.txt
        requirements = self.generate_requirements_txt()
        if not requirements:
            return False
        
        # Step 2: Upload to host
        if not self.upload_requirements(requirements):
            return False
        
        # Step 3: Install dependencies
        if not self.install_dependencies_remote():
            return False
        
        # Step 4: Verify installation
        if not self.verify_installation():
            return False
        
        print("🎉 Dependency synchronization completed successfully!")
        return True


def main():
    parser = argparse.ArgumentParser(description="Sync dependencies to Django Europe hosting")
    parser.add_argument('--host', default='148.251.140.153', help='Django Europe host IP')
    parser.add_argument('--user', default='mdubiel', help='SSH username')
    parser.add_argument('--project-path', default='~/beryl3-preprod', help='Remote project path')
    parser.add_argument('--venv-path', default='~/.virtualenvs/beryl3-preprod', help='Remote virtual environment path')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing installation')
    
    args = parser.parse_args()
    
    host_config = {
        'host': args.host,
        'user': args.user,
        'project_path': args.project_path,
        'venv_path': args.venv_path,
        'python_version': '3.11'
    }
    
    sync = DjangoEuropeDependencySync(host_config)
    
    if args.verify_only:
        success = sync.verify_installation()
    else:
        success = sync.sync_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()