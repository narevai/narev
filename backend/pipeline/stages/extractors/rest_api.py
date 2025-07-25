"""
REST API Extractor
"""

import logging
from datetime import datetime
from typing import Any

from dlt.sources.rest_api import rest_api_source

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class RestApiExtractor(BaseExtractor):
    """Extractor for REST API sources."""

    async def extract(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Extract data from REST API."""
        self.validate_source_config(source_config)

        self.logger.info(f"Extracting from REST API: {source_config['name']}")

        # Create DLT source
        source = self.create_dlt_source(source_config, start_date, end_date)

        # Extract records
        records = []
        record_count = 0

        try:
            # Handle both source with resources and direct iterables
            if hasattr(source, "resources"):
                # Source with multiple resources
                for resource_name, resource in source.resources.items():
                    self.logger.debug(f"Processing resource: {resource_name}")
                    for record in resource:
                        records.append(record)
                        record_count += 1

                        # Log progress every 100 records
                        if record_count % 100 == 0:
                            self.logger.debug(
                                f"Extracted {record_count} records so far..."
                            )
            else:
                # Direct iterable source
                for record in source:
                    records.append(record)
                    record_count += 1

                    if record_count % 100 == 0:
                        self.logger.debug(f"Extracted {record_count} records so far...")

        except Exception as e:
            self.logger.error(f"Error extracting from REST API: {e}")
            raise

        self.logger.info(
            f"Successfully extracted {len(records)} records from {source_config['name']}"
        )
        return records

    def create_dlt_source(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> Any:
        """Create REST API source."""
        config = source_config.get("config", {})
        endpoint_config = config.get("endpoint", {})

        # Build DLT configuration
        dlt_config = {
            "client": {
                "base_url": self.provider.api_endpoint,
                "auth": self._get_auth(),
                "headers": self._get_headers(),
                "paginator": self._get_paginator(),
            },
            "resources": [
                {
                    "name": source_config["name"],
                    "endpoint": {
                        "path": endpoint_config.get("path", ""),
                        "method": endpoint_config.get("method", "GET"),
                        "params": endpoint_config.get("params", {}),
                    },
                }
            ],
        }

        # Add JSON body if present (for POST requests)
        if "json" in endpoint_config:
            dlt_config["resources"][0]["endpoint"]["json"] = endpoint_config["json"]

        # Add data selector if present
        if "data_selector" in config:
            dlt_config["resources"][0]["endpoint"]["data_selector"] = config[
                "data_selector"
            ]

        # Add primary key if present
        if "primary_key" in config:
            dlt_config["resources"][0]["primary_key"] = config["primary_key"]

        # Add response actions if present
        if "response_actions" in config:
            dlt_config["resources"][0]["response_actions"] = config["response_actions"]

        self.logger.debug(f"Creating REST API source with config: {dlt_config}")

        return rest_api_source(dlt_config)

    def _get_auth(self) -> Any:
        """Get authentication configuration from provider."""
        if hasattr(self.provider, "get_auth"):
            return self.provider.get_auth()
        return None

    def _get_headers(self) -> dict[str, str]:
        """Get request headers from provider."""
        if hasattr(self.provider, "get_request_headers"):
            return self.provider.get_request_headers()
        return {}

    def _get_paginator(self) -> Any:
        """Get paginator configuration from provider."""
        if hasattr(self.provider, "get_paginator"):
            return self.provider.get_paginator()
        return None
