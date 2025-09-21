#!/usr/bin/env python3
"""
Intelligent QA secrets setup script.
Compares existing secret values and only creates new versions when content differs.
"""

import logging
import subprocess
import sys
from typing import Optional


class SecretManager:
    """Manages Google Cloud Secret Manager secrets with intelligent versioning."""

    def __init__(self, project_id: str, service_account: str):
        self.project_id = project_id
        self.service_account = service_account
        self.secrets_created = 0
        self.secrets_updated = 0
        self.secrets_unchanged = 0

    def run_gcloud_command(self, command: list) -> tuple[bool, str]:
        """Run a gcloud command and return success status and output."""
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

    def secret_exists(self, secret_name: str) -> bool:
        """Check if a secret exists."""
        command = [
            "gcloud", "secrets", "describe", secret_name,
            "--project", self.project_id
        ]
        success, _ = self.run_gcloud_command(command)
        return success

    def get_secret_value(self, secret_name: str) -> Optional[str]:
        """Get the current value of a secret."""
        if not self.secret_exists(secret_name):
            return None

        command = [
            "gcloud", "secrets", "versions", "access", "latest",
            "--secret", secret_name,
            "--project", self.project_id
        ]
        success, output = self.run_gcloud_command(command)
        return output if success else None

    def create_secret(self, secret_name: str, value: str) -> bool:
        """Create a new secret."""
        command = [
            "gcloud", "secrets", "create", secret_name,
            "--data-file", "-",
            "--project", self.project_id
        ]

        try:
            subprocess.run(
                command,
                input=value,
                text=True,
                capture_output=True,
                check=True
            )
            logging.info("  Created secret: %s", secret_name)
            self.secrets_created += 1
            return True
        except subprocess.CalledProcessError as e:
            logging.error("  ERROR creating secret %s: %s", secret_name, e.stderr.strip())
            return False

    def add_secret_version(self, secret_name: str, value: str) -> bool:
        """Add a new version to an existing secret."""
        command = [
            "gcloud", "secrets", "versions", "add", secret_name,
            "--data-file", "-",
            "--project", self.project_id
        ]

        try:
            subprocess.run(
                command,
                input=value,
                text=True,
                capture_output=True,
                check=True
            )
            logging.info("  Updated secret: %s (new version)", secret_name)
            self.secrets_updated += 1
            return True
        except subprocess.CalledProcessError as e:
            logging.error("  ERROR updating secret %s: %s", secret_name, e.stderr.strip())
            return False

    def ensure_secret(self, secret_name: str, value: str) -> bool:
        """Ensure secret exists with the correct value."""
        current_value = self.get_secret_value(secret_name)

        if current_value is None:
            # Secret doesn't exist, create it
            return self.create_secret(secret_name, value)
        if current_value != value:
            # Secret exists but value is different, add new version
            return self.add_secret_version(secret_name, value)
        # Secret exists with same value, no action needed
        logging.info("  Secret unchanged: %s", secret_name)
        self.secrets_unchanged += 1
        return True

    def grant_iam_permission(self, secret_name: str) -> bool:
        """Grant IAM permission to service account."""
        command = [
            "gcloud", "secrets", "add-iam-policy-binding", secret_name,
            "--member", f"serviceAccount:{self.service_account}",
            "--role", "roles/secretmanager.secretAccessor",
            "--project", self.project_id
        ]

        success, _ = self.run_gcloud_command(command)
        if not success:
            logging.warning("  WARNING: Failed to grant IAM permission for %s", secret_name)
        return success

    def _load_secrets_from_env_file(self) -> dict:
        """Load QA environment variables from generated qa.env file."""
        import os
        from pathlib import Path
        
        # Path to generated QA environment file
        script_dir = Path(__file__).parent
        env_file = script_dir.parent / "envs" / "generated" / "qa.env"
        
        if not env_file.exists():
            raise FileNotFoundError(f"QA environment file not found: {env_file}")
        
        secrets = {}
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert environment variable name to secret name
                        secret_name = f"beryl3-qa-{key.lower().replace('_', '-')}"
                        secrets[secret_name] = value
                        
                    except ValueError:
                        continue
        
        logging.info(f"Loaded {len(secrets)} secrets from {env_file}")
        return secrets

    def setup_all_secrets(self):
        """Setup all QA secrets with intelligent versioning."""
        logging.info("Setting up QA environment secrets with intelligent versioning...")

        # Load secrets from generated QA environment file
        secrets = self._load_secrets_from_env_file()

        logging.info("Creating/updating secrets...")
        success_count = 0

        for secret_name, value in secrets.items():
            if self.ensure_secret(secret_name, value):
                success_count += 1

        logging.info("Granting IAM permissions to service account...")

        # Grant IAM permissions for all secrets
        iam_success_count = 0
        for secret_name in secrets:
            if self.grant_iam_permission(secret_name):
                iam_success_count += 1

        logging.info("Summary:")
        logging.info("=" * 40)
        logging.info("Secrets created:   %d", self.secrets_created)
        logging.info("Secrets updated:   %d", self.secrets_updated)
        logging.info("Secrets unchanged: %d", self.secrets_unchanged)
        logging.info("Total secrets:     %d", len(secrets))
        logging.info("IAM permissions:   %d/%d", iam_success_count, len(secrets))

        if success_count == len(secrets):
            logging.info("✅ QA secrets setup completed successfully!")
        else:
            logging.error("⚠️  Some secrets failed: %d failures", len(secrets) - success_count)
            sys.exit(1)


def main():
    """Main function to setup QA secrets."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Configuration
    project_id = "beryl3"
    service_account = "beryl3-qa-storage@beryl3.iam.gserviceaccount.com"

    # Create secret manager and setup secrets
    manager = SecretManager(project_id, service_account)
    manager.setup_all_secrets()


if __name__ == "__main__":
    main()