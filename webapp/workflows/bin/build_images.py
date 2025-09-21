#!/usr/bin/env python3
"""
Build Docker images with version bumping using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class ImageBuilder:
    """Builds Docker images with automatic version bumping."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.docker_config = secrets_manager.get_docker_config()
        self.project_root = Path(__file__).parent.parent.parent
        self.version_file = self.project_root / "VERSION"
        
    def read_version(self) -> Tuple[int, int, int]:
        """Read current version from VERSION file."""
        if not self.version_file.exists():
            logging.info("VERSION file not found. Creating initial version file...")
            self.write_version(0, 1, 0)
            return 0, 1, 0
        
        version_data = {}
        with open(self.version_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    version_data[key] = int(value)
        
        return version_data.get('MAJOR', 0), version_data.get('MINOR', 1), version_data.get('BUILD', 0)
    
    def write_version(self, major: int, minor: int, build: int):
        """Write version to VERSION file."""
        with open(self.version_file, 'w') as f:
            f.write(f"MAJOR={major}\n")
            f.write(f"MINOR={minor}\n")
            f.write(f"BUILD={build}\n")
    
    def run_docker_command(self, command: list) -> bool:
        """Run a docker command and return success status."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root
            )
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Docker command failed: %s", e.stderr.strip())
            return False
    
    def build_unified_image(self, image_name: str, version_tag: str) -> bool:
        """Build unified Docker image for both webapp and jobs."""
        registry = self.docker_config['registry']
        
        logging.info("Building unified application image...")
        
        # Build unified image (no target needed)
        build_cmd = [
            "docker", "build",
            "-t", f"{image_name}:{version_tag}",
            "-t", f"{image_name}:latest",
            "."
        ]
        
        if not self.run_docker_command(build_cmd):
            return False
        
        # Tag for registry
        tag_commands = [
            ["docker", "tag", f"{image_name}:{version_tag}", f"{registry}/{image_name}:{version_tag}"],
            ["docker", "tag", f"{image_name}:latest", f"{registry}/{image_name}:latest"]
        ]
        
        for tag_cmd in tag_commands:
            if not self.run_docker_command(tag_cmd):
                return False
        
        return True
    
    def build_all_images(self) -> bool:
        """Build all Docker images with version bump."""
        logging.info("Building Docker images with version bump...")
        logging.info("Project root: %s", self.project_root)
        
        # Read and increment version
        major, minor, build = self.read_version()
        build += 1
        self.write_version(major, minor, build)
        
        version_tag = f"{major}.{minor}-build{build}"
        logging.info("New version: %s", version_tag)
        
        # Get image name from config - using single unified image
        app_image = self.docker_config['images']['webapp']  # Use webapp name for unified image
        registry = self.docker_config['registry']
        
        # Build unified application image
        if not self.build_unified_image(app_image, version_tag):
            logging.error("Failed to build application image")
            return False
        
        logging.info("Build completed successfully!")
        logging.info("Version: %s", version_tag)
        logging.info("")
        logging.info("Local images tagged:")
        logging.info("  %s:%s", app_image, version_tag)
        logging.info("  %s:latest", app_image)
        logging.info("")
        logging.info("Registry images tagged:")
        logging.info("  %s/%s:%s", registry, app_image, version_tag)
        logging.info("  %s/%s:latest", registry, app_image)
        logging.info("")
        logging.info("To push images to registry, run: ./workflows/bin/push_images.py")
        
        return True


def main():
    """Main function to build images."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and image builder
        manager = SecretsManager()
        builder = ImageBuilder(manager)
        
        success = builder.build_all_images()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to build images: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()