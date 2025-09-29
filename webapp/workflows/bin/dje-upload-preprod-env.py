#!/usr/bin/env python3
"""
Upload custom preprod.env file to Django Europe hosting
"""

import subprocess
import sys
from pathlib import Path


def upload_preprod_env():
    """Upload the manually configured preprod.env file."""
    preprod_env_path = Path(__file__).parent.parent / "envs" / "generated" / "preprod.env"
    
    if not preprod_env_path.exists():
        print(f"❌ Preprod env file not found: {preprod_env_path}")
        return False
    
    print("📤 Uploading custom preprod.env to Django Europe...")
    
    # Upload the preprod.env file (to project root as .env)
    result = subprocess.run([
        'scp', str(preprod_env_path),
        'mdubiel@148.251.140.153:~/beryl3-preprod/.env'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error uploading preprod.env: {result.stderr}")
        return False
    
    print("✅ Custom preprod.env uploaded successfully")
    return True


if __name__ == "__main__":
    success = upload_preprod_env()
    sys.exit(0 if success else 1)