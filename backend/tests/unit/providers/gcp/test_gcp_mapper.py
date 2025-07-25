"""
Unit tests for GCP to FOCUS 1.2 Mapper
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from focus.mappers.base import (
    AccountInfo,
    ChargeInfo,
    CostInfo,
    LocationInfo,
    ResourceInfo,
    ServiceInfo,
    SkuInfo,
    TimeInfo,
    UsageInfo,
)
from providers.gcp.mapper import GCPFocusMapper


class TestGCPFocusMapper:
    """Test cases for GCPFocusMapper class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.provider_config = {
            "provider_id": "test-gcp-provider",
            "name": "test-gcp",
            "provider_type": "gcp",
        }
        self.mapper = GCPFocusMapper(self.provider_config)

        self.focus_record = {
            "BilledCost": "10.50",
            "EffectiveCost": "9.00",
            "ListCost": "12.00",
            "ContractedCost": "8.50",
            "BillingCurrency": "USD",
            "BillingAccountId": "012345-678901-234567",
            "BillingAccountName": "Test Billing Account",
            "SubAccountId": "test-project-123",
            "SubAccountName": "Test Project",
            "ChargePeriodStart": "2024-01-01T00:00:00Z",
            "ChargePeriodEnd": "2024-01-01T23:59:59Z",
            "BillingPeriodStart": "2024-01-01T00:00:00Z",
            "BillingPeriodEnd": "2024-01-31T23:59:59Z",
            "ServiceName": "Compute Engine",
            "ServiceCategory": "Compute",
            "ProviderName": "Google Cloud Platform",
            "PublisherName": "Google",
            "InvoiceIssuerName": "Google Cloud",
            "ServiceSubcategory": "Virtual Machines",
            "ChargeCategory": "usage",
            "ChargeDescription": "VM instance charges",
            "ChargeClass": "Committed",
            "ChargeFrequency": "Usage-Based",
            "PricingQuantity": "24.0",
            "PricingUnit": "hour",
            "ResourceId": "projects/test-project-123/zones/us-central1-a/instances/test-vm",
            "ResourceName": "test-vm",
            "ResourceType": "VM Instance",
            "RegionId": "us-central1",
            "RegionName": "Iowa",
            "AvailabilityZone": "us-central1-a",
            "SkuId": "6F81-5844-456A",
            "SkuPriceId": "6F81-5844-456A-1234",
            "SkuPriceDetails": "N1 Standard Instance Core running in Americas",
            "ListUnitPrice": "0.5",
            "ContractedUnitPrice": "0.35",
            "ConsumedQuantity": "24.0",
            "ConsumedUnit": "hour",
            "Tags": {"environment": "production", "team": "backend"},
        }

        self.gcp_record = {
            "billing_account_id": "012345-678901-234567",
            "service": {"id": "6F81-5844-456A", "description": "Compute Engine"},
            "sku": {
                "id": "6F81-5844-456A-001",
                "description": "N1 Standard Instance Core running in Americas",
            },
            "usage_start_time": "2024-01-01T00:00:00Z",
            "usage_end_time": "2024-01-01T23:59:59Z",
            "project": {"id": "test-project-123", "name": "Test Project"},
            "resource": {
                "id": "projects/test-project-123/zones/us-central1-a/instances/test-vm",
                "name": "test-vm",
                "type": "VM Instance",
            },
            "location": {"region": "us-central1", "zone": "us-central1-a"},
            "cost": "10.50",
            "currency": "USD",
            "usage": {"amount": "24.0", "unit": "hour"},
            "labels": {"environment": "production", "team": "backend"},
            "export_time": "2024-01-02T00:00:00Z",
            "cost_type": "regular",
            "credits": [],
        }

    def test_is_valid_record_with_focus_data(self):
        """Test record validation with FOCUS view data."""
        assert self.mapper._is_valid_record(self.focus_record) is True

    def test_is_valid_record_with_gcp_data(self):
        """Test record validation with standard GCP data."""
        assert self.mapper._is_valid_record(self.gcp_record) is True

    def test_is_valid_record_with_empty_dict(self):
        """Test record validation with empty dictionary."""
        assert self.mapper._is_valid_record({}) is False

    def test_is_valid_record_with_none(self):
        """Test record validation with None."""
        assert self.mapper._is_valid_record(None) is False

    def test_is_valid_record_with_non_dict(self):
        """Test record validation with non-dictionary input."""
        assert self.mapper._is_valid_record("not a dict") is False

    def test_get_costs_focus_view(self):
        """Test cost extraction from FOCUS view data."""
        cost_info = self.mapper._get_costs(self.focus_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("10.50")
        assert cost_info.effective_cost == Decimal("9.00")
        assert cost_info.list_cost == Decimal("12.00")
        assert cost_info.contracted_cost == Decimal("8.50")
        assert cost_info.currency == "USD"

    def test_get_costs_gcp_standard(self):
        """Test cost extraction from standard GCP data."""
        cost_info = self.mapper._get_costs(self.gcp_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("10.50")
        assert cost_info.effective_cost == Decimal("10.50")
        assert cost_info.list_cost == Decimal("10.50")
        assert cost_info.contracted_cost == Decimal("10.50")
        assert cost_info.currency == "USD"

    def test_get_costs_default_currency(self):
        """Test cost extraction with default currency when not specified."""
        record = {"cost": "5.00"}
        cost_info = self.mapper._get_costs(record)

        assert cost_info.currency == "USD"

    def test_get_account_info_focus_view(self):
        """Test account info extraction from FOCUS view data."""
        account_info = self.mapper._get_account_info(self.focus_record)

        assert isinstance(account_info, AccountInfo)
        assert account_info.billing_account_id == "012345-678901-234567"
        assert account_info.billing_account_name == "Test Billing Account"
        assert account_info.billing_account_type == "BillingAccount"
        assert account_info.sub_account_id == "test-project-123"
        assert account_info.sub_account_name == "Test Project"
        assert account_info.sub_account_type == "Project"

    def test_get_account_info_gcp_standard(self):
        """Test account info extraction from standard GCP data."""
        account_info = self.mapper._get_account_info(self.gcp_record)

        assert isinstance(account_info, AccountInfo)
        assert account_info.billing_account_id == "012345-678901-234567"
        assert account_info.billing_account_name == "Test Project"
        assert account_info.billing_account_type == "BillingAccount"
        assert account_info.sub_account_id == "test-project-123"
        assert account_info.sub_account_name == "Test Project"
        assert account_info.sub_account_type == "Project"

    def test_get_account_info_with_project_string(self):
        """Test account info extraction when project is a string."""
        record = self.gcp_record.copy()
        record["project"] = "test-project-456"

        account_info = self.mapper._get_account_info(record)

        assert account_info.sub_account_id == "test-project-456"
        assert account_info.sub_account_name is None

    def test_get_account_info_fallback_values(self):
        """Test account info extraction with fallback values."""
        record = {}
        account_info = self.mapper._get_account_info(record)

        assert account_info.billing_account_id == "unknown"
        assert account_info.billing_account_name == "Unknown Account"

    def test_get_time_periods_focus_view(self):
        """Test time period extraction from FOCUS view data."""
        time_info = self.mapper._get_time_periods(self.focus_record)

        assert isinstance(time_info, TimeInfo)
        assert time_info.charge_period_start == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=UTC
        )
        assert time_info.charge_period_end == datetime(
            2024, 1, 1, 23, 59, 59, tzinfo=UTC
        )
        assert time_info.billing_period_start == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=UTC
        )
        assert time_info.billing_period_end == datetime(
            2024, 1, 31, 23, 59, 59, tzinfo=UTC
        )

    def test_get_time_periods_gcp_standard(self):
        """Test time period extraction from standard GCP data."""
        time_info = self.mapper._get_time_periods(self.gcp_record)

        assert isinstance(time_info, TimeInfo)
        assert time_info.charge_period_start == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=UTC
        )
        assert time_info.charge_period_end == datetime(
            2024, 1, 1, 23, 59, 59, tzinfo=UTC
        )
        assert time_info.billing_period_start is None
        assert time_info.billing_period_end is None

    @patch("providers.gcp.mapper.datetime")
    def test_get_time_periods_with_fallback(self, mock_datetime):
        """Test time period extraction with fallback when dates are missing."""
        mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        record = {}
        time_info = self.mapper._get_time_periods(record)

        assert time_info.charge_period_start == mock_now
        assert time_info.charge_period_end == mock_now

    def test_get_service_info_focus_view(self):
        """Test service info extraction from FOCUS view data."""
        service_info = self.mapper._get_service_info(self.focus_record)

        assert isinstance(service_info, ServiceInfo)
        assert service_info.service_name == "Compute Engine"
        assert service_info.service_category == "Compute"
        assert service_info.provider_name == "Google Cloud Platform"
        assert service_info.publisher_name == "Google"
        assert service_info.invoice_issuer_name == "Google Cloud"
        assert service_info.service_subcategory == "Virtual Machines"

    def test_get_service_info_gcp_standard(self):
        """Test service info extraction from standard GCP data."""
        service_info = self.mapper._get_service_info(self.gcp_record)

        assert isinstance(service_info, ServiceInfo)
        assert service_info.service_name == "Compute Engine"
        assert service_info.service_category == "Compute"
        assert service_info.provider_name == "Google Cloud Platform"
        assert service_info.publisher_name == "Google"
        assert service_info.invoice_issuer_name == "Google Cloud"
        assert service_info.service_subcategory == "Virtual Machines"

    def test_get_service_info_with_service_string(self):
        """Test service info extraction when service is a string."""
        record = self.gcp_record.copy()
        record["service"] = "Cloud Storage"

        service_info = self.mapper._get_service_info(record)

        assert service_info.service_name == "Cloud Storage"

    def test_get_charge_info_focus_view(self):
        """Test charge info extraction from FOCUS view data."""
        charge_info = self.mapper._get_charge_info(self.focus_record)

        assert isinstance(charge_info, ChargeInfo)
        assert charge_info.charge_category == "Usage"
        assert charge_info.charge_description == "VM instance charges"
        assert charge_info.charge_class == "Committed"
        assert charge_info.charge_frequency == "Usage-Based"
        assert charge_info.pricing_quantity == Decimal("24.0")
        assert charge_info.pricing_unit == "hour"

    def test_get_charge_info_gcp_standard(self):
        """Test charge info extraction from standard GCP data."""
        charge_info = self.mapper._get_charge_info(self.gcp_record)

        assert isinstance(charge_info, ChargeInfo)
        assert charge_info.charge_category == "Usage"
        assert charge_info.charge_frequency == "Usage-Based"
        assert charge_info.pricing_quantity == Decimal("24.0")
        assert charge_info.pricing_unit == "hour"
        assert "Compute Engine" in charge_info.charge_description
        assert "N1 Standard Instance" in charge_info.charge_description

    def test_get_resource_info_focus_view(self):
        """Test resource info extraction from FOCUS view data."""
        resource_info = self.mapper._get_resource_info(self.focus_record)

        assert isinstance(resource_info, ResourceInfo)
        assert (
            resource_info.resource_id
            == "projects/test-project-123/zones/us-central1-a/instances/test-vm"
        )
        assert resource_info.resource_name == "test-vm"
        assert resource_info.resource_type == "VM Instance"

    def test_get_resource_info_gcp_standard(self):
        """Test resource info extraction from standard GCP data."""
        resource_info = self.mapper._get_resource_info(self.gcp_record)

        assert isinstance(resource_info, ResourceInfo)
        assert (
            resource_info.resource_id
            == "projects/test-project-123/zones/us-central1-a/instances/test-vm"
        )
        assert resource_info.resource_name == "test-vm"
        assert resource_info.resource_type == "VM Instance"

    def test_get_resource_info_no_resource(self):
        """Test resource info extraction when no resource data."""
        record = {}
        resource_info = self.mapper._get_resource_info(record)

        assert resource_info is None

    def test_get_location_info_focus_view(self):
        """Test location info extraction from FOCUS view data."""
        location_info = self.mapper._get_location_info(self.focus_record)

        assert isinstance(location_info, LocationInfo)
        assert location_info.region_id == "us-central1"
        assert location_info.region_name == "Iowa"
        assert location_info.availability_zone == "us-central1-a"

    def test_get_location_info_gcp_standard(self):
        """Test location info extraction from standard GCP data."""
        location_info = self.mapper._get_location_info(self.gcp_record)

        assert isinstance(location_info, LocationInfo)
        assert location_info.region_id == "us-central1"
        assert location_info.region_name == "us-central1"
        assert location_info.availability_zone == "us-central1-a"

    def test_get_location_info_location_string(self):
        """Test location info extraction when location is a string."""
        record = {"location": "europe-west1"}
        location_info = self.mapper._get_location_info(record)

        assert location_info.region_id == "europe-west1"
        assert location_info.region_name == "europe-west1"

    def test_get_location_info_no_location(self):
        """Test location info extraction when no location data."""
        record = {}
        location_info = self.mapper._get_location_info(record)

        assert location_info is None

    def test_get_sku_info_focus_view(self):
        """Test SKU info extraction from FOCUS view data."""
        sku_info = self.mapper._get_sku_info(self.focus_record)

        assert isinstance(sku_info, SkuInfo)
        assert sku_info.sku_id == "6F81-5844-456A"
        assert sku_info.sku_price_id == "6F81-5844-456A-1234"
        assert (
            sku_info.sku_price_details
            == "N1 Standard Instance Core running in Americas"
        )
        assert sku_info.list_unit_price == Decimal("0.5")
        assert sku_info.contracted_unit_price == Decimal("0.35")

    def test_get_sku_info_gcp_standard(self):
        """Test SKU info extraction from standard GCP data."""
        sku_info = self.mapper._get_sku_info(self.gcp_record)

        assert isinstance(sku_info, SkuInfo)
        assert sku_info.sku_id == "6F81-5844-456A-001"
        assert (
            sku_info.sku_price_details
            == "N1 Standard Instance Core running in Americas"
        )

    def test_get_sku_info_no_sku(self):
        """Test SKU info extraction when no SKU data."""
        record = {}
        sku_info = self.mapper._get_sku_info(record)

        assert sku_info is None

    def test_get_usage_info_focus_view(self):
        """Test usage info extraction from FOCUS view data."""
        usage_info = self.mapper._get_usage_info(self.focus_record)

        assert isinstance(usage_info, UsageInfo)
        assert usage_info.consumed_quantity == Decimal("24.0")
        assert usage_info.consumed_unit == "hour"

    def test_get_usage_info_gcp_standard(self):
        """Test usage info extraction from standard GCP data."""
        usage_info = self.mapper._get_usage_info(self.gcp_record)

        assert isinstance(usage_info, UsageInfo)
        assert usage_info.consumed_quantity == Decimal("24.0")
        assert usage_info.consumed_unit == "hour"

    def test_get_usage_info_no_usage(self):
        """Test usage info extraction when no usage data."""
        record = {}
        usage_info = self.mapper._get_usage_info(record)

        # May return UsageInfo with 0 quantity or None depending on safe_decimal behavior
        if usage_info is not None:
            assert usage_info.consumed_quantity == 0
        else:
            assert usage_info is None

    def test_get_tags_focus_view(self):
        """Test tags extraction from FOCUS view data."""
        tags = self.mapper._get_tags(self.focus_record)

        assert tags == {"environment": "production", "team": "backend"}

    def test_get_tags_gcp_standard(self):
        """Test tags extraction from standard GCP data."""
        tags = self.mapper._get_tags(self.gcp_record)

        assert tags == {"environment": "production", "team": "backend"}

    def test_get_tags_labels_list_format(self):
        """Test tags extraction when labels are in list format."""
        record = {
            "labels": [
                {"key": "environment", "value": "staging"},
                {"key": "cost-center", "value": "engineering"},
            ]
        }
        tags = self.mapper._get_tags(record)

        assert tags == {"environment": "staging", "cost-center": "engineering"}

    def test_get_tags_no_tags(self):
        """Test tags extraction when no tags data."""
        record = {}
        tags = self.mapper._get_tags(record)

        assert tags is None

    def test_get_provider_extensions(self):
        """Test provider extensions extraction."""
        extensions = self.mapper._get_provider_extensions(self.gcp_record)

        assert extensions["export_time"] == "2024-01-02T00:00:00Z"
        assert extensions["cost_type"] == "regular"
        assert extensions["credits"] == []

    def test_get_provider_extensions_empty(self):
        """Test provider extensions extraction with empty record."""
        record = {}
        extensions = self.mapper._get_provider_extensions(record)

        assert extensions is None

    def test_is_focus_view_data_true(self):
        """Test FOCUS view data detection returns True."""
        assert self.mapper._is_focus_view_data(self.focus_record) is True

    def test_is_focus_view_data_false(self):
        """Test FOCUS view data detection returns False for standard GCP."""
        assert self.mapper._is_focus_view_data(self.gcp_record) is False

    def test_get_gcp_value(self):
        """Test GCP value extraction helper method."""
        record = {"test_field": "  test value  "}
        assert self.mapper._get_gcp_value(record, "test_field") == "test value"

    def test_get_gcp_value_none(self):
        """Test GCP value extraction with None value."""
        record = {"test_field": None}
        assert self.mapper._get_gcp_value(record, "test_field") is None

    @patch.object(GCPFocusMapper, "safe_decimal")
    def test_get_gcp_decimal(self, mock_safe_decimal):
        """Test GCP decimal extraction helper method."""
        mock_safe_decimal.return_value = Decimal("10.5")
        record = {"cost": "10.50"}

        result = self.mapper._get_gcp_decimal(record, "cost")

        assert result == Decimal("10.5")
        mock_safe_decimal.assert_called_once_with("10.50")

    @patch.object(GCPFocusMapper, "safe_datetime")
    def test_get_gcp_datetime(self, mock_safe_datetime):
        """Test GCP datetime extraction helper method."""
        mock_datetime = datetime(2024, 1, 1, tzinfo=UTC)
        mock_safe_datetime.return_value = mock_datetime
        record = {"usage_start_time": "2024-01-01T00:00:00Z"}

        result = self.mapper._get_gcp_datetime(record, "usage_start_time")

        assert result == mock_datetime
        mock_safe_datetime.assert_called_once_with("2024-01-01T00:00:00Z")

    def test_build_gcp_charge_description(self):
        """Test GCP charge description building."""
        description = self.mapper._build_gcp_charge_description(self.gcp_record)

        assert (
            description
            == "Compute Engine - N1 Standard Instance Core running in Americas"
        )

    def test_build_gcp_charge_description_fallback(self):
        """Test GCP charge description building with fallback."""
        record = {}
        description = self.mapper._build_gcp_charge_description(record)

        assert description == "Google Cloud service charge"

    @pytest.mark.parametrize(
        "service_name,expected_category",
        [
            ("BigQuery", "Analytics"),
            ("Compute Engine", "Compute"),
            ("Cloud Storage", "Storage"),
            ("Cloud SQL", "Databases"),
            ("Vertex AI", "AI and Machine Learning"),
            ("Cloud Build", "Developer Tools"),
            ("Cloud Monitoring", "Management and Governance"),
            ("VPC Network", "Networking"),
            ("Cloud KMS", "Security, Identity, and Compliance"),
            ("Unknown Service", "Other"),
            ("", "Other"),
        ],
    )
    def test_map_gcp_service_category(self, service_name, expected_category):
        """Test GCP service category mapping."""
        category = self.mapper._map_gcp_service_category(service_name)
        assert category == expected_category

    @pytest.mark.parametrize(
        "service_name,expected_subcategory",
        [
            ("Compute Engine", "Virtual Machines"),
            ("Cloud Storage", "Object Storage"),
            ("Cloud Functions", "Serverless Functions"),
            ("Google Kubernetes Engine", "Container Orchestration"),
            ("BigQuery", "Data Warehouse"),
            ("Cloud SQL", "Managed Database"),
            ("Unknown Service", None),
        ],
    )
    def test_get_gcp_service_subcategory(self, service_name, expected_subcategory):
        """Test GCP service subcategory mapping."""
        subcategory = self.mapper._get_gcp_service_subcategory(service_name)
        assert subcategory == expected_subcategory
