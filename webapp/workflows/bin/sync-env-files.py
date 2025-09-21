#!/usr/bin/env python3
"""
Fixed Environment File Synchronization Script

This is a simplified version that properly handles environment-specific values.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class EnvVar:
    """Simple environment variable representation."""
    name: str
    value: str
    environments: Set[str]
    env_specific_values: Dict[str, str]  # env_type -> value


class FixedEnvironmentSync:
    """Fixed synchronization logic."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.golden_file = self.project_root / "envs" / "env.gold"
        self.envs_dir = self.project_root / "envs"
    
    def parse_golden_file(self) -> Dict[str, EnvVar]:
        """Parse the golden file and extract environment-specific values."""
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
            
            # Extract the default value (first line)
            lines = rest.split('\n')
            default_value = lines[0] if lines else ""
            
            # Find the comment block before this variable
            prev_block = variable_blocks[i - 1] if i > 0 else ""
            comment_lines = prev_block.split('\n')
            
            # Extract environment-specific values and environments
            env_specific_values = {}
            environments = set()
            
            for line in comment_lines:
                # Look for environment-specific values: # 🧪 QA: beryl3-qa-bucket
                if '🏠' in line or 'DEV' in line:
                    environments.add('dev')
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            value = parts[1].strip()
                            # Clean up value
                            if '(' in value:
                                value = value.split('(')[0].strip()
                            if value and not any(word in value.lower() for word in ['generate', 'automatically', 'not used']):
                                env_specific_values['dev'] = value
                
                if '🧪' in line or 'QA' in line and 'QA:' in line:
                    environments.add('qa')
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            value = parts[1].strip()
                            # Clean up value
                            if '(' in value:
                                value = value.split('(')[0].strip()
                            if value and not any(word in value.lower() for word in ['generate', 'automatically', 'not used']):
                                env_specific_values['qa'] = value
                
                if '🚀' in line or ('PROD' in line and 'PROD:' in line):
                    environments.add('prod')
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            value = parts[1].strip()
                            # Clean up value
                            if '(' in value:
                                value = value.split('(')[0].strip()
                            if value and not any(word in value.lower() for word in ['generate', 'automatically', 'not used']):
                                env_specific_values['prod'] = value
            
            # If no environments specified, assume all
            if not environments:
                environments = {'dev', 'qa', 'prod'}
            
            variables[var_name] = EnvVar(
                name=var_name,
                value=default_value,
                environments=environments,
                env_specific_values=env_specific_values
            )
        
        return variables
    
    def generate_environment_file(self, env_type: str, variables: Dict[str, EnvVar]) -> str:
        """Generate environment file content for specific environment."""
        env_mapping = {'local': 'dev', 'qa': 'qa', 'prod': 'prod'}
        target_env = env_mapping.get(env_type, env_type)
        
        lines = [
            "# ==============================================================================",
            f"# BERYL3 {env_type.upper()} ENVIRONMENT CONFIGURATION",
            "# ==============================================================================",
            f"# Generated from env.gold on {datetime.now().isoformat()}",
            "# ⚠️  DO NOT EDIT MANUALLY - Use sync-env-files.py to update",
            "# ==============================================================================",
            "",
        ]
        
        for var_name, var_obj in variables.items():
            if target_env not in var_obj.environments:
                continue
            
            # Get environment-specific value or default
            value = var_obj.env_specific_values.get(target_env, var_obj.value)
            
            lines.append(f"{var_name}={value}")
        
        return "\n".join(lines) + "\n"
    
    def sync_environment(self, env_type: str):
        """Sync a specific environment."""
        print(f"Syncing {env_type} environment...")
        
        # Parse golden file
        variables = self.parse_golden_file()
        
        # Generate environment file
        content = self.generate_environment_file(env_type, variables)
        
        # Write to appropriate file
        if env_type == 'local':
            output_file = self.envs_dir / "generated" / ".env"
            app_env_file = self.project_root.parent / ".env"
        else:
            output_file = self.envs_dir / "generated" / f"{env_type}.env"
            app_env_file = None
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Generated {output_file}")
        
        # For local environment, create/update symlink to app root
        if env_type == 'local' and app_env_file:
            self._create_symlink(output_file, app_env_file)
        
        return True
    
    def _create_symlink(self, source_file, target_file):
        """Create or update symlink from generated file to app location."""
        import os
        
        # Remove existing file/symlink if it exists
        if target_file.exists() or target_file.is_symlink():
            target_file.unlink()
        
        # Create relative path for the symlink
        relative_source = os.path.relpath(source_file, target_file.parent)
        
        # Create symlink
        target_file.symlink_to(relative_source)
        print(f"🔗 Created symlink: {target_file} -> {relative_source}")


def main():
    parser = argparse.ArgumentParser(description="Fixed environment synchronization")
    parser.add_argument('environments', nargs='*', default=['qa', 'prod'], 
                       help='Environments to sync')
    
    args = parser.parse_args()
    
    syncer = FixedEnvironmentSync()
    
    for env in args.environments:
        try:
            syncer.sync_environment(env)
        except Exception as e:
            print(f"❌ Error syncing {env}: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())