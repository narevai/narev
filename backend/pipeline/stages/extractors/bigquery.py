"""
BigQuery Extractor for GCP Billing Data
Supports both FOCUS and standard billing export formats
"""

import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import dlt
from google.cloud import bigquery
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class BigQueryExtractor:
    """Extractor for BigQuery billing data."""

    def __init__(self, provider, pipeline=None):
        """
        Initialize BigQuery extractor.

        Args:
            provider: Provider instance or provider config dict
            pipeline: DLT pipeline instance (optional, not used for BigQuery)
        """
        logger.info(
            f"Initializing BigQueryExtractor with provider type: {type(provider)}"
        )

        # Handle both provider instance and config dict
        if hasattr(provider, "config"):
            # It's a provider instance
            self.provider_config = provider.config
            logger.debug(f"Using provider.config: {list(self.provider_config.keys())}")
        else:
            # It's already a config dict
            self.provider_config = provider
            logger.debug(
                f"Using provider as config: {list(self.provider_config.keys())}"
            )

        # Try different locations for configuration
        # 1. Check additional_config first (common pattern)
        additional = self.provider_config.get("additional_config", {})
        self.project_id = additional.get("project_id")
        self.dataset_id = additional.get("dataset_id")
        self.table_name = additional.get("table_name")
        self.location = additional.get("location")
        self.credentials_json = additional.get("credentials")
        self.table_type = additional.get("table_type")

        # 2. If not found in additional_config, check root level
        if not self.project_id:
            self.project_id = self.provider_config.get("project_id")
            self.dataset_id = self.provider_config.get("dataset_id")
            self.table_name = self.provider_config.get("table_name")
            self.location = self.provider_config.get("location")
            self.credentials_json = self.provider_config.get("credentials")
            self.table_type = self.provider_config.get("table_type")

        # 3. If provider is an instance, try direct attributes
        if hasattr(provider, "project_id"):
            self.project_id = self.project_id or provider.project_id
            self.dataset_id = self.dataset_id or provider.dataset_id
            self.table_name = self.table_name or provider.table_name
            self.location = self.location or getattr(provider, "location", None)
            self.credentials_json = self.credentials_json or provider.credentials_json
            self.table_type = self.table_type or getattr(provider, "table_type", None)

        # Set defaults
        self.location = self.location or "US"
        self.table_type = self.table_type or "focus"

        # Log what we found
        logger.debug(
            f"Configuration found - project_id: {self.project_id}, dataset_id: {self.dataset_id}, "
            f"table_name: {self.table_name}, location: {self.location}, "
            f"credentials: {'present' if self.credentials_json else 'missing'}"
        )

        # Validate required fields
        if not all(
            [self.project_id, self.dataset_id, self.table_name, self.credentials_json]
        ):
            logger.error(
                f"Missing configuration - project_id: {bool(self.project_id)}, "
                f"dataset_id: {bool(self.dataset_id)}, table_name: {bool(self.table_name)}, "
                f"credentials: {bool(self.credentials_json)}"
            )
            logger.error(f"Provider config keys: {list(self.provider_config.keys())}")
            if additional:
                logger.error(f"Additional config keys: {list(additional.keys())}")
            raise ValueError("Missing required BigQuery configuration")

    def _get_credentials(self) -> service_account.Credentials:
        """Get service account credentials from JSON."""
        if isinstance(self.credentials_json, str):
            try:
                credentials_dict = json.loads(self.credentials_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in credentials: {e}") from e
        else:
            credentials_dict = self.credentials_json

        return service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                "https://www.googleapis.com/auth/bigquery",
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        )

    def _detect_table_type(self, client: bigquery.Client) -> str:
        """Auto-detect table type by checking schema with comprehensive FOCUS field detection."""
        try:
            table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_name}"
            table = client.get_table(table_ref)
            schema_fields = [field.name for field in table.schema]

            logger.debug(f"Table schema fields (first 20): {schema_fields[:20]}")

            # Check for FOCUS mandatory fields
            focus_mandatory_fields = [
                "BilledCost",
                "EffectiveCost",
                "ListCost",
                "ContractedCost",
                "BillingAccountId",
                "BillingAccountType",
                "BillingCurrency",
                "ServiceName",
                "ServiceCategory",
                "ProviderName",
                "PublisherName",
                "InvoiceIssuerName",
                "ChargeCategory",
                "ChargeDescription",
            ]

            focus_date_fields = [
                "ChargePeriodStart",
                "ChargePeriodEnd",
                "BillingPeriodStart",
                "BillingPeriodEnd",
            ]

            # Count FOCUS fields present
            focus_mandatory_present = sum(
                1 for field in focus_mandatory_fields if field in schema_fields
            )
            focus_date_present = sum(
                1 for field in focus_date_fields if field in schema_fields
            )

            # Check for standard export fields
            standard_fields = [
                "usage_start_time",
                "usage_end_time",
                "service.description",
                "sku.description",
                "project.id",
                "cost",
                "currency",
            ]

            standard_present = sum(
                1 for field in standard_fields if field in schema_fields
            )

            logger.info(
                f"FOCUS mandatory fields found: {focus_mandatory_present}/{len(focus_mandatory_fields)}"
            )
            logger.info(
                f"FOCUS date fields found: {focus_date_present}/{len(focus_date_fields)}"
            )
            logger.info(
                f"Standard export fields found: {standard_present}/{len(standard_fields)}"
            )

            # Decision logic
            if focus_mandatory_present >= 8 and focus_date_present >= 2:
                logger.info("Detected FOCUS 1.2 compliant table format")
                return "focus"
            elif focus_date_present >= 2:
                logger.info("Detected partial FOCUS table format")
                return "focus"
            elif standard_present >= 4:
                logger.info("Detected standard billing export format")
                return "standard"
            else:
                logger.warning(
                    f"Could not clearly detect table type. Available fields: {schema_fields[:10]}"
                )
                logger.warning("Defaulting to configured table type")
                return self.table_type

        except Exception as e:
            logger.error(f"Could not detect table type: {e}")
            return self.table_type

    def _get_billing_query(
        self, start_date: datetime, end_date: datetime, table_type: str
    ) -> str:
        """Get the appropriate query based on table type with enhanced FOCUS support."""
        table_ref = f"`{self.project_id}.{self.dataset_id}.{self.table_name}`"

        # Format dates
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        if table_type == "focus":
            # Enhanced FOCUS query with fallback logic
            return f"""
                SELECT *
                FROM {table_ref}
                WHERE (
                    -- Try ChargePeriodStart first (FOCUS 1.2 standard)
                    (ChargePeriodStart IS NOT NULL
                    AND ChargePeriodStart >= TIMESTAMP('{start_str}')
                    AND ChargePeriodStart < TIMESTAMP('{end_str}'))
                    OR
                    -- Fallback to BillingPeriodStart if ChargePeriodStart not available
                    (ChargePeriodStart IS NULL
                    AND BillingPeriodStart >= TIMESTAMP('{start_str}')
                    AND BillingPeriodStart < TIMESTAMP('{end_str}'))
                )
                ORDER BY
                    COALESCE(ChargePeriodStart, BillingPeriodStart)
                LIMIT 100000
            """
        else:
            # Standard billing export query with nested field support
            return f"""
                SELECT
                    *,
                    -- Extract nested fields for easier processing
                    service.description as service_description,
                    service.id as service_id,
                    sku.description as sku_description,
                    sku.id as sku_id,
                    project.id as project_id,
                    project.name as project_name,
                    location.location as location_name,
                    location.country as location_country,
                    location.region as location_region,
                    location.zone as location_zone
                FROM {table_ref}
                WHERE usage_start_time >= TIMESTAMP('{start_str}')
                AND usage_start_time < TIMESTAMP('{end_str}')
                ORDER BY usage_start_time
                LIMIT 100000
            """

    async def extract(
        self, source_config: dict[str, Any], start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Extract billing data from BigQuery with enhanced FOCUS support."""
        source_name = source_config.get("name", "bigquery_billing")

        logger.info(f"Starting BigQuery extraction for source: {source_name}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(
            f"Configuration: project={self.project_id}, dataset={self.dataset_id}, table={self.table_name}"
        )

        @dlt.resource(name=source_name, write_disposition="merge")
        def bigquery_resource():
            # Get credentials and create client
            credentials = self._get_credentials()
            client = bigquery.Client(
                project=self.project_id, credentials=credentials, location=self.location
            )

            # Auto-detect table type
            detected_type = self._detect_table_type(client)
            table_type = detected_type

            # Build and execute query
            query = self._get_billing_query(start_date, end_date, table_type)
            logger.info(f"Executing query for {table_type} table type")
            logger.debug(f"Query: {query[:300]}...")

            try:
                # Execute query
                query_job = client.query(query)

                # Validate results structure
                if not self._validate_query_results(query_job, table_type):
                    raise ValueError(
                        f"Query results validation failed for {table_type} table"
                    )

                # Re-execute for actual data extraction
                query_job = client.query(query)

                # Yield results
                count = 0
                for row in query_job:
                    if count == 0:
                        logger.debug(f"First row keys: {list(dict(row).keys())[:10]}")

                    # Convert row to dict
                    record = dict(row)

                    # Add metadata for downstream processing
                    record["_source_table_type"] = table_type
                    record["_extraction_timestamp"] = datetime.now(UTC).isoformat()

                    yield record

                    count += 1
                    if count % 1000 == 0:
                        logger.info(f"Processed {count} records...")

                logger.info(
                    f"Extracted {count} total records from BigQuery ({table_type} format)"
                )

            except Exception as e:
                logger.error(f"BigQuery extraction failed: {e}")
                raise

        # Return the DLT resource as a list of records
        records = []
        for record in bigquery_resource():
            records.append(record)

        return records

    def _validate_query_results(self, query_job, table_type: str) -> bool:
        """Validate that query returned expected data structure."""
        try:
            # Get first row to validate structure
            first_row = next(iter(query_job.result(max_results=1)), None)

            if not first_row:
                logger.warning("Query returned no results")
                return True  # Empty result is valid

            row_dict = dict(first_row)
            fields = list(row_dict.keys())

            if table_type == "focus":
                # Check for essential FOCUS fields
                required_focus = [
                    "BilledCost",
                    "EffectiveCost",
                    "ServiceName",
                    "ChargeCategory",
                ]
                missing = [f for f in required_focus if f not in fields]

                if missing:
                    logger.warning(f"FOCUS table missing expected fields: {missing}")
                    return False

            else:
                # Check for essential standard export fields
                required_standard = ["cost", "currency", "usage_start_time"]
                missing = [f for f in required_standard if f not in fields]

                if missing:
                    logger.warning(f"Standard table missing expected fields: {missing}")
                    return False

            logger.debug(f"Query validation passed for {table_type} table")
            return True

        except Exception as e:
            logger.error(f"Error validating query results: {e}")
            return False


# For backwards compatibility - if the extract stage expects a function
async def extract(
    provider_config: dict[str, Any],
    source_name: str,
    start_date: datetime,
    end_date: datetime,
) -> Iterator[dict[str, Any]]:
    """
    Extract function for backwards compatibility.

    Args:
        provider_config: Provider configuration dict
        source_name: Name of the source
        start_date: Start date for extraction
        end_date: End date for extraction

    Returns:
        Iterator of records
    """
    extractor = BigQueryExtractor(provider_config)
    return await extractor.extract(source_name, start_date, end_date)
