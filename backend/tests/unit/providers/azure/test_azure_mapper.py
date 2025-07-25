"""
Unit tests for Azure to FOCUS 1.2 Mapper
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from focus.mappers.base import (
    AccountInfo,
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
from providers.azure.mapper import AzureFocusMapper


class TestAzureFocusMapper:
    """Test suite for AzureFocusMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider_config = {"provider_type": "azure", "provider_id": "test-azure"}
        self.mapper = AzureFocusMapper(provider_config=self.provider_config)

        self.valid_azure_record = {
            "BilledCost": "100.50",
            "EffectiveCost": "95.00",
            "ListCost": "110.00",
            "ContractedCost": "95.00",
            "BillingCurrency": "USD",
            "BillingAccountId": "12345-67890",
            "BillingAccountName": "Test Billing Account",
            "SubAccountId": "sub-123",
            "SubAccountName": "Test Subscription",
            "ChargePeriodStart": "2024-01-01T00:00:00Z",
            "ChargePeriodEnd": "2024-01-02T00:00:00Z",
            "BillingPeriodStart": "2024-01-01T00:00:00Z",
            "BillingPeriodEnd": "2024-01-31T23:59:59Z",
            "ServiceName": "Virtual Machines",
            "ServiceCategory": "Compute",
            "ChargeCategory": "Usage",
            "ChargeDescription": "VM usage charge",
            "PricingQuantity": "24.0",
            "PricingUnit": "Hours",
            "ResourceId": "/subscriptions/sub-123/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/vm-test",
            "ResourceName": "vm-test",
            "ResourceType": "Microsoft.Compute/virtualMachines",
            "RegionId": "eastus",
            "RegionName": "East US",
            "AvailabilityZone": "1",
            "SkuId": "Standard_D2s_v3",
            "SkuPriceId": "price-123",
            "ListUnitPrice": "0.096",
            "ContractedUnitPrice": "0.096",
            "ConsumedQuantity": "24.0",
            "ConsumedUnit": "Hours",
        }

    def test_is_valid_record_success(self):
        """Test valid record detection."""
        assert self.mapper._is_valid_record(self.valid_azure_record) is True

    def test_is_valid_record_with_minimal_fields(self):
        """Test valid record with minimal required fields."""
        minimal_record = {"BilledCost": "10.00"}
        assert self.mapper._is_valid_record(minimal_record) is True

    def test_is_valid_record_empty(self):
        """Test invalid empty record."""
        assert self.mapper._is_valid_record({}) is False
        assert self.mapper._is_valid_record(None) is False

    def test_is_valid_record_wrong_type(self):
        """Test invalid record type."""
        assert self.mapper._is_valid_record("not a dict") is False
        assert self.mapper._is_valid_record(123) is False

    def test_is_valid_record_missing_indicators(self):
        """Test record missing required indicators."""
        invalid_record = {"RandomField": "value"}
        assert self.mapper._is_valid_record(invalid_record) is False

    def test_get_costs_complete(self):
        """Test cost extraction with all fields."""
        cost_info = self.mapper._get_costs(self.valid_azure_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("100.50")
        assert cost_info.effective_cost == Decimal("95.00")
        assert cost_info.list_cost == Decimal("110.00")
        assert cost_info.contracted_cost == Decimal("95.00")
        assert cost_info.currency == "USD"

    def test_get_costs_missing_currency(self):
        """Test cost extraction with missing currency."""
        record = dict(self.valid_azure_record)
        del record["BillingCurrency"]
        cost_info = self.mapper._get_costs(record)

        assert cost_info.currency == "USD"  # Default

    def test_get_costs_invalid_amounts(self):
        """Test cost extraction with invalid amounts."""
        record = {"BilledCost": "", "EffectiveCost": "", "ListCost": None}
        cost_info = self.mapper._get_costs(record)

        assert cost_info.billed_cost == Decimal("0")
        assert cost_info.effective_cost == Decimal("0")
        assert cost_info.list_cost == Decimal("0")

    def test_get_account_info_complete(self):
        """Test account info extraction with all fields."""
        account_info = self.mapper._get_account_info(self.valid_azure_record)

        assert isinstance(account_info, AccountInfo)
        assert account_info.billing_account_id == "12345-67890"
        assert account_info.billing_account_name == "Test Billing Account"
        assert account_info.billing_account_type == "BillingAccount"
        assert account_info.sub_account_id == "sub-123"
        assert account_info.sub_account_name == "Test Subscription"
        assert account_info.sub_account_type == "Subscription"

    def test_get_account_info_minimal(self):
        """Test account info extraction with minimal fields."""
        record = {"BillingAccountId": "12345"}
        account_info = self.mapper._get_account_info(record)

        assert account_info.billing_account_id == "12345"
        assert account_info.billing_account_name == "12345"  # Falls back to ID
        assert account_info.sub_account_id is None
        assert account_info.sub_account_type is None

    def test_get_account_info_missing_id(self):
        """Test account info extraction with missing billing account ID."""
        record = {}
        account_info = self.mapper._get_account_info(record)

        assert account_info.billing_account_id == "unknown"
        assert account_info.billing_account_name == "Unknown Account"

    def test_get_time_periods_complete(self):
        """Test time period extraction with all fields."""
        time_info = self.mapper._get_time_periods(self.valid_azure_record)

        assert isinstance(time_info, TimeInfo)

        assert time_info.charge_period_start == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=UTC
        )
        assert time_info.charge_period_end == datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)
        assert time_info.billing_period_start == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=UTC
        )
        assert time_info.billing_period_end == datetime(
            2024, 1, 31, 23, 59, 59, tzinfo=UTC
        )

    def test_get_time_periods_missing_charge_dates(self):
        """Test time period extraction with missing charge dates."""
        record = {
            "BillingPeriodStart": "2024-01-01T00:00:00Z",
            "BillingPeriodEnd": "2024-01-31T23:59:59Z",
        }
        time_info = self.mapper._get_time_periods(record)

        assert time_info.charge_period_start is not None  # Should fallback to now
        assert time_info.charge_period_end is not None

        assert time_info.billing_period_start == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=UTC
        )

    def test_get_service_info_complete(self):
        """Test service info extraction with all fields."""
        service_info = self.mapper._get_service_info(self.valid_azure_record)

        assert isinstance(service_info, ServiceInfo)
        assert service_info.service_name == "Virtual Machines"
        assert service_info.service_category == "Compute"
        assert service_info.provider_name == "Microsoft Azure"
        assert service_info.publisher_name == "Microsoft"
        assert service_info.invoice_issuer_name == "Microsoft Azure"

    def test_get_service_info_ai_category_fix(self):
        """Test service info with AI + Machine Learning category fix."""
        record = dict(self.valid_azure_record)
        record["ServiceCategory"] = "AI + Machine Learning"
        service_info = self.mapper._get_service_info(record)

        assert service_info.service_category == "AI and Machine Learning"

    def test_get_service_info_database_category_fix(self):
        """Test service info with Database to Databases category fix."""
        record = dict(self.valid_azure_record)
        record["ServiceCategory"] = "Database"
        service_info = self.mapper._get_service_info(record)

        assert service_info.service_category == "Databases"

    def test_get_service_info_no_category_with_charge_class(self):
        """Test service info without category but with charge class."""
        record = dict(self.valid_azure_record)
        del record["ServiceCategory"]
        record["ChargeClass"] = "Storage"
        service_info = self.mapper._get_service_info(record)

        assert service_info.service_category == "Storage"

    def test_get_service_info_fallback_to_service_name(self):
        """Test service info fallback to determining category from service name."""
        record = {
            "ServiceName": "Azure SQL Database",
        }
        service_info = self.mapper._get_service_info(record)

        assert service_info.service_category == "Databases"  # Determined from name

    def test_get_charge_info_complete(self):
        """Test charge info extraction with all fields."""
        charge_info = self.mapper._get_charge_info(self.valid_azure_record)

        assert isinstance(charge_info, ChargeInfo)
        assert charge_info.charge_category == "Usage"
        assert charge_info.charge_description == "VM usage charge"
        assert charge_info.charge_class is None  # Non-FOCUS compliant values filtered
        assert charge_info.pricing_quantity == Decimal("24.0")
        assert charge_info.pricing_unit == "Hours"

    def test_get_charge_info_correction_charge_class(self):
        """Test charge info with Correction charge class."""
        record = dict(self.valid_azure_record)
        record["ChargeClass"] = "Correction"
        charge_info = self.mapper._get_charge_info(record)

        assert charge_info.charge_class == "Correction"

    def test_get_charge_info_non_focus_charge_class(self):
        """Test charge info with non-FOCUS compliant charge class."""
        record = dict(self.valid_azure_record)
        record["ChargeClass"] = "Compute"  # Not FOCUS compliant
        charge_info = self.mapper._get_charge_info(record)

        assert charge_info.charge_class is None  # Should be filtered out

    def test_get_resource_info_complete(self):
        """Test resource info extraction with all fields."""
        resource_info = self.mapper._get_resource_info(self.valid_azure_record)

        assert isinstance(resource_info, ResourceInfo)
        assert (
            resource_info.resource_id
            == "/subscriptions/sub-123/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/vm-test"
        )
        assert resource_info.resource_name == "vm-test"
        assert resource_info.resource_type == "Microsoft.Compute/virtualMachines"

    def test_get_resource_info_missing_id(self):
        """Test resource info extraction with missing resource ID."""
        record = {"ResourceName": "vm-test"}
        resource_info = self.mapper._get_resource_info(record)

        assert resource_info is None

    def test_get_resource_info_id_fallback_name(self):
        """Test resource info with ID but no name."""
        record = {"ResourceId": "/subscriptions/sub-123/vm"}
        resource_info = self.mapper._get_resource_info(record)

        assert resource_info.resource_name == "/subscriptions/sub-123/vm"

    def test_get_location_info_complete(self):
        """Test location info extraction with all fields."""
        location_info = self.mapper._get_location_info(self.valid_azure_record)

        assert isinstance(location_info, LocationInfo)
        assert location_info.region_id == "eastus"
        assert location_info.region_name == "East US"
        assert location_info.availability_zone == "1"

    def test_get_location_info_missing_all(self):
        """Test location info extraction with no location fields."""
        record = {}
        location_info = self.mapper._get_location_info(record)

        assert location_info is None

    def test_get_location_info_partial(self):
        """Test location info extraction with partial fields."""
        record = {"RegionId": "westus"}
        location_info = self.mapper._get_location_info(record)

        assert location_info.region_id == "westus"
        assert location_info.region_name is None

    def test_get_sku_info_complete(self):
        """Test SKU info extraction with all fields."""
        sku_info = self.mapper._get_sku_info(self.valid_azure_record)

        assert isinstance(sku_info, SkuInfo)
        assert sku_info.sku_id == "Standard_D2s_v3"
        assert sku_info.sku_price_id == "price-123"
        assert sku_info.list_unit_price == Decimal("0.096")
        assert sku_info.contracted_unit_price == Decimal("0.096")

    def test_get_sku_info_missing_id(self):
        """Test SKU info extraction with missing SKU ID."""
        record = {"SkuPriceId": "price-123"}
        sku_info = self.mapper._get_sku_info(record)

        assert sku_info is None

    def test_get_commitment_info_complete(self):
        """Test commitment info extraction with all fields."""
        record = dict(self.valid_azure_record)
        record.update(
            {
                "CommitmentDiscountId": "commitment-123",
                "CommitmentDiscountType": "Reserved Instance",
                "CommitmentDiscountCategory": "Committed Use",
                "CommitmentDiscountName": "Azure RI",
                "CommitmentDiscountStatus": "Used",
                "CommitmentDiscountQuantity": "100.0",
                "CommitmentDiscountUnit": "Hours",
            }
        )
        commitment_info = self.mapper._get_commitment_info(record)

        assert isinstance(commitment_info, CommitmentInfo)
        assert commitment_info.commitment_discount_id == "commitment-123"
        assert commitment_info.commitment_discount_type == "Reserved Instance"
        assert commitment_info.commitment_discount_status == "Used"
        assert commitment_info.commitment_discount_quantity == Decimal("100.0")

    def test_get_commitment_info_active_status_filtered(self):
        """Test commitment info with non-FOCUS compliant status."""
        record = {
            "CommitmentDiscountId": "commitment-123",
            "CommitmentDiscountStatus": "Active",  # Not FOCUS compliant
        }
        commitment_info = self.mapper._get_commitment_info(record)

        assert commitment_info.commitment_discount_status is None

    def test_get_commitment_info_missing_id(self):
        """Test commitment info extraction with missing ID."""
        record = {"CommitmentDiscountType": "Reserved Instance"}
        commitment_info = self.mapper._get_commitment_info(record)

        assert commitment_info is None

    def test_get_usage_info_complete(self):
        """Test usage info extraction with all fields."""
        usage_info = self.mapper._get_usage_info(self.valid_azure_record)

        assert isinstance(usage_info, UsageInfo)
        assert usage_info.consumed_quantity == Decimal("24.0")
        assert usage_info.consumed_unit == "Hours"

    def test_get_usage_info_missing_quantity(self):
        """Test usage info extraction with missing quantity."""
        record = {"ConsumedUnit": "Hours"}
        usage_info = self.mapper._get_usage_info(record)

        # Azure mapper returns UsageInfo with quantity=0 when ConsumedQuantity is missing
        assert usage_info.consumed_quantity == Decimal("0")

    def test_get_tags_with_prefix(self):
        """Test tag extraction with Tags/ prefix."""
        record = {
            "Tags/Environment": "Production",
            "Tags/Team": "DevOps",
            "Tags/CostCenter": "Engineering",
            "OtherField": "ignored",
        }
        tags = self.mapper._get_tags(record)

        expected = {
            "Environment": "Production",
            "Team": "DevOps",
            "CostCenter": "Engineering",
        }
        assert tags == expected

    def test_get_tags_dict_format(self):
        """Test tag extraction with Tags dict format."""
        record = {"Tags": {"Environment": "Production", "Team": "DevOps"}}
        tags = self.mapper._get_tags(record)

        expected = {"Environment": "Production", "Team": "DevOps"}
        assert tags == expected

    def test_get_tags_mixed_formats(self):
        """Test tag extraction with mixed formats."""
        record = {"Tags/Environment": "Production", "Tags": {"Team": "DevOps"}}
        tags = self.mapper._get_tags(record)

        expected = {"Environment": "Production", "Team": "DevOps"}
        assert tags == expected

    def test_get_tags_no_tags(self):
        """Test tag extraction with no tags."""
        record = {"ServiceName": "VM"}
        tags = self.mapper._get_tags(record)

        assert tags is None

    def test_get_provider_extensions(self):
        """Test provider extensions extraction."""
        record = {
            "SubscriptionId": "sub-123",
            "ResourceGroup": "rg-test",
            "DepartmentName": "Engineering",
            "x_custom_field": "custom_value",
            "IgnoredField": "ignored",
        }
        extensions = self.mapper._get_provider_extensions(record)

        expected = {
            "SubscriptionId": "sub-123",
            "ResourceGroup": "rg-test",
            "DepartmentName": "Engineering",
            "x_custom_field": "custom_value",
        }
        assert extensions == expected

    def test_get_provider_extensions_no_extensions(self):
        """Test provider extensions with no relevant fields."""
        record = {"ServiceName": "VM"}
        extensions = self.mapper._get_provider_extensions(record)

        assert extensions is None

    def test_get_azure_value_success(self):
        """Test Azure value extraction."""
        record = {"TestField": "test_value"}
        value = self.mapper._get_azure_value(record, "TestField")

        assert value == "test_value"

    def test_get_azure_value_missing(self):
        """Test Azure value extraction with missing field."""
        record = {}
        value = self.mapper._get_azure_value(record, "MissingField")

        assert value is None

    def test_get_azure_value_none(self):
        """Test Azure value extraction with None value."""
        record = {"TestField": None}
        value = self.mapper._get_azure_value(record, "TestField")

        assert value is None

    def test_get_azure_value_whitespace(self):
        """Test Azure value extraction with whitespace."""
        record = {"TestField": "  test_value  "}
        value = self.mapper._get_azure_value(record, "TestField")

        assert value == "test_value"

    def test_get_azure_decimal_valid(self):
        """Test Azure decimal extraction with valid value."""
        record = {"Amount": "123.45"}
        decimal_value = self.mapper._get_azure_decimal(record, "Amount")

        assert decimal_value == Decimal("123.45")

    def test_get_azure_decimal_invalid(self):
        """Test Azure decimal extraction with invalid value."""
        record = {"Amount": ""}  # Empty string instead of invalid
        decimal_value = self.mapper._get_azure_decimal(record, "Amount")

        assert decimal_value == Decimal("0")

    def test_get_azure_datetime_valid(self):
        """Test Azure datetime extraction with valid value."""
        record = {"Date": "2024-01-01T10:30:00Z"}
        datetime_value = self.mapper._get_azure_datetime(record, "Date")

        assert datetime_value == datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC)

    def test_get_azure_datetime_invalid(self):
        """Test Azure datetime extraction with invalid value."""
        record = {"Date": "invalid"}
        datetime_value = self.mapper._get_azure_datetime(record, "Date")

        assert datetime_value is None

    def test_map_azure_charge_class_to_service_category(self):
        """Test charge class to service category mapping."""
        assert (
            self.mapper._map_azure_charge_class_to_service_category("Database")
            == "Databases"
        )
        assert (
            self.mapper._map_azure_charge_class_to_service_category("Storage")
            == "Storage"
        )
        assert (
            self.mapper._map_azure_charge_class_to_service_category("Compute")
            == "Compute"
        )
        assert (
            self.mapper._map_azure_charge_class_to_service_category("Network")
            == "Networking"
        )
        assert (
            self.mapper._map_azure_charge_class_to_service_category("Unknown") is None
        )
        assert self.mapper._map_azure_charge_class_to_service_category(None) is None

    @pytest.mark.parametrize(
        "service_name,expected_category",
        [
            ("Azure Cognitive Services", "AI and Machine Learning"),
            ("Azure Machine Learning", "AI and Machine Learning"),
            ("Azure Bot Service", "AI and Machine Learning"),
            ("Azure Data Factory", "Analytics"),
            ("Azure Synapse Analytics", "Analytics"),
            ("Azure Databricks", "Analytics"),
            ("Virtual Machine", "Compute"),
            ("Azure App Service", "Compute"),
            ("Azure Functions", "Compute"),
            ("Azure SQL Database", "Databases"),
            ("Azure Cosmos DB", "Databases"),
            ("Azure Database for MySQL", "Databases"),
            ("Azure DevOps", "Developer Tools"),
            ("Visual Studio Subscriptions", "Developer Tools"),
            ("Azure Monitor", "Management and Governance"),
            ("Azure Backup", "Management and Governance"),
            ("Azure Automation", "Management and Governance"),
            ("Azure Virtual Network", "Networking"),
            ("Azure Load Balancer", "Networking"),
            ("Azure VPN Gateway", "Networking"),
            ("Azure Key Vault", "Security, Identity, and Compliance"),
            ("Azure Active Directory", "Security, Identity, and Compliance"),
            ("Azure Security Center", "Security, Identity, and Compliance"),
            ("Azure Storage", "Storage"),
            ("Azure Blob Storage", "Storage"),
            ("Azure Disk Storage", "Storage"),
            ("Unknown Service", "Other"),
        ],
    )
    def test_determine_azure_service_category(self, service_name, expected_category):
        """Test Azure service category determination from service name."""
        category = self.mapper._determine_azure_service_category(service_name)
        assert category == expected_category
