"""
Base Extractor for different source types - Fixed version
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import dlt

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for data extractors."""

    def __init__(self, provider: Any, pipeline: dlt.Pipeline):
        """
        Initialize extractor.

        Args:
            provider: Provider instance with configuration and credentials
            pipeline: DLT pipeline instance
        """
        self.provider = provider
        self.pipeline = pipeline
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def extract(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """
        Extract data from source.

        Args:
            source_config: Source configuration from provider
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of extracted records
        """
        pass

    @abstractmethod
    def create_dlt_source(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> Any:
        """
        Create DLT source for extraction.

        Args:
            source_config: Source configuration from provider
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            DLT source instance
        """
        pass

    def validate_source_config(self, source_config: dict[str, Any]) -> None:
        """
        Validate source configuration.

        Args:
            source_config: Source configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not source_config.get("name"):
            raise ValueError("Source configuration must have a 'name' field")

        if not source_config.get("source_type"):
            raise ValueError("Source configuration must have a 'source_type' field")

        if "config" not in source_config:
            raise ValueError("Source configuration must have a 'config' field")

    def get_provider_value(self, key: str, default: Any = None) -> Any:
        """
        Get value from provider configuration.

        This method checks multiple locations in order:
        1. Provider instance attributes (e.g., self.provider.project_id)
        2. Provider config dict root level
        3. Provider additional_config dict
        4. Provider config dict with the key

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        # 1. Try provider instance attributes first
        # This handles providers like GCP that store values as instance attributes
        if hasattr(self.provider, key):
            value = getattr(self.provider, key)
            # Don't return None values as they might be uninitialized
            if value is not None:
                return value

        # 2. Try config dict root level
        if hasattr(self.provider, "config") and isinstance(self.provider.config, dict):
            if key in self.provider.config:
                value = self.provider.config[key]
                if value is not None:
                    return value

            # 3. Try additional_config within config
            if "additional_config" in self.provider.config:
                additional = self.provider.config["additional_config"]
                if isinstance(additional, dict) and key in additional:
                    value = additional[key]
                    if value is not None:
                        return value

        # 4. Try additional_config as provider attribute
        if hasattr(self.provider, "additional_config") and isinstance(
            self.provider.additional_config, dict
        ):
            if key in self.provider.additional_config:
                value = self.provider.additional_config[key]
                if value is not None:
                    return value

        # Return default if nothing found
        return default
