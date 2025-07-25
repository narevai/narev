"""
Extractor Factory - Updated with BigQuery support
"""

import logging
from typing import Any

import dlt

from .base import BaseExtractor
from .bigquery import BigQueryExtractor
from .filesystem import FilesystemExtractor
from .rest_api import RestApiExtractor
from .sql_database import SQLDatabaseExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """Factory for creating extractors based on source type."""

    # Mapping of source types to extractor classes
    _extractors: dict[str, type[BaseExtractor]] = {
        # API extractors
        "rest_api": RestApiExtractor,
        "api": RestApiExtractor,  # Alias
        # File extractors
        "filesystem": FilesystemExtractor,
        "s3": FilesystemExtractor,  # Alias
        "file": FilesystemExtractor,  # Alias
        # SQL extractors
        "sql_database": SQLDatabaseExtractor,
        "sql": SQLDatabaseExtractor,  # Alias
        "postgresql": SQLDatabaseExtractor,
        "postgres": SQLDatabaseExtractor,  # Alias
        "mysql": SQLDatabaseExtractor,
        # BigQuery gets its own extractor
        "bigquery": BigQueryExtractor,
        "gcp_bigquery": BigQueryExtractor,  # Alias
    }

    @classmethod
    def create_extractor(
        cls,
        source_type: str,
        provider: Any,
        pipeline: dlt.Pipeline,
    ) -> BaseExtractor:
        """
        Create extractor for source type.

        Args:
            source_type: Type of source (rest_api, filesystem, sql_database, bigquery, etc.)
            provider: Provider instance
            pipeline: DLT pipeline instance

        Returns:
            Extractor instance

        Raises:
            ValueError: If source type is not supported
        """
        # Normalize source type to lowercase
        source_type = source_type.lower()

        # Get extractor class
        extractor_class = cls._extractors.get(source_type)

        if not extractor_class:
            available_types = ", ".join(sorted(cls._extractors.keys()))
            raise ValueError(
                f"Unknown source type: '{source_type}'. "
                f"Available types: {available_types}"
            )

        logger.debug(
            f"Creating {extractor_class.__name__} for source type: {source_type}"
        )

        # Create and return extractor instance
        return extractor_class(provider, pipeline)

    @classmethod
    def register_extractor(
        cls,
        source_type: str,
        extractor_class: type[BaseExtractor],
    ) -> None:
        """
        Register custom extractor.

        Args:
            source_type: Source type identifier
            extractor_class: Extractor class to register
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise TypeError(f"{extractor_class} must inherit from BaseExtractor")

        cls._extractors[source_type.lower()] = extractor_class
        logger.info(
            f"Registered extractor {extractor_class.__name__} for type: {source_type}"
        )

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported source types."""
        return sorted(cls._extractors.keys())

    @classmethod
    def is_supported(cls, source_type: str) -> bool:
        """Check if source type is supported."""
        return source_type.lower() in cls._extractors
