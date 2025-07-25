"""
AWS to FOCUS 1.2 Mapper
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


class AWSFocusMapper(BaseFocusMapper):
    """
    AWS Cost and Usage Report to FOCUS 1.2 mapper.
    """

    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate AWS FOCUS 1.0 record structure."""
        if not isinstance(record, dict) or not record:
            return False

        # Check for essential FOCUS 1.0 fields first
        focus_indicators = [
            "BilledCost",
            "EffectiveCost",
            "BillingAccountId",
        ]

        # If FOCUS fields exist, it's a valid FOCUS record
        if any(field in record for field in focus_indicators):
            return True

        # Fallback to legacy AWS CUR fields (for backward compatibility)
        legacy_indicators = [
            "lineItem/UnblendedCost",
            "lineItem_UnblendedCost",
            "lineItemUnblendedCost",
        ]
        return any(field in record for field in legacy_indicators)

    def _get_costs(self, record: dict[str, Any]) -> CostInfo:
        """Extract cost information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "BilledCost" in record:
            billed_cost = self.safe_decimal(record.get("BilledCost"))
            effective_cost = self.safe_decimal(record.get("EffectiveCost", billed_cost))
            list_cost = self.safe_decimal(record.get("ListCost", billed_cost))
            contracted_cost = self.safe_decimal(
                record.get("ContractedCost", effective_cost)
            )
            currency = record.get("BillingCurrency", "USD")
        else:
            # Fallback to legacy CUR format
            billed_cost = self._get_aws_field_decimal(record, "lineItem/UnblendedCost")
            effective_cost = (
                self._get_aws_field_decimal(record, "lineItem/NetUnblendedCost")
                or billed_cost
            )
            list_cost = (
                self._get_aws_field_decimal(record, "pricing/publicOnDemandCost")
                or billed_cost
            )
            contracted_cost = effective_cost
            currency = (
                self._get_aws_field_value(record, "lineItem/CurrencyCode") or "USD"
            )

        return CostInfo(
            billed_cost=billed_cost,
            effective_cost=effective_cost,
            list_cost=list_cost,
            contracted_cost=contracted_cost,
            currency=currency,
        )

    def _get_account_info(self, record: dict[str, Any]) -> AccountInfo:
        """Extract account information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "BillingAccountId" in record:
            billing_account_id = record.get("BillingAccountId")
            billing_account_name = record.get("BillingAccountName", billing_account_id)
            sub_account_id = record.get("SubAccountId")
            sub_account_name = record.get("SubAccountName")
        else:
            # Fallback to legacy CUR format
            billing_account_id = self._get_aws_field_value(
                record, "bill/PayerAccountId"
            )
            billing_account_name = (
                self._get_aws_field_value(record, "bill/PayerAccountName")
                or billing_account_id
            )
            sub_account_id = self._get_aws_field_value(
                record, "lineItem/UsageAccountId"
            )
            sub_account_name = self._get_aws_field_value(
                record, "lineItem/UsageAccountName"
            )

        return AccountInfo(
            billing_account_id=billing_account_id or "unknown",
            billing_account_name=billing_account_name or "Unknown Account",
            billing_account_type="BillingAccount",
            sub_account_id=sub_account_id,
            sub_account_name=sub_account_name,
            sub_account_type="Account" if sub_account_id else None,
        )

    def _get_time_periods(self, record: dict[str, Any]) -> TimeInfo:
        """Extract time periods from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "ChargePeriodStart" in record:
            charge_start = self.safe_datetime(record.get("ChargePeriodStart"))
            charge_end = self.safe_datetime(record.get("ChargePeriodEnd"))
            billing_start = self.safe_datetime(record.get("BillingPeriodStart"))
            billing_end = self.safe_datetime(record.get("BillingPeriodEnd"))
        else:
            # Fallback to legacy CUR format
            charge_start = self._get_aws_field_datetime(
                record, "lineItem/UsageStartDate"
            )
            charge_end = self._get_aws_field_datetime(record, "lineItem/UsageEndDate")
            billing_start = self._get_aws_field_datetime(
                record, "bill/BillingPeriodStartDate"
            )
            billing_end = self._get_aws_field_datetime(
                record, "bill/BillingPeriodEndDate"
            )

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
        """Extract service information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "ServiceName" in record:
            service_name = record.get("ServiceName", "AWS Service")
            service_category = record.get("ServiceCategory", "Other")
            provider_name = record.get("ProviderName", "Amazon Web Services")
            publisher_name = record.get("PublisherName", "Amazon Web Services")
            invoice_issuer_name = record.get("InvoiceIssuerName", "Amazon Web Services")
        else:
            # Fallback to legacy CUR format
            service_name = (
                self._get_aws_field_value(record, "product/ProductName")
                or "AWS Service"
            )
            product_code = self._get_aws_field_value(record, "lineItem/ProductCode")
            service_category = self._map_aws_service_category(
                product_code or service_name
            )
            provider_name = "Amazon Web Services"
            publisher_name = "Amazon Web Services"
            invoice_issuer_name = "Amazon Web Services"

        return ServiceInfo(
            service_name=service_name,
            service_category=service_category,
            provider_name=provider_name,
            publisher_name=publisher_name,
            invoice_issuer_name=invoice_issuer_name,
            service_subcategory=self._get_aws_service_subcategory(service_name),
        )

    def _get_charge_info(self, record: dict[str, Any]) -> ChargeInfo:
        """Extract charge information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "ChargeDescription" in record:
            description = record.get("ChargeDescription", "AWS Usage Charge")
            charge_category = record.get("ChargeCategory", "Usage")
            charge_frequency = record.get("ChargeFrequency", "Usage-Based")
            pricing_quantity = self.safe_decimal(record.get("PricingQuantity"))
            pricing_unit = record.get("PricingUnit")
        else:
            # Fallback to legacy CUR format
            description = (
                self._get_aws_field_value(record, "lineItem/LineItemDescription")
                or "AWS Usage Charge"
            )
            line_item_type = self._get_aws_field_value(record, "lineItem/LineItemType")
            charge_category = self._map_aws_charge_category(line_item_type)
            charge_frequency = "Usage-Based"
            pricing_quantity = self._get_aws_field_decimal(
                record, "lineItem/UsageAmount"
            )
            pricing_unit = self._get_aws_field_value(record, "pricing/unit")

        return ChargeInfo(
            charge_category=charge_category,
            charge_description=description,
            charge_frequency=charge_frequency,
            pricing_quantity=pricing_quantity,
            pricing_unit=pricing_unit,
        )

    def _get_resource_info(self, record: dict[str, Any]) -> ResourceInfo | None:
        """Extract resource information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "ResourceId" in record:
            resource_id = record.get("ResourceId")
            resource_name = record.get("ResourceName", resource_id)
            resource_type = record.get("ResourceType")
        else:
            # Fallback to legacy CUR format
            resource_id = self._get_aws_field_value(record, "lineItem/ResourceId")
            resource_name = resource_id  # AWS often uses ID as name
            resource_type = self._get_aws_field_value(record, "product/resourceType")

        if not resource_id:
            return None

        return ResourceInfo(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
        )

    def _get_location_info(self, record: dict[str, Any]) -> LocationInfo | None:
        """Extract location information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if (
            "RegionId" in record
            or "RegionName" in record
            or "AvailabilityZone" in record
        ):
            region_id = record.get("RegionId")
            region_name = record.get("RegionName")
            availability_zone = record.get("AvailabilityZone")
        else:
            # Fallback to legacy CUR format
            region_id = self._get_aws_field_value(record, "product/regionCode")
            region_name = self._get_aws_field_value(record, "product/region")
            availability_zone = self._get_aws_field_value(
                record, "product/availabilityZone"
            )

        if not any([region_id, region_name, availability_zone]):
            return None

        return LocationInfo(
            region_id=region_id,
            region_name=region_name,
            availability_zone=availability_zone,
        )

    def _get_sku_info(self, record: dict[str, Any]) -> SkuInfo:
        """Extract SKU information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "SkuId" in record:
            sku_id = record.get("SkuId")
            sku_price_id = record.get("SkuPriceId")
            list_unit_price = self.safe_decimal(record.get("ListUnitPrice"))
            contracted_unit_price = self.safe_decimal(record.get("ContractedUnitPrice"))
        else:
            # Fallback to legacy CUR format
            sku_id = self._get_aws_field_value(record, "product/sku")

            # Generate fallback SKU ID if not available
            if not sku_id:
                product_code = (
                    self._get_aws_field_value(record, "lineItem/ProductCode")
                    or "unknown"
                )
                line_item_type = (
                    self._get_aws_field_value(record, "lineItem/LineItemType")
                    or "usage"
                )
                sku_id = f"aws-{product_code.lower()}-{line_item_type.lower()}"

            sku_price_id = self._get_aws_field_value(record, "pricing/RateId")
            list_unit_price = self._get_aws_field_decimal(
                record, "lineItem/UnblendedRate"
            )
            contracted_unit_price = self._get_aws_field_decimal(
                record, "lineItem/NetUnblendedRate"
            )

        return SkuInfo(
            sku_id=sku_id,
            sku_price_id=sku_price_id,
            list_unit_price=list_unit_price,
            contracted_unit_price=contracted_unit_price,
        )

    def _get_commitment_info(self, record: dict[str, Any]) -> CommitmentInfo | None:
        """Extract commitment discount information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "CommitmentDiscountId" in record:
            commitment_id = record.get("CommitmentDiscountId")
            if not commitment_id:
                return None

            return CommitmentInfo(
                commitment_discount_id=commitment_id,
                commitment_discount_type=record.get("CommitmentDiscountType"),
                commitment_discount_category=record.get("CommitmentDiscountCategory"),
                commitment_discount_name=record.get("CommitmentDiscountName"),
                commitment_discount_status=record.get("CommitmentDiscountStatus"),
            )
        else:
            # Fallback to legacy CUR format
            ri_arn = self._get_aws_field_value(record, "reservation/ReservationARN")
            sp_arn = self._get_aws_field_value(record, "savingsPlan/SavingsPlanARN")

            if ri_arn:
                ri_offering_type = self._get_aws_field_value(
                    record, "reservation/OfferingType"
                )
                return CommitmentInfo(
                    commitment_discount_id=ri_arn,
                    commitment_discount_type="Reserved Instance",
                    commitment_discount_category="Committed Use",
                    commitment_discount_name=f"Reserved Instance - {ri_offering_type}"
                    if ri_offering_type
                    else "Reserved Instance",
                    commitment_discount_status="Used",
                )
            elif sp_arn:
                sp_offering_type = self._get_aws_field_value(
                    record, "savingsPlan/OfferingType"
                )
                return CommitmentInfo(
                    commitment_discount_id=sp_arn,
                    commitment_discount_type="Savings Plan",
                    commitment_discount_category="Committed Use",
                    commitment_discount_name=f"Savings Plan - {sp_offering_type}"
                    if sp_offering_type
                    else "Savings Plan",
                    commitment_discount_status="Used",
                )

        return None

    def _get_usage_info(self, record: dict[str, Any]) -> UsageInfo | None:
        """Extract usage information from AWS FOCUS 1.0 or legacy CUR record."""
        # Try FOCUS 1.0 fields first
        if "ConsumedQuantity" in record:
            consumed_quantity = self.safe_decimal(record.get("ConsumedQuantity"))
            consumed_unit = record.get("ConsumedUnit")
        else:
            # Fallback to legacy CUR format
            consumed_quantity = self._get_aws_field_decimal(
                record, "lineItem/UsageAmount"
            )
            consumed_unit = self._get_aws_field_value(record, "pricing/unit")

        if consumed_quantity is None:
            return None

        return UsageInfo(
            consumed_quantity=consumed_quantity, consumed_unit=consumed_unit
        )

    def _get_tags(self, record: dict[str, Any]) -> dict[str, str] | None:
        """Extract tags from AWS FOCUS 1.0 or legacy CUR record."""
        tags = {}

        # Try FOCUS 1.0 tags field first
        if "Tags" in record and record["Tags"]:
            if isinstance(record["Tags"], dict):
                tags.update(
                    {k: str(v) for k, v in record["Tags"].items() if v is not None}
                )
            elif isinstance(record["Tags"], str):
                # Handle JSON string format
                try:
                    import json

                    parsed_tags = json.loads(record["Tags"])
                    if isinstance(parsed_tags, dict):
                        tags.update(
                            {k: str(v) for k, v in parsed_tags.items() if v is not None}
                        )
                except (json.JSONDecodeError, TypeError):
                    pass
        else:
            # Fallback to legacy AWS CUR tag formats
            for key, value in record.items():
                if key.startswith("resourceTags/") and value is not None:
                    tag_name = key[13:]  # Remove "resourceTags/" prefix
                    tags[tag_name] = str(value)
                elif (
                    key.startswith("user:") or key.startswith("aws:")
                ) and value is not None:
                    tags[key] = str(value)

        return tags if tags else None

    def _get_provider_extensions(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Extract AWS-specific data for x_provider_data field."""
        extensions = {}

        # Handle FOCUS 1.0 AWS-specific extension fields (x_ prefix)
        focus_aws_extensions = [
            "x_CostCategories",
            "x_Discounts",
            "x_Operation",
            "x_ServiceCode",
            "x_UsageType",
        ]

        for field in focus_aws_extensions:
            if field in record and record[field] is not None:
                # Remove x_ prefix and convert to lowercase
                clean_key = field[2:].lower()
                extensions[clean_key] = record[field]

        # Legacy AWS-specific fields to preserve (for backward compatibility)
        aws_fields = [
            "bill/BillType",
            "lineItem/LineItemType",
            "lineItem/ProductCode",
            "lineItem/OperationType",
            "product/instanceType",
            "product/operatingSystem",
            "pricing/LeaseContractLength",
            "reservation/OfferingType",
        ]

        for field in aws_fields:
            value = self._get_aws_field_value(record, field)
            if value is not None:
                simple_key = field.replace("/", "_")
                extensions[simple_key] = value

        return extensions if extensions else None

    # AWS-specific helper methods

    def _get_aws_field_value(self, record: dict, field_path: str) -> str | None:
        """Get field value from AWS CUR record with multiple access patterns."""
        # Try direct access
        if field_path in record:
            return str(record[field_path]).strip() if record[field_path] else None

        # Try underscore format
        underscore_path = field_path.replace("/", "_")
        if underscore_path in record:
            return (
                str(record[underscore_path]).strip()
                if record[underscore_path]
                else None
            )

        # Try nested dict access
        parts = field_path.split("/")
        if len(parts) == 2:
            category, field = parts
            if category in record and isinstance(record[category], dict):
                value = record[category].get(field)
                return str(value).strip() if value else None

        return None

    def _get_aws_field_decimal(self, record: dict, field_path: str) -> Decimal:
        """Get decimal field value from AWS CUR record."""
        value = self._get_aws_field_value(record, field_path)
        return self.safe_decimal(value)

    def _get_aws_field_datetime(self, record: dict, field_path: str) -> datetime | None:
        """Get datetime field value from AWS CUR record."""
        value = self._get_aws_field_value(record, field_path)
        return self.safe_datetime(value)

    def _map_aws_service_category(self, service: str) -> str:
        """Map AWS service to FOCUS service category."""
        if not service:
            return "Other"

        service_lower = service.lower()

        # AI and Machine Learning
        if any(
            term in service_lower
            for term in [
                "sagemaker",
                "rekognition",
                "comprehend",
                "polly",
                "transcribe",
                "translate",
                "textract",
                "personalize",
                "forecast",
                "lex",
                "kendra",
                "augmented ai",
                "deepracer",
                "machine learning",
            ]
        ):
            return "AI and Machine Learning"

        # Analytics
        elif any(
            term in service_lower
            for term in [
                "athena",
                "emr",
                "kinesis",
                "glue",
                "quicksight",
                "elasticsearch",
                "opensearch",
                "msk",
                "data pipeline",
                "lake formation",
                "redshift",
            ]
        ):
            return "Analytics"

        # Compute
        elif any(
            term in service_lower
            for term in [
                "ec2",
                "lambda",
                "ecs",
                "fargate",
                "batch",
                "lightsail",
                "elastic beanstalk",
                "app runner",
                "outposts",
                "wavelength",
            ]
        ):
            return "Compute"

        # Databases
        elif any(
            term in service_lower
            for term in [
                "rds",
                "dynamodb",
                "elasticache",
                "neptune",
                "documentdb",
                "keyspaces",
                "qldb",
                "timestream",
                "aurora",
            ]
        ):
            return "Databases"

        # Developer Tools
        elif any(
            term in service_lower
            for term in [
                "codecommit",
                "codebuild",
                "codedeploy",
                "codepipeline",
                "codestar",
                "cloud9",
                "x-ray",
                "codeartifact",
                "codeguru",
            ]
        ):
            return "Developer Tools"

        # Management and Governance
        elif any(
            term in service_lower
            for term in [
                "cloudwatch",
                "cloudtrail",
                "config",
                "systems manager",
                "cloudformation",
                "service catalog",
                "trusted advisor",
                "well-architected",
                "control tower",
                "organizations",
                "resource groups",
            ]
        ):
            return "Management and Governance"

        # Networking
        elif any(
            term in service_lower
            for term in [
                "vpc",
                "cloudfront",
                "route 53",
                "direct connect",
                "global accelerator",
                "api gateway",
                "app mesh",
                "cloud map",
                "transit gateway",
                "elastic load balancing",
            ]
        ):
            return "Networking"

        # Security, Identity, and Compliance
        elif any(
            term in service_lower
            for term in [
                "iam",
                "cognito",
                "guardduty",
                "inspector",
                "macie",
                "shield",
                "waf",
                "secrets manager",
                "certificate manager",
                "key management",
                "security hub",
                "detective",
                "firewall manager",
            ]
        ):
            return "Security, Identity, and Compliance"

        # Storage
        elif any(
            term in service_lower
            for term in [
                "s3",
                "ebs",
                "efs",
                "fsx",
                "storage gateway",
                "backup",
                "datasync",
                "snow family",
                "s3 glacier",
            ]
        ):
            return "Storage"

        return "Other"

    def _get_aws_service_subcategory(self, service_name: str) -> str | None:
        """Get AWS service subcategory."""
        if not service_name:
            return None

        service_lower = service_name.lower()

        if "ec2" in service_lower:
            return "Virtual Machines"
        elif "s3" in service_lower:
            return "Object Storage"
        elif "lambda" in service_lower:
            return "Serverless Functions"
        elif "rds" in service_lower:
            return "Relational Database"
        elif "dynamodb" in service_lower:
            return "NoSQL Database"
        elif "cloudfront" in service_lower:
            return "Content Delivery Network"
        elif "eks" in service_lower or "kubernetes" in service_lower:
            return "Container Orchestration"

        return None

    def _map_aws_charge_category(self, line_item_type: str) -> str:
        """Map AWS LineItemType to FOCUS ChargeCategory."""
        if not line_item_type:
            return "Usage"

        mapping = {
            "Usage": "Usage",
            "Tax": "Tax",
            "Refund": "Credit",
            "Credit": "Credit",
            "DiscountedUsage": "Usage",
            "RIFee": "Purchase",  # Reserved Instance upfront fee
            "Fee": "Purchase",  # Various AWS fees
            "SavingsPlanUpfrontFee": "Purchase",
            "SavingsPlanRecurringFee": "Purchase",
            "SavingsPlanNegation": "Adjustment",
            "Support": "Purchase",  # Support plan charges
        }

        return mapping.get(line_item_type, "Usage")
