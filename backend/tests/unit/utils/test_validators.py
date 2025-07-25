"""
Tests for FOCUS validators
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from focus.models import FocusRecord
from focus.validators import FocusValidator, ValidationError, ValidationResult


@pytest.fixture
def validator():
    """Create a FocusValidator instance."""
    return FocusValidator()


@pytest.fixture
def valid_focus_record():
    """Create a valid FOCUS record for testing."""
    base_time = datetime.now(UTC) - timedelta(days=7)  # Past date
    return FocusRecord(
        billed_cost=Decimal("10.50"),
        effective_cost=Decimal("10.50"),
        list_cost=Decimal("12.00"),
        contracted_cost=Decimal("10.50"),
        billing_account_id="account-1",
        billing_account_name="Test Account",
        billing_account_type="Direct",
        billing_period_start=base_time,
        billing_period_end=base_time + timedelta(days=1),
        charge_period_start=base_time,
        charge_period_end=base_time + timedelta(hours=1),
        billing_currency="USD",
        service_name="GPT-4",
        service_category="AI and Machine Learning",
        provider_name="OpenAI",
        publisher_name="OpenAI",
        invoice_issuer_name="OpenAI",
        charge_category="Usage",
        charge_description="GPT-4 API usage",
        consumed_quantity=Decimal("1000"),
        consumed_unit="tokens",
    )


def test_validate_valid_record(validator, valid_focus_record):
    """Test validating a valid FOCUS record."""
    result = validator.validate_record(valid_focus_record)

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.has_warnings is False


def test_validate_missing_mandatory_fields(validator):
    """Test validation fails for missing mandatory fields."""
    # Create record with missing mandatory fields using model_construct to bypass validation
    record = FocusRecord.model_construct(
        billed_cost=None,  # Missing required field
        effective_cost=None,  # Missing required field
        list_cost=None,  # Missing required field
        contracted_cost=None,  # Missing required field
        billing_account_id="",  # Empty string - should be treated as missing
        billing_account_type="Direct",  # Valid
        billing_period_start=None,
        billing_period_end=None,
        charge_period_start=None,
        charge_period_end=None,
        billing_currency="",  # Empty string - should be treated as missing
        service_name="",  # Empty string - should be treated as missing
        service_category="Test",  # Valid
        provider_name="Test",  # Valid
        publisher_name="Test",  # Valid
        invoice_issuer_name="Test",  # Valid
        charge_category="Usage",  # Valid
        charge_description="Test",  # Valid
    )

    result = validator.validate_record(record)

    assert result.is_valid is False
    assert len(result.errors) > 0

    # Check specific mandatory field errors
    error_fields = [e.field for e in result.errors]
    assert "BilledCost" in error_fields
    assert "ServiceName" in error_fields
    assert "BillingCurrency" in error_fields


def test_validate_negative_costs(validator, valid_focus_record):
    """Test validation warns about negative costs."""
    valid_focus_record.billed_cost = Decimal("-10.50")

    result = validator.validate_record(valid_focus_record)

    # Should have warnings, not errors (unless in strict mode)
    assert result.is_valid is True
    assert result.has_warnings is True

    warning_fields = [w.field for w in result.warnings]
    assert "BilledCost" in warning_fields


def test_validate_time_periods(validator, valid_focus_record):
    """Test validation of time period logic."""
    # Make charge period end before start
    valid_focus_record.charge_period_end = (
        valid_focus_record.charge_period_start.replace(hour=0)
    )
    valid_focus_record.charge_period_start = (
        valid_focus_record.charge_period_start.replace(hour=12)
    )

    result = validator.validate_record(valid_focus_record)

    assert result.is_valid is False
    error_fields = [e.field for e in result.errors]
    assert "ChargePeriod" in error_fields


def test_validate_conditional_fields(validator, valid_focus_record):
    """Test validation of conditional field dependencies."""
    # Add SubAccountName without SubAccountId
    valid_focus_record.sub_account_name = "Test SubAccount"
    valid_focus_record.sub_account_id = None

    result = validator.validate_record(valid_focus_record)

    assert result.is_valid is False
    error_fields = [e.field for e in result.errors]
    assert "SubAccountName" in error_fields


def test_validate_batch(validator, valid_focus_record):
    """Test batch validation of records."""
    # Create mix of valid and invalid records
    # Create an invalid record by copying valid one and removing mandatory field
    invalid_record = valid_focus_record.model_copy()
    invalid_record.service_name = ""  # Make it invalid

    records = [
        valid_focus_record,
        invalid_record,  # Invalid - missing mandatory field
        valid_focus_record,
    ]

    result = validator.validate_batch(records)

    assert result["total_records"] == 3
    assert result["valid_records"] == 2
    assert result["invalid_records"] == 1
    assert result["compliance_rate"] == pytest.approx(66.67, rel=0.01)


def test_strict_mode(validator, valid_focus_record):
    """Test strict mode converts warnings to errors."""
    strict_validator = FocusValidator(strict_mode=True)

    # Add something that causes a warning
    valid_focus_record.effective_cost = Decimal("15.00")  # Greater than list cost
    valid_focus_record.list_cost = Decimal("10.00")

    result = strict_validator.validate_record(valid_focus_record)

    assert result.is_valid is False  # In strict mode, warnings become errors
    assert len(result.warnings) == 0  # Warnings converted to errors
    assert len(result.errors) > 0


def test_validation_result():
    """Test ValidationResult class."""
    result = ValidationResult()

    # Initially valid
    assert result.is_valid is True
    assert result.has_warnings is False

    # Add error
    result.add_error("TestField", "Test error message")
    assert result.is_valid is False
    assert len(result.errors) == 1

    # Add warning
    result.add_warning("TestField2", "Test warning message")
    assert result.has_warnings is True
    assert len(result.warnings) == 1

    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict["is_valid"] is False
    assert result_dict["error_count"] == 1
    assert result_dict["warning_count"] == 1


def test_validation_error():
    """Test ValidationError class."""
    error = ValidationError("TestField", "Test message", "error")

    assert error.field == "TestField"
    assert error.message == "Test message"
    assert error.severity == "error"

    error_dict = error.to_dict()
    assert error_dict["field"] == "TestField"
    assert error_dict["message"] == "Test message"
    assert error_dict["severity"] == "error"


def test_timezone_aware_validation(validator):
    """Test that validator handles timezone-aware and naive datetimes."""
    # Create record with naive datetimes
    record = FocusRecord(
        billed_cost=Decimal("10.00"),
        effective_cost=Decimal("10.00"),
        list_cost=Decimal("10.00"),
        contracted_cost=Decimal("10.00"),
        billing_account_id="test",
        billing_account_type="Direct",
        billing_period_start=datetime.now(),  # Naive
        billing_period_end=datetime.now() + timedelta(days=1),  # Naive
        charge_period_start=datetime.now(UTC),  # Aware
        charge_period_end=datetime.now(UTC) + timedelta(hours=1),  # Aware
        billing_currency="USD",
        service_name="Test",
        service_category="Test",
        provider_name="Test",
        publisher_name="Test",
        invoice_issuer_name="Test",
        charge_category="Usage",
        charge_description="Test",
    )

    # Should not raise exception
    result = validator.validate_record(record)
    assert isinstance(result, ValidationResult)
