"""
GCP Provider Authentication Module
"""

import logging
from typing import Any

from google.cloud import bigquery
from google.oauth2 import service_account

from app.models.auth import AuthMethod

logger = logging.getLogger(__name__)


class GCPAuth:
    """Handle authentication for GCP provider."""

    # GCP authentication - only what makes sense for web UI
    SUPPORTED_METHODS = [
        AuthMethod.SERVICE_ACCOUNT,  # JSON key file - the standard way
    ]
    DEFAULT_METHOD = AuthMethod.SERVICE_ACCOUNT

    # Auth field definitions for UI
    AUTH_FIELDS = {
        AuthMethod.SERVICE_ACCOUNT: {
            "credentials": {
                "required": True,
                "type": "json_upload",
                "placeholder": '{\n  "type": "service_account",\n  "project_id": "your-project",\n  "private_key_id": "...",\n  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",\n  "client_email": "...@...iam.gserviceaccount.com",\n  "client_id": "...",\n  "auth_uri": "https://accounts.google.com/o/oauth2/auth",\n  "token_uri": "https://oauth2.googleapis.com/token",\n  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",\n  "client_x509_cert_url": "..."\n}',
                "description": "Service account JSON key (download from GCP Console > IAM & Admin > Service Accounts)",
            }
        }
    }

    def __init__(self, auth_config: dict[str, Any]):
        """Initialize GCP authentication."""
        self.auth_config = auth_config
        self.method = auth_config.get("method", self.DEFAULT_METHOD)
        self._credentials = None
        self._project_id = None

    def get_credentials(self) -> service_account.Credentials:
        """Get Google Cloud credentials object."""
        if self._credentials:
            return self._credentials

        service_account_info = self.auth_config.get("credentials")
        if not service_account_info:
            raise ValueError("Service account credentials not provided")

        # Extract project_id
        self._project_id = service_account_info.get("project_id")

        # Create credentials
        self._credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        return self._credentials

    def get_project_id(self) -> str | None:
        """Get project ID from service account."""
        if not self._project_id and self.auth_config.get("credentials"):
            self._project_id = self.auth_config["credentials"].get("project_id")
        return self._project_id

    def create_bigquery_client(
        self, project_id: str, location: str = "US"
    ) -> bigquery.Client:
        """Create BigQuery client with authentication."""
        credentials = self.get_credentials()

        return bigquery.Client(
            credentials=credentials, project=project_id, location=location
        )

    def validate(self) -> None:
        """Validate authentication configuration."""
        if not self.auth_config:
            raise ValueError("Authentication configuration is required")

        if self.method != AuthMethod.SERVICE_ACCOUNT:
            raise ValueError(
                f"GCP only supports {AuthMethod.SERVICE_ACCOUNT} authentication"
            )

        credentials = self.auth_config.get("credentials")
        if not credentials:
            raise ValueError("Service account credentials are required")

        if not isinstance(credentials, dict):
            raise ValueError("Credentials must be a JSON object")

        # Validate required fields in service account
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing_fields = [f for f in required_fields if f not in credentials]

        if missing_fields:
            raise ValueError(
                f"Missing required fields in service account: {', '.join(missing_fields)}"
            )

        if credentials.get("type") != "service_account":
            raise ValueError("Credentials type must be 'service_account'")
