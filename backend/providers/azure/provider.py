"""
Azure Provider Implementation
"""

import logging
from datetime import datetime
from typing import Any

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient

from providers.base import BaseProvider
from providers.registry import ProviderRegistry

from .auth import AzureAuth
from .mapper import AzureFocusMapper
from .sources import AzureSource

logger = logging.getLogger(__name__)


@ProviderRegistry.register(
    provider_type="azure",
    display_name="Microsoft Azure",
    description="Azure Cost Management and Billing",
    supported_features=[
        "billing_export",
        "cost_analysis",
        "resource_tags",
        "budget_alerts",
        "focus_format",
    ],
    required_config=["storage_account", "container_name"],
    optional_config=["export_path"],
    version="1.0.0",
    mapper_class=AzureFocusMapper,
    source_class=AzureSource,
    default_source_type="filesystem",
    default_config={},
    # Auth metadata from auth module
    supported_auth_methods=AzureAuth.SUPPORTED_METHODS,
    default_auth_method=AzureAuth.DEFAULT_METHOD,
    auth_fields=AzureAuth.AUTH_FIELDS,
    # Other fields
    field_descriptions={
        "storage_account": "Azure Storage account name containing billing exports",
        "container_name": "Container name for billing exports",
        "export_path": "Path prefix for export files",
    },
    field_types={
        "storage_account": "string",
        "container_name": "string",
        "export_path": "string",
    },
    field_placeholders={
        "storage_account": "mybillingstorage",
        "container_name": "billing-exports",
        "export_path": "exports/daily",
    },
    standard_fields={
        "name": {
            "required": True,
            "type": "string",
            "pattern": "^[a-z0-9-_]+$",
            "placeholder": "azure-prod (lowercase, no spaces)",
            "description": "Unique identifier",
        },
        "display_name": {
            "required": False,
            "type": "string",
            "placeholder": "Azure Production",
            "description": "Human-readable name for the interface",
        },
    },
)
class AzureProvider(BaseProvider):
    """Azure billing data provider."""

    def __init__(self, config: dict[str, Any]):
        """Initialize Azure provider."""
        super().__init__(config)

        # Get configuration
        config.get("additional_config", {})
        self.storage_account = self._get_config_value("storage_account")
        self.container_name = self._get_config_value("container_name")
        self.export_path = self._get_config_value("export_path", "")

        # Validate required fields
        if not self.storage_account:
            raise ValueError("storage_account is required")
        if not self.container_name:
            raise ValueError("container_name is required")

        # Initialize authentication handler
        self.auth_handler = AzureAuth(self.auth_config, self.storage_account)

        # Store source class
        self.source_class = AzureSource

        # Blob service client (lazy loading)
        self._blob_service_client = None

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Get config value from root or additional_config."""
        value = self.config.get(key)
        if value is None and "additional_config" in self.config:
            value = self.config["additional_config"].get(key)
        return value if value is not None else default

    def get_blob_service_client(self) -> BlobServiceClient:
        """Get configured Blob Service client."""
        if not self._blob_service_client:
            self._blob_service_client = self.auth_handler.create_blob_service_client()
        return self._blob_service_client

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Get Azure data sources for the date range."""
        if self.source_class:
            source = self.source_class(provider=self)
            return source.get_sources(start_date, end_date)

        logger.warning("No source class registered for Azure provider")
        return []

    def test_connection(self) -> dict[str, Any]:
        """Test Azure Storage connection and permissions."""
        try:
            # Validate auth config
            self.auth_handler.validate()

            # Get blob service client
            blob_service_client = self.get_blob_service_client()

            # Test container access
            container_client = blob_service_client.get_container_client(
                self.container_name
            )

            # Check if container exists
            if not container_client.exists():
                return {
                    "success": False,
                    "message": f"Container '{self.container_name}' not found",
                    "details": {
                        "storage_account": self.storage_account,
                        "container": self.container_name,
                    },
                }

            # Try to list some blobs
            blob_prefix = self.export_path if self.export_path else ""
            blobs = container_client.list_blobs(name_starts_with=blob_prefix)

            # Count blobs (limit to first 10)
            blob_count = 0
            for _ in blobs:
                blob_count += 1
                if blob_count >= 10:
                    break

            return {
                "success": True,
                "message": "Successfully connected to Azure Storage",
                "details": {
                    "storage_account": self.storage_account,
                    "container": self.container_name,
                    "export_path": self.export_path,
                    "files_found": blob_count,
                    "auth_method": str(self.auth_handler.method),
                },
            }

        except ValueError as e:
            return {
                "success": False,
                "message": f"Invalid configuration: {str(e)}",
                "details": {"error": str(e)},
            }
        except AzureError as e:
            error_code = getattr(e, "error_code", "Unknown")
            return {
                "success": False,
                "message": f"Azure Error: {error_code}",
                "details": {
                    "error": str(e),
                    "error_code": error_code,
                    "storage_account": self.storage_account,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "details": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "storage_account": self.storage_account,
                },
            }

    def get_filesystem_config(self) -> dict[str, Any]:
        """Get filesystem configuration for sources."""
        # Build bucket URL
        bucket_url = f"az://{self.container_name}"
        if self.export_path:
            bucket_url = f"{bucket_url}/{self.export_path}"

        # Get auth config
        config = {"bucket_url": bucket_url, **self.auth_handler.get_filesystem_config()}

        return config
