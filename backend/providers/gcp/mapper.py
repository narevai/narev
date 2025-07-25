"""
GCP to FOCUS 1.2 Mapper
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from focus.mappers.base import (
    AccountInfo,
    BaseFocusMapper,
    ChargeInfo,
    CostInfo,
    LocationInfo,
    ResourceInfo,
    ServiceInfo,
    SkuInfo,
    TimeInfo,
    UsageInfo,
)

logger = logging.getLogger(__name__)


class GCPFocusMapper(BaseFocusMapper):
    """
    GCP billing data to FOCUS 1.2 mapper.

    Handles dual input formats:
    1. FOCUS view data (PascalCase, like Azure)
    2. Standard GCP billing export (native GCP format)
    """

    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate GCP billing record structure."""
        if not isinstance(record, dict) or not record:
            return False

        # Check for FOCUS view indicators (PascalCase)
        focus_indicators = [
            "BilledCost",
            "EffectiveCost",
            "ChargePeriodStart",
            "ServiceCategory",
        ]
        if any(field in record for field in focus_indicators):
            return True

        # Check for standard GCP billing indicators
        gcp_indicators = ["cost", "service", "project", "usage_start_time"]
        return any(field in record for field in gcp_indicators)

    def _get_costs(self, record: dict[str, Any]) -> CostInfo:
        """Extract cost information from GCP record."""
        if self._is_focus_view_data(record):
            # FOCUS view format
            return CostInfo(
                billed_cost=self._get_gcp_decimal(record, "BilledCost"),
                effective_cost=self._get_gcp_decimal(record, "EffectiveCost"),
                list_cost=self._get_gcp_decimal(record, "ListCost"),
                contracted_cost=self._get_gcp_decimal(record, "ContractedCost"),
                currency=self._get_gcp_value(record, "BillingCurrency") or "USD",
            )
        else:
            # Standard GCP billing format
            cost = self._get_gcp_decimal(record, "cost")
            currency = self._get_gcp_value(record, "currency") or "USD"

            return CostInfo(
                billed_cost=cost,
                effective_cost=cost,
                list_cost=cost,
                contracted_cost=cost,
                currency=currency,
            )

    def _get_account_info(self, record: dict[str, Any]) -> AccountInfo:
        """Extract account information from GCP record."""
        if self._is_focus_view_data(record):
            # FOCUS view format
            billing_account_id = self._get_gcp_value(record, "BillingAccountId")
            billing_account_name = (
                self._get_gcp_value(record, "BillingAccountName") or billing_account_id
            )
            sub_account_id = self._get_gcp_value(record, "SubAccountId")
            sub_account_name = self._get_gcp_value(record, "SubAccountName")

            return AccountInfo(
                billing_account_id=billing_account_id or "unknown",
                billing_account_name=billing_account_name or "Unknown Account",
                billing_account_type="BillingAccount",
                sub_account_id=sub_account_id,
                sub_account_name=sub_account_name,
                sub_account_type="Project" if sub_account_id else None,
            )
        else:
            # Standard GCP format
            project = record.get("project", {})
            billing_account_id = self._get_gcp_value(record, "billing_account_id")

            if isinstance(project, dict):
                project_id = project.get("id")
                project_name = project.get("name")
            else:
                project_id = str(project) if project else None
                project_name = None

            return AccountInfo(
                billing_account_id=billing_account_id or project_id or "unknown",
                billing_account_name=project_name
                or billing_account_id
                or "Unknown Account",
                billing_account_type="BillingAccount",
                sub_account_id=project_id,
                sub_account_name=project_name,
                sub_account_type="Project" if project_id else None,
            )

    def _get_time_periods(self, record: dict[str, Any]) -> TimeInfo:
        """Extract time periods from GCP record."""
        if self._is_focus_view_data(record):
            # FOCUS view format
            charge_start = self._get_gcp_datetime(record, "ChargePeriodStart")
            charge_end = self._get_gcp_datetime(record, "ChargePeriodEnd")
            billing_start = self._get_gcp_datetime(record, "BillingPeriodStart")
            billing_end = self._get_gcp_datetime(record, "BillingPeriodEnd")
        else:
            # Standard GCP format
            charge_start = self._get_gcp_datetime(record, "usage_start_time")
            charge_end = self._get_gcp_datetime(record, "usage_end_time")
            billing_start = None
            billing_end = None

        # Fallback if dates are missing
        if not charge_start or not charge_end:
            now = datetime.now(UTC)
            charge_start = charge_start or now
            charge_end = charge_end or now

        return TimeInfo(
            charge_period_start=charge_start,
            charge_period_end=charge_end,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
        )

    def _get_service_info(self, record: dict[str, Any]) -> ServiceInfo:
        """Extract service information from GCP record."""
        if self._is_focus_view_data(record):
            # FOCUS view format
            service_name = (
                self._get_gcp_value(record, "ServiceName") or "Google Cloud Service"
            )
            service_category = self._get_gcp_value(
                record, "ServiceCategory"
            ) or self._map_gcp_service_category(service_name)

            return ServiceInfo(
                service_name=service_name,
                service_category=service_category,
                provider_name=self._get_gcp_value(record, "ProviderName")
                or "Google Cloud Platform",
                publisher_name=self._get_gcp_value(record, "PublisherName") or "Google",
                invoice_issuer_name=self._get_gcp_value(record, "InvoiceIssuerName")
                or "Google Cloud",
                service_subcategory=self._get_gcp_value(record, "ServiceSubcategory"),
            )
        else:
            # Standard GCP format
            service = record.get("service", {})
            if isinstance(service, dict):
                service_name = (
                    service.get("description")
                    or service.get("id")
                    or "Google Cloud Service"
                )
            else:
                service_name = str(service) if service else "Google Cloud Service"

            service_category = self._map_gcp_service_category(service_name)

            return ServiceInfo(
                service_name=service_name,
                service_category=service_category,
                provider_name="Google Cloud Platform",
                publisher_name="Google",
                invoice_issuer_name="Google Cloud",
                service_subcategory=self._get_gcp_service_subcategory(service_name),
            )

    def _get_charge_info(self, record: dict[str, Any]) -> ChargeInfo:
        """Extract charge information from GCP record."""
        if self._is_focus_view_data(record):
            # FOCUS view format
            return ChargeInfo(
                charge_category=self._get_gcp_value(
                    record, "ChargeCategory"
                ).capitalize()
                or "Usage",
                charge_description=self._get_gcp_value(record, "ChargeDescription")
                or "Google Cloud Usage",
                charge_class=self._get_gcp_value(record, "ChargeClass"),
                charge_frequency=self._get_gcp_value(record, "ChargeFrequency"),
                pricing_quantity=self._get_gcp_decimal(record, "PricingQuantity"),
                pricing_unit=self._get_gcp_value(record, "PricingUnit"),
            )
        else:
            # Standard GCP format - build description
            description = self._build_gcp_charge_description(record)

            # Extract usage info
            usage = record.get("usage", {})
            if isinstance(usage, dict):
                pricing_quantity = self._get_gcp_decimal(usage, "amount")
                pricing_unit = self._get_gcp_value(usage, "unit")
            else:
                pricing_quantity = None
                pricing_unit = None

            return ChargeInfo(
                charge_category="Usage",
                charge_description=description,
                charge_frequency="Usage-Based",
                pricing_quantity=pricing_quantity,
                pricing_unit=pricing_unit,
            )

    def _get_resource_info(self, record: dict[str, Any]) -> ResourceInfo | None:
        """Extract resource information from GCP record."""
        if self._is_focus_view_data(record):
            resource_id = self._get_gcp_value(record, "ResourceId")
            if not resource_id:
                return None

            return ResourceInfo(
                resource_id=resource_id,
                resource_name=self._get_gcp_value(record, "ResourceName")
                or resource_id,
                resource_type=self._get_gcp_value(record, "ResourceType"),
            )
        else:
            # Standard GCP format
            resource = record.get("resource", {})
            if not isinstance(resource, dict):
                return None

            resource_id = resource.get("id")
            if not resource_id:
                return None

            return ResourceInfo(
                resource_id=resource_id,
                resource_name=resource.get("name") or resource_id,
                resource_type=resource.get("type"),
            )

    def _get_location_info(self, record: dict[str, Any]) -> LocationInfo | None:
        """Extract location information from GCP record."""
        if self._is_focus_view_data(record):
            region_id = self._get_gcp_value(record, "RegionId")
            region_name = self._get_gcp_value(record, "RegionName")
            availability_zone = self._get_gcp_value(record, "AvailabilityZone")
        else:
            # Standard GCP format
            location = record.get("location", {})
            if isinstance(location, dict):
                region_id = location.get("region")
                region_name = location.get("region")  # GCP often uses same for both
                availability_zone = location.get("zone")
            elif "location" in record:
                region_id = record["location"]
                region_name = record["location"]
                availability_zone = None
            else:
                return None

        if not any([region_id, region_name, availability_zone]):
            return None

        return LocationInfo(
            region_id=region_id,
            region_name=region_name,
            availability_zone=availability_zone,
        )

    def _get_sku_info(self, record: dict[str, Any]) -> SkuInfo | None:
        """Extract SKU information from GCP record."""
        if self._is_focus_view_data(record):
            sku_id = self._get_gcp_value(record, "SkuId")
            if not sku_id:
                return None

            return SkuInfo(
                sku_id=sku_id,
                sku_price_id=self._get_gcp_value(record, "SkuPriceId"),
                sku_price_details=self._get_gcp_value(record, "SkuPriceDetails"),
                list_unit_price=self._get_gcp_decimal(record, "ListUnitPrice"),
                contracted_unit_price=self._get_gcp_decimal(
                    record, "ContractedUnitPrice"
                ),
            )
        else:
            # Standard GCP format
            sku = record.get("sku", {})
            if not isinstance(sku, dict):
                return None

            sku_id = sku.get("id")
            if not sku_id:
                return None

            return SkuInfo(sku_id=sku_id, sku_price_details=sku.get("description"))

    def _get_usage_info(self, record: dict[str, Any]) -> UsageInfo | None:
        """Extract usage information from GCP record."""
        if self._is_focus_view_data(record):
            consumed_quantity = self._get_gcp_decimal(record, "ConsumedQuantity")
            if consumed_quantity is None:
                return None

            return UsageInfo(
                consumed_quantity=consumed_quantity,
                consumed_unit=self._get_gcp_value(record, "ConsumedUnit"),
            )
        else:
            # Standard GCP format
            usage = record.get("usage", {})
            if isinstance(usage, dict):
                consumed_quantity = self._get_gcp_decimal(usage, "amount")
                consumed_unit = self._get_gcp_value(usage, "unit")

                if consumed_quantity is not None:
                    return UsageInfo(
                        consumed_quantity=consumed_quantity, consumed_unit=consumed_unit
                    )

        return None

    def _get_tags(self, record: dict[str, Any]) -> dict[str, str] | None:
        """Extract tags from GCP record."""
        tags = {}

        if self._is_focus_view_data(record):
            # FOCUS view format
            if "Tags" in record and isinstance(record["Tags"], dict):
                for tag_key, tag_value in record["Tags"].items():
                    if tag_value is not None:
                        tags[tag_key] = str(tag_value)
        else:
            # Standard GCP format - labels
            labels = record.get("labels")
            if isinstance(labels, dict):
                for key, value in labels.items():
                    if value is not None:
                        tags[key] = str(value)
            elif isinstance(labels, list):
                # Convert GCP label list to dict
                for label in labels:
                    if isinstance(label, dict):
                        if "key" in label and "value" in label:
                            tags[label["key"]] = str(label["value"])

        return tags if tags else None

    def _get_provider_extensions(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Extract GCP-specific data for x_provider_data field."""
        extensions = {}

        # GCP-specific fields to preserve
        gcp_fields = [
            "export_time",
            "cost_type",
            "adjustment_info",
            "system_labels",
            "credits",
            "invoice",
            "cost_at_list",
        ]

        for field in gcp_fields:
            value = record.get(field)
            if value is not None:
                extensions[field] = value

        # Add source table type if available
        if "_source_table_type" in record:
            extensions["source_table_type"] = record["_source_table_type"]

        return extensions if extensions else None

    # GCP-specific helper methods

    def _is_focus_view_data(self, record: dict[str, Any]) -> bool:
        """Detect if record is from FOCUS view or standard billing export."""
        focus_indicators = [
            "BilledCost",
            "EffectiveCost",
            "ChargePeriodStart",
            "BillingAccountId",
        ]
        return any(field in record for field in focus_indicators)

    def _get_gcp_value(self, record: dict, field_name: str) -> str | None:
        """Get string value from GCP record."""
        value = record.get(field_name)
        return str(value).strip() if value is not None else None

    def _get_gcp_decimal(self, record: dict, field_name: str) -> Decimal:
        """Get decimal value from GCP record."""
        value = record.get(field_name)
        return self.safe_decimal(value)

    def _get_gcp_datetime(self, record: dict, field_name: str) -> datetime | None:
        """Get datetime value from GCP record."""
        value = record.get(field_name)
        return self.safe_datetime(value)

    def _build_gcp_charge_description(self, record: dict[str, Any]) -> str:
        """Build charge description from GCP record."""
        parts = []

        # Service description
        service = record.get("service", {})
        if isinstance(service, dict) and service.get("description"):
            parts.append(service["description"])

        # SKU description
        sku = record.get("sku", {})
        if isinstance(sku, dict) and sku.get("description"):
            parts.append(sku["description"])

        # Fallback
        if not parts:
            parts.append("Google Cloud service charge")

        return " - ".join(parts)

    def _map_gcp_service_category(self, service_name: str) -> str:
        """Map GCP service name to FOCUS service category."""
        if not service_name:
            return "Other"

        service_lower = service_name.lower()

        # AI and Machine Learning
        if any(
            term in service_lower
            for term in [
                "ai platform",
                "vertex",
                "automl",
                "vision",
                "natural language",
                "translation",
                "speech",
                "dialogflow",
                "recommendations",
            ]
        ):
            return "AI and Machine Learning"

        # Analytics
        elif any(
            term in service_lower
            for term in [
                "bigquery",
                "dataflow",
                "dataproc",
                "pubsub",
                "datastore",
                "analytics",
                "data studio",
                "looker",
            ]
        ):
            return "Analytics"

        # Compute
        elif any(
            term in service_lower
            for term in [
                "compute engine",
                "kubernetes",
                "gke",
                "app engine",
                "cloud run",
                "cloud functions",
                "compute",
                "instances",
            ]
        ):
            return "Compute"

        # Databases
        elif any(
            term in service_lower
            for term in [
                "cloud sql",
                "firestore",
                "bigtable",
                "spanner",
                "memorystore",
                "database",
                "sql",
            ]
        ):
            return "Databases"

        # Developer Tools
        elif any(
            term in service_lower
            for term in [
                "cloud build",
                "source repositories",
                "cloud shell",
                "deployment manager",
                "container registry",
                "artifact registry",
            ]
        ):
            return "Developer Tools"

        # Management and Governance
        elif any(
            term in service_lower
            for term in [
                "cloud logging",
                "cloud monitoring",
                "cloud trace",
                "cloud profiler",
                "resource manager",
                "iam",
                "logging",
                "monitoring",
            ]
        ):
            return "Management and Governance"

        # Networking
        elif any(
            term in service_lower
            for term in [
                "vpc",
                "cloud load balancing",
                "cloud cdn",
                "cloud dns",
                "cloud nat",
                "network",
                "load balancing",
                "cdn",
            ]
        ):
            return "Networking"

        # Security, Identity, and Compliance
        elif any(
            term in service_lower
            for term in [
                "cloud kms",
                "cloud iam",
                "security",
                "identity",
                "access management",
                "binary authorization",
                "cloud security scanner",
            ]
        ):
            return "Security, Identity, and Compliance"

        # Storage
        elif any(
            term in service_lower
            for term in [
                "cloud storage",
                "persistent disk",
                "filestore",
                "cloud backup",
                "storage",
                "disk",
            ]
        ):
            return "Storage"

        return "Other"

    def _get_gcp_service_subcategory(self, service_name: str) -> str | None:
        """Get GCP service subcategory."""
        if not service_name:
            return None

        service_lower = service_name.lower()

        if "compute engine" in service_lower:
            return "Virtual Machines"
        elif "cloud storage" in service_lower:
            return "Object Storage"
        elif "cloud functions" in service_lower:
            return "Serverless Functions"
        elif "gke" in service_lower or "kubernetes" in service_lower:
            return "Container Orchestration"
        elif "bigquery" in service_lower:
            return "Data Warehouse"
        elif "cloud sql" in service_lower:
            return "Managed Database"

        return None
