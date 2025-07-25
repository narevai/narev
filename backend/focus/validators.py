"""
FOCUS 1.2 Validators
"""

from datetime import UTC, datetime
from typing import Any

from focus.models import FocusRecord
from focus.spec import FocusSpec


class ValidationError:
    """Represents a validation error."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error", "warning", "info"

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "message": self.message, "severity": self.severity}


class ValidationResult:
    """Result of validation."""

    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self.info: list[ValidationError] = []

    @property
    def is_valid(self) -> bool:
        """Check if record is valid (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0

    def add_error(self, field: str, message: str):
        """Add an error."""
        self.errors.append(ValidationError(field, message, "error"))

    def add_warning(self, field: str, message: str):
        """Add a warning."""
        self.warnings.append(ValidationError(field, message, "warning"))

    def add_info(self, field: str, message: str):
        """Add an info message."""
        self.info.append(ValidationError(field, message, "info"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info],
        }


class FocusValidator:
    """Validator for FOCUS 1.2 compliance."""

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.

        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode

    def _utcnow(self) -> datetime:
        """Get current UTC time with timezone info."""
        return datetime.now(UTC)

    def _ensure_timezone_aware(self, dt: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware."""
        if dt is None:
            return None

        if dt.tzinfo is None:
            # Make it UTC if naive
            return dt.replace(tzinfo=UTC)

        return dt

    def validate_record(self, record: FocusRecord) -> ValidationResult:
        """
        Validate a single FOCUS record with timezone awareness.

        Args:
            record: The FocusRecord to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()

        try:
            # Validate mandatory fields
            self._validate_mandatory_fields(record, result)

            # Validate field values
            self._validate_field_values(record, result)

            # Validate conditional fields
            self._validate_conditional_fields(record, result)

            # POPRAWKA: Validate time periods with timezone awareness
            self._validate_time_periods_safe(record, result)

            # Validate costs
            self._validate_costs(record, result)

            # Validate relationships
            self._validate_relationships(record, result)

            # In strict mode, convert warnings to errors
            if self.strict_mode and result.warnings:
                result.errors.extend(result.warnings)
                result.warnings = []

        except Exception as e:
            result.add_error("validation", f"Validation exception: {e}")

        return result

    def _validate_mandatory_fields(self, record: FocusRecord, result: ValidationResult):
        """Validate mandatory FOCUS fields."""
        # Cost fields
        if record.billed_cost is None:
            result.add_error("BilledCost", "BilledCost is mandatory")
        if record.effective_cost is None:
            result.add_error("EffectiveCost", "EffectiveCost is mandatory")
        if record.list_cost is None:
            result.add_error("ListCost", "ListCost is mandatory")
        if record.contracted_cost is None:
            result.add_error("ContractedCost", "ContractedCost is mandatory")

        # Account identification
        if not record.billing_account_id:
            result.add_error("BillingAccountId", "BillingAccountId is mandatory")

        # Time periods
        if record.billing_period_start is None:
            result.add_error("BillingPeriodStart", "BillingPeriodStart is mandatory")
        if record.billing_period_end is None:
            result.add_error("BillingPeriodEnd", "BillingPeriodEnd is mandatory")
        if record.charge_period_start is None:
            result.add_error("ChargePeriodStart", "ChargePeriodStart is mandatory")
        if record.charge_period_end is None:
            result.add_error("ChargePeriodEnd", "ChargePeriodEnd is mandatory")

        # Currency
        if not record.billing_currency:
            result.add_error("BillingCurrency", "BillingCurrency is mandatory")

        # Services
        if not record.service_name:
            result.add_error("ServiceName", "ServiceName is mandatory")
        if not record.service_category:
            result.add_error("ServiceCategory", "ServiceCategory is mandatory")
        if not record.provider_name:
            result.add_error("ProviderName", "ProviderName is mandatory")
        if not record.publisher_name:
            result.add_error("PublisherName", "PublisherName is mandatory")
        if not record.invoice_issuer_name:
            result.add_error("InvoiceIssuerName", "InvoiceIssuerName is mandatory")

        # Charge details
        if not record.charge_category:
            result.add_error("ChargeCategory", "ChargeCategory is mandatory")
        if not record.charge_description:
            result.add_error("ChargeDescription", "ChargeDescription is mandatory")

    def _validate_field_values(self, record: FocusRecord, result: ValidationResult):
        """Validate field values against FOCUS spec."""
        # Validate service category (using FocusSpec if available)
        if record.service_category:
            try:
                # Try to validate against spec if FocusSpec has validation method
                if hasattr(FocusSpec, "is_valid_service_category"):
                    if not FocusSpec.is_valid_service_category(
                        str(record.service_category)
                    ):
                        result.add_error(
                            "ServiceCategory",
                            f"Invalid service category: {record.service_category}",
                        )
            except Exception:
                # Skip validation if spec validation not available
                pass

        # Validate charge category
        if record.charge_category:
            try:
                if hasattr(FocusSpec, "is_valid_charge_category"):
                    if not FocusSpec.is_valid_charge_category(
                        str(record.charge_category)
                    ):
                        result.add_error(
                            "ChargeCategory",
                            f"Invalid charge category: {record.charge_category}",
                        )
            except Exception:
                pass

        # Validate currency codes (should be 3 letters for national currencies)
        if (
            record.billing_currency
            and len(record.billing_currency) == 3
            and not record.billing_currency.isalpha()
        ):
            result.add_warning(
                "BillingCurrency",
                f"Currency code should be 3 letters: {record.billing_currency}",
            )

        # Validate costs are non-negative
        cost_fields = [
            ("BilledCost", record.billed_cost),
            ("EffectiveCost", record.effective_cost),
            ("ListCost", record.list_cost),
            ("ContractedCost", record.contracted_cost),
        ]

        for field_name, cost_value in cost_fields:
            if cost_value is not None and cost_value < 0:
                result.add_warning(
                    field_name, f"{field_name} is negative: {cost_value}"
                )

    def _validate_conditional_fields(
        self, record: FocusRecord, result: ValidationResult
    ):
        """Validate conditional field dependencies."""
        # SubAccountName requires SubAccountId
        if record.sub_account_name and not record.sub_account_id:
            result.add_error("SubAccountName", "SubAccountName requires SubAccountId")

        # PricingUnit requires PricingQuantity
        if record.pricing_unit and record.pricing_quantity is None:
            result.add_error("PricingUnit", "PricingUnit requires PricingQuantity")

        # ResourceName and ResourceType require ResourceId
        if record.resource_name and not record.resource_id:
            result.add_error("ResourceName", "ResourceName requires ResourceId")

        if record.resource_type and not record.resource_id:
            result.add_error("ResourceType", "ResourceType requires ResourceId")

        # RegionName requires RegionId
        if record.region_name and not record.region_id:
            result.add_error("RegionName", "RegionName requires RegionId")

        # ConsumedUnit requires ConsumedQuantity
        if record.consumed_unit and record.consumed_quantity is None:
            result.add_error("ConsumedUnit", "ConsumedUnit requires ConsumedQuantity")

    def _validate_time_periods_safe(
        self, record: FocusRecord, result: ValidationResult
    ):
        """Validate time period logic with timezone safety."""
        try:
            # Ensure all datetime fields are timezone-aware
            billing_start = self._ensure_timezone_aware(record.billing_period_start)
            billing_end = self._ensure_timezone_aware(record.billing_period_end)
            charge_start = self._ensure_timezone_aware(record.charge_period_start)
            charge_end = self._ensure_timezone_aware(record.charge_period_end)

            # Validate billing period
            if billing_start and billing_end:
                if billing_start >= billing_end:
                    result.add_error(
                        "BillingPeriod",
                        "BillingPeriodEnd must be after BillingPeriodStart",
                    )

            # Validate charge period
            if charge_start and charge_end:
                if charge_start >= charge_end:
                    result.add_error(
                        "ChargePeriod",
                        "ChargePeriodEnd must be after ChargePeriodStart",
                    )

            # Validate charge period is within billing period (warning)
            if billing_start and charge_start and charge_start < billing_start:
                result.add_warning(
                    "ChargePeriod", "ChargePeriodStart is before BillingPeriodStart"
                )

            if billing_end and charge_end and charge_end > billing_end:
                result.add_warning(
                    "ChargePeriod", "ChargePeriodEnd is after BillingPeriodEnd"
                )

            # Check for future dates (with timezone-aware comparison)
            now = self._utcnow()

            if billing_end and billing_end > now:
                result.add_warning("BillingPeriod", "BillingPeriodEnd is in the future")

            if charge_end and charge_end > now:
                result.add_warning("ChargePeriod", "ChargePeriodEnd is in the future")

        except Exception as e:
            result.add_error("TimeValidation", f"Error validating time periods: {e}")

    def _validate_costs(self, record: FocusRecord, result: ValidationResult):
        """Validate cost relationships."""
        # Basic cost validation
        costs = [
            record.billed_cost,
            record.effective_cost,
            record.list_cost,
            record.contracted_cost,
        ]
        valid_costs = [c for c in costs if c is not None]

        if not valid_costs:
            result.add_error("Costs", "At least one cost field must be present")
            return

        # Check for reasonable cost relationships (warnings)
        if (
            record.effective_cost is not None
            and record.list_cost is not None
            and record.effective_cost > record.list_cost
        ):
            result.add_warning("Costs", "EffectiveCost is greater than ListCost")

        if (
            record.contracted_cost is not None
            and record.list_cost is not None
            and record.contracted_cost > record.list_cost
        ):
            result.add_warning("Costs", "ContractedCost is greater than ListCost")

    def _validate_relationships(self, record: FocusRecord, result: ValidationResult):
        """Validate logical relationships between fields."""
        # Pricing quantity and costs relationship
        if (
            record.pricing_quantity is not None
            and record.pricing_quantity > 0
            and record.list_cost is not None
            and record.list_cost == 0
        ):
            result.add_warning("Pricing", "PricingQuantity > 0 but ListCost is 0")

        # Consumed quantity should not exceed pricing quantity for most cases
        if (
            record.consumed_quantity is not None
            and record.pricing_quantity is not None
            and record.consumed_quantity > record.pricing_quantity
        ):
            result.add_info("Usage", "ConsumedQuantity exceeds PricingQuantity")

    def validate_batch(self, records: list[FocusRecord]) -> dict[str, Any]:
        """
        Validate a batch of records.

        Args:
            records: List of FocusRecord objects to validate

        Returns:
            Dictionary with validation summary
        """
        total_records = len(records)
        valid_records = 0
        total_errors = 0
        total_warnings = 0

        validation_details = []

        for i, record in enumerate(records):
            result = self.validate_record(record)

            if result.is_valid:
                valid_records += 1

            total_errors += len(result.errors)
            total_warnings += len(result.warnings)

            if not result.is_valid or result.has_warnings:
                validation_details.append(
                    {
                        "record_index": i,
                        "record_id": getattr(record, "id", "unknown"),
                        "validation": result.to_dict(),
                    }
                )

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": total_records - valid_records,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "compliance_rate": (valid_records / total_records * 100)
            if total_records > 0
            else 0,
            "validation_details": validation_details[
                :10
            ],  # Limit to first 10 for performance
        }
