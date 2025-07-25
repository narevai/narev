"""
Base Provider Class
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Base class for all billing data providers."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize base provider.

        Args:
            config: Provider configuration containing:
                - provider_type: Type of provider
                - auth_config: Authentication configuration
                - api_endpoint: API endpoint URL
                - additional_config: Additional provider-specific config
        """
        self.config = config
        self.provider_type = config.get("provider_type", "")
        self.api_endpoint = config.get("api_endpoint", "")
        self.additional_config = config.get("additional_config", {})
        self.auth_config = config.get("auth_config", {})

        # Source class can be set by registry
        self.source_class = None

    @abstractmethod
    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get data sources for the given date range.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations
        """
        pass

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to the provider's API.

        Returns:
            Dictionary with:
                - success: bool
                - message: str
                - details: dict (optional)
        """
        pass

    def get_auth(self) -> Any:
        """
        Get authentication object for DLT.

        Override this method to provide custom authentication.

        Returns:
            Authentication object for DLT or None
        """
        return None

    def get_request_headers(self) -> dict[str, str]:
        """
        Get default request headers.

        Override this method to add custom headers.

        Returns:
            Dictionary of headers
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_paginator(self) -> Any:
        """
        Get paginator configuration for DLT.

        Override this method to provide custom pagination.

        Returns:
            Paginator object for DLT
        """
        return None

    def __repr__(self) -> str:
        """String representation of provider."""
        return f"{self.__class__.__name__}(type={self.provider_type})"
