"""
Azure to FOCUS 1.2 Mapper
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from focus.mappers.base import (
    AccountInfo,
    BaseFocusMapper,
    ChargeInfo,
    CommitmentInfo,
    CostInfo,
    LocationInfo,
    ResourceInfo,
    ServiceInfo,
    SkuInfo,
    TimeInfo,
    UsageInfo,
)

logger = logging.getLogger(__name__)


class AzureFocusMapper(BaseFocusMapper):
    """
    Azure FOCUS export to FOCUS 1.2 mapper.

    Simplest implementation since Azure already provides FOCUS-compliant data.

    Main task: PascalCase -> snake_case mapping + Azure-specific service categorization.
    """

    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate Azure FOCUS record structure."""
        if not isinstance(record, dict) or not record:
            return False

        # Check for essential Azure FOCUS fields
        required_indicators = [
            "BilledCost",
            "EffectiveCost",
            "ServiceName",
            "ChargeCategory",
        ]
        return any(field in record for field in required_indicators)

    def _get_costs(self, record: dict[str, Any]) -> CostInfo:
        """Extract cost information from Azure FOCUS record."""
        return CostInfo(
            billed_cost=self._get_azure_decimal(record, "BilledCost"),
            effective_cost=self._get_azure_decimal(record, "EffectiveCost"),
            list_cost=self._get_azure_decimal(record, "ListCost"),
            contracted_cost=self._get_azure_decimal(record, "ContractedCost"),
            currency=self._get_azure_value(record, "BillingCurrency") or "USD",
        )

    def _get_account_info(self, record: dict[str, Any]) -> AccountInfo:
        """Extract account information from Azure FOCUS record."""
        billing_account_id = self._get_azure_value(record, "BillingAccountId")
        billing_account_name = (
            self._get_azure_value(record, "BillingAccountName") or billing_account_id
        )

        sub_account_id = self._get_azure_value(record, "SubAccountId")
        sub_account_name = self._get_azure_value(record, "SubAccountName")

        return AccountInfo(
            billing_account_id=billing_account_id or "unknown",
            billing_account_name=billing_account_name or "Unknown Account",
            billing_account_type=self._get_azure_value(record, "BillingAccountType")
            or "BillingAccount",
            sub_account_id=sub_account_id,
            sub_account_name=sub_account_name,
            sub_account_type=self._get_azure_value(record, "SubAccountType")
            or ("Subscription" if sub_account_id else None),
        )

    def _get_time_periods(self, record: dict[str, Any]) -> TimeInfo:
        """Extract time periods from Azure FOCUS record."""
        charge_start = self._get_azure_datetime(record, "ChargePeriodStart")
        charge_end = self._get_azure_datetime(record, "ChargePeriodEnd")
        billing_start = self._get_azure_datetime(record, "BillingPeriodStart")
        billing_end = self._get_azure_datetime(record, "BillingPeriodEnd")

        # Fallback if dates are missing
        if not charge_start or not charge_end:
            now = datetime.now()
            charge_start = charge_start or now
            charge_end = charge_end or now

        return TimeInfo(
            charge_period_start=charge_start,
            charge_period_end=charge_end,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
        )

    def _get_service_info(self, record: dict[str, Any]) -> ServiceInfo:
        """Extract service information from Azure FOCUS record."""
        service_name = self._get_azure_value(record, "ServiceName") or "Azure Service"

        # Use provided service category or determine from service name
        azure_service_category = self._get_azure_value(record, "ServiceCategory")

        # Fix Azure service category to match FOCUS 1.2 format
        if azure_service_category == "AI + Machine Learning":
            service_category = "AI and Machine Learning"
        elif azure_service_category == "Database":
            service_category = "Databases"  # FOCUS uses plural form
        elif not azure_service_category:
            # If no service category provided, try to map from Azure charge_class
            azure_charge_class = self._get_azure_value(record, "ChargeClass")
            service_category = self._map_azure_charge_class_to_service_category(
                azure_charge_class
            ) or self._determine_azure_service_category(service_name)
        else:
            service_category = azure_service_category

        return ServiceInfo(
            service_name=service_name,
            service_category=service_category,
            provider_name=self._get_azure_value(record, "ProviderName")
            or "Microsoft Azure",
            publisher_name=self._get_azure_value(record, "PublisherName")
            or "Microsoft",
            invoice_issuer_name=self._get_azure_value(record, "InvoiceIssuerName")
            or "Microsoft Azure",
            service_subcategory=self._get_azure_value(record, "ServiceSubcategory"),
        )

    def _get_charge_info(self, record: dict[str, Any]) -> ChargeInfo:
        """Extract charge information from Azure FOCUS record."""
        # Azure provides non-FOCUS compliant charge_class values
        # FOCUS 1.2 only accepts "Correction" or None for charge_class
        azure_charge_class = self._get_azure_value(record, "ChargeClass")
        focus_charge_class = None
        if azure_charge_class == "Correction":
            focus_charge_class = azure_charge_class
        # All other Azure charge classes (Database, Storage, Compute, Network) are ignored

        return ChargeInfo(
            charge_category=self._get_azure_value(record, "ChargeCategory") or "Usage",
            charge_description=self._get_azure_value(record, "ChargeDescription")
            or "Azure Usage Charge",
            charge_class=focus_charge_class,
            charge_frequency=self._get_azure_value(record, "ChargeFrequency"),
            pricing_quantity=self._get_azure_decimal(record, "PricingQuantity"),
            pricing_unit=self._get_azure_value(record, "PricingUnit"),
        )

    def _get_resource_info(self, record: dict[str, Any]) -> ResourceInfo | None:
        """Extract resource information from Azure FOCUS record."""
        resource_id = self._get_azure_value(record, "ResourceId")
        if not resource_id:
            return None

        return ResourceInfo(
            resource_id=resource_id,
            resource_name=self._get_azure_value(record, "ResourceName") or resource_id,
            resource_type=self._get_azure_value(record, "ResourceType"),
        )

    def _get_location_info(self, record: dict[str, Any]) -> LocationInfo | None:
        """Extract location information from Azure FOCUS record."""
        region_id = self._get_azure_value(record, "RegionId")
        region_name = self._get_azure_value(record, "RegionName")
        availability_zone = self._get_azure_value(record, "AvailabilityZone")

        if not any([region_id, region_name, availability_zone]):
            return None

        return LocationInfo(
            region_id=region_id,
            region_name=region_name,
            availability_zone=availability_zone,
        )

    def _get_sku_info(self, record: dict[str, Any]) -> SkuInfo | None:
        """Extract SKU information from Azure FOCUS record."""
        sku_id = self._get_azure_value(record, "SkuId")
        if not sku_id:
            return None

        return SkuInfo(
            sku_id=sku_id,
            sku_price_id=self._get_azure_value(record, "SkuPriceId"),
            sku_meter=self._get_azure_value(record, "SkuMeter"),
            sku_price_details=self._get_azure_value(record, "SkuPriceDetails"),
            list_unit_price=self._get_azure_decimal(record, "ListUnitPrice"),
            contracted_unit_price=self._get_azure_decimal(
                record, "ContractedUnitPrice"
            ),
        )

    def _get_commitment_info(self, record: dict[str, Any]) -> CommitmentInfo | None:
        """Extract commitment discount information from Azure FOCUS record."""
        commitment_id = self._get_azure_value(record, "CommitmentDiscountId")
        if not commitment_id:
            return None

        # Azure provides non-FOCUS compliant commitment_discount_status values
        # FOCUS 1.2 only accepts "Used", "Unused" or None for commitment_discount_status
        azure_status = self._get_azure_value(record, "CommitmentDiscountStatus")
        focus_status = None
        if azure_status in ["Used", "Unused"]:
            focus_status = azure_status
        # Azure "Active" status is ignored as it doesn't map to FOCUS 1.2

        return CommitmentInfo(
            commitment_discount_id=commitment_id,
            commitment_discount_type=self._get_azure_value(
                record, "CommitmentDiscountType"
            ),
            commitment_discount_category=self._get_azure_value(
                record, "CommitmentDiscountCategory"
            ),
            commitment_discount_name=self._get_azure_value(
                record, "CommitmentDiscountName"
            ),
            commitment_discount_status=focus_status,
            commitment_discount_quantity=self._get_azure_decimal(
                record, "CommitmentDiscountQuantity"
            ),
            commitment_discount_unit=self._get_azure_value(
                record, "CommitmentDiscountUnit"
            ),
        )

    def _get_usage_info(self, record: dict[str, Any]) -> UsageInfo | None:
        """Extract usage information from Azure FOCUS record."""
        consumed_quantity = self._get_azure_decimal(record, "ConsumedQuantity")
        if consumed_quantity is None:
            return None

        return UsageInfo(
            consumed_quantity=consumed_quantity,
            consumed_unit=self._get_azure_value(record, "ConsumedUnit"),
        )

    def _get_tags(self, record: dict[str, Any]) -> dict[str, str] | None:
        """Extract tags from Azure FOCUS record."""
        tags = {}

        # Azure FOCUS format uses Tags/ prefix for tag columns
        for key, value in record.items():
            if key.startswith("Tags/") and value is not None:
                tag_name = key[5:]  # Remove "Tags/" prefix
                tags[tag_name] = str(value)

        # Also check for direct Tags field as dict
        if "Tags" in record and isinstance(record["Tags"], dict):
            for tag_key, tag_value in record["Tags"].items():
                if tag_value is not None:
                    tags[tag_key] = str(tag_value)

        return tags if tags else None

    def _get_provider_extensions(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Extract Azure-specific data for x_provider_data field."""
        extensions = {}

        # Azure-specific fields to preserve
        azure_fields = [
            "SubscriptionId",
            "SubscriptionName",
            "ResourceGroup",
            "ResourceGroupName",
            "DepartmentName",
            "AccountName",
            "CostCenter",
            "BillingProfileId",
            "BillingProfileName",
            "InvoiceSectionId",
            "InvoiceSectionName",
            "ReservationId",
            "ReservationName",
            "PlanName",
            "OfferType",
            "Term",
            "Frequency",
            "PublisherType",
            "IsAzureCreditEligible",
        ]

        for field in azure_fields:
            value = self._get_azure_value(record, field)
            if value is not None:
                extensions[field] = value

        # Preserve any x_ prefixed fields
        for key, value in record.items():
            if key.startswith("x_") and value is not None:
                extensions[key] = value

        return extensions if extensions else None

    # Azure-specific helper methods

    def _get_azure_value(self, record: dict, field_name: str) -> str | None:
        """Get string value from Azure record."""
        value = record.get(field_name)
        return str(value).strip() if value is not None else None

    def _get_azure_decimal(self, record: dict, field_name: str) -> Decimal:
        """Get decimal value from Azure record."""
        value = record.get(field_name)
        return self.safe_decimal(value)

    def _get_azure_datetime(self, record: dict, field_name: str) -> datetime | None:
        """Get datetime value from Azure record."""
        value = record.get(field_name)
        return self.safe_datetime(value)

    def _map_azure_charge_class_to_service_category(
        self, azure_charge_class: str | None
    ) -> str | None:
        """Map Azure charge_class values to FOCUS service_category."""
        if not azure_charge_class:
            return None

        mapping = {
            "Database": "Databases",
            "Storage": "Storage",
            "Compute": "Compute",
            "Network": "Networking",
        }

        return mapping.get(azure_charge_class)

    def _determine_azure_service_category(self, service_name: str) -> str:
        """Determine FOCUS service category from Azure service name."""
        if not service_name:
            return "Other"

        service_lower = service_name.lower()

        # AI and Machine Learning
        if any(
            term in service_lower
            for term in [
                "cognitive",
                "machine learning",
                "bot",
                "ai",
                "openai",
                "applied ai",
                "form recognizer",
                "translator",
                "speech",
                "language",
                "vision",
            ]
        ):
            return "AI and Machine Learning"

        # Analytics
        elif any(
            term in service_lower
            for term in [
                "data factory",
                "synapse",
                "databricks",
                "analytics",
                "hdinsight",
                "stream analytics",
                "data lake",
                "purview",
                "power bi",
            ]
        ):
            return "Analytics"

        # Compute
        elif any(
            term in service_lower
            for term in [
                "virtual machine",
                "app service",
                "function",
                "container",
                "kubernetes",
                "compute",
                "batch",
                "service fabric",
                "cloud services",
            ]
        ):
            return "Compute"

        # Databases
        elif any(
            term in service_lower
            for term in [
                "sql",
                "database",
                "cosmos",
                "redis",
                "cache",
                "mysql",
                "postgresql",
                "mariadb",
                "managed instance",
            ]
        ):
            return "Databases"

        # Developer Tools
        elif any(
            term in service_lower
            for term in [
                "devops",
                "visual studio",
                "github",
                "app configuration",
                "notification hubs",
            ]
        ):
            return "Developer Tools"

        # Management and Governance
        elif any(
            term in service_lower
            for term in [
                "monitor",
                "log analytics",
                "automation",
                "backup",
                "site recovery",
                "policy",
                "blueprints",
                "cost management",
                "advisor",
            ]
        ):
            return "Management and Governance"

        # Networking
        elif any(
            term in service_lower
            for term in [
                "network",
                "load balancer",
                "vpn",
                "cdn",
                "firewall",
                "dns",
                "virtual wan",
                "peering",
                "expressroute",
                "bastion",
            ]
        ):
            return "Networking"

        # Security, Identity, and Compliance
        elif any(
            term in service_lower
            for term in [
                "key vault",
                "active directory",
                "security",
                "sentinel",
                "defender",
                "information protection",
                "privileged identity",
            ]
        ):
            return "Security, Identity, and Compliance"

        # Storage
        elif any(
            term in service_lower
            for term in ["storage", "blob", "disk", "file", "data box", "archive"]
        ):
            return "Storage"

        return "Other"
