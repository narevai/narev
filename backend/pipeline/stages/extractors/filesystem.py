"""
Filesystem/S3 Extractor
"""

import logging
from datetime import UTC, datetime
from typing import Any

from dlt.sources.filesystem import filesystem, read_csv, read_jsonl, read_parquet

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class FilesystemExtractor(BaseExtractor):
    """Extractor for filesystem sources (S3, local files, etc.)."""

    async def extract(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Extract data from filesystem/S3."""
        self.validate_source_config(source_config)

        self.logger.info(f"Extracting from filesystem: {source_config['name']}")

        # Create DLT source
        source = self.create_dlt_source(source_config, start_date, end_date)

        # Extract records
        all_records = []

        try:
            # Process the source
            for record in source:
                all_records.append(record)

                if len(all_records) % 1000 == 0:
                    self.logger.debug(f"Extracted {len(all_records)} records so far...")

        except Exception as e:
            self.logger.error(f"Error extracting from filesystem: {e}")
            raise

        self.logger.info(f"Successfully extracted {len(all_records)} records")
        return all_records

    def create_dlt_source(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> Any:
        """Create filesystem source with appropriate transformer."""
        config = source_config.get("config", {})

        # Get bucket URL - either from config or provider
        bucket_url = self._get_bucket_url(config)

        # Get credentials - either from config or provider
        credentials = self._get_credentials(config)

        # Get file pattern from config or determine from parse options
        file_pattern = config.get("file_pattern")
        if not file_pattern:
            # Determine pattern based on expected format
            parse_options = config.get("parse_options", {})
            file_format = parse_options.get("format", "parquet")

            if file_format == "parquet":
                file_pattern = "**/*.parquet"
            elif file_format == "csv":
                compression = parse_options.get("compression", "")
                if compression == "gzip":
                    file_pattern = "**/*.csv.gz"
                else:
                    file_pattern = "**/*.csv"
            elif file_format == "json":
                file_pattern = "**/*.json"
            else:
                # Default to looking for parquet files
                file_pattern = "**/*.parquet"

        # Add date filtering to pattern if needed
        if "{year}" in file_pattern or "{month}" in file_pattern:
            file_pattern = self._format_date_pattern(file_pattern, start_date, end_date)

        self.logger.debug(
            f"Creating filesystem source: {bucket_url} with pattern: {file_pattern}"
        )

        # Create filesystem source
        fs_source = filesystem(
            bucket_url=bucket_url,
            file_glob=file_pattern,
            credentials=credentials,
        )

        # Apply appropriate transformer based on file type
        return self._apply_transformer(fs_source, file_pattern, config)

    def _apply_transformer(
        self, fs_source: Any, file_pattern: str, config: dict[str, Any]
    ) -> Any:
        """Apply the appropriate transformer based on file type."""
        # Check file extension from pattern
        if ".parquet" in file_pattern:
            self.logger.debug("Using parquet transformer")
            transformed = fs_source | read_parquet()
        elif ".csv" in file_pattern:
            self.logger.debug("Using CSV transformer")
            # Get CSV parsing options
            parse_options = config.get("parse_options", {})
            transformed = fs_source | read_csv(
                sep=parse_options.get("delimiter", ","),
                encoding=parse_options.get("encoding", "utf-8"),
            )
        elif ".json" in file_pattern:
            self.logger.debug("Using JSONL transformer")
            transformed = fs_source | read_jsonl()
        else:
            # Try to detect from first file or default to parquet
            self.logger.warning(
                f"Unknown file pattern {file_pattern}, defaulting to parquet"
            )
            transformed = fs_source | read_parquet()

        # Apply date filtering if configured
        if "filters" in config and "date_column" in config["filters"]:
            filters = config["filters"]
            date_col = filters["date_column"]
            start_date = filters.get("start_date")
            end_date = filters.get("end_date")

            if start_date and end_date:
                self.logger.debug(f"Applying date filter on column {date_col}")
                # Add filter function
                transformed.add_filter(
                    lambda record: self._is_record_in_date_range(
                        record, date_col, start_date, end_date
                    )
                )

        return transformed

    def _is_record_in_date_range(
        self, record: dict[str, Any], date_column: str, start_date: str, end_date: str
    ) -> bool:
        """Check if record falls within date range."""
        try:
            if date_column not in record:
                return True  # Include if no date column

            record_date = record[date_column]
            if isinstance(record_date, str):
                # Parse ISO format dates
                from dateutil import parser

                record_date = parser.parse(record_date)

            # Convert string dates to datetime if needed
            if isinstance(start_date, str):
                from dateutil import parser

                start_date = parser.parse(start_date)
            if isinstance(end_date, str):
                from dateutil import parser

                end_date = parser.parse(end_date)

            # Make all datetimes timezone-aware or naive

            # If record_date is naive, make it aware (assume UTC)
            if record_date.tzinfo is None:
                record_date = record_date.replace(tzinfo=UTC)

            # Make start/end dates aware if they're naive
            if hasattr(start_date, "tzinfo") and start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=UTC)
            if hasattr(end_date, "tzinfo") and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=UTC)

            return start_date <= record_date <= end_date

        except Exception as e:
            self.logger.warning(f"Error parsing date for filtering: {e}")
            return True  # Include on error

    def _get_bucket_url(self, config: dict[str, Any]) -> str:
        """Get bucket URL from config or provider."""
        # First check if URL is provided directly in config
        if "bucket_url" in config:
            return config["bucket_url"]

        # Try to get from provider's get_filesystem_config method
        if hasattr(self.provider, "get_filesystem_config"):
            fs_config = self.provider.get_filesystem_config()
            if fs_config and "bucket_url" in fs_config:
                return fs_config["bucket_url"]

        # Fallback error - provider should provide bucket_url
        raise ValueError(
            "No bucket_url found. Provider must supply bucket_url in "
            "source config or implement get_filesystem_config() method"
        )

    def _get_credentials(self, config: dict[str, Any]) -> dict[str, Any] | None:
        """Get credentials from config or provider."""
        # First check for credentials in config
        # Look for any credential-like keys
        credential_keys = [
            "aws_access_key_id",
            "aws_secret_access_key",
            "azure_storage_account_key",
            "azure_storage_account_name",
            "google_application_credentials",
        ]

        config_creds = {}
        for key in credential_keys:
            if key in config:
                config_creds[key] = config[key]

        if config_creds:
            return config_creds

        # Try to get from provider's get_filesystem_config method
        if hasattr(self.provider, "get_filesystem_config"):
            fs_config = self.provider.get_filesystem_config()
            if fs_config:
                # Remove non-credential keys
                return {
                    k: v
                    for k, v in fs_config.items()
                    if k != "bucket_url" and not k.startswith("_")
                }

        # No credentials needed (e.g., public buckets)
        return None

    def _format_date_pattern(
        self, pattern: str, start_date: datetime, end_date: datetime
    ) -> str:
        """Format file pattern with date variables."""
        # For now, use start date for pattern
        # Could be enhanced to generate multiple patterns for date ranges
        return pattern.format(
            year=start_date.year,
            month=start_date.month,
            day=start_date.day,
            year_month=start_date.strftime("%Y-%m"),
            date=start_date.strftime("%Y-%m-%d"),
        )
