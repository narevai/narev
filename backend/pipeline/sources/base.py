"""
Base Source Definition
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseSource(ABC):
    """Base class for defining data sources."""

    @abstractmethod
    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get source configurations for date range.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations, each containing:
                - name: Source identifier (required)
                - source_type: Type of source - rest_api, filesystem, sql_database (required)
                - config: Source-specific configuration (required)

        Example:
            [
                {
                    "name": "usage_data",
                    "source_type": "rest_api",
                    "config": {
                        "endpoint": {
                            "path": "/v1/usage",
                            "method": "GET",
                            "params": {"date": "2024-01-01"}
                        },
                        "data_selector": "data",
                        "primary_key": ["id"]
                    }
                }
            ]
        """
        pass

    def validate_source_configs(
        self, sources: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Validate source configurations.

        Args:
            sources: List of source configurations

        Returns:
            Validated source configurations

        Raises:
            ValueError: If any source configuration is invalid
        """
        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                raise ValueError(f"Source {idx} must be a dictionary")

            # Required fields
            if "name" not in source:
                raise ValueError(f"Source {idx} missing required field: name")

            if "source_type" not in source:
                raise ValueError(
                    f"Source '{source['name']}' missing required field: source_type"
                )

            if "config" not in source:
                raise ValueError(
                    f"Source '{source['name']}' missing required field: config"
                )

            # Validate source type
            valid_types = [
                "rest_api",
                "filesystem",
                "sql_database",
                "bigquery",
                "custom",
            ]
            if source["source_type"] not in valid_types:
                raise ValueError(
                    f"Source '{source['name']}' has invalid source_type: {source['source_type']}. "
                    f"Valid types: {', '.join(valid_types)}"
                )

        return sources
