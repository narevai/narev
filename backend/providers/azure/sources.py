"""
Azure Data Sources Configuration
"""

from datetime import datetime
from typing import Any

from pipeline.sources.base import BaseSource


class AzureSource(BaseSource):
    """Azure Cost Management Export sources configuration."""

    def __init__(self, provider: Any = None):
        """Initialize with optional provider reference."""
        self.provider = provider

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get Azure FOCUS export sources.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations
        """
        # Get filesystem config from provider if available
        fs_config = {}
        if self.provider and hasattr(self.provider, "get_filesystem_config"):
            fs_config = self.provider.get_filesystem_config()

        sources = [
            {
                "name": "azure_focus_export",
                "source_type": "filesystem",
                "config": {
                    # Include filesystem config from provider (bucket_url, credentials)
                    **fs_config,
                    # Pattern to match all parquet partition files
                    "file_pattern": "**/part*.parquet",
                    # Parse options for FOCUS format
                    "parse_options": {
                        "format": "parquet",
                    },
                    # Date filtering using FOCUS standard columns
                    "filters": {
                        "date_column": "ChargePeriodStart",
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                },
            }
        ]

        return self.validate_source_configs(sources)
