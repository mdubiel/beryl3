#!/usr/bin/env python3
"""
Django Europe - Master Deployment Script

This script orchestrates the complete deployment of beryl3 to Django Europe hosting.
It runs all deployment steps in the correct order.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


class DjangoEuropeMasterDeploy:
    """Orchestrates the complete Django Europe deployment process."""
    
    def __init__(self, host_config=None):
        self.scripts_dir = Path(__file__).parent
        
        # Default Django Europe configuration
        self.host_config = host_config or {
            'host': '148.251.140.153',
            'user': 'mdubiel',
            'project_path': '~/beryl3-preprod',
            'venv_path': '~/.virtualenvs/beryl3-preprod'
        }
    
    def run_script(self, script_name: str, args: List[str] = None) -> Tuple[bool, str]:
        """Run a deployment script and return success status and output."""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            return False, f"Script not found: {script_path}"
        
        command = [str(script_path)]
        if args:
            command.extend(args)
        
        print(f"🔧 Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"Error: {result.stderr}\\nStdout: {result.stdout}"
                
        except subprocess.TimeoutExpired:
            return False, "Script timed out after 10 minutes"
        except Exception as e:
            return False, f"Exception running script: {str(e)}"
    
    def deploy_full(self, skip_dependencies: bool = False, skip_env: bool = False, git_commit: str = 'HEAD') -> bool:
        """Run the complete deployment process."""
        print("🚀 Starting complete Django Europe git-based deployment for beryl3...")
        print("=" * 70)
        
        deployment_steps = []
        
        # Step 1: Upload preprod environment (unless skipped)
        if not skip_env:
            deployment_steps.append({
                'name': 'Upload Preprod Environment',
                'script': 'dje-upload-preprod-env.py',
                'args': []
            })
        
        # Step 2: Sync dependencies (unless skipped)
        if not skip_dependencies:
            deployment_steps.append({
                'name': 'Dependencies Synchronization',
                'script': 'dje-sync-dependencies.py',
                'args': [
                    '--host', self.host_config['host'],
                    '--user', self.host_config['user'],
                    '--project-path', self.host_config['project_path'],
                    '--venv-path', self.host_config['venv_path']
                ]
            })
        
        # Step 3: Deploy project from git
        deployment_steps.append({
            'name': 'Git-Based Project Deployment',
            'script': 'dje-deploy-project.py',
            'args': [
                '--host', self.host_config['host'],
                '--user', self.host_config['user'],
                '--project-path', self.host_config['project_path'],
                '--venv-path', self.host_config['venv_path'],
                '--commit', git_commit
            ]
        })
        
        # Execute all deployment steps
        for i, step in enumerate(deployment_steps, 1):
            print(f"\\n📋 Step {i}/{len(deployment_steps)}: {step['name']}")
            print("-" * 50)
            
            success, output = self.run_script(step['script'], step['args'])
            
            if success:
                print(f"✅ {step['name']} completed successfully")
                if output.strip():
                    print(f"Output: {output}")
            else:
                print(f"❌ {step['name']} failed!")
                print(f"Error details: {output}")
                return False
        
        print("\\n" + "=" * 70)
        print("🎉 Complete Django Europe deployment finished successfully!")
        print("\\n📋 Deployment Summary:")
        print(f"  🌐 Production URL: http://beryl3-preprod.mdubiel.org/")
        print(f"  🛠️  Development URL: http://dev.beryl3-preprod.mdubiel.org/")
        print(f"  📁 Project Path: {self.host_config['project_path']}")
        print(f"  🐍 Virtual Environment: {self.host_config['venv_path']}")
        print(f"  🖥️  Server: {self.host_config['user']}@{self.host_config['host']}")
        
        print("\\n🔧 Next Steps:")
        print("  1. Test the application at the URLs above")
        print("  2. Create a superuser account if needed:")
        print(f"     ssh {self.host_config['user']}@{self.host_config['host']}")
        print(f"     cd {self.host_config['project_path']}")
        print(f"     source {self.host_config['venv_path']}/bin/activate")
        print("     export DJANGO_SETTINGS_MODULE=production_settings")
        print("     python manage.py createsuperuser")
        print("  3. Configure any additional settings as needed")
        
        return True
    
    def deploy_quick_update(self, git_commit: str = 'HEAD') -> bool:
        """Run a quick update deployment (only git pull, no dependencies or env)."""
        print("⚡ Starting quick git update deployment...")
        
        success, output = self.run_script('dje-deploy-project.py', [
            '--host', self.host_config['host'],
            '--user', self.host_config['user'],
            '--project-path', self.host_config['project_path'],
            '--venv-path', self.host_config['venv_path'],
            '--commit', git_commit
        ])
        
        if success:
            print("✅ Quick git update completed successfully!")
            print(f"🌐 Application available at: http://beryl3-preprod.mdubiel.org/")
            return True
        else:
            print(f"❌ Quick git update failed: {output}")
            return False
    
    def verify_deployment(self) -> bool:
        """Verify that the deployment is working correctly."""
        print("🔍 Verifying Django Europe deployment...")
        
        verification_steps = [
            {
                'name': 'Environment Variables',
                'script': 'dje-sync-env.py',
                'args': ['--verify-only', '--host', self.host_config['host'], '--user', self.host_config['user']]
            },
            {
                'name': 'Dependencies',
                'script': 'dje-sync-dependencies.py', 
                'args': ['--verify-only', '--host', self.host_config['host'], '--user', self.host_config['user']]
            }
        ]
        
        all_success = True
        
        for step in verification_steps:
            print(f"\\n🔍 Verifying {step['name']}...")
            success, output = self.run_script(step['script'], step['args'])
            
            if success:
                print(f"✅ {step['name']} verification passed")
            else:
                print(f"❌ {step['name']} verification failed: {output}")
                all_success = False
        
        if all_success:
            print("\\n🎉 All verification checks passed!")
        else:
            print("\\n⚠️  Some verification checks failed. Please review the output above.")
        
        return all_success


def main():
    parser = argparse.ArgumentParser(description="Master deployment script for Django Europe hosting with git")
    parser.add_argument('--host', default='148.251.140.153', help='Django Europe host IP')
    parser.add_argument('--user', default='mdubiel', help='SSH username')
    parser.add_argument('--project-path', default='~/beryl3-preprod', help='Remote project path')
    parser.add_argument('--venv-path', default='~/.virtualenvs/beryl3-preprod', help='Remote virtual environment path')
    parser.add_argument('--commit', default='HEAD', help='Git commit/tag to deploy')
    
    # Deployment modes
    parser.add_argument('--quick-update', action='store_true', help='Quick git update (project files only)')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing deployment')
    parser.add_argument('--skip-dependencies', action='store_true', help='Skip dependency installation')
    parser.add_argument('--skip-env', action='store_true', help='Skip environment variable sync')
    
    args = parser.parse_args()
    
    host_config = {
        'host': args.host,
        'user': args.user,
        'project_path': args.project_path,
        'venv_path': args.venv_path
    }
    
    deploy = DjangoEuropeMasterDeploy(host_config)
    
    if args.verify_only:
        success = deploy.verify_deployment()
    elif args.quick_update:
        success = deploy.deploy_quick_update(git_commit=args.commit)
    else:
        success = deploy.deploy_full(
            skip_dependencies=args.skip_dependencies,
            skip_env=args.skip_env,
            git_commit=args.commit
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()