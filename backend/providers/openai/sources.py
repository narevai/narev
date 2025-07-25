"""
OpenAI Data Sources Configuration
"""

from datetime import datetime
from typing import Any

from pipeline.sources.base import BaseSource


class OpenAISource(BaseSource):
    """OpenAI API sources configuration."""

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get OpenAI API sources based on current endpoints implementation.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations
        """
        # Convert to Unix timestamps (OpenAI preference)
        start_time = int(start_date.timestamp())
        end_time = int(end_date.timestamp())

        # Common parameters for all endpoints
        common_params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": "1d",
            "group_by": ["model", "api_key_id"],
            "limit": 30,
        }

        sources = [
            {
                "name": "completions_usage",
                "source_type": "rest_api",
                "config": {
                    "endpoint": {
                        "path": "/organization/usage/completions",
                        "method": "GET",
                        "params": common_params.copy(),
                    },
                    "data_selector": "data",
                    "primary_key": ["bucket_start_time", "model", "api_key_id"],
                },
            },
            {
                "name": "embeddings_usage",
                "source_type": "rest_api",
                "config": {
                    "endpoint": {
                        "path": "/organization/usage/embeddings",
                        "method": "GET",
                        "params": common_params.copy(),
                    },
                    "data_selector": "data",
                    "primary_key": ["bucket_start_time", "model", "api_key_id"],
                },
            },
            {
                "name": "images_usage",
                "source_type": "rest_api",
                "config": {
                    "endpoint": {
                        "path": "/organization/usage/images",
                        "method": "GET",
                        "params": common_params.copy(),
                    },
                    "data_selector": "data",
                    "primary_key": ["bucket_start_time", "model", "api_key_id"],
                },
            },
            {
                "name": "audio_speeches_usage",
                "source_type": "rest_api",
                "config": {
                    "endpoint": {
                        "path": "/organization/usage/audio_speeches",
                        "method": "GET",
                        "params": common_params.copy(),
                    },
                    "data_selector": "data",
                    "primary_key": ["bucket_start_time", "model", "api_key_id"],
                },
            },
            {
                "name": "audio_transcriptions_usage",
                "source_type": "rest_api",
                "config": {
                    "endpoint": {
                        "path": "/organization/usage/audio_transcriptions",
                        "method": "GET",
                        "params": common_params.copy(),
                    },
                    "data_selector": "data",
                    "primary_key": ["bucket_start_time", "model", "api_key_id"],
                },
            },
            {
                "name": "moderations_usage",
                "source_type": "rest_api",
                "config": {
                    "endpoint": {
                        "path": "/organization/usage/moderations",
                        "method": "GET",
                        "params": common_params.copy(),
                    },
                    "data_selector": "data",
                    "primary_key": ["bucket_start_time", "model", "api_key_id"],
                },
            },
        ]

        # Validate and return sources
        return self.validate_source_configs(sources)
