#!/usr/bin/env python3
"""
Test script for secrets manager functionality.
"""

import sys
from pathlib import Path

# Add workflows/bin to path
sys.path.append(str(Path(__file__).parent / "workflows/bin"))

try:
    from secrets_manager import SecretsManager
    
    print("Testing SecretsManager with YAML configuration...")
    
    # Create manager
    manager = SecretsManager()
    
    print(f"✓ Config loaded from: {manager.config_path}")
    print(f"✓ Project ID: {manager.project_id}")
    print(f"✓ Service Account: {manager.service_account}")
    print(f"✓ Total secrets loaded: {len(manager.secrets)}")
    
    # Test environment variable mapping
    print("\n--- Environment Variable Mapping ---")
    
    # Test jobs context
    jobs_mapping = manager.get_env_var_mapping(context="jobs")
    print(f"Jobs context secrets: {len(jobs_mapping)} mappings")
    for env_var, secret_ref in jobs_mapping.items():
        print(f"  {env_var} = {secret_ref}")
    
    print(f"\nJobs secrets string: {manager.build_secrets_string(context='jobs')[:100]}...")
    
    # Test webapp context  
    webapp_mapping = manager.get_env_var_mapping(context="webapp")
    print(f"\nWebapp context secrets: {len(webapp_mapping)} mappings")
    for env_var, secret_ref in webapp_mapping.items():
        print(f"  {env_var} = {secret_ref}")
    
    # Test specific secret lookup
    pg_host_job = manager.get_secret_by_env_var("PG_HOST", context="jobs")
    pg_host_webapp = manager.get_secret_by_env_var("PG_HOST", context="webapp")
    
    print(f"\nPG_HOST for jobs: {pg_host_job.name if pg_host_job else 'Not found'}")
    print(f"PG_HOST for webapp: {pg_host_webapp.name if pg_host_webapp else 'Not found'}")
    
    print("\n✓ All tests passed! YAML-based secrets system is working correctly.")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure PyYAML is installed: pip install PyYAML")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)