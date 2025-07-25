"""
Unit tests for OpenAI to FOCUS 1.2 Mapper
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from focus.mappers.base import (
    AccountInfo,
    ChargeInfo,
    CostInfo,
    ResourceInfo,
    ServiceInfo,
    TimeInfo,
    UsageInfo,
)
from providers.openai.mapper import OpenAIFocusMapper


class TestOpenAIFocusMapper:
    """Test suite for OpenAIFocusMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider_config = {
            "provider_type": "openai",
            "provider_id": "test-openai",
            "organization_id": "org-1234567890abcdef",
        }
        self.mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        self.valid_token_record = {
            "object": "usage_aggregation",
            "model": "gpt-4o",
            "api_key_id": "sk-admin-abc123",
            "input_tokens": 1000,
            "output_tokens": 500,
            "bucket_start_time": 1704067200,  # 2024-01-01 00:00:00 UTC
            "bucket_end_time": 1704153600,  # 2024-01-02 00:00:00 UTC
            "num_model_requests": 10,
        }

        self.valid_image_record = {
            "object": "usage_aggregation",
            "model": "dall-e-3",
            "api_key_id": "sk-admin-xyz789",
            "num_images": 5,
            "image_size": "1024x1024",
            "bucket_start_time": 1704067200,
            "bucket_end_time": 1704153600,
            "num_model_requests": 5,
        }

        self.valid_audio_record = {
            "object": "usage_aggregation",
            "model": "whisper-1",
            "api_key_id": "sk-admin-def456",
            "num_seconds": 300,
            "bucket_start_time": 1704067200,
            "bucket_end_time": 1704153600,
            "num_model_requests": 2,
        }

    def test_mapper_initialization(self):
        """Test mapper initialization."""
        assert self.mapper.organization_id == "org-1234567890abcdef"
        assert hasattr(self.mapper, "cost_calculator")

    def test_mapper_initialization_no_org(self):
        """Test mapper initialization without organization."""
        config = {"provider_type": "openai", "provider_id": "test-openai"}
        mapper = OpenAIFocusMapper(provider_config=config)

        assert mapper.organization_id == ""

    def test_is_valid_record_success(self):
        """Test valid record detection."""
        assert self.mapper._is_valid_record(self.valid_token_record) is True

    def test_is_valid_record_bucket_filtered(self):
        """Test bucket records are filtered out."""
        bucket_record = {"object": "bucket", "model": "gpt-4o", "api_key_id": "sk-test"}
        assert self.mapper._is_valid_record(bucket_record) is False

    def test_is_valid_record_missing_required_fields(self):
        """Test record missing required fields."""
        invalid_record = {
            "object": "usage_aggregation",
            "model": "gpt-4o",
            # missing api_key_id
        }
        assert self.mapper._is_valid_record(invalid_record) is False

    def test_is_valid_record_no_usage_data(self):
        """Test record with no meaningful usage data."""
        no_usage_record = {
            "object": "usage_aggregation",
            "model": "gpt-4o",
            "api_key_id": "sk-test",
            # no tokens, images, seconds, or requests
        }
        assert self.mapper._is_valid_record(no_usage_record) is False

    def test_is_valid_record_empty(self):
        """Test empty record."""
        assert self.mapper._is_valid_record({}) is False
        assert self.mapper._is_valid_record(None) is False

    def test_split_record_both_tokens(self):
        """Test record splitting with both input and output tokens."""
        records = self.mapper._split_record(self.valid_token_record)

        assert len(records) == 2

        # Input record
        input_record = records[0]
        assert input_record["_openai_token_type"] == "input"
        assert input_record["_openai_token_count"] == 1000

        # Output record
        output_record = records[1]
        assert output_record["_openai_token_type"] == "output"
        assert output_record["_openai_token_count"] == 500

    def test_split_record_only_input_tokens(self):
        """Test record splitting with only input tokens."""
        record = dict(self.valid_token_record)
        record["output_tokens"] = 0

        records = self.mapper._split_record(record)

        assert len(records) == 1
        assert "_openai_token_type" not in records[0]

    def test_split_record_only_output_tokens(self):
        """Test record splitting with only output tokens."""
        record = dict(self.valid_token_record)
        record["input_tokens"] = 0

        records = self.mapper._split_record(record)

        assert len(records) == 1
        assert "_openai_token_type" not in records[0]

    def test_split_record_no_tokens(self):
        """Test record splitting with no tokens."""
        records = self.mapper._split_record(self.valid_image_record)

        assert len(records) == 1
        assert "_openai_token_type" not in records[0]

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_costs_split_token_record_input(self, mock_calculator_class):
        """Test cost extraction for split input token record."""
        mock_calculator = Mock()
        mock_calculator.calculate_token_cost.return_value = {"total": 0.02}
        mock_calculator_class.return_value = mock_calculator

        # Create new mapper to use mocked calculator
        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        split_record = dict(self.valid_token_record)
        split_record["_openai_token_type"] = "input"
        split_record["_openai_token_count"] = 1000

        cost_info = mapper._get_costs(split_record)

        assert isinstance(cost_info, CostInfo)
        assert cost_info.billed_cost == Decimal("0.02")
        assert cost_info.currency == "USD"

        mock_calculator.calculate_token_cost.assert_called_once_with(
            "gpt-4o", input_tokens=1000, output_tokens=0
        )

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_costs_split_token_record_output(self, mock_calculator_class):
        """Test cost extraction for split output token record."""
        mock_calculator = Mock()
        mock_calculator.calculate_token_cost.return_value = {"total": 0.04}
        mock_calculator_class.return_value = mock_calculator

        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        split_record = dict(self.valid_token_record)
        split_record["_openai_token_type"] = "output"
        split_record["_openai_token_count"] = 500

        cost_info = mapper._get_costs(split_record)

        assert cost_info.billed_cost == Decimal("0.04")
        mock_calculator.calculate_token_cost.assert_called_once_with(
            "gpt-4o", input_tokens=0, output_tokens=500
        )

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_costs_regular_record(self, mock_calculator_class):
        """Test cost extraction for regular record."""
        mock_calculator = Mock()
        mock_calculator.calculate_costs.return_value = {"total": 0.06}
        mock_calculator_class.return_value = mock_calculator

        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        cost_info = mapper._get_costs(self.valid_token_record)

        assert cost_info.billed_cost == Decimal("0.06")
        mock_calculator.calculate_costs.assert_called_once()

    def test_get_account_info_with_org(self):
        """Test account info extraction with organization."""
        account_info = self.mapper._get_account_info(self.valid_token_record)

        assert isinstance(account_info, AccountInfo)
        assert account_info.billing_account_id == "openai_org_org-1234567890abcdef"
        assert (
            account_info.billing_account_name
            == "OpenAI Organization org-1234567890abcdef"
        )
        assert account_info.billing_account_type == "BillingAccount"
        assert account_info.sub_account_id == "sk-admin-abc123"
        assert account_info.sub_account_name == "API Key: ...n-abc123"  # Last 8 chars
        assert account_info.sub_account_type == "APIKey"

    def test_get_account_info_no_org(self):
        """Test account info extraction without organization."""
        config = {"provider_type": "openai", "provider_id": "test-openai"}
        mapper = OpenAIFocusMapper(provider_config=config)

        account_info = mapper._get_account_info(self.valid_token_record)

        assert account_info.billing_account_id == "openai_org_unknown"
        assert account_info.billing_account_name == "OpenAI Organization"

    def test_get_time_periods_with_bucket_times(self):
        """Test time period extraction with bucket times."""
        time_info = self.mapper._get_time_periods(self.valid_token_record)

        assert isinstance(time_info, TimeInfo)
        expected_start = datetime.fromtimestamp(1704067200, tz=UTC)
        expected_end = datetime.fromtimestamp(1704153600, tz=UTC)
        assert time_info.charge_period_start == expected_start
        assert time_info.charge_period_end == expected_end

    def test_get_time_periods_no_bucket_times(self):
        """Test time period extraction without bucket times."""
        record = dict(self.valid_token_record)
        del record["bucket_start_time"]
        del record["bucket_end_time"]

        time_info = self.mapper._get_time_periods(record)

        # Should fallback to current day
        assert time_info.charge_period_start is not None
        assert time_info.charge_period_end is not None

    def test_get_time_periods_invalid_timestamps(self):
        """Test time period extraction with invalid timestamps."""
        record = dict(self.valid_token_record)
        record["bucket_start_time"] = "invalid"
        record["bucket_end_time"] = "also_invalid"

        time_info = self.mapper._get_time_periods(record)

        # Should fallback to current time
        assert time_info.charge_period_start is not None
        assert time_info.charge_period_end is not None

    def test_get_service_info_gpt4(self):
        """Test service info extraction for GPT-4."""
        service_info = self.mapper._get_service_info(self.valid_token_record)

        assert isinstance(service_info, ServiceInfo)
        assert service_info.service_name == "Chat Completions"
        assert service_info.service_category == "AI and Machine Learning"
        assert service_info.provider_name == "OpenAI"
        assert service_info.service_subcategory == "Advanced Models"

    def test_get_service_info_dall_e(self):
        """Test service info extraction for DALL-E."""
        service_info = self.mapper._get_service_info(self.valid_image_record)

        assert service_info.service_name == "Image Generation"
        assert service_info.service_subcategory == "DALL-E 3"

    def test_get_service_info_whisper(self):
        """Test service info extraction for Whisper."""
        service_info = self.mapper._get_service_info(self.valid_audio_record)

        assert service_info.service_name == "Speech to Text"
        assert service_info.service_subcategory == "Speech-to-Text"

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_charge_info_split_token_record(self, mock_calculator_class):
        """Test charge info extraction for split token record."""
        mock_calculator = Mock()
        mock_calculator_class.return_value = mock_calculator

        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        split_record = dict(self.valid_token_record)
        split_record["_openai_token_type"] = "input"
        split_record["_openai_token_count"] = 1000

        # Mock the _get_costs method
        with patch.object(mapper, "_get_costs") as mock_get_costs:
            mock_get_costs.return_value = Mock(billed_cost=Decimal("0.02"))

            charge_info = mapper._get_charge_info(split_record)

            assert isinstance(charge_info, ChargeInfo)
            assert charge_info.charge_category == "Usage"
            assert "1,000 input tokens" in charge_info.charge_description
            assert charge_info.pricing_quantity == Decimal("1000")
            assert charge_info.pricing_unit == "tokens"

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_charge_info_image_record(self, mock_calculator_class):
        """Test charge info extraction for image record."""
        mock_calculator = Mock()
        mock_calculator_class.return_value = mock_calculator

        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        with patch.object(mapper, "_get_costs") as mock_get_costs:
            mock_get_costs.return_value = Mock(billed_cost=Decimal("0.20"))

            charge_info = mapper._get_charge_info(self.valid_image_record)

            assert "5 images" in charge_info.charge_description
            assert charge_info.pricing_quantity == Decimal("5")
            assert charge_info.pricing_unit == "images"

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_charge_info_audio_record(self, mock_calculator_class):
        """Test charge info extraction for audio record."""
        mock_calculator = Mock()
        mock_calculator_class.return_value = mock_calculator

        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        with patch.object(mapper, "_get_costs") as mock_get_costs:
            mock_get_costs.return_value = Mock(billed_cost=Decimal("0.018"))

            charge_info = mapper._get_charge_info(self.valid_audio_record)

            assert "5.00 minutes" in charge_info.charge_description
            assert charge_info.pricing_quantity == Decimal("300")
            assert charge_info.pricing_unit == "seconds"

    def test_get_resource_info(self):
        """Test resource info extraction."""
        resource_info = self.mapper._get_resource_info(self.valid_token_record)

        assert isinstance(resource_info, ResourceInfo)
        assert resource_info.resource_id == "gpt-4o"
        assert resource_info.resource_name == "OpenAI Model: gpt-4o"
        assert resource_info.resource_type == "AI Model"

    def test_get_usage_info_split_record(self):
        """Test usage info extraction for split record."""
        split_record = dict(self.valid_token_record)
        split_record["_openai_token_type"] = "input"
        split_record["_openai_token_count"] = 1000

        usage_info = self.mapper._get_usage_info(split_record)

        assert isinstance(usage_info, UsageInfo)
        assert usage_info.consumed_quantity == Decimal("1000")
        assert usage_info.consumed_unit == "tokens"

    @patch("providers.openai.mapper.OpenAICostCalculator")
    def test_get_usage_info_regular_record(self, mock_calculator_class):
        """Test usage info extraction for regular record."""
        mock_calculator = Mock()
        mock_calculator_class.return_value = mock_calculator

        mapper = OpenAIFocusMapper(provider_config=self.provider_config)

        # Mock _get_charge_info to return expected values
        with patch.object(mapper, "_get_charge_info") as mock_charge_info:
            mock_charge_info.return_value = Mock(
                pricing_quantity=Decimal("1500"), pricing_unit="tokens"
            )

            usage_info = mapper._get_usage_info(self.valid_token_record)

            assert usage_info.consumed_quantity == Decimal("1500")
            assert usage_info.consumed_unit == "tokens"

    def test_get_tags_basic(self):
        """Test tag extraction."""
        tags = self.mapper._get_tags(self.valid_token_record)

        assert isinstance(tags, dict)
        assert tags["openai_model"] == "gpt-4o"
        assert tags["openai_api_key_id"] == "sk-admin-abc123"
        assert tags["openai_usage_type"] == "tokens"
        assert tags["openai_object_type"] == "usage_aggregation"
        assert tags["openai_organization_id"] == "org-1234567890abcdef"
        assert tags["openai_input_tokens"] == "1000"
        assert tags["openai_output_tokens"] == "500"

    def test_get_tags_split_record(self):
        """Test tag extraction for split record."""
        split_record = dict(self.valid_token_record)
        split_record["_openai_token_type"] = "input"

        tags = self.mapper._get_tags(split_record)

        assert tags["openai_token_type"] == "input"

    def test_get_tags_no_org(self):
        """Test tag extraction without organization."""
        config = {"provider_type": "openai", "provider_id": "test-openai"}
        mapper = OpenAIFocusMapper(provider_config=config)

        tags = mapper._get_tags(self.valid_token_record)

        assert "openai_organization_id" not in tags

    def test_get_provider_extensions_split_record(self):
        """Test provider extensions for split record."""
        split_record = dict(self.valid_token_record)
        split_record["_openai_token_type"] = "input"
        split_record["_openai_token_count"] = 1000

        extensions = self.mapper._get_provider_extensions(split_record)

        assert extensions["token_type"] == "input"
        assert extensions["input_tokens"] == 1000

    def test_get_provider_extensions_regular_record(self):
        """Test provider extensions for regular record."""
        extensions = self.mapper._get_provider_extensions(self.valid_token_record)

        assert extensions["api_key_id"] == "sk-admin-abc123"
        assert extensions["model"] == "gpt-4o"
        assert extensions["usage_type"] == "tokens"
        assert extensions["input_tokens"] == 1000
        assert extensions["output_tokens"] == 500

    def test_get_provider_extensions_image_record(self):
        """Test provider extensions for image record."""
        extensions = self.mapper._get_provider_extensions(self.valid_image_record)

        assert extensions["num_images"] == 5
        assert extensions["image_size"] == "1024x1024"

    def test_build_usage_data(self):
        """Test usage data building."""
        usage_data = self.mapper._build_usage_data(self.valid_token_record)

        expected = {
            "model": "gpt-4o",
            "usage_type": "tokens",
            "input_tokens": 1000,
            "output_tokens": 500,
            "num_images": 0,
            "image_size": "1024x1024",
            "duration_seconds": 0,
            "num_requests": 10,
        }
        assert usage_data == expected

    @pytest.mark.parametrize(
        "record,expected_type",
        [
            ({"input_tokens": 100}, "tokens"),
            ({"output_tokens": 50}, "tokens"),
            ({"num_images": 3}, "images"),
            ({"num_seconds": 120}, "audio"),
            ({"model": "gpt-4"}, "requests"),
        ],
    )
    def test_determine_usage_type(self, record, expected_type):
        """Test usage type determination."""
        usage_type = self.mapper._determine_usage_type(record)
        assert usage_type == expected_type

    @pytest.mark.parametrize(
        "model,expected_service",
        [
            ("gpt-4o", "Chat Completions"),
            ("gpt-3.5-turbo", "Chat Completions"),
            ("text-embedding-ada-002", "Text Embeddings"),
            ("dall-e-3", "Image Generation"),
            ("tts-1", "Text to Speech"),
            ("whisper-1", "Speech to Text"),
            ("text-moderation-latest", "OpenAI API"),
            ("unknown-model", "OpenAI API"),
        ],
    )
    def test_get_service_name(self, model, expected_service):
        """Test service name extraction from model."""
        service_name = self.mapper._get_service_name(model)
        assert service_name == expected_service

    @pytest.mark.parametrize(
        "model,expected_subcategory",
        [
            ("gpt-4o", "Advanced Models"),
            ("gpt-4o-mini", "Efficient Models"),
            ("gpt-3.5-turbo", "Standard Models"),
            ("text-embedding-3-large", "Large Embeddings"),
            ("text-embedding-3-small", "Standard Embeddings"),
            ("dall-e-3", "DALL-E 3"),
            ("dall-e-2", "DALL-E 2"),
            ("o1-preview", "Reasoning Models"),
            ("unknown-model", None),
        ],
    )
    def test_get_service_subcategory(self, model, expected_subcategory):
        """Test service subcategory extraction from model."""
        subcategory = self.mapper._get_service_subcategory(model)
        assert subcategory == expected_subcategory
