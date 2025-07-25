"""
GCP Provider Implementation - Updated for flexible authentication
"""

import logging
from datetime import datetime
from typing import Any

from providers.base import BaseProvider
from providers.registry import ProviderRegistry

from .auth import GCPAuth
from .mapper import GCPFocusMapper
from .sources import GCPSource

logger = logging.getLogger(__name__)


@ProviderRegistry.register(
    provider_type="gcp",
    display_name="Google Cloud Platform",
    description="GCP billing",
    supported_features=[
        "bigquery_export",
        "focus_format",
        "cost_breakdown",
        "resource_hierarchy",
        "labels_and_tags",
    ],
    required_config=["dataset_id", "table_name"],
    optional_config=["location"],
    version="1.0.0",
    mapper_class=GCPFocusMapper,
    source_class=GCPSource,
    default_source_type="bigquery",
    default_config={"location": "US"},
    # Auth metadata from auth module
    supported_auth_methods=GCPAuth.SUPPORTED_METHODS,
    default_auth_method=GCPAuth.DEFAULT_METHOD,
    auth_fields=GCPAuth.AUTH_FIELDS,
    # Field descriptions
    field_descriptions={
        "project_id": "GCP project ID containing the BigQuery dataset",
        "dataset_id": "BigQuery dataset ID with billing export",
        "table_name": "Table name containing billing data",
        "location": "BigQuery dataset location",
    },
    field_types={
        "dataset_id": "string",
        "table_name": "string",
        "location": "select",
    },
    field_placeholders={
        "dataset_id": "billing_export",
        "table_name": "gcp_billing_export_v1_01AB23_456789_ABCDEF",
        "location": "US",
    },
    field_options={
        "location": [
            # Multi-regional locations
            {"value": "US", "label": "United States (multi-regional)"},
            {"value": "EU", "label": "European Union (multi-regional)"},
            # Americas
            {"value": "us-central1", "label": "Iowa (us-central1)"},
            {"value": "us-east1", "label": "South Carolina (us-east1)"},
            {"value": "us-east4", "label": "Northern Virginia (us-east4)"},
            {"value": "us-west1", "label": "Oregon (us-west1)"},
            {"value": "us-west2", "label": "Los Angeles (us-west2)"},
            {"value": "us-west3", "label": "Salt Lake City (us-west3)"},
            {"value": "us-west4", "label": "Las Vegas (us-west4)"},
            {
                "value": "northamerica-northeast1",
                "label": "Montreal (northamerica-northeast1)",
            },
            {
                "value": "northamerica-northeast2",
                "label": "Toronto (northamerica-northeast2)",
            },
            {"value": "southamerica-east1", "label": "São Paulo (southamerica-east1)"},
            {"value": "southamerica-west1", "label": "Santiago (southamerica-west1)"},
            # Europe
            {"value": "europe-central2", "label": "Warsaw (europe-central2)"},
            {"value": "europe-north1", "label": "Finland (europe-north1)"},
            {"value": "europe-west1", "label": "Belgium (europe-west1)"},
            {"value": "europe-west2", "label": "London (europe-west2)"},
            {"value": "europe-west3", "label": "Frankfurt (europe-west3)"},
            {"value": "europe-west4", "label": "Netherlands (europe-west4)"},
            {"value": "europe-west6", "label": "Zurich (europe-west6)"},
            # Asia Pacific
            {"value": "asia-east1", "label": "Taiwan (asia-east1)"},
            {"value": "asia-east2", "label": "Hong Kong (asia-east2)"},
            {"value": "asia-northeast1", "label": "Tokyo (asia-northeast1)"},
            {"value": "asia-northeast2", "label": "Osaka (asia-northeast2)"},
            {"value": "asia-northeast3", "label": "Seoul (asia-northeast3)"},
            {"value": "asia-south1", "label": "Mumbai (asia-south1)"},
            {"value": "asia-south2", "label": "Delhi (asia-south2)"},
            {"value": "asia-southeast1", "label": "Singapore (asia-southeast1)"},
            {"value": "asia-southeast2", "label": "Jakarta (asia-southeast2)"},
            {"value": "australia-southeast1", "label": "Sydney (australia-southeast1)"},
            {
                "value": "australia-southeast2",
                "label": "Melbourne (australia-southeast2)",
            },
        ]
    },
    standard_fields={
        "name": {
            "required": True,
            "type": "string",
            "pattern": "^[a-z0-9-_]+$",
            "placeholder": "gcp-prod (lowercase, no spaces)",
            "description": "Unique identifier",
        },
        "display_name": {
            "required": False,
            "type": "string",
            "placeholder": "GCP Production",
            "description": "Human-readable name for the interface",
        },
    },
)
class GCPProvider(BaseProvider):
    """GCP billing data provider with flexible authentication."""

    def __init__(self, config: dict[str, Any]):
        """Initialize GCP provider."""
        super().__init__(config)

        # Initialize auth handler
        self.auth_handler = GCPAuth(self.auth_config or {})
        self.project_id = self.auth_handler.get_project_id()
        if not self.project_id:
            raise ValueError("project_id not found in service account credentials")

        # Get configuration from additional_config
        additional = config.get("additional_config", {})
        self.dataset_id = additional.get("dataset_id") or config.get("dataset_id")
        self.table_name = additional.get("table_name") or config.get("table_name")
        self.location = additional.get("location", "US") or config.get("location", "US")

        # Validate required fields
        if not all([self.project_id, self.dataset_id, self.table_name]):
            raise ValueError(
                "Missing required GCP configuration: project_id, dataset_id, table_name"
            )

        # Initialize BigQuery client
        self._init_bigquery_client()

        # Store source class from registry
        self.source_class = GCPSource

    def _init_bigquery_client(self):
        """Initialize BigQuery client with proper authentication."""
        try:
            # Use auth handler to create client
            self.client = self.auth_handler.create_bigquery_client(
                project_id=self.project_id, location=self.location
            )
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise

    async def fetch_billing_data(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch billing data from BigQuery."""
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.{self.table_name}`
        WHERE export_time >= TIMESTAMP('{start_date.isoformat()}')
          AND export_time < TIMESTAMP('{end_date.isoformat()}')
        ORDER BY export_time DESC
        """

        try:
            query_job = self.client.query(query)
            results = query_job.result()

            billing_data = []
            for row in results:
                billing_data.append(dict(row))

            logger.info(
                f"Fetched {len(billing_data)} billing records from GCP BigQuery"
            )
            return billing_data

        except Exception as e:
            logger.error(f"Failed to fetch GCP billing data: {e}")
            raise

    def get_source_config(self) -> dict[str, Any]:
        """Get configuration for DLT source."""
        return {
            "provider_type": "gcp",
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "table_name": self.table_name,
            "location": self.location,
            "auth_config": self.auth_config,
            # Pass auth handler for source to use
            "_auth_handler": self.auth_handler,
        }

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get GCP data sources for the date range.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations
        """
        if self.source_class:
            source = self.source_class()
            return source.get_sources(start_date, end_date)

        logger.warning("No source class registered for GCP provider")
        return []

    def test_connection(self) -> dict[str, Any]:
        """Test connection to BigQuery and verify permissions."""
        try:
            # Test 1: Can we access the dataset?
            dataset_ref = self.client.dataset(self.dataset_id, project=self.project_id)
            self.client.get_dataset(dataset_ref)

            # Test 2: Can we access the table?
            table_ref = dataset_ref.table(self.table_name)
            table = self.client.get_table(table_ref)

            # Test 3: Can we query the table?
            query = f"""
                SELECT COUNT(*) as count
                FROM `{self.project_id}.{self.dataset_id}.{self.table_name}`
                LIMIT 1
            """

            query_job = self.client.query(query)
            results = list(query_job)

            row_count = results[0]["count"] if results else 0

            return {
                "success": True,
                "message": "Successfully connected to BigQuery",
                "details": {
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "table_name": self.table_name,
                    "location": self.location,
                    "row_count": row_count,
                    "table_size_mb": table.num_bytes / (1024 * 1024)
                    if table.num_bytes
                    else 0,
                    "auth_method": self.get_auth_method(),
                },
            }

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            # Provide helpful error messages
            if "404" in error_msg:
                if "dataset" in error_msg.lower():
                    message = f"Dataset '{self.dataset_id}' not found in project '{self.project_id}'"
                elif "table" in error_msg.lower():
                    message = f"Table '{self.table_name}' not found in dataset '{self.dataset_id}'"
                else:
                    message = "Resource not found"
            elif "403" in error_msg:
                message = "Permission denied - check service account permissions"
            elif "401" in error_msg:
                message = "Authentication failed - check credentials"
            else:
                message = f"Connection test failed: {error_msg}"

            return {
                "success": False,
                "message": message,
                "details": {
                    "error": error_msg,
                    "error_type": error_type,
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "table_name": self.table_name,
                    "auth_method": self.get_auth_method(),
                },
            }

    def get_auth_method(self) -> str:
        """Get the authentication method being used."""
        if not self.auth_config:
            return "default"
        return self.auth_config.get("method", "unknown")

    def get_bigquery_config(self) -> dict[str, Any]:
        """Get BigQuery configuration for sources."""
        return {
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "table_name": self.table_name,
            "location": self.location,
        }

    def get_credentials(self) -> Any:
        """Get Google Cloud credentials for use by sources."""
        # Return the auth handler's credentials
        return self.auth_handler.get_credentials()

    def get_credentials_json(self) -> dict[str, Any]:
        """Get service account credentials JSON for BigQuery client."""
        return self.auth_handler.auth_config.get("credentials", {})

    @property
    def credentials_json(self) -> dict[str, Any]:
        """Compatibility property for BigQueryExtractor."""
        return self.get_credentials_json()
