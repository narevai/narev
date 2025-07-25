"""
SQL Database Extractor - Fixed version with GCP support and debug logging
"""

import logging
from datetime import datetime
from typing import Any

from dlt.sources.sql_database import sql_database

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class SQLDatabaseExtractor(BaseExtractor):
    """Extractor for SQL database sources including BigQuery."""

    async def extract(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Extract data from SQL database."""
        self.validate_source_config(source_config)

        self.logger.info(f"Extracting from SQL database: {source_config['name']}")

        # Create DLT source
        source = self.create_dlt_source(source_config, start_date, end_date)

        # Extract records
        records = []
        record_count = 0

        try:
            # SQL database source returns a generator
            for record in source:
                records.append(record)
                record_count += 1

                # Log progress
                if record_count % 1000 == 0:
                    self.logger.debug(f"Extracted {record_count} records so far...")

        except Exception as e:
            self.logger.error(f"Error extracting from SQL database: {e}")
            raise

        self.logger.info(f"Successfully extracted {len(records)} records")
        return records

    def create_dlt_source(
        self,
        source_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> Any:
        """Create SQL database source."""
        config = source_config.get("config", {})

        # Get connection string
        connection_string = self._get_connection_string()

        # Prepare source kwargs
        source_kwargs = {
            "credentials": connection_string,
        }

        # Add table names if specified
        if "table_names" in config:
            source_kwargs["table_names"] = config["table_names"]

        # Add schema if specified
        if "schema" in config:
            source_kwargs["schema"] = config["schema"]

        # Handle query-based extraction
        if "query" in config or "query_template" in config:
            query = self._build_query(config, start_date, end_date)
            source_kwargs["query"] = query

        # Add other options
        if "chunk_size" in config:
            source_kwargs["chunk_size"] = config["chunk_size"]

        # Backend for specific databases
        if self.provider.provider_type in ["gcp", "bigquery"]:
            source_kwargs["backend"] = "pandas"

        self.logger.debug(
            f"Creating SQL source with connection: {self._mask_connection_string(connection_string)}"
        )

        return sql_database(**source_kwargs)

    def _get_connection_string(self) -> str:
        """Build connection string from provider configuration."""
        provider_type = self.get_provider_value("provider_type")

        # Debug logging
        self.logger.debug(
            f"Building connection string for provider type: {provider_type}"
        )
        self.logger.debug(f"Provider config keys: {list(self.provider.config.keys())}")
        self.logger.debug(f"Additional config: {self.provider.additional_config}")

        # Special handling for GCP/BigQuery
        if provider_type in ["gcp", "bigquery"]:
            # For GCP, we need to create a BigQuery-specific connection
            project_id = self.get_provider_value("project_id")

            self.logger.debug(f"GCP project_id: {project_id}")

            if not project_id:
                # Log all available values for debugging
                self.logger.error(f"Provider config: {self.provider.config}")
                raise ValueError("GCP/BigQuery provider missing project_id")

            # For BigQuery with DLT, we use the bigquery:// scheme
            # DLT will handle authentication via environment or credentials
            connection = f"bigquery://{project_id}"

            # Add dataset if available
            dataset_id = self.get_provider_value("dataset_id")
            if dataset_id:
                connection += f"/{dataset_id}"

            self.logger.debug(f"Built BigQuery connection string: {connection}")

            # Note: For BigQuery, credentials are handled separately
            # by DLT through environment variables or explicit config
            return connection

        elif provider_type in ["postgresql", "postgres"]:
            # PostgreSQL connection string
            host = self.get_provider_value("host", "localhost")
            port = self.get_provider_value("port", 5432)
            database = self.get_provider_value("database")
            username = self.get_provider_value("username")
            password = self.get_provider_value("password")

            if not all([database, username]):
                raise ValueError("PostgreSQL provider missing required fields")

            return f"postgresql://{username}:{password}@{host}:{port}/{database}"

        elif provider_type == "mysql":
            # MySQL connection string
            host = self.get_provider_value("host", "localhost")
            port = self.get_provider_value("port", 3306)
            database = self.get_provider_value("database")
            username = self.get_provider_value("username")
            password = self.get_provider_value("password")

            if not all([database, username]):
                raise ValueError("MySQL provider missing required fields")

            return f"mysql://{username}:{password}@{host}:{port}/{database}"

        elif provider_type == "snowflake":
            # Snowflake connection string
            account = self.get_provider_value("account")
            username = self.get_provider_value("username")
            password = self.get_provider_value("password")
            database = self.get_provider_value("database")
            warehouse = self.get_provider_value("warehouse")

            if not all([account, username, database]):
                raise ValueError("Snowflake provider missing required fields")

            connection = f"snowflake://{username}:{password}@{account}/{database}"
            if warehouse:
                connection += f"?warehouse={warehouse}"

            return connection

        else:
            # Try to get generic connection string
            connection_string = self.get_provider_value("connection_string")
            if connection_string:
                return connection_string

            raise ValueError(
                f"Cannot build connection string for provider type: {provider_type}"
            )

    def _build_query(
        self, config: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> str:
        """Build SQL query from template or direct query."""
        # Direct query takes precedence
        if "query" in config:
            return config["query"]

        # Build from template
        if "query_template" in config:
            template = config["query_template"]

            # Get parameters
            params = config.get("query_params", {}).copy()

            # Add standard date parameters
            params.update(
                {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "start_datetime": start_date.isoformat(),
                    "end_datetime": end_date.isoformat(),
                    "start_timestamp": int(start_date.timestamp()),
                    "end_timestamp": int(end_date.timestamp()),
                }
            )

            # Add provider-specific parameters
            if self.provider.provider_type in ["gcp", "bigquery"]:
                project_id = self.get_provider_value("project_id")
                dataset_id = self.get_provider_value("dataset_id")
                table_name = self.get_provider_value("table_name")

                if all([project_id, dataset_id, table_name]):
                    params["full_table_name"] = (
                        f"`{project_id}.{dataset_id}.{table_name}`"
                    )
                    params["table_id"] = f"{project_id}.{dataset_id}.{table_name}"

            # Format template
            return template.format(**params)

        raise ValueError("No query or query_template provided in source configuration")

    def _mask_connection_string(self, connection_string: str) -> str:
        """Mask sensitive parts of connection string for logging."""
        # Simple masking - could be enhanced
        if "://" in connection_string and "@" in connection_string:
            parts = connection_string.split("://", 1)
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                if "@" in rest:
                    creds, location = rest.split("@", 1)
                    if ":" in creds:
                        user = creds.split(":", 1)[0]
                        return f"{protocol}://{user}:****@{location}"

        return connection_string

    def validate_source_config(self, source_config: dict[str, Any]) -> None:
        """Validate SQL database source configuration."""
        super().validate_source_config(source_config)

        config = source_config.get("config", {})

        # Must have either table_names or query/query_template
        if not any(
            [
                config.get("table_names"),
                config.get("query"),
                config.get("query_template"),
            ]
        ):
            raise ValueError(
                "SQL database source must specify either 'table_names' or 'query'/'query_template'"
            )
