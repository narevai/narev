"""
Tests for billing API endpoints
"""


def test_billing_health_endpoint(client):
    """Test the billing health endpoint."""
    response = client.get("/api/v1/billing/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "billing_api"


def test_get_billing_summary(client, test_db_session, sample_billing_data):
    """Test getting billing summary - success case."""
    from datetime import UTC, datetime
    from unittest.mock import patch

    # Mock service to return proper summary data
    mock_summary_data = {
        "total_cost": 100.50,
        "total_records": 10,
        "start_date": datetime.now(UTC),
        "end_date": datetime.now(UTC),
        "currency": "USD",
        "providers": {"openai": 100.50},
        "services": {"GPT-4": 100.50},
        "daily_costs": [],
    }

    with patch(
        "app.services.billing_service.BillingService.get_billing_summary"
    ) as mock_summary:
        mock_summary.return_value = mock_summary_data

        response = client.get("/api/v1/billing/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] == 100.50
        assert data["total_records"] == 10
        assert data["currency"] == "USD"


def test_get_billing_summary_with_filters(client, test_db_session, sample_billing_data):
    """Test getting billing summary with filters - success case."""
    from datetime import UTC, datetime
    from unittest.mock import patch

    # Mock service to return filtered summary data
    mock_summary_data = {
        "total_cost": 50.25,
        "total_records": 5,
        "start_date": datetime.now(UTC),
        "end_date": datetime.now(UTC),
        "currency": "USD",
        "providers": {"openai": 50.25},
        "services": {"GPT-4": 50.25},
        "daily_costs": [],
    }

    with patch(
        "app.services.billing_service.BillingService.get_billing_summary"
    ) as mock_summary:
        mock_summary.return_value = mock_summary_data

        response = client.get("/api/v1/billing/summary?currency=USD")
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] == 50.25
        assert data["total_records"] == 5


def test_get_billing_data(client, test_db_session, sample_billing_data):
    """Test getting billing data."""
    from unittest.mock import patch
    from uuid import uuid4

    # Create proper mock data that matches the expected schema
    mock_record = sample_billing_data.copy()
    mock_record["id"] = str(uuid4())  # Use proper UUID

    mock_billing_data = {
        "data": [mock_record],
        "pagination": {
            "total": 1,
            "skip": 0,
            "limit": 100,
            "has_more": False,  # Add required field
        },
    }

    with patch(
        "app.services.billing_service.BillingService.get_billing_data"
    ) as mock_get:
        mock_get.return_value = mock_billing_data

        response = client.get("/api/v1/billing/data")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 1
        assert "total" in data["pagination"]
        assert "skip" in data["pagination"]
        assert "limit" in data["pagination"]
        # Check that pagination values are correct
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 100


def test_get_billing_data_pagination(client, test_db_session, sample_billing_data):
    """Test billing data pagination."""
    from unittest.mock import patch
    from uuid import uuid4

    # Create mock records for pagination testing
    mock_records = []
    for _i in range(15):
        record = sample_billing_data.copy()
        record["id"] = str(uuid4())
        mock_records.append(record)

    def mock_get_billing_data(skip=0, limit=100, **kwargs):
        # Simulate pagination
        end = min(skip + limit, len(mock_records))
        return {
            "data": mock_records[skip:end],
            "pagination": {
                "total": len(mock_records),
                "skip": skip,
                "limit": limit,
                "has_more": end < len(mock_records),
            },
        }

    with patch(
        "app.services.billing_service.BillingService.get_billing_data"
    ) as mock_get:
        mock_get.side_effect = mock_get_billing_data

        # Test with limit parameter (API uses skip/limit, not page/size)
        response = client.get("/api/v1/billing/data?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10  # Should return exactly 10 records
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["total"] == 15

        # Test second page with different skip
        response = client.get("/api/v1/billing/data?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5  # Remaining records
        assert data["pagination"]["skip"] == 10
        assert data["pagination"]["limit"] == 10


def test_get_billing_services(client, test_db_session, sample_billing_data):
    """Test getting list of services - success case."""
    from unittest.mock import patch

    # Mock service to return services breakdown data
    mock_services_data = [
        {
            "service_name": "GPT-4",
            "total_cost": 75.50,
            "record_count": 8,
            "percentage": 60.0,
        },
        {
            "service_name": "GPT-3.5",
            "total_cost": 25.00,
            "record_count": 5,
            "percentage": 40.0,
        },
    ]

    with patch(
        "app.services.billing_service.BillingService.get_cost_by_service"
    ) as mock_services:
        mock_services.return_value = mock_services_data

        response = client.get("/api/v1/billing/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "total_services" in data
        assert len(data["services"]) == 2
        assert data["services"][0]["service_name"] == "GPT-4"
        assert data["services"][0]["total_cost"] == 75.50


def test_get_billing_trends(client, test_db_session, sample_billing_data):
    """Test getting billing trends - success case."""
    from datetime import UTC, datetime
    from unittest.mock import patch

    # Mock service to return trends data
    mock_trends_data = [
        {"date": datetime.now(UTC), "cost": 25.50, "record_count": 3},
        {"date": datetime.now(UTC), "cost": 30.00, "record_count": 4},
    ]

    with patch(
        "app.services.billing_service.BillingService.get_cost_by_period"
    ) as mock_trends:
        mock_trends.return_value = mock_trends_data

        response = client.get("/api/v1/billing/trends")
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "group_by" in data
        assert data["group_by"] == "day"
        assert len(data["trends"]) == 2


def test_get_billing_statistics(client, test_db_session, sample_billing_data):
    """Test getting billing statistics - success case."""
    from datetime import UTC, datetime
    from unittest.mock import patch

    # Mock service to return statistics data
    mock_stats_data = {
        "total_records": 15,
        "total_cost": 250.75,
        "average_cost_per_record": 16.72,
        "cost_by_provider": {"openai": 250.75},
        "cost_by_service": {"GPT-4": 150.00, "GPT-3.5": 100.75},
        "period_start": datetime.now(UTC),
        "period_end": datetime.now(UTC),
    }

    with patch(
        "app.services.billing_service.BillingService.get_billing_statistics"
    ) as mock_stats:
        mock_stats.return_value = mock_stats_data

        response = client.get("/api/v1/billing/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 15
        assert data["total_cost"] == 250.75
        assert "cost_by_provider" in data
        assert "cost_by_service" in data


def test_get_billing_summary_empty_data(client):
    """Test billing summary with no data - should return 200 with zeros."""
    from datetime import UTC, datetime
    from unittest.mock import patch

    # Mock service to return empty summary data
    mock_empty_summary = {
        "total_cost": 0.0,
        "total_records": 0,
        "start_date": datetime.now(UTC),
        "end_date": datetime.now(UTC),
        "currency": "USD",
        "providers": {},
        "services": {},
        "daily_costs": [],
    }

    with patch(
        "app.services.billing_service.BillingService.get_billing_summary"
    ) as mock_summary:
        mock_summary.return_value = mock_empty_summary

        response = client.get("/api/v1/billing/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] == 0.0
        assert data["total_records"] == 0
        assert len(data["providers"]) == 0
        assert len(data["services"]) == 0


def test_get_billing_data_empty(client):
    """Test billing data with no records - should return 200 with empty list."""
    from unittest.mock import patch

    # Mock service to return empty data
    mock_empty_data = {
        "data": [],
        "pagination": {"skip": 0, "limit": 100, "total": 0, "has_more": False},
    }

    with patch(
        "app.services.billing_service.BillingService.get_billing_data"
    ) as mock_get:
        mock_get.return_value = mock_empty_data

        response = client.get("/api/v1/billing/data")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["has_more"] is False


def test_get_billing_services_empty(client):
    """Test services breakdown with no data - should return 200 with empty list."""
    from unittest.mock import patch

    with patch(
        "app.services.billing_service.BillingService.get_cost_by_service"
    ) as mock_services:
        mock_services.return_value = []

        response = client.get("/api/v1/billing/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert len(data["services"]) == 0
        assert data["total_services"] == 0


def test_get_billing_summary_invalid_currency(client):
    """Test billing summary with invalid currency format - should return 400."""
    # Test with invalid currency format (should be 3 letters)
    response = client.get("/api/v1/billing/summary?currency=INVALID")
    assert response.status_code == 422  # Validation error from FastAPI

    response = client.get("/api/v1/billing/summary?currency=US")
    assert response.status_code == 422  # Too short


def test_get_billing_data_invalid_pagination(client):
    """Test billing data with invalid pagination parameters."""
    # Negative skip should be rejected
    response = client.get("/api/v1/billing/data?skip=-1")
    assert response.status_code == 422

    # Limit too high should be rejected
    response = client.get("/api/v1/billing/data?limit=2000")  # Max is 1000
    assert response.status_code == 422


def test_get_billing_trends_invalid_group_by(client):
    """Test billing trends with invalid group_by parameter."""
    response = client.get("/api/v1/billing/trends?group_by=invalid")
    assert response.status_code == 422  # Should validate against pattern


# Note: Billing API doesn't have export endpoint - that's in /export/billing
# These tests would be in test_export_api.py instead
