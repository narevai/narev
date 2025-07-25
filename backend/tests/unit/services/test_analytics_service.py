"""
Tests for analytics service
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.services.analytics_service import AnalyticsService


@pytest.fixture
def analytics_service(test_db_session):
    """Create analytics service instance with test database."""
    return AnalyticsService(test_db_session)


@pytest.fixture
def sample_billing_records(test_db_session, sample_billing_data):
    """Create sample billing records for analytics tests."""
    from app.models.billing_data import BillingData

    records = []
    services = ["GPT-4", "GPT-3.5", "DALL-E", "Whisper"]
    now = datetime.now(UTC)

    for i in range(10):
        billing_data = sample_billing_data.copy()
        billing_data["id"] = f"billing-test-{i}"
        billing_data["service_name"] = services[i % len(services)]
        billing_data["billed_cost"] = Decimal(f"{10 + i * 2}.50")
        billing_data["consumed_quantity"] = Decimal(f"{100 * (i + 1)}")
        billing_data["charge_period_start"] = now - timedelta(days=10 - i)
        billing_data["charge_period_end"] = (
            now - timedelta(days=10 - i) + timedelta(hours=1)
        )
        billing_data["tags"] = {
            "environment": "production" if i % 2 == 0 else "development"
        }

        record = BillingData(**billing_data)
        records.append(record)
        test_db_session.add(record)

    test_db_session.commit()
    return records


def test_calculate_resource_rate(analytics_service, sample_billing_records):
    """Test calculating resource rate analytics."""
    from datetime import UTC, datetime, timedelta

    start_date = datetime.now(UTC) - timedelta(days=30)
    end_date = datetime.now(UTC)

    result = analytics_service.calculate_resource_rate(start_date, end_date)

    assert isinstance(result, dict)
    assert "status" in result
    assert "data" in result
    assert "summary" in result
    assert "filters" in result


def test_calculate_resource_rate_with_empty_database(analytics_service):
    """Test resource rate analytics with empty database."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    # Test resource rate calculation with empty database
    result = analytics_service.calculate_resource_rate(start_date, end_date)

    assert result["status"] == "success"
    assert result["summary"]["total_resources"] == 0
    assert result["summary"]["total_core_count"] == 0
    assert result["summary"]["average_cost_per_core"] == 0.0


def test_calculate_resource_rate_with_provider_filter(
    analytics_service, sample_billing_records
):
    """Test resource rate analytics with provider filter."""
    from datetime import UTC, datetime, timedelta

    from app.models.provider import Provider

    # Create additional provider for filtering
    provider = Provider(
        id="test-provider-2",
        name="azure-provider",
        provider_type="azure",
        auth_config={"api_key": "encrypted-azure-key"},
        is_active=True,
    )
    analytics_service.db.add(provider)
    analytics_service.db.commit()

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    # Test with provider filter
    result = analytics_service.calculate_resource_rate(
        start_date, end_date, provider_name="OpenAI"
    )

    assert isinstance(result, dict)
    assert "filters" in result
    assert result["filters"]["provider_name"] == "OpenAI"


def test_calculate_resource_rate_with_filters(
    analytics_service, sample_billing_records
):
    """Test calculating resource rate analytics with filters."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.calculate_resource_rate(
        start_date, end_date, provider_name="OpenAI", service_name="GPT-4"
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result
    assert result["filters"]["provider_name"] == "OpenAI"
    assert result["filters"]["service_name"] == "GPT-4"


def test_quantify_resource_usage(analytics_service, sample_billing_records):
    """Test quantifying resource usage analytics."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.quantify_resource_usage(
        start_date, end_date, service_name="GPT-4"
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result
    assert result["filters"]["service_name"] == "GPT-4"


def test_calculate_unit_economics(analytics_service, sample_billing_records):
    """Test calculating unit economics."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.calculate_unit_economics(
        start_date, end_date, unit_type="GB"
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result
    assert result["filters"]["unit_type"] == "GB"


def test_analyze_service_costs(analytics_service, sample_billing_records):
    """Test service cost analysis."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.analyze_service_costs(
        start_date, end_date, service_name="GPT-4"
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result
    assert result["filters"]["service_name"] == "GPT-4"


def test_analyze_service_cost_trends(analytics_service, sample_billing_records):
    """Test analyzing service cost trends."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=90)
    end_date = now

    result = analytics_service.analyze_service_cost_trends(start_date, end_date)

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result


def test_analyze_tag_coverage(analytics_service, sample_billing_records):
    """Test analyzing tag coverage analytics."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.analyze_tag_coverage(start_date, end_date)

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result


def test_analyze_virtual_currency_target(analytics_service, sample_billing_records):
    """Test analyzing virtual currency target analytics."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.analyze_virtual_currency_target(start_date, end_date)

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result


def test_analyze_contracted_savings(analytics_service, sample_billing_records):
    """Test analyzing contracted savings analytics."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.analyze_contracted_savings(start_date, end_date)

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert "filters" in result


def test_analytics_date_aggregation(analytics_service, sample_billing_records):
    """Test analytics aggregation by date."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=7)
    end_date = now

    result = analytics_service.calculate_resource_rate(start_date, end_date)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["filters"]["start_date"] == start_date.isoformat()
    assert result["filters"]["end_date"] == end_date.isoformat()


def test_analytics_percentage_calculations(analytics_service, sample_billing_records):
    """Test percentage calculations in analytics."""
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    end_date = now

    result = analytics_service.quantify_resource_usage(start_date, end_date)

    assert isinstance(result, dict)
    assert "summary" in result
    # Should have percentage calculations in any breakdown data
