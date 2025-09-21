#!/usr/bin/env python3
"""
Secrets Manager Library for Beryl3 Workflows
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class Secret:
    """Represents a single secret with its metadata."""
    
    def __init__(self, name: str, value: str, env_var: str, description: str = "", context: str = None):
        self.name = name
        self.value = value
        self.env_var = env_var
        self.description = description
        self.context = context  # 'webapp', 'jobs', or None for both
    
    def __repr__(self):
        context_str = f", context='{self.context}'" if self.context else ""
        return f"Secret(name='{self.name}', env_var='{self.env_var}'{context_str})"


class SecretsManager:
    """Manages secrets from YAML configuration and Google Cloud Secret Manager."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self.secrets: List[Secret] = self._load_secrets()
        self.project_id = self.config['project']['id']
        self.service_account = self.config['project']['service_account']
        
        # Statistics for operations
        self.secrets_created = 0
        self.secrets_updated = 0
        self.secrets_unchanged = 0
        
    def _find_config_file(self) -> str:
        """Find the secrets.yaml configuration file."""
        # Look for config relative to script location
        script_dir = Path(__file__).parent
        config_paths = [
            script_dir / "../envs/qa/secrets.yaml",
            Path.cwd() / "workflows/envs/qa/secrets.yaml",
            Path.cwd() / "secrets.yaml"
        ]
        
        for path in config_paths:
            if path.exists():
                return str(path.resolve())
                
        raise FileNotFoundError(
            "Could not find secrets.yaml. Expected locations:\n" +
            "\n".join(str(p) for p in config_paths)
        )
    
    def _load_config(self) -> dict:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logging.info("Loaded config from: %s", self.config_path)
                return config
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {self.config_path}: {e}") from e
    
    def _load_secrets(self) -> List[Secret]:
        """Load secrets from configuration."""
        secrets = []
        for secret_config in self.config.get('secrets', []):
            secret = Secret(
                name=secret_config['name'],
                value=secret_config['value'],
                env_var=secret_config['env_var'],
                description=secret_config.get('description', ''),
                context=secret_config.get('context')
            )
            secrets.append(secret)
        return secrets
    
    def get_secret(self, name: str) -> Optional[Dict[str, str]]:
        """Get a secret by name, returning dict with key and value."""
        for secret in self.secrets:
            if secret.name == name:
                return {'key': secret.name, 'value': secret.value}
        return None
    
    def get_all_secrets(self) -> Dict[str, str]:
        """Get all secrets as a dictionary."""
        return {secret.name: secret.value for secret in self.secrets}
    
    def get_secrets_by_context(self, context: str = None) -> List[Secret]:
        """Get secrets filtered by context (webapp, jobs, or None for both)."""
        if context is None:
            return self.secrets
        return [secret for secret in self.secrets if secret.context is None or secret.context == context]
    
    def get_env_var_mapping(self, context: str = None) -> Dict[str, str]:
        """Get mapping of environment variables to secret names for deployment."""
        mapping = {}
        for secret in self.get_secrets_by_context(context):
            mapping[secret.env_var] = f"{secret.name}:latest"
        return mapping
    
    def build_secrets_string(self, context: str = None) -> str:
        """Build --set-secrets parameter string for gcloud deployment."""
        env_mapping = self.get_env_var_mapping(context)
        return ",".join([f"{env_var}={secret_ref}" for env_var, secret_ref in env_mapping.items()])
    
    def get_secret_by_env_var(self, env_var: str, context: str = None) -> Optional[Secret]:
        """Get a secret by its environment variable name and context."""
        for secret in self.get_secrets_by_context(context):
            if secret.env_var == env_var:
                return secret
        return None
    
    def run_gcloud_command(self, command: List[str]) -> Tuple[bool, str]:
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
        """Check if a secret exists in Google Cloud Secret Manager."""
        command = [
            "gcloud", "secrets", "describe", secret_name,
            "--project", self.project_id
        ]
        success, _ = self.run_gcloud_command(command)
        return success
    
    def get_cloud_secret_value(self, secret_name: str) -> Optional[str]:
        """Get the current value of a secret from Google Cloud."""
        if not self.secret_exists(secret_name):
            return None
        
        command = [
            "gcloud", "secrets", "versions", "access", "latest",
            "--secret", secret_name,
            "--project", self.project_id
        ]
        success, output = self.run_gcloud_command(command)
        return output if success else None
    
    def create_cloud_secret(self, secret: Secret) -> bool:
        """Create a new secret in Google Cloud Secret Manager."""
        command = [
            "gcloud", "secrets", "create", secret.name,
            "--data-file", "-",
            "--project", self.project_id
        ]
        
        try:
            subprocess.run(
                command,
                input=secret.value,
                text=True,
                capture_output=True,
                check=True
            )
            logging.info("  Created secret: %s", secret.name)
            self.secrets_created += 1
            return True
        except subprocess.CalledProcessError as e:
            logging.error("  ERROR creating secret %s: %s", secret.name, e.stderr.strip())
            return False
    
    def update_cloud_secret(self, secret: Secret) -> bool:
        """Add a new version to an existing secret."""
        command = [
            "gcloud", "secrets", "versions", "add", secret.name,
            "--data-file", "-",
            "--project", self.project_id
        ]
        
        try:
            subprocess.run(
                command,
                input=secret.value,
                text=True,
                capture_output=True,
                check=True
            )
            logging.info("  Updated secret: %s (new version)", secret.name)
            self.secrets_updated += 1
            return True
        except subprocess.CalledProcessError as e:
            logging.error("  ERROR updating secret %s: %s", secret.name, e.stderr.strip())
            return False
    
    def ensure_cloud_secret(self, secret: Secret) -> bool:
        """Ensure secret exists in cloud with the correct value."""
        current_value = self.get_cloud_secret_value(secret.name)
        
        if current_value is None:
            # Secret doesn't exist, create it
            return self.create_cloud_secret(secret)
        if current_value != secret.value:
            # Secret exists but value is different, add new version
            return self.update_cloud_secret(secret)
        # Secret exists with same value, no action needed
        logging.info("  Secret unchanged: %s", secret.name)
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
    
    def setup_all_cloud_secrets(self) -> bool:
        """Setup all secrets in Google Cloud Secret Manager."""
        logging.info("Setting up QA environment secrets with intelligent versioning...")
        logging.info("Config file: %s", self.config_path)
        logging.info("Project: %s", self.project_id)
        logging.info("Service Account: %s", self.service_account)
        
        logging.info("Creating/updating secrets...")
        success_count = 0
        
        for secret in self.secrets:
            if self.ensure_cloud_secret(secret):
                success_count += 1
        
        logging.info("Granting IAM permissions to service account...")
        
        # Grant IAM permissions for all secrets
        iam_success_count = 0
        for secret in self.secrets:
            if self.grant_iam_permission(secret.name):
                iam_success_count += 1
        
        logging.info("Summary:")
        logging.info("=" * 40)
        logging.info("Secrets created:   %d", self.secrets_created)
        logging.info("Secrets updated:   %d", self.secrets_updated)
        logging.info("Secrets unchanged: %d", self.secrets_unchanged)
        logging.info("Total secrets:     %d", len(self.secrets))
        logging.info("IAM permissions:   %d/%d", iam_success_count, len(self.secrets))
        
        if success_count == len(self.secrets):
            logging.info("✅ QA secrets setup completed successfully!")
            return True
        else:
            logging.error("⚠️  Some secrets failed: %d failures", len(self.secrets) - success_count)
            return False
    
    def get_cloud_run_config(self) -> dict:
        """Get Cloud Run configuration from YAML."""
        return self.config.get('cloud_run', {})
    
    def get_docker_config(self) -> dict:
        """Get Docker configuration from YAML."""
        return self.config.get('docker', {})
    
    def get_project_config(self) -> dict:
        """Get project configuration from YAML."""
        return self.config.get('project', {})