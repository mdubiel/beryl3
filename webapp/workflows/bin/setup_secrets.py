#!/usr/bin/env python3
"""
Setup QA environment secrets using YAML configuration.
"""

import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


def main():
    """Main function to setup QA secrets from YAML configuration."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and setup secrets
        manager = SecretsManager()
        success = manager.setup_all_cloud_secrets()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to setup secrets: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()