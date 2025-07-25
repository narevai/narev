"""
Azure Provider Authentication Module
"""

import logging
from typing import Any

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

from app.models.auth import AuthMethod

logger = logging.getLogger(__name__)


class AzureAuth:
    """Handle authentication for Azure provider."""

    # Azure authentication methods that make sense for web app
    SUPPORTED_METHODS = [
        AuthMethod.API_KEY,  # Storage Account Key
        AuthMethod.OAUTH2_CLIENT_CREDENTIALS,  # Service Principal for advanced users
    ]
    DEFAULT_METHOD = AuthMethod.API_KEY

    # Auth field definitions for UI
    AUTH_FIELDS = {
        AuthMethod.API_KEY: {
            "key": {
                "required": True,
                "type": "password",
                "placeholder": "your-storage-account-key",
                "description": "Azure Storage Account Key (found in Azure Portal > Storage Account > Access Keys)",
            }
        },
        AuthMethod.OAUTH2_CLIENT_CREDENTIALS: {
            "tenant_id": {
                "required": True,
                "type": "string",
                "placeholder": "12345678-1234-1234-1234-123456789012",
                "description": "Azure AD Tenant ID",
            },
            "client_id": {
                "required": True,
                "type": "string",
                "placeholder": "12345678-1234-1234-1234-123456789012",
                "description": "Azure AD Application (client) ID",
            },
            "client_secret": {
                "required": True,
                "type": "password",
                "placeholder": "your-client-secret",
                "description": "Client secret value",
            },
        },
    }

    def __init__(self, auth_config: dict[str, Any], storage_account: str | None = None):
        """Initialize Azure authentication."""
        self.auth_config = auth_config
        self.method = auth_config.get("method", self.DEFAULT_METHOD)
        self.storage_account = storage_account
        self._credential = None

    def get_storage_key(self) -> str | None:
        """Get storage account key for direct authentication."""
        if self.method == AuthMethod.API_KEY:
            return self.auth_config.get("key")
        return None

    def get_credential(self) -> ClientSecretCredential | None:
        """Get Azure credential object for Service Principal auth."""
        if self.method == AuthMethod.OAUTH2_CLIENT_CREDENTIALS:
            if not self._credential:
                tenant_id = self.auth_config.get("tenant_id")
                client_id = self.auth_config.get("client_id")
                client_secret = self.auth_config.get("client_secret")

                if not all([tenant_id, client_id, client_secret]):
                    raise ValueError(
                        "tenant_id, client_id, and client_secret are required"
                    )

                self._credential = ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
            return self._credential
        return None

    def create_blob_service_client(
        self, storage_account: str | None = None
    ) -> BlobServiceClient:
        """Create BlobServiceClient with appropriate authentication."""
        account = storage_account or self.storage_account
        if not account:
            raise ValueError("Storage account name is required")

        account_url = f"https://{account}.blob.core.windows.net"

        if self.method == AuthMethod.API_KEY:
            # Use storage account key
            key = self.get_storage_key()
            if not key:
                raise ValueError("Storage account key is required")
            return BlobServiceClient(account_url=account_url, credential=key)

        elif self.method == AuthMethod.OAUTH2_CLIENT_CREDENTIALS:
            # Use Service Principal
            credential = self.get_credential()
            return BlobServiceClient(account_url=account_url, credential=credential)

        else:
            raise ValueError(f"Unsupported auth method: {self.method}")

    def validate(self) -> None:
        """Validate authentication configuration."""
        if not self.auth_config:
            raise ValueError("Authentication configuration is required")

        if self.method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported auth method: {self.method}. "
                f"Supported methods: {', '.join(str(m) for m in self.SUPPORTED_METHODS)}"
            )

        if self.method == AuthMethod.API_KEY:
            if not self.auth_config.get("key"):
                raise ValueError("Storage account key is required")

        elif self.method == AuthMethod.OAUTH2_CLIENT_CREDENTIALS:
            required = ["tenant_id", "client_id", "client_secret"]
            missing = [f for f in required if not self.auth_config.get(f)]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

    def get_filesystem_config(self) -> dict[str, Any]:
        """Get configuration for DLT filesystem operations."""
        config = {}

        if self.method == AuthMethod.API_KEY:
            key = self.get_storage_key()
            if key:
                config["azure_storage_account_key"] = key
                if self.storage_account:
                    config["azure_storage_account_name"] = self.storage_account

        elif self.method == AuthMethod.OAUTH2_CLIENT_CREDENTIALS:
            # For filesystem ops with Service Principal, we'd need to handle this differently
            # DLT filesystem might not support this directly
            logger.warning(
                "Service Principal auth for filesystem operations may require custom implementation"
            )

        return config
