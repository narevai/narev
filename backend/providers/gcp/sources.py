"""
GCP Data Sources Configuration
"""

from datetime import datetime
from typing import Any

from pipeline.sources.base import BaseSource


class GCPSource(BaseSource):
    """GCP BigQuery billing export sources configuration."""

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get GCP billing sources.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations
        """
        sources = []

        # Standard billing export table
        sources.append(
            {
                "name": "billing_export",
                "source_type": "bigquery",
                "config": {
                    # Query template - will be formatted by SQL extractor
                    "query_template": """
                    SELECT *
                    FROM {full_table_name}
                    WHERE DATE(usage_start_time) >= DATE('{start_date}')
                      AND DATE(usage_start_time) <= DATE('{end_date}')
                    ORDER BY usage_start_time
                """,
                    # Query parameters
                    "query_params": {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                    },
                    # BigQuery-specific options
                    "chunk_size": 10000,
                    "use_legacy_sql": False,
                    # Cost optimization
                    "partition_filter": True,  # Use partition filtering if available
                },
            }
        )

        # Validate and return sources
        return self.validate_source_configs(sources)
