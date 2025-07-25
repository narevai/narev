"""
AWS Data Sources Configuration
"""

from datetime import datetime
from typing import Any

from pipeline.sources.base import BaseSource


class AWSSource(BaseSource):
    """AWS Cost and Usage Report sources configuration."""

    def __init__(self, provider: Any = None):
        """Initialize with optional provider reference."""
        self.provider = provider

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get AWS FOCUS 1.0 export or legacy CUR sources.

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

        # Determine source type based on provider config
        export_type = self._detect_export_type(fs_config)

        if export_type == "focus":
            sources = self._get_focus_sources(start_date, end_date, fs_config)
        else:
            sources = self._get_legacy_cur_sources(start_date, end_date, fs_config)

        # Validate and return sources
        return self.validate_source_configs(sources)

    def _detect_export_type(self, fs_config: dict[str, Any]) -> str:
        """
        Detect if this is a FOCUS 1.0 export or legacy CUR based on bucket structure.

        Args:
            fs_config: Filesystem configuration from provider

        Returns:
            "focus" for FOCUS 1.0 exports, "legacy" for traditional CUR
        """
        # Check if provider has explicit export type configuration
        if hasattr(self.provider, "export_type"):
            return getattr(self.provider, "export_type", "focus")

        # Default to FOCUS for new implementations
        return "focus"

    def _get_focus_sources(
        self, start_date: datetime, end_date: datetime, fs_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Get sources for AWS FOCUS 1.0 Data Exports.

        FOCUS exports are typically stored as Parquet files with different organization than legacy CUR.
        """
        return [
            {
                "name": "aws_focus_export",
                "source_type": "filesystem",
                "config": {
                    # Include filesystem config from provider
                    **fs_config,
                    # File pattern for FOCUS exports (typically parquet)
                    "file_pattern": self._build_focus_file_pattern(
                        start_date, end_date
                    ),
                    # Parse options for FOCUS format
                    "parse_options": {
                        "format": "parquet",  # FOCUS exports are typically parquet
                        "compression": "snappy",  # Default parquet compression
                    },
                    # Date filtering for FOCUS format
                    "filters": {
                        "date_column": "ChargePeriodStart",  # FOCUS standard field
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                    # Metadata for processing
                    "metadata": {
                        "export_format": "focus_1_0",
                        "schema_version": "1.0",
                        "provider": "aws",
                    },
                },
            }
        ]

    def _get_legacy_cur_sources(
        self, start_date: datetime, end_date: datetime, fs_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Get sources for legacy AWS Cost and Usage Reports.
        """
        return [
            {
                "name": "cost_and_usage_report",
                "source_type": "filesystem",
                "config": {
                    # Include filesystem config from provider
                    **fs_config,
                    # File pattern to match legacy CUR files
                    "file_pattern": self._build_legacy_file_pattern(
                        start_date, end_date
                    ),
                    # Parse options for legacy format
                    "parse_options": {
                        "compression": "gzip",  # Legacy CUR often uses gzip
                        "format": "csv",  # or "parquet" depending on setup
                    },
                    # Date filtering for legacy format
                    "filters": {
                        "date_column": "lineItem/UsageStartDate",  # Legacy CUR field
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                    # Metadata for processing
                    "metadata": {
                        "export_format": "cur_legacy",
                        "schema_version": "2.0",
                        "provider": "aws",
                    },
                },
            }
        ]

    def _build_focus_file_pattern(
        self, start_date: datetime, end_date: datetime
    ) -> str:
        """
        Build file pattern for AWS FOCUS 1.0 Data Export files.

        FOCUS exports typically have a different organization than legacy CUR:
        - Files are organized by export date
        - Typically stored as parquet files
        - May have different naming conventions
        """
        # For FOCUS exports, we typically want all parquet files in the export path
        # The filtering will be done by date columns rather than file path patterns
        return "**/*.parquet"

    def _build_legacy_file_pattern(
        self, start_date: datetime, end_date: datetime
    ) -> str:
        """
        Build file pattern for legacy AWS CUR files.

        AWS CUR files are organized by billing period (monthly).
        Pattern examples:
        - **/*.parquet - All parquet files
        - **/2024-01/**/*.parquet - Specific month
        - **/manifest.json - Manifest files only
        """
        # If within same month, use specific month pattern
        if start_date.year == end_date.year and start_date.month == end_date.month:
            year_month = start_date.strftime("%Y%m")
            return f"**/{year_month}*/**/*.parquet"

        # Otherwise, use general pattern and rely on date filtering
        return "**/*.parquet"
