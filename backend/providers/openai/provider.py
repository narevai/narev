"""
OpenAI Provider Implementation
"""

import logging
from datetime import datetime
from typing import Any

import httpx
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import HeaderLinkPaginator

from providers.base import BaseProvider
from providers.registry import ProviderRegistry

from .auth import OpenAIAuth
from .mapper import OpenAIFocusMapper
from .sources import OpenAISource

logger = logging.getLogger(__name__)


@ProviderRegistry.register(
    provider_type="openai",
    display_name="OpenAI",
    description="OpenAI API billing and usage",
    supported_features=[
        "usage_by_model",
        "usage_by_api_key",
        "daily_aggregation",
        "hourly_aggregation",
        "organization_support",
    ],
    required_config=[],
    optional_config=["organization_id"],
    version="1.0.0",
    mapper_class=OpenAIFocusMapper,
    source_class=OpenAISource,
    default_source_type="rest_api",
    default_config={},
    # Auth metadata from auth module
    supported_auth_methods=OpenAIAuth.SUPPORTED_METHODS,
    default_auth_method=OpenAIAuth.DEFAULT_METHOD,
    auth_fields=OpenAIAuth.AUTH_FIELDS,
    # Other fields
    field_descriptions={"organization_id": "OpenAI organization ID"},
    field_types={"organization_id": "string"},
    field_placeholders={"organization_id": "org-XXXXXXXXXXXXXXXXXX"},
    standard_fields={
        "name": {
            "required": True,
            "type": "string",
            "pattern": "^[a-z0-9-_]+$",
            "placeholder": "openai-main (lowercase, no spaces)",
            "description": "Unique identifier",
        },
        "display_name": {
            "required": False,
            "type": "string",
            "placeholder": "Main OpenAI Account",
            "description": "Human-readable name for the interface",
        },
        "api_endpoint": {
            "required": False,
            "type": "string",
            "placeholder": "https://api.openai.com/v1",
            "description": "Custom API endpoint",
        },
    },
)
class OpenAIProvider(BaseProvider):
    """OpenAI billing data provider."""

    def __init__(self, config: dict[str, Any]):
        """Initialize OpenAI provider."""
        super().__init__(config)

        # Set default endpoint if not provided
        if not self.api_endpoint:
            self.api_endpoint = "https://api.openai.com/v1"

        # Get organization_id from additional_config
        additional = config.get("additional_config", {})
        self.organization_id = additional.get("organization_id")

        # Initialize authentication handler
        self.auth_handler = OpenAIAuth(self.auth_config)

        # Store source class
        self.source_class = OpenAISource

        # REST client (lazy loading)
        self._client = None

    def get_rest_client(self) -> RESTClient:
        """Get configured REST client for DLT."""
        if not self._client:
            self._client = RESTClient(
                base_url=self.api_endpoint,
                headers=self.get_request_headers(),
                auth=self.get_auth(),
                paginator=self.get_paginator(),
            )
        return self._client

    def get_auth(self) -> Any:
        """Get authentication configuration."""
        return self.auth_handler.get_dlt_auth()

    def get_paginator(self) -> HeaderLinkPaginator:
        """Get paginator for OpenAI API."""
        return HeaderLinkPaginator()

    def get_request_headers(self) -> dict[str, str]:
        """Get request headers including organization."""
        headers = super().get_request_headers()

        # Add organization header if specified
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id

        # Add auth headers
        headers.update(self.auth_handler.get_headers())

        return headers

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Get OpenAI data sources for the date range."""
        if self.source_class:
            source = self.source_class()
            return source.get_sources(start_date, end_date)

        logger.warning("No source class registered for OpenAI provider")
        return []

    def test_connection(self) -> dict[str, Any]:
        """Test connection to OpenAI API."""
        try:
            # Validate auth config
            self.auth_handler.validate()

            # Test with billing endpoint
            headers = self.get_request_headers()

            with httpx.Client() as client:
                response = client.get(
                    f"{self.api_endpoint}/organization/usage/completions?start_time=1751546804",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Successfully connected to OpenAI API",
                        "details": {
                            "endpoint": self.api_endpoint,
                            "organization": self.organization_id,
                        },
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "message": "Authentication failed - please check your API key",
                        "details": {"status_code": response.status_code},
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Connection failed with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text[:200],
                        },
                    }

        except ValueError as e:
            return {
                "success": False,
                "message": f"Invalid authentication configuration: {str(e)}",
                "details": {"error": str(e)},
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "details": {"error": str(e), "error_type": type(e).__name__},
            }
