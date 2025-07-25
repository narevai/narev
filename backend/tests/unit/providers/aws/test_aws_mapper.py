"""
Unit tests for AWS to FOCUS 1.2 Mapper
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
)
from providers.aws.mapper import AWSFocusMapper


class TestAWSFocusMapper:
    """Test cases for AWSFocusMapper class."""

    def setup_method(self):
        self.provider_config = {
            "provider_id": "test-aws-provider",
            "name": "test-aws",
            "provider_type": "aws",
        }
        self.mapper = AWSFocusMapper(self.provider_config)

        # Sample AWS FOCUS 1.0 record
        self.aws_focus_record = {
            "BilledCost": 25.50,
            "EffectiveCost": 22.00,
            "ListCost": 30.00,
            "ContractedCost": 22.00,
            "BillingCurrency": "USD",
            "BillingAccountId": "123456789012",
            "BillingAccountName": "Main Account",
            "SubAccountId": "123456789012",
            "SubAccountName": "Test Account",
            "ChargePeriodStart": "2024-01-01T00:00:00Z",
            "ChargePeriodEnd": "2024-01-01T23:59:59Z",
            "BillingPeriodStart": "2024-01-01T00:00:00Z",
            "BillingPeriodEnd": "2024-01-31T23:59:59Z",
            "ServiceName": "Amazon Elastic Compute Cloud",
            "ServiceCategory": "Compute",
            "ProviderName": "Amazon Web Services",
            "PublisherName": "Amazon Web Services",
            "InvoiceIssuerName": "Amazon Web Services",
            "ChargeDescription": "EC2 Instance Usage",
            "ChargeCategory": "Usage",
            "ChargeFrequency": "Usage-Based",
            "ResourceId": "i-1234567890abcdef0",
            "ResourceName": "Web Server Instance",
            "ResourceType": "Instance",
            "RegionId": "us-east-1",
            "RegionName": "US East (N. Virginia)",
            "AvailabilityZone": "us-east-1a",
            "SkuId": "DQ578CGN99KG6ECF.JRTCKXETXF.6YS6EN2CT7",
            "SkuPriceId": "VCPU.4PVRG2PTYX.6KQSW6XZMQ.3T5X9V5M6Q",
            "ListUnitPrice": 0.0464,
            "ContractedUnitPrice": 0.0464,
            "PricingQuantity": 1.0,
            "PricingUnit": "Hrs",
            "ConsumedQuantity": 1.0,
            "ConsumedUnit": "Hrs",
            "Tags": {"Environment": "Production", "Owner": "TeamA"},
            "x_CostCategories": "On-Demand",
            "x_Discounts": None,
            "x_Operation": "RunInstances",
            "x_ServiceCode": "AmazonEC2",
            "x_UsageType": "BoxUsage:m5.large",
        }

        # Sample AWS CUR record with slash format (legacy)
        self.aws_slash_record = {
            "lineItem/UnblendedCost": "25.50",
            "lineItem/NetUnblendedCost": "22.00",
            "pricing/publicOnDemandCost": "30.00",
            "lineItem/CurrencyCode": "USD",
            "bill/PayerAccountId": "123456789012",
            "bill/PayerAccountName": "Main Account",
            "lineItem/UsageAccountId": "123456789012",
            "lineItem/UsageAccountName": "Test Account",
            "lineItem/UsageStartDate": "2024-01-01T00:00:00Z",
            "lineItem/UsageEndDate": "2024-01-01T23:59:59Z",
            "bill/BillingPeriodStartDate": "2024-01-01T00:00:00Z",
            "bill/BillingPeriodEndDate": "2024-01-31T23:59:59Z",
            "product/ProductName": "Amazon Elastic Compute Cloud",
            "lineItem/ProductCode": "AmazonEC2",
            "lineItem/LineItemDescription": "EC2 Instance usage",
            "lineItem/LineItemType": "Usage",
            "lineItem/UsageAmount": "24.0",
            "pricing/unit": "Hrs",
            "lineItem/ResourceId": "i-1234567890abcdef0",
            "product/resourceType": "Instance",
            "product/regionCode": "us-east-1",
            "product/region": "US East (N. Virginia)",
            "product/availabilityZone": "us-east-1a",
            "product/sku": "JRTCKXETXF",
            "pricing/RateId": "123456789",
            "lineItem/UnblendedRate": "1.063",
            "lineItem/NetUnblendedRate": "0.917",
        }

        # Sample AWS CUR record with underscore format
        self.aws_underscore_record = {
            "lineItem_UnblendedCost": "15.25",
            "lineItem_NetUnblendedCost": "13.50",
            "pricing_publicOnDemandCost": "18.00",
            "lineItem_CurrencyCode": "EUR",
            "bill_PayerAccountId": "987654321098",
            "lineItem_UsageAccountId": "987654321098",
            "lineItem_UsageStartDate": "2024-02-01T00:00:00Z",
            "lineItem_UsageEndDate": "2024-02-01T23:59:59Z",
            "product_ProductName": "Amazon Simple Storage Service",
            "lineItem_ProductCode": "AmazonS3",
            "lineItem_LineItemDescription": "S3 storage usage",
            "lineItem_LineItemType": "Usage",
            "lineItem_ResourceId": "my-bucket-name",
        }

        # Sample AWS CUR record with nested dict format
        self.aws_nested_record = {
            "lineItem": {
                "UnblendedCost": "8.75",
                "CurrencyCode": "GBP",
                "UsageAccountId": "555666777888",
                "ProductCode": "AmazonRDS",
                "LineItemDescription": "RDS instance usage",
                "ResourceId": "mydb-instance",
            },
            "product": {
                "ProductName": "Amazon Relational Database Service",
                "sku": "ABC123DEF456",
            },
        }

    def test_is_valid_record_with_slash_format(self):
        """Test record validation with slash format AWS CUR data."""
        assert self.mapper._is_valid_record(self.aws_slash_record) is True

    def test_is_valid_record_with_underscore_format(self):
        """Test record validation with underscore format AWS CUR data."""
        assert self.mapper._is_valid_record(self.aws_underscore_record) is True

    def test_is_valid_record_with_nested_format(self):
        """Test record validation with nested dict format AWS CUR data."""
        record = {"lineItem": {"UnblendedCost": "10.00"}}
        assert self.mapper._is_valid_record(record) is False

    def test_is_valid_record_with_empty_dict(self):
        """Test record validation with empty dictionary."""
        assert self.mapper._is_valid_record({}) is False

    def test_is_valid_record_with_none(self):
        """Test record validation with None."""
        assert self.mapper._is_valid_record(None) is False

    def test_is_valid_record_with_non_dict(self):
        """Test record validation with non-dictionary input."""
        assert self.mapper._is_valid_record("not a dict") is False

    def test_is_valid_record_without_required_field(self):
        """Test record validation without required cost field."""
        record = {"some/other/field": "value"}
        assert self.mapper._is_valid_record(record) is False

    def test_get_costs_slash_format(self):
        """Test cost extraction from slash format AWS CUR data."""
        cost_info = self.mapper._get_costs(self.aws_slash_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("25.50")
        assert cost_info.effective_cost == Decimal("22.00")
        assert cost_info.list_cost == Decimal("30.00")
        assert cost_info.contracted_cost == Decimal("22.00")
        assert cost_info.currency == "USD"

    def test_get_costs_underscore_format(self):
        """Test cost extraction from underscore format AWS CUR data."""
        cost_info = self.mapper._get_costs(self.aws_underscore_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("15.25")
        assert cost_info.effective_cost == Decimal("13.50")
        assert cost_info.list_cost == Decimal("18.00")
        assert cost_info.contracted_cost == Decimal("13.50")
        assert cost_info.currency == "EUR"

    def test_get_costs_with_fallbacks(self):
        """Test cost extraction with fallback values."""
        record = {"lineItem/UnblendedCost": "10.00"}
        cost_info = self.mapper._get_costs(record)

        assert cost_info.billed_cost == Decimal("10.00")
        assert cost_info.effective_cost == Decimal("10.00")
        assert cost_info.list_cost == Decimal("10.00")
        assert cost_info.contracted_cost == Decimal("10.00")
        assert cost_info.currency == "USD"

    def test_get_account_info_slash_format(self):
        """Test account info extraction from slash format AWS CUR data."""
        account_info = self.mapper._get_account_info(self.aws_slash_record)

        assert isinstance(account_info, AccountInfo)
        assert account_info.billing_account_id == "123456789012"
        assert account_info.billing_account_name == "Main Account"
        assert account_info.billing_account_type == "BillingAccount"
        assert account_info.sub_account_id == "123456789012"
        assert account_info.sub_account_name == "Test Account"
        assert account_info.sub_account_type == "Account"

    def test_get_account_info_with_fallbacks(self):
        """Test account info extraction with fallback values."""
        record = {"bill/PayerAccountId": "999888777666"}
        account_info = self.mapper._get_account_info(record)

        assert account_info.billing_account_id == "999888777666"
        assert account_info.billing_account_name == "999888777666"
        assert account_info.sub_account_id is None
        assert account_info.sub_account_name is None
        assert account_info.sub_account_type is None

    def test_get_account_info_unknown_fallback(self):
        """Test account info extraction with unknown fallback."""
        record = {}
        account_info = self.mapper._get_account_info(record)

        assert account_info.billing_account_id == "unknown"
        assert account_info.billing_account_name == "Unknown Account"

    def test_get_time_periods_slash_format(self):
        """Test time period extraction from slash format AWS CUR data."""
        time_info = self.mapper._get_time_periods(self.aws_slash_record)

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

    @patch("providers.aws.mapper.datetime")
    def test_get_time_periods_with_fallback(self, mock_datetime):
        """Test time period extraction with fallback when dates are missing."""
        mock_now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        record = {}
        time_info = self.mapper._get_time_periods(record)

        assert time_info.charge_period_start == mock_now
        assert time_info.charge_period_end == mock_now

    def test_get_service_info_slash_format(self):
        """Test service info extraction from slash format AWS CUR data."""
        service_info = self.mapper._get_service_info(self.aws_slash_record)

        assert isinstance(service_info, ServiceInfo)
        assert service_info.service_name == "Amazon Elastic Compute Cloud"
        assert service_info.service_category == "Compute"
        assert service_info.provider_name == "Amazon Web Services"
        assert service_info.publisher_name == "Amazon Web Services"
        assert service_info.invoice_issuer_name == "Amazon Web Services"
        assert service_info.service_subcategory is None

    def test_get_service_info_with_fallbacks(self):
        """Test service info extraction with fallback values."""
        record = {"lineItem/ProductCode": "AmazonS3"}
        service_info = self.mapper._get_service_info(record)

        assert service_info.service_name == "AWS Service"
        assert service_info.service_category == "Storage"

    def test_get_charge_info_slash_format(self):
        """Test charge info extraction from slash format AWS CUR data."""
        charge_info = self.mapper._get_charge_info(self.aws_slash_record)

        assert isinstance(charge_info, ChargeInfo)
        assert charge_info.charge_category == "Usage"
        assert charge_info.charge_description == "EC2 Instance usage"
        assert charge_info.charge_frequency == "Usage-Based"
        assert charge_info.pricing_quantity == Decimal("24.0")
        assert charge_info.pricing_unit == "Hrs"

    def test_get_charge_info_with_fallbacks(self):
        """Test charge info extraction with fallback values."""
        record = {"lineItem/LineItemType": "Tax"}
        charge_info = self.mapper._get_charge_info(record)

        assert charge_info.charge_description == "AWS Usage Charge"
        assert charge_info.charge_category == "Tax"

    def test_get_resource_info_slash_format(self):
        """Test resource info extraction from slash format AWS CUR data."""
        resource_info = self.mapper._get_resource_info(self.aws_slash_record)

        assert isinstance(resource_info, ResourceInfo)
        assert resource_info.resource_id == "i-1234567890abcdef0"
        assert resource_info.resource_name == "i-1234567890abcdef0"
        assert resource_info.resource_type == "Instance"

    def test_get_resource_info_no_resource_id(self):
        """Test resource info extraction when no resource ID."""
        record = {}
        resource_info = self.mapper._get_resource_info(record)

        assert resource_info is None

    def test_get_location_info_slash_format(self):
        """Test location info extraction from slash format AWS CUR data."""
        location_info = self.mapper._get_location_info(self.aws_slash_record)

        assert isinstance(location_info, LocationInfo)
        assert location_info.region_id == "us-east-1"
        assert location_info.region_name == "US East (N. Virginia)"
        assert location_info.availability_zone == "us-east-1a"

    def test_get_location_info_no_location(self):
        """Test location info extraction when no location data."""
        record = {}
        location_info = self.mapper._get_location_info(record)

        assert location_info is None

    def test_get_sku_info_with_sku_id(self):
        """Test SKU info extraction with SKU ID."""
        sku_info = self.mapper._get_sku_info(self.aws_slash_record)

        assert isinstance(sku_info, SkuInfo)
        assert sku_info.sku_id == "JRTCKXETXF"
        assert sku_info.sku_price_id == "123456789"
        assert sku_info.list_unit_price == Decimal("1.063")
        assert sku_info.contracted_unit_price == Decimal("0.917")

    def test_get_sku_info_fallback_sku_id(self):
        """Test SKU info extraction with fallback SKU ID generation."""
        record = {"lineItem/ProductCode": "AmazonS3", "lineItem/LineItemType": "Usage"}
        sku_info = self.mapper._get_sku_info(record)

        assert sku_info.sku_id == "aws-amazons3-usage"

    def test_get_sku_info_fallback_sku_id_unknown(self):
        """Test SKU info extraction with unknown fallback SKU ID."""
        record = {}
        sku_info = self.mapper._get_sku_info(record)

        assert sku_info.sku_id == "aws-unknown-usage"

    def test_get_aws_field_value_slash_format(self):
        """Test AWS field value extraction with slash format."""
        value = self.mapper._get_aws_field_value(
            self.aws_slash_record, "lineItem/UnblendedCost"
        )
        assert value == "25.50"

    def test_get_aws_field_value_underscore_format(self):
        """Test AWS field value extraction with underscore format."""
        value = self.mapper._get_aws_field_value(
            self.aws_underscore_record, "lineItem/UnblendedCost"
        )
        assert value == "15.25"

    def test_get_aws_field_value_nested_format(self):
        """Test AWS field value extraction with nested dict format."""
        value = self.mapper._get_aws_field_value(
            self.aws_nested_record, "lineItem/UnblendedCost"
        )
        assert value == "8.75"

    def test_get_aws_field_value_not_found(self):
        """Test AWS field value extraction when field not found."""
        value = self.mapper._get_aws_field_value({}, "nonexistent/field")
        assert value is None

    def test_get_aws_field_value_empty_string(self):
        """Test AWS field value extraction with empty string."""
        record = {"lineItem/UnblendedCost": ""}
        value = self.mapper._get_aws_field_value(record, "lineItem/UnblendedCost")
        assert value is None

    def test_get_aws_field_value_whitespace(self):
        """Test AWS field value extraction with whitespace trimming."""
        record = {"lineItem/UnblendedCost": "  25.50  "}
        value = self.mapper._get_aws_field_value(record, "lineItem/UnblendedCost")
        assert value == "25.50"

    @patch.object(AWSFocusMapper, "safe_decimal")
    def test_get_aws_field_decimal(self, mock_safe_decimal):
        """Test AWS decimal field extraction."""
        mock_safe_decimal.return_value = Decimal("25.50")

        result = self.mapper._get_aws_field_decimal(
            self.aws_slash_record, "lineItem/UnblendedCost"
        )

        assert result == Decimal("25.50")
        mock_safe_decimal.assert_called_once_with("25.50")

    @patch.object(AWSFocusMapper, "safe_datetime")
    def test_get_aws_field_datetime(self, mock_safe_datetime):
        """Test AWS datetime field extraction."""
        mock_datetime = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        mock_safe_datetime.return_value = mock_datetime

        result = self.mapper._get_aws_field_datetime(
            self.aws_slash_record, "lineItem/UsageStartDate"
        )

        assert result == mock_datetime
        mock_safe_datetime.assert_called_once_with("2024-01-01T00:00:00Z")

    @pytest.mark.parametrize(
        "service_name,expected_category",
        [
            ("sagemaker", "AI and Machine Learning"),
            ("AmazonEC2", "Compute"),
            ("AmazonS3", "Storage"),
            ("AmazonRDS", "Databases"),
            ("elasticsearch", "Analytics"),
            ("codebuild", "Developer Tools"),
            ("cloudwatch", "Management and Governance"),
            ("vpc", "Networking"),
            ("iam", "Security, Identity, and Compliance"),
            ("unknown-service", "Other"),
            ("", "Other"),
        ],
    )
    def test_map_aws_service_category(self, service_name, expected_category):
        """Test AWS service category mapping."""
        category = self.mapper._map_aws_service_category(service_name)
        assert category == expected_category

    @pytest.mark.parametrize(
        "service_name,expected_subcategory",
        [
            ("Amazon EC2", "Virtual Machines"),
            ("Amazon S3", "Object Storage"),
            ("AWS Lambda", "Serverless Functions"),
            ("Amazon EKS", "Container Orchestration"),
            ("Amazon Redshift", None),
            ("Amazon RDS", "Relational Database"),
            ("Unknown Service", None),
        ],
    )
    def test_get_aws_service_subcategory(self, service_name, expected_subcategory):
        """Test AWS service subcategory mapping."""
        subcategory = self.mapper._get_aws_service_subcategory(service_name)
        assert subcategory == expected_subcategory

    @pytest.mark.parametrize(
        "line_item_type,expected_category",
        [
            ("Usage", "Usage"),
            ("Tax", "Tax"),
            ("Fee", "Purchase"),
            ("Refund", "Credit"),
            ("Credit", "Credit"),
            ("RIFee", "Purchase"),
            ("SavingsPlansRecurringFee", "Usage"),
            ("Unknown", "Usage"),
        ],
    )
    def test_map_aws_charge_category(self, line_item_type, expected_category):
        """Test AWS charge category mapping."""
        category = self.mapper._map_aws_charge_category(line_item_type)
        assert category == expected_category

    # FOCUS 1.0 Tests

    def test_is_valid_record_focus(self):
        """Test record validation for FOCUS 1.0 format."""
        assert self.mapper._is_valid_record(self.aws_focus_record) is True

    def test_get_costs_focus(self):
        """Test cost extraction from FOCUS 1.0 record."""
        cost_info = self.mapper._get_costs(self.aws_focus_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("25.50")
        assert cost_info.effective_cost == Decimal("22.00")
        assert cost_info.list_cost == Decimal("30.00")
        assert cost_info.contracted_cost == Decimal("22.00")
        assert cost_info.currency == "USD"

    def test_get_account_info_focus(self):
        """Test account info extraction from FOCUS 1.0 record."""
        account_info = self.mapper._get_account_info(self.aws_focus_record)

        assert isinstance(account_info, AccountInfo)
        assert account_info.billing_account_id == "123456789012"
        assert account_info.billing_account_name == "Main Account"
        assert account_info.billing_account_type == "BillingAccount"
        assert account_info.sub_account_id == "123456789012"
        assert account_info.sub_account_name == "Test Account"
        assert account_info.sub_account_type == "Account"

    def test_get_time_periods_focus(self):
        """Test time period extraction from FOCUS 1.0 record."""
        time_info = self.mapper._get_time_periods(self.aws_focus_record)

        assert isinstance(time_info, TimeInfo)
        assert time_info.charge_period_start.year == 2024
        assert time_info.charge_period_start.month == 1
        assert time_info.charge_period_start.day == 1

    def test_get_service_info_focus(self):
        """Test service info extraction from FOCUS 1.0 record."""
        service_info = self.mapper._get_service_info(self.aws_focus_record)

        assert isinstance(service_info, ServiceInfo)
        assert service_info.service_name == "Amazon Elastic Compute Cloud"
        assert service_info.service_category == "Compute"
        assert service_info.provider_name == "Amazon Web Services"
        assert service_info.publisher_name == "Amazon Web Services"
        assert service_info.invoice_issuer_name == "Amazon Web Services"

    def test_get_charge_info_focus(self):
        """Test charge info extraction from FOCUS 1.0 record."""
        charge_info = self.mapper._get_charge_info(self.aws_focus_record)

        assert isinstance(charge_info, ChargeInfo)
        assert charge_info.charge_category == "Usage"
        assert charge_info.charge_description == "EC2 Instance Usage"
        assert charge_info.charge_frequency == "Usage-Based"
        assert charge_info.pricing_quantity == Decimal("1.0")
        assert charge_info.pricing_unit == "Hrs"

    def test_get_resource_info_focus(self):
        """Test resource info extraction from FOCUS 1.0 record."""
        resource_info = self.mapper._get_resource_info(self.aws_focus_record)

        assert isinstance(resource_info, ResourceInfo)
        assert resource_info.resource_id == "i-1234567890abcdef0"
        assert resource_info.resource_name == "Web Server Instance"
        assert resource_info.resource_type == "Instance"

    def test_get_location_info_focus(self):
        """Test location info extraction from FOCUS 1.0 record."""
        location_info = self.mapper._get_location_info(self.aws_focus_record)

        assert isinstance(location_info, LocationInfo)
        assert location_info.region_id == "us-east-1"
        assert location_info.region_name == "US East (N. Virginia)"
        assert location_info.availability_zone == "us-east-1a"

    def test_get_sku_info_focus(self):
        """Test SKU info extraction from FOCUS 1.0 record."""
        sku_info = self.mapper._get_sku_info(self.aws_focus_record)

        assert isinstance(sku_info, SkuInfo)
        assert sku_info.sku_id == "DQ578CGN99KG6ECF.JRTCKXETXF.6YS6EN2CT7"
        assert sku_info.sku_price_id == "VCPU.4PVRG2PTYX.6KQSW6XZMQ.3T5X9V5M6Q"
        assert sku_info.list_unit_price == Decimal("0.0464")
        assert sku_info.contracted_unit_price == Decimal("0.0464")

    def test_get_tags_focus(self):
        """Test tag extraction from FOCUS 1.0 record."""
        tags = self.mapper._get_tags(self.aws_focus_record)

        assert tags is not None
        assert tags["Environment"] == "Production"
        assert tags["Owner"] == "TeamA"

    def test_get_provider_extensions_focus(self):
        """Test AWS extension extraction from FOCUS 1.0 record."""
        extensions = self.mapper._get_provider_extensions(self.aws_focus_record)

        assert extensions is not None
        assert extensions["costcategories"] == "On-Demand"
        assert extensions["operation"] == "RunInstances"
        assert extensions["servicecode"] == "AmazonEC2"
        assert extensions["usagetype"] == "BoxUsage:m5.large"
        assert extensions.get("discounts") is None  # Should be None, not missing
