"""
FOCUS Base Mapper
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from focus.models import FocusRecord
from focus.spec import FocusSpec

logger = logging.getLogger(__name__)


@dataclass
class CostInfo:
    """Cost information for FOCUS record."""

    billed_cost: Decimal
    effective_cost: Decimal
    list_cost: Decimal
    contracted_cost: Decimal
    currency: str = "USD"


@dataclass
class AccountInfo:
    """Account information for FOCUS record."""

    billing_account_id: str
    billing_account_name: str
    billing_account_type: str
    sub_account_id: str | None = None
    sub_account_name: str | None = None
    sub_account_type: str | None = None


@dataclass
class TimeInfo:
    """Time period information for FOCUS record."""

    charge_period_start: datetime
    charge_period_end: datetime
    billing_period_start: datetime | None = None
    billing_period_end: datetime | None = None


@dataclass
class ServiceInfo:
    """Service information for FOCUS record."""

    service_name: str
    service_category: str
    provider_name: str
    publisher_name: str
    invoice_issuer_name: str
    service_subcategory: str | None = None


@dataclass
class ChargeInfo:
    """Charge information for FOCUS record."""

    charge_category: str
    charge_description: str
    charge_class: str | None = None
    charge_frequency: str | None = None
    pricing_quantity: Decimal | None = None
    pricing_unit: str | None = None


@dataclass
class ResourceInfo:
    """Resource information for FOCUS record (optional)."""

    resource_id: str | None = None
    resource_name: str | None = None
    resource_type: str | None = None


@dataclass
class LocationInfo:
    """Location information for FOCUS record (optional)."""

    region_id: str | None = None
    region_name: str | None = None
    availability_zone: str | None = None


@dataclass
class SkuInfo:
    """SKU information for FOCUS record (optional)."""

    sku_id: str | None = None
    sku_price_id: str | None = None
    sku_meter: str | None = None
    sku_price_details: str | None = None
    list_unit_price: Decimal | None = None
    contracted_unit_price: Decimal | None = None


@dataclass
class CommitmentInfo:
    """Commitment discount information for FOCUS record (optional)."""

    commitment_discount_id: str | None = None
    commitment_discount_type: str | None = None
    commitment_discount_category: str | None = None
    commitment_discount_name: str | None = None
    commitment_discount_status: str | None = None
    commitment_discount_quantity: Decimal | None = None
    commitment_discount_unit: str | None = None


@dataclass
class UsageInfo:
    """Usage information for FOCUS record (optional)."""

    consumed_quantity: Decimal | None = None
    consumed_unit: str | None = None


class BaseFocusMapper:
    """
    Base class for FOCUS format mappers with standardized workflow.

    """

    def __init__(self, provider_config: dict[str, Any]):
        """Initialize mapper with provider configuration."""
        self.provider_config = provider_config
        self.provider_id = provider_config.get("provider_id") or provider_config.get(
            "id"
        )
        if not self.provider_id:
            raise ValueError("provider_id is required in provider configuration")

        self.strict_validation = provider_config.get("strict_validation", False)

    def map_to_focus(self, record: dict[str, Any]) -> list[FocusRecord] | None:
        """
        Main mapping method with standardized workflow.

        This method orchestrates the mapping process by calling abstract methods
        implemented by concrete mappers.
        """
        if not record:
            return None

        try:
            # Validate record structure
            if not self._is_valid_record(record):
                logger.debug(f"Invalid record structure: {record}")
                return None

            # Check if record should be split into multiple FOCUS records
            record_splits = self._split_record(record)

            focus_records = []
            for split_record in record_splits:
                focus_record = self._build_focus_record(split_record)
                if focus_record:
                    focus_records.append(focus_record)

            return focus_records if focus_records else None

        except Exception as e:
            logger.error(f"Error mapping record to FOCUS: {e}")
            logger.debug(f"Failed record: {record}")
            return None

    def _build_focus_record(self, record: dict[str, Any]) -> FocusRecord | None:
        """
        Build a single FOCUS record using standardized workflow.

        This method calls abstract methods to extract data and builds FocusRecord.
        """
        try:
            # Extract all required data using abstract methods
            costs = self._get_costs(record)
            account_info = self._get_account_info(record)
            time_info = self._get_time_periods(record)
            service_info = self._get_service_info(record)
            charge_info = self._get_charge_info(record)

            # Extract optional data
            resource_info = self._get_resource_info(record)
            location_info = self._get_location_info(record)
            sku_info = self._get_sku_info(record)
            commitment_info = self._get_commitment_info(record)
            usage_info = self._get_usage_info(record)
            tags = self._get_tags(record)
            provider_data = self._get_provider_extensions(record)

            # Build FOCUS data dictionary
            focus_data = {
                "id": str(uuid4()),
                # MANDATORY: Costs
                "billed_cost": costs.billed_cost,
                "effective_cost": costs.effective_cost,
                "list_cost": costs.list_cost,
                "contracted_cost": costs.contracted_cost,
                # MANDATORY: Account identification
                "billing_account_id": account_info.billing_account_id,
                "billing_account_name": account_info.billing_account_name,
                "billing_account_type": account_info.billing_account_type,
                "sub_account_id": account_info.sub_account_id,
                "sub_account_name": account_info.sub_account_name,
                "sub_account_type": account_info.sub_account_type,
                # MANDATORY: Time periods
                "charge_period_start": time_info.charge_period_start,
                "charge_period_end": time_info.charge_period_end,
                "billing_period_start": time_info.billing_period_start
                or time_info.charge_period_start,
                "billing_period_end": time_info.billing_period_end
                or time_info.charge_period_end,
                # MANDATORY: Currency
                "billing_currency": costs.currency,
                # MANDATORY: Services
                "service_name": service_info.service_name,
                "service_category": service_info.service_category,
                "provider_name": service_info.provider_name,
                "publisher_name": service_info.publisher_name,
                "invoice_issuer_name": service_info.invoice_issuer_name,
                # MANDATORY: Charges
                "charge_category": charge_info.charge_category,
                "charge_description": charge_info.charge_description,
                # CONDITIONAL: Charge details
                "charge_class": charge_info.charge_class,
                "charge_frequency": charge_info.charge_frequency,
                "pricing_quantity": charge_info.pricing_quantity,
                "pricing_unit": charge_info.pricing_unit,
                # RECOMMENDED
                "service_subcategory": service_info.service_subcategory,
                # Provider-specific
                "x_provider_id": self.provider_id,
                "x_provider_data": provider_data,
            }

            # Add optional fields if present
            self._add_optional_fields(
                focus_data,
                resource_info,
                location_info,
                sku_info,
                commitment_info,
                usage_info,
                tags,
            )

            # Apply standardized processing
            self._apply_defaults(focus_data)
            self._validate_and_correct_enums(focus_data)

            # Validate if strict mode
            if self.strict_validation:
                errors = self._validate_focus_data(focus_data)
                if errors:
                    logger.error(f"FOCUS validation failed: {errors}")
                    if len(errors) > 3:
                        return None

            # Create and return FocusRecord
            return FocusRecord(**focus_data)

        except Exception as e:
            logger.error(f"Error building FOCUS record: {e}")
            return None

    def _add_optional_fields(
        self,
        focus_data: dict,
        resource_info: ResourceInfo,
        location_info: LocationInfo,
        sku_info: SkuInfo,
        commitment_info: CommitmentInfo,
        usage_info: UsageInfo,
        tags: dict[str, str] | None,
    ) -> None:
        """Add optional fields to focus_data if present."""

        # Resource info
        if resource_info:
            focus_data.update(
                {
                    "resource_id": resource_info.resource_id,
                    "resource_name": resource_info.resource_name,
                    "resource_type": resource_info.resource_type,
                }
            )

        # Location info
        if location_info:
            focus_data.update(
                {
                    "region_id": location_info.region_id,
                    "region_name": location_info.region_name,
                    "availability_zone": location_info.availability_zone,
                }
            )

        # SKU info
        if sku_info:
            focus_data.update(
                {
                    "sku_id": sku_info.sku_id,
                    "sku_price_id": sku_info.sku_price_id,
                    "sku_meter": sku_info.sku_meter,
                    "sku_price_details": sku_info.sku_price_details,
                    "list_unit_price": sku_info.list_unit_price,
                    "contracted_unit_price": sku_info.contracted_unit_price,
                }
            )

        # Commitment info
        if commitment_info:
            focus_data.update(
                {
                    "commitment_discount_id": commitment_info.commitment_discount_id,
                    "commitment_discount_type": commitment_info.commitment_discount_type,
                    "commitment_discount_category": commitment_info.commitment_discount_category,
                    "commitment_discount_name": commitment_info.commitment_discount_name,
                    "commitment_discount_status": commitment_info.commitment_discount_status,
                    "commitment_discount_quantity": commitment_info.commitment_discount_quantity,
                    "commitment_discount_unit": commitment_info.commitment_discount_unit,
                }
            )

        # Usage info
        if usage_info:
            focus_data.update(
                {
                    "consumed_quantity": usage_info.consumed_quantity,
                    "consumed_unit": usage_info.consumed_unit,
                }
            )

        # Tags
        if tags:
            focus_data["tags"] = tags

    def _apply_defaults(self, focus_data: dict[str, Any]) -> None:
        """Apply standardized defaults."""
        # Currency defaults
        if not focus_data.get("billing_currency"):
            focus_data["billing_currency"] = "USD"

        # Billing period defaults
        if not focus_data.get("billing_period_start") and focus_data.get(
            "charge_period_start"
        ):
            billing_start, billing_end = self._get_billing_period(
                focus_data["charge_period_start"]
            )
            focus_data["billing_period_start"] = billing_start
            focus_data["billing_period_end"] = billing_end

    def _validate_and_correct_enums(self, focus_data: dict[str, Any]) -> None:
        """Validate and correct enum values using FOCUS spec."""

        # Service Category
        if focus_data.get("service_category"):
            if not FocusSpec.is_valid_service_category(focus_data["service_category"]):
                logger.warning(
                    f"Invalid service_category: {focus_data['service_category']}, defaulting to 'Other'"
                )
                focus_data["service_category"] = "Other"

        # Charge Category
        if focus_data.get("charge_category"):
            if not FocusSpec.is_valid_charge_category(focus_data["charge_category"]):
                logger.warning(
                    f"Invalid charge_category: {focus_data['charge_category']}, defaulting to 'Usage'"
                )
                focus_data["charge_category"] = "Usage"

        # Charge Class
        if focus_data.get("charge_class"):
            if not FocusSpec.is_valid_charge_class(focus_data["charge_class"]):
                logger.warning(
                    f"Invalid charge_class: {focus_data['charge_class']}, removing"
                )
                focus_data["charge_class"] = None

        # Commitment Discount Status
        if focus_data.get("commitment_discount_status"):
            if not FocusSpec.is_valid_commitment_discount_status(
                focus_data["commitment_discount_status"]
            ):
                logger.warning(
                    f"Invalid commitment_discount_status: {focus_data['commitment_discount_status']}, removing"
                )
                focus_data["commitment_discount_status"] = None

        # Charge Frequency
        if focus_data.get("charge_frequency"):
            if not FocusSpec.is_valid_charge_frequency(focus_data["charge_frequency"]):
                logger.warning(
                    f"Invalid charge_frequency: {focus_data['charge_frequency']}, removing"
                )
                focus_data["charge_frequency"] = None

    def _validate_focus_data(self, focus_data: dict[str, Any]) -> list[str]:
        """Validate FOCUS data completeness."""
        errors = []

        # Check mandatory fields
        mandatory_fields = [
            "billed_cost",
            "effective_cost",
            "list_cost",
            "contracted_cost",
            "billing_account_id",
            "billing_account_type",
            "billing_currency",
            "service_name",
            "service_category",
            "provider_name",
            "publisher_name",
            "invoice_issuer_name",
            "charge_category",
            "charge_description",
        ]

        for field in mandatory_fields:
            if not focus_data.get(field):
                errors.append(f"Missing mandatory field: {field}")

        return errors

    # Abstract methods that concrete mappers must implement

    @abstractmethod
    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate that record has minimum required structure."""
        pass

    def _split_record(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Split record into multiple records if needed.
        Default implementation returns single record.
        Override for providers that need record splitting (e.g., OpenAI tokens).
        """
        return [record]

    @abstractmethod
    def _get_costs(self, record: dict[str, Any]) -> CostInfo:
        """Extract cost information from provider record."""
        pass

    @abstractmethod
    def _get_account_info(self, record: dict[str, Any]) -> AccountInfo:
        """Extract account information from provider record."""
        pass

    @abstractmethod
    def _get_time_periods(self, record: dict[str, Any]) -> TimeInfo:
        """Extract time period information from provider record."""
        pass

    @abstractmethod
    def _get_service_info(self, record: dict[str, Any]) -> ServiceInfo:
        """Extract service information from provider record."""
        pass

    @abstractmethod
    def _get_charge_info(self, record: dict[str, Any]) -> ChargeInfo:
        """Extract charge information from provider record."""
        pass

    def _get_resource_info(self, record: dict[str, Any]) -> ResourceInfo | None:
        """Extract resource information (optional)."""
        return None

    def _get_location_info(self, record: dict[str, Any]) -> LocationInfo | None:
        """Extract location information (optional)."""
        return None

    def _get_sku_info(self, record: dict[str, Any]) -> SkuInfo | None:
        """Extract SKU information (optional)."""
        return None

    def _get_commitment_info(self, record: dict[str, Any]) -> CommitmentInfo | None:
        """Extract commitment discount information (optional)."""
        return None

    def _get_usage_info(self, record: dict[str, Any]) -> UsageInfo | None:
        """Extract usage information (optional)."""
        return None

    def _get_tags(self, record: dict[str, Any]) -> dict[str, str] | None:
        """Extract tags from provider record (optional)."""
        return None

    def _get_provider_extensions(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Extract provider-specific data for x_provider_data field (optional)."""
        return None

    # Utils

    def safe_decimal(self, value: Any, default: Decimal = Decimal("0")) -> Decimal:
        """
        Safely convert value to Decimal.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Decimal value
        """
        if value is None:
            return default

        try:
            if isinstance(value, Decimal):
                return value
            elif isinstance(value, int | float):
                return Decimal(str(value))
            elif isinstance(value, str):
                cleaned = value.strip().replace(",", "")
                return Decimal(cleaned) if cleaned else default
            else:
                return default
        except (ValueError, TypeError):
            return default

    def safe_datetime(self, value: Any) -> datetime | None:
        """
        Safely convert value to timezone-aware datetime.

        Args:
            value: Value to convert (timestamp, ISO string, datetime)

        Returns:
            timezone-aware datetime object or None
        """
        if value is None:
            return None

        try:
            dt = None

            if isinstance(value, datetime):
                dt = value
            elif isinstance(value, int | float):
                # Assume Unix timestamp - fromtimestamp creates timezone-aware datetime
                dt = datetime.fromtimestamp(value, tz=UTC)
            elif isinstance(value, str):
                # Try common datetime formats
                for fmt in [
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue

                # Try ISO format if standard formats didn't work
                if dt is None:
                    try:
                        # This handles timezone-aware ISO strings
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        logger.warning(f"Failed to parse datetime: {value}")
                        return None
            else:
                return None

            if dt and dt.tzinfo is None:
                # If naive, assume UTC
                dt = dt.replace(tzinfo=UTC)
                logger.debug(f"Converted naive datetime to UTC: {dt}")

            return dt

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse datetime '{value}': {e}")
            return None

    def _get_billing_period(self, charge_date: datetime) -> tuple[datetime, datetime]:
        """
        Get billing period for a charge date with timezone awareness.
        Default: monthly billing periods.

        Args:
            charge_date: Date of the charge (should be timezone-aware)

        Returns:
            Tuple of (billing_period_start, billing_period_end) - both timezone-aware
        """
        # Ensure charge_date is timezone-aware
        if charge_date.tzinfo is None:
            charge_date = charge_date.replace(tzinfo=UTC)
            logger.debug(f"Made charge_date timezone-aware: {charge_date}")

        # Start of the month in the same timezone
        billing_start = charge_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Start of next month in the same timezone
        if billing_start.month == 12:
            billing_end = billing_start.replace(year=billing_start.year + 1, month=1)
        else:
            billing_end = billing_start.replace(month=billing_start.month + 1)

        return billing_start, billing_end
