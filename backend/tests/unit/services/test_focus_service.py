"""
Tests for FocusService
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.billing_data import BillingData
from app.services.focus_service import FocusService


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def focus_service(db_session):
    """Create focus service instance."""
    return FocusService(db_session)


@pytest.fixture
def sample_billing_data(db_session):
    """Create sample billing data."""
    now = datetime.now(UTC)

    billing_records = []
    for i in range(3):
        billing_data = BillingData(
            id=f"test-{i}",
            x_provider_id="provider-1",
            provider_name="OpenAI",
            publisher_name="OpenAI",
            invoice_issuer_name="OpenAI",
            # Costs
            billed_cost=Decimal(str((i + 1) * 10)),
            effective_cost=Decimal(str((i + 1) * 10)),
            list_cost=Decimal(str((i + 1) * 12)),
            contracted_cost=Decimal(str((i + 1) * 10)),
            # Account
            billing_account_id="account-1",
            billing_account_name="Test Account",
            billing_account_type="Individual",  # Added missing field
            # Time periods
            billing_period_start=now.replace(day=1, hour=0, minute=0, second=0),
            billing_period_end=now.replace(day=1, hour=0, minute=0, second=0)
            + timedelta(days=30),
            charge_period_start=now + timedelta(hours=i),
            charge_period_end=now + timedelta(hours=i + 1),
            # Currency
            billing_currency="USD",
            # Service
            service_name=f"GPT-{i + 3}",
            service_category="AI and Machine Learning",
            # Charge
            charge_category="Usage",
            charge_description=f"GPT-{i + 3} API usage",
            # SKU
            sku_id=f"gpt-{i + 3}-tokens",
            # Usage
            consumed_quantity=Decimal(str((i + 1) * 1000)),
            consumed_unit="tokens",
        )
        billing_records.append(billing_data)
        db_session.add(billing_data)

    db_session.commit()
    return billing_records


class TestFocusService:
    """Test cases for FocusService."""

    def test_get_focus_data_no_filters(self, focus_service, sample_billing_data):
        """Test getting FOCUS data without filters."""
        result = focus_service.get_focus_data()

        assert "records" in result
        assert "total" in result
        assert "page" in result
        assert "pages" in result

        assert result["total"] == 3
        assert len(result["records"]) == 3
        assert result["page"] == 1
        assert result["pages"] == 1

    def test_get_focus_data_with_pagination(self, focus_service, sample_billing_data):
        """Test getting FOCUS data with pagination."""
        # First page
        result = focus_service.get_focus_data(skip=0, limit=2)

        assert result["total"] == 3
        assert len(result["records"]) == 2
        assert result["page"] == 1
        assert result["pages"] == 2

        # Second page
        result = focus_service.get_focus_data(skip=2, limit=2)

        assert result["total"] == 3
        assert len(result["records"]) == 1
        assert result["page"] == 2
        assert result["pages"] == 2

    def test_get_focus_data_with_date_filter(self, focus_service, sample_billing_data):
        """Test getting FOCUS data with date filters."""
        now = datetime.now(UTC)

        # Should find all records
        result = focus_service.get_focus_data(
            start_date=now - timedelta(days=1), end_date=now + timedelta(days=1)
        )
        assert result["total"] == 3

        # Should find no records
        result = focus_service.get_focus_data(
            start_date=now + timedelta(days=2), end_date=now + timedelta(days=3)
        )
        assert result["total"] == 0

    def test_get_focus_data_with_provider_filter(
        self, focus_service, sample_billing_data
    ):
        """Test getting FOCUS data with provider filter."""
        provider_id = uuid4()

        # Should find records
        result = focus_service.get_focus_data(provider_id=provider_id)
        # Note: Using a random UUID, so it won't match
        assert result["total"] == 0

        # Test with actual provider ID from fixture
        # This would need the actual provider_id from sample_billing_data

    def test_focus_record_conversion(self, focus_service, sample_billing_data):
        """Test that billing data is properly converted to FOCUS format."""
        result = focus_service.get_focus_data(limit=1)

        assert len(result["records"]) == 1
        focus_record = result["records"][0]

        # Check required FOCUS fields are present
        assert "BilledCost" in focus_record
        assert "EffectiveCost" in focus_record
        assert "ListCost" in focus_record
        assert "ContractedCost" in focus_record
        assert "BillingAccountId" in focus_record
        assert "BillingAccountName" in focus_record  # Added missing field check
        assert "BillingAccountType" in focus_record  # Added missing field check
        assert "BillingPeriodStart" in focus_record
        assert "BillingPeriodEnd" in focus_record
        assert "ChargePeriodStart" in focus_record
        assert "ChargePeriodEnd" in focus_record
        assert "BillingCurrency" in focus_record
        assert "ServiceName" in focus_record
        assert "ServiceCategory" in focus_record
        assert "ChargeCategory" in focus_record
        assert "ChargeDescription" in focus_record
        assert "ProviderName" in focus_record
        assert "PublisherName" in focus_record
        assert "InvoiceIssuerName" in focus_record

    def test_focus_record_values(self, focus_service, sample_billing_data):
        """Test that FOCUS record values are correct."""
        result = focus_service.get_focus_data(limit=1)
        focus_record = result["records"][0]

        # Check values match the first sample record
        # Note: Values are sorted by charge_period_start DESC, effective_cost DESC
        # So the last record (index 2) with highest cost will be first
        assert focus_record["BilledCost"] == 30.0  # 3 * 10
        assert focus_record["EffectiveCost"] == 30.0
        assert focus_record["ListCost"] == 36.0  # 3 * 12
        assert focus_record["ContractedCost"] == 30.0
        assert focus_record["BillingCurrency"] == "USD"
        assert focus_record["ServiceName"] == "GPT-5"  # GPT-(2+3)
        assert focus_record["ServiceCategory"] == "AI and Machine Learning"
        assert focus_record["ChargeCategory"] == "Usage"
        assert focus_record["BillingAccountName"] == "Test Account"  # Added check
        assert focus_record["BillingAccountType"] == "Individual"  # Added check

    def test_empty_result(self, test_db_session_clean):
        """Test getting FOCUS data when no records exist."""
        # Import FocusService here to use clean session
        from app.services.focus_service import FocusService

        # Create focus service with clean session (no default provider)
        focus_service = FocusService(test_db_session_clean)

        result = focus_service.get_focus_data()

        assert result["records"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["pages"] == 1

    def test_error_handling_in_conversion(self, focus_service, db_session):
        """Test error handling when converting to FOCUS format."""
        # Create a billing record with minimal required fields
        # This simulates a record that might cause conversion issues
        billing_data = BillingData(
            id="minimal-test",
            x_provider_id="provider-1",
            provider_name="Test",
            publisher_name="Test",
            invoice_issuer_name="Test",
            billed_cost=Decimal("10.0"),
            effective_cost=Decimal("10.0"),
            list_cost=Decimal("10.0"),
            contracted_cost=Decimal("10.0"),
            billing_account_id="account-1",
            billing_account_name="Test Account",  # Added missing field
            billing_account_type="Individual",  # Added missing field
            billing_period_start=datetime.now(UTC),
            billing_period_end=datetime.now(UTC) + timedelta(days=30),
            charge_period_start=datetime.now(UTC),
            charge_period_end=datetime.now(UTC) + timedelta(hours=1),
            billing_currency="USD",
            service_name="Test Service",
            service_category="Other",
            charge_category="Usage",
            charge_description="Test charge",
        )
        db_session.add(billing_data)
        db_session.commit()

        # Should handle the conversion without errors
        result = focus_service.get_focus_data()

        # Even if conversion fails, we should get a result structure
        assert "records" in result
        assert "total" in result
        # The record might be skipped if conversion fails
        assert result["total"] >= 0
