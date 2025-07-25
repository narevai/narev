"""
Unit tests for OpenAI Pricing Module
"""

from decimal import Decimal

import pytest

from providers.openai.utils.pricing import OpenAIPricing


class TestOpenAIPricing:
    """Test suite for OpenAIPricing class."""

    def test_get_token_pricing_existing_model(self):
        """Test token pricing retrieval for existing model."""
        result = OpenAIPricing.get_token_pricing("gpt-4o")

        assert result is not None
        input_price, output_price, currency = result
        assert isinstance(input_price, Decimal)
        assert isinstance(output_price, Decimal)
        assert currency == "USD"
        assert input_price > 0
        assert output_price > 0

    def test_get_token_pricing_nonexistent_model(self):
        """Test token pricing retrieval for non-existent model."""
        result = OpenAIPricing.get_token_pricing("nonexistent-model")
        assert result is None

    def test_get_token_pricing_audio_model(self):
        """Test token pricing retrieval for audio model."""
        result = OpenAIPricing.get_token_pricing("gpt-4o-audio-preview-2024-12-17")

        assert result is not None
        input_price, output_price, currency = result
        assert isinstance(input_price, Decimal)
        assert isinstance(output_price, Decimal)
        assert currency == "USD"

    def test_get_token_pricing_image_token_model(self):
        """Test token pricing retrieval for image token model."""
        result = OpenAIPricing.get_token_pricing("gpt-image-1")

        assert result is not None
        input_price, output_price, currency = result
        assert isinstance(input_price, Decimal)
        assert output_price == Decimal("0.00")
        assert currency == "USD"

    def test_get_token_pricing_flex_processing(self):
        """Test token pricing with flex processing enabled."""
        result = OpenAIPricing.get_token_pricing("o3-2025-04-16", flex_processing=True)

        assert result is not None
        input_price, output_price, currency = result
        assert isinstance(input_price, Decimal)
        assert isinstance(output_price, Decimal)
        assert currency == "USD"

    def test_get_token_pricing_flex_priority(self):
        """Test that flex pricing takes priority when enabled."""
        regular_result = OpenAIPricing.get_token_pricing(
            "o3-2025-04-16", flex_processing=False
        )
        flex_result = OpenAIPricing.get_token_pricing(
            "o3-2025-04-16", flex_processing=True
        )

        assert regular_result != flex_result

    def test_calculate_token_cost_success(self):
        """Test successful token cost calculation."""
        result = OpenAIPricing.calculate_token_cost("gpt-4o", 1000, 500)

        assert "input_cost" in result
        assert "output_cost" in result
        assert "total_cost" in result
        assert "currency" in result
        assert result["currency"] == "USD"
        assert isinstance(result["input_cost"], Decimal)
        assert isinstance(result["output_cost"], Decimal)
        assert result["total_cost"] == result["input_cost"] + result["output_cost"]

    def test_calculate_token_cost_nonexistent_model(self):
        """Test token cost calculation for non-existent model."""
        result = OpenAIPricing.calculate_token_cost("nonexistent-model", 1000, 500)

        assert result["input_cost"] == Decimal("0")
        assert result["output_cost"] == Decimal("0")
        assert result["total_cost"] == Decimal("0")
        assert result["currency"] == "USD"

    def test_calculate_token_cost_zero_tokens(self):
        """Test token cost calculation with zero tokens."""
        result = OpenAIPricing.calculate_token_cost("gpt-4o", 0, 0)

        assert result["input_cost"] == Decimal("0")
        assert result["output_cost"] == Decimal("0")
        assert result["total_cost"] == Decimal("0")

    def test_calculate_token_cost_flex_processing(self):
        """Test token cost calculation with flex processing."""
        result = OpenAIPricing.calculate_token_cost(
            "o3-2025-04-16", 1000, 500, flex_processing=True
        )

        assert "flex_processing" in result
        assert result["flex_processing"] is True

    def test_get_non_token_pricing_dall_e(self):
        """Test non-token pricing for DALL-E."""
        result = OpenAIPricing.get_non_token_pricing("dall-e-3")

        assert result is not None
        assert "price" in result
        assert "currency" in result
        assert "unit" in result
        assert result["unit"] == "images"
        assert isinstance(result["price"], Decimal)

    def test_get_non_token_pricing_whisper(self):
        """Test non-token pricing for Whisper."""
        result = OpenAIPricing.get_non_token_pricing("whisper-1")

        assert result is not None
        assert result["unit"] == "minutes"
        assert isinstance(result["price"], Decimal)

    def test_get_non_token_pricing_free_model(self):
        """Test non-token pricing for free model."""
        result = OpenAIPricing.get_non_token_pricing("text-moderation-latest")

        assert result is not None
        assert result["price"] == Decimal("0.00")
        assert result["unit"] == "requests"

    def test_get_non_token_pricing_nonexistent(self):
        """Test non-token pricing for non-existent model."""
        result = OpenAIPricing.get_non_token_pricing("nonexistent-model")
        assert result is None

    def test_is_free_model_moderation(self):
        """Test free model detection for moderation models."""
        assert OpenAIPricing._is_free_model("text-moderation-latest") is True
        assert OpenAIPricing._is_free_model("text-moderation-stable") is True
        assert OpenAIPricing._is_free_model("omni-moderation-latest") is True

    def test_is_free_model_non_free(self):
        """Test free model detection for paid models."""
        assert OpenAIPricing._is_free_model("gpt-4o") is False
        assert OpenAIPricing._is_free_model("dall-e-3") is False

    def test_estimate_non_token_cost_images(self):
        """Test non-token cost estimation for images."""
        usage_data = {"num_images": 5}
        result = OpenAIPricing.estimate_non_token_cost("dall-e-3", usage_data)

        assert "total_cost" in result
        assert "currency" in result
        assert result["currency"] == "USD"
        assert result["total_cost"] > Decimal("0")

    def test_estimate_non_token_cost_minutes(self):
        """Test non-token cost estimation for minutes."""
        usage_data = {"num_seconds": 300}
        result = OpenAIPricing.estimate_non_token_cost("whisper-1", usage_data)

        assert result["total_cost"] > Decimal("0")
        assert result["currency"] == "USD"

    def test_estimate_non_token_cost_characters(self):
        """Test non-token cost estimation for characters."""
        usage_data = {"num_model_requests": 100}
        result = OpenAIPricing.estimate_non_token_cost("tts-1", usage_data)

        assert result["total_cost"] > Decimal("0")
        assert result["currency"] == "USD"

    def test_estimate_non_token_cost_free_model(self):
        """Test non-token cost estimation for free model."""
        usage_data = {"num_model_requests": 100}
        result = OpenAIPricing.estimate_non_token_cost(
            "text-moderation-latest", usage_data
        )

        assert result["total_cost"] == Decimal("0")

    def test_is_token_based_model_true(self):
        """Test token-based model detection for token models."""
        assert OpenAIPricing.is_token_based_model("gpt-4o") is True
        assert (
            OpenAIPricing.is_token_based_model("gpt-4o-audio-preview-2024-12-17")
            is True
        )
        assert OpenAIPricing.is_token_based_model("gpt-image-1") is True
        assert OpenAIPricing.is_token_based_model("o3-2025-04-16") is True

    def test_is_token_based_model_false(self):
        """Test token-based model detection for non-token models."""
        assert OpenAIPricing.is_token_based_model("dall-e-3") is False
        assert OpenAIPricing.is_token_based_model("whisper-1") is False
        assert OpenAIPricing.is_token_based_model("nonexistent-model") is False

    def test_supports_flex_processing_true(self):
        """Test flex processing support detection for supported models."""
        assert OpenAIPricing.supports_flex_processing("o3-2025-04-16") is True
        assert OpenAIPricing.supports_flex_processing("o4-mini-2025-04-16") is True

    def test_supports_flex_processing_false(self):
        """Test flex processing support detection for unsupported models."""
        assert OpenAIPricing.supports_flex_processing("gpt-4o") is False
        assert OpenAIPricing.supports_flex_processing("dall-e-3") is False

    def test_get_all_supported_models(self):
        """Test getting all supported models."""
        models = OpenAIPricing.get_all_supported_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "gpt-4o" in models
        assert "dall-e-3" in models
        assert "whisper-1" in models

        assert models == sorted(set(models))

    def test_get_stats(self):
        """Test pricing statistics."""
        stats = OpenAIPricing.get_stats()

        expected_keys = [
            "text_token_models",
            "audio_token_models",
            "image_token_models",
            "non_token_models",
            "flex_models",
            "total_models",
        ]

        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], int)
            assert stats[key] >= 0

    def test_get_model_pricing_token_based(self):
        """Test model pricing retrieval for token-based model."""
        result = OpenAIPricing.get_model_pricing("gpt-4o")

        assert result is not None
        assert "input" in result
        assert "output" in result
        assert "currency" in result
        assert result["currency"] == "USD"
        assert isinstance(result["input"], Decimal)
        assert isinstance(result["output"], Decimal)

    def test_get_model_pricing_non_token_based(self):
        """Test model pricing retrieval for non-token-based model."""
        result = OpenAIPricing.get_model_pricing("dall-e-3")

        assert result is not None
        assert "per_unit" in result
        assert "unit" in result
        assert "currency" in result
        assert result["unit"] == "images"
        assert isinstance(result["per_unit"], Decimal)

    def test_get_model_pricing_flex_processing(self):
        """Test model pricing retrieval with flex processing."""
        result = OpenAIPricing.get_model_pricing("o3-2025-04-16", flex_processing=True)

        assert result is not None
        assert "flex_processing" in result
        assert result["flex_processing"] is True

    def test_get_model_pricing_nonexistent(self):
        """Test model pricing retrieval for non-existent model."""
        result = OpenAIPricing.get_model_pricing("nonexistent-model")
        assert result is None

    @pytest.mark.parametrize(
        "model_id,expected_in_token_pricing",
        [
            ("gpt-4o", True),
            ("gpt-4o-mini", True),
            ("gpt-3.5-turbo", True),
            ("text-embedding-3-large", True),
            ("o1", True),
            ("dall-e-3", False),
            ("whisper-1", False),
        ],
    )
    def test_model_in_token_pricing(self, model_id, expected_in_token_pricing):
        """Test whether specific models are in token pricing."""
        result = OpenAIPricing.get_token_pricing(model_id)
        if expected_in_token_pricing:
            assert result is not None
        else:
            assert result is None

    @pytest.mark.parametrize(
        "model_id,expected_in_non_token_pricing",
        [
            ("dall-e-3", True),
            ("dall-e-2", True),
            ("whisper-1", True),
            ("tts-1", True),
            ("text-moderation-latest", True),
            ("gpt-4o", False),
            ("gpt-3.5-turbo", False),
        ],
    )
    def test_model_in_non_token_pricing(self, model_id, expected_in_non_token_pricing):
        """Test whether specific models are in non-token pricing."""
        result = OpenAIPricing.get_non_token_pricing(model_id)
        if expected_in_non_token_pricing:
            assert result is not None
        else:
            assert result is None

    def test_decimal_precision(self):
        """Test that all prices use Decimal for precision."""
        # Test token pricing
        result = OpenAIPricing.get_token_pricing("gpt-4o")
        if result:
            input_price, output_price, currency = result
            assert isinstance(input_price, Decimal)
            assert isinstance(output_price, Decimal)

        # Test non-token pricing
        result = OpenAIPricing.get_non_token_pricing("dall-e-3")
        if result:
            assert isinstance(result["price"], Decimal)

    def test_currency_consistency(self):
        """Test that all models use USD currency."""
        for model in ["gpt-4o", "gpt-3.5-turbo", "text-embedding-3-large"]:
            result = OpenAIPricing.get_token_pricing(model)
            if result:
                _, _, currency = result
                assert currency == "USD"

        for model in ["dall-e-3", "whisper-1", "tts-1"]:
            result = OpenAIPricing.get_non_token_pricing(model)
            if result:
                assert result["currency"] == "USD"
