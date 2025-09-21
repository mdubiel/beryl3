#!/usr/bin/env python3
"""
Push Docker images to Google Artifact Registry using YAML configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from secrets_manager import SecretsManager


class ImagePusher:
    """Pushes Docker images to Google Artifact Registry."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
        self.docker_config = secrets_manager.get_docker_config()
        self.project_config = secrets_manager.get_project_config()
        self.project_root = Path(__file__).parent.parent.parent
        self.version_file = self.project_root / "VERSION"
        
    def read_version(self) -> Tuple[int, int, int]:
        """Read current version from VERSION file."""
        if not self.version_file.exists():
            raise FileNotFoundError("VERSION file not found. Run ./workflows/bin/build_images.py first.")
        
        version_data = {}
        with open(self.version_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    version_data[key] = int(value)
        
        return version_data.get('MAJOR', 0), version_data.get('MINOR', 1), version_data.get('BUILD', 0)
    
    def run_command(self, command: list) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
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
    
    def image_exists_locally(self, image_name: str) -> bool:
        """Check if a Docker image exists locally."""
        success, _ = self.run_command(["docker", "image", "inspect", image_name])
        return success
    
    def configure_docker_auth(self) -> bool:
        """Configure Docker authentication for Google Artifact Registry."""
        logging.info("Configuring Docker authentication for GAR...")
        
        # Use the registry domain from config
        registry_domain = self.docker_config['registry'].split('/')[0]  # Extract domain part
        
        command = [
            "/home/mdubiel/google-cloud-sdk/bin/gcloud", "auth", "configure-docker",
            registry_domain, "--quiet"
        ]
        
        success, output = self.run_command(command)
        if not success:
            logging.error("Failed to configure Docker authentication: %s", output)
        return success
    
    def push_image(self, image_name: str, tag: str) -> bool:
        """Push a single image to the registry."""
        registry = self.docker_config['registry']
        full_image_name = f"{registry}/{image_name}:{tag}"
        
        logging.info("Pushing %s...", full_image_name)
        
        success, output = self.run_command(["docker", "push", full_image_name])
        if not success:
            logging.error("Failed to push %s: %s", full_image_name, output)
        return success
    
    def push_all_images(self) -> bool:
        """Push all Docker images to Google Artifact Registry."""
        logging.info("Pushing Docker images to Google Artifact Registry...")
        logging.info("Project root: %s", self.project_root)
        
        # Read version
        major, minor, build = self.read_version()
        version_tag = f"{major}.{minor}-build{build}"
        
        logging.info("Pushing version: %s", version_tag)
        
        # Get image name from config - using unified image
        app_image = self.docker_config['images']['webapp']  # Use webapp name for unified image
        registry = self.docker_config['registry']
        
        # Check if image exists locally
        if not self.image_exists_locally(f"{app_image}:{version_tag}"):
            logging.error("Local image %s:%s not found. Run ./workflows/bin/build_images.py first.", app_image, version_tag)
            return False
        
        # Configure Docker authentication
        if not self.configure_docker_auth():
            return False
        
        # Push application images
        logging.info("Pushing application images...")
        if not self.push_image(app_image, version_tag):
            return False
        if not self.push_image(app_image, "latest"):
            return False
        
        logging.info("Push completed successfully!")
        logging.info("")
        logging.info("Pushed images:")
        logging.info("  %s/%s:%s", registry, app_image, version_tag)
        logging.info("  %s/%s:latest", registry, app_image)
        logging.info("")
        logging.info("Images are now available in Google Artifact Registry")
        logging.info("To deploy with new images, run:")
        logging.info("  ./workflows/bin/deploy_webapp.py    # Deploy webapp")
        logging.info("  ./workflows/bin/deploy_jobs.py      # Deploy jobs")
        
        return True


def main():
    """Main function to push images."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        # Create secrets manager and image pusher
        manager = SecretsManager()
        pusher = ImagePusher(manager)
        
        success = pusher.push_all_images()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.error("Failed to push images: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()