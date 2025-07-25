"""
AWS Provider Implementation
"""

import logging
from datetime import datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError

from providers.base import BaseProvider
from providers.registry import ProviderRegistry

from .auth import AWSAuth
from .mapper import AWSFocusMapper
from .sources import AWSSource

logger = logging.getLogger(__name__)


@ProviderRegistry.register(
    provider_type="aws",
    display_name="Amazon Web Services",
    description="AWS FOCUS 1.0 Data Export and legacy Cost and Usage Report (CUR)",
    supported_features=[
        "focus_1_0_export",
        "cost_and_usage_report",
        "detailed_billing",
        "resource_tags",
        "cost_allocation_tags",
        "savings_plans",
        "reserved_instances",
        "focus_format",
        "carbon_emissions",
        "cost_optimization_recommendations",
    ],
    required_config=["bucket_name", "report_name", "region"],
    optional_config=["report_prefix", "role_arn", "external_id", "export_type"],
    version="1.0.0",
    mapper_class=AWSFocusMapper,
    source_class=AWSSource,
    default_source_type="filesystem",
    default_config={
        "region": "us-east-1",
    },
    # Auth metadata from auth module
    supported_auth_methods=AWSAuth.SUPPORTED_METHODS,
    default_auth_method=AWSAuth.DEFAULT_METHOD,
    auth_fields=AWSAuth.AUTH_FIELDS,
    # Field descriptions
    field_descriptions={
        "bucket_name": "S3 bucket containing AWS exports or Cost and Usage Reports",
        "report_name": "Name of the Data Export or Cost and Usage Report",
        "report_prefix": "S3 prefix for export/report files",
        "region": "AWS region where the S3 bucket is located",
        "role_arn": "IAM role ARN for cross-account access",
        "external_id": "External ID for assuming IAM role",
        "export_type": "Type of AWS export (focus for FOCUS 1.0, legacy for traditional CUR)",
    },
    field_types={
        "bucket_name": "string",
        "report_name": "string",
        "report_prefix": "string",
        "region": "select",
        "role_arn": "string",
        "external_id": "string",
        "export_type": "select",
    },
    field_placeholders={
        "bucket_name": "narevfocusexport",
        "report_name": "MyCostExport",
        "report_prefix": "focus/",
        "region": "us-east-1",
        "role_arn": "arn:aws:iam::123456789012:role/CURAccessRole",
        "external_id": "unique-external-id",
        "export_type": "focus",
    },
    field_options={
        "region": [
            {"value": "us-east-1", "label": "US East (N. Virginia)"},
            {"value": "us-west-2", "label": "US West (Oregon)"},
            {"value": "eu-west-1", "label": "EU (Ireland)"},
            {"value": "eu-central-1", "label": "EU (Frankfurt)"},
            {"value": "ap-southeast-1", "label": "Asia Pacific (Singapore)"},
            {"value": "ap-northeast-1", "label": "Asia Pacific (Tokyo)"},
        ],
        "export_type": [
            {"value": "focus", "label": "FOCUS 1.0 Data Export (Recommended)"},
            {"value": "legacy", "label": "Legacy Cost and Usage Report (CUR)"},
        ],
    },
    standard_fields={
        "name": {
            "required": True,
            "type": "string",
            "pattern": "^[a-z0-9-_]+$",
            "placeholder": "aws-prod (lowercase, no spaces)",
            "description": "Unique identifier",
        },
        "display_name": {
            "required": False,
            "type": "string",
            "placeholder": "AWS Production",
            "description": "Human-readable name for the interface",
        },
    },
)
class AWSProvider(BaseProvider):
    """AWS FOCUS 1.0 Data Export and legacy Cost and Usage Report provider with flexible authentication."""

    def __init__(self, config: dict[str, Any]):
        """Initialize AWS provider."""
        super().__init__(config)

        # Get configuration
        self.bucket_name = self._get_config_value("bucket_name")
        self.report_name = self._get_config_value("report_name")
        self.report_prefix = self._get_config_value("report_prefix", "")
        self.region = self._get_config_value("region", "us-east-1")
        self.export_type = self._get_config_value(
            "export_type", "focus"
        )  # Default to FOCUS

        # Extract role configuration (can come from auth_config or additional_config)
        self.role_arn = self._get_role_arn()
        self.external_id = self._get_external_id()

        # Initialize auth handler
        self.auth_handler = AWSAuth(self.auth_config or {}, region=self.region)

        # Initialize AWS clients
        self._init_aws_clients()

        # Store source class from registry
        self.source_class = AWSSource

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Get config value from root or additional_config."""
        value = self.config.get(key)
        if value is None and "additional_config" in self.config:
            value = self.config["additional_config"].get(key)
        return value if value is not None else default

    def _get_role_arn(self) -> str | None:
        """Get role ARN from auth_config or additional_config."""
        # Check auth_config first
        if self.auth_config:
            # For multi-factor auth, check secondary config
            if self.auth_config.get("method") == "multi_factor":
                secondary = self.auth_config.get("secondary", {})
                if secondary.get("role_arn"):
                    return secondary["role_arn"]
            # Direct role_arn in auth_config
            if self.auth_config.get("role_arn"):
                return self.auth_config["role_arn"]

        # Fall back to additional_config
        return self._get_config_value("role_arn")

    def _get_external_id(self) -> str | None:
        """Get external ID from auth_config or additional_config."""
        # Check auth_config first
        if self.auth_config:
            # For multi-factor auth, check secondary config
            if self.auth_config.get("method") == "multi_factor":
                secondary = self.auth_config.get("secondary", {})
                if secondary.get("external_id"):
                    return secondary["external_id"]
            # Direct external_id in auth_config
            if self.auth_config.get("external_id"):
                return self.auth_config["external_id"]

        # Fall back to additional_config
        return self._get_config_value("external_id")

    def _init_aws_clients(self):
        """Initialize AWS clients with proper authentication."""
        try:
            # Get boto3 session from auth handler
            self.session = self.auth_handler.get_boto3_session()

            # Create S3 client
            self.s3_client = self.session.client("s3", region_name=self.region)

            # If we have role configuration, assume the role
            if self.role_arn:
                sts_client = self.session.client("sts", region_name=self.region)

                assume_role_params = {
                    "RoleArn": self.role_arn,
                    "RoleSessionName": "billing-analyzer-session",
                }

                if self.external_id:
                    assume_role_params["ExternalId"] = self.external_id

                response = sts_client.assume_role(**assume_role_params)
                credentials = response["Credentials"]

                # Create new session with assumed role credentials
                self.session = boto3.Session(
                    aws_access_key_id=credentials["AccessKeyId"],
                    aws_secret_access_key=credentials["SecretAccessKey"],
                    aws_session_token=credentials["SessionToken"],
                    region_name=self.region,
                )

                # Recreate S3 client with new credentials
                self.s3_client = self.session.client("s3", region_name=self.region)

        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise

    def test_connection(self) -> dict[str, Any]:
        """Test connection to AWS S3 and verify export/CUR access."""
        try:
            # Test S3 bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)

            # List objects in the report/export path
            prefix = (
                f"{self.report_prefix}{self.report_name}/"
                if self.report_prefix
                else f"{self.report_name}/"
            )
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=10
            )

            object_count = response.get("KeyCount", 0)

            # Detect file types to confirm export format
            file_types = set()
            if "Contents" in response:
                for obj in response["Contents"][:5]:  # Check first 5 files
                    if obj["Key"].endswith(".parquet"):
                        file_types.add("parquet")
                    elif obj["Key"].endswith(".csv") or obj["Key"].endswith(".csv.gz"):
                        file_types.add("csv")

            return {
                "success": True,
                "message": f"Successfully connected to AWS S3 ({self.export_type} export)",
                "details": {
                    "bucket": self.bucket_name,
                    "report_name": self.report_name,
                    "region": self.region,
                    "objects_found": object_count,
                    "role_assumed": bool(self.role_arn),
                    "export_type": self.export_type,
                    "file_types_found": list(file_types) if file_types else [],
                },
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            return {
                "success": False,
                "message": f"AWS connection failed: {error_code}",
                "details": {
                    "error": str(e),
                    "error_code": error_code,
                    "bucket": self.bucket_name,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "details": {"error": str(e), "type": type(e).__name__},
            }

    async def fetch_billing_data(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch billing data from S3."""
        # This is typically handled by the DLT source
        # Placeholder implementation
        return []

    def get_source_config(self) -> dict[str, Any]:
        """Get configuration for DLT source."""
        return {
            "provider_type": "aws",
            "bucket_name": self.bucket_name,
            "report_name": self.report_name,
            "report_prefix": self.report_prefix,
            "region": self.region,
            "export_type": self.export_type,
            "auth_config": self.auth_config,
            # Pass session for source to use
            "_session": self.session,
        }

    def get_sources(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Get AWS FOCUS 1.0 or legacy CUR data sources for the date range.

        Args:
            start_date: Start date for data extraction
            end_date: End date for data extraction

        Returns:
            List of source configurations
        """
        if self.source_class:
            source = self.source_class(provider=self)
            return source.get_sources(start_date, end_date)

        logger.warning("No source class registered for AWS provider")
        return []

    def get_auth_method(self) -> str:
        """Get the authentication method being used."""
        if not self.auth_config:
            return "default"
        return self.auth_config.get("method", "unknown")

    def get_auth(self) -> None:
        """AWS uses boto3 session, no auth object needed for DLT."""
        return None

    def get_paginator(self) -> None:
        """AWS CUR files are processed differently, no paginator needed."""
        return None

    def get_filesystem_config(self) -> dict[str, Any]:
        """Get filesystem configuration for sources."""
        # Build S3 URL
        bucket_url = f"s3://{self.bucket_name}"
        if self.report_prefix:
            bucket_url += f"/{self.report_prefix.strip('/')}"
        if self.report_name:
            bucket_url += f"/{self.report_name.strip('/')}"

        # Build credentials config based on auth method
        credentials = {}

        if self.auth_config and self.auth_config.get("method") == "multi_factor":
            primary = self.auth_config.get("primary", {})

            if primary.get("access_key_id") and primary.get("secret_access_key"):
                credentials = {
                    "aws_access_key_id": primary["access_key_id"],
                    "aws_secret_access_key": primary["secret_access_key"],
                }
                if primary.get("session_token"):
                    credentials["aws_session_token"] = primary["session_token"]

            # Handle role assumption
            secondary = self.auth_config.get("secondary", {})
            if secondary.get("role_arn"):
                credentials["role_arn"] = secondary["role_arn"]
                if secondary.get("external_id"):
                    credentials["external_id"] = secondary["external_id"]

        return {"bucket_url": bucket_url, **credentials}
