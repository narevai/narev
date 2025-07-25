"""
Unit tests for OpenAI Cost Calculator
"""

from unittest.mock import Mock, patch

from providers.openai.utils.cost_calculator import OpenAICostCalculator


class TestOpenAICostCalculator:
    """Test suite for OpenAICostCalculator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = OpenAICostCalculator()

    @patch("providers.openai.utils.cost_calculator.OpenAIPricing")
    def test_init(self, mock_pricing_class):
        """Test calculator initialization."""
        mock_pricing = Mock()
        mock_pricing_class.return_value = mock_pricing

        calculator = OpenAICostCalculator()

        assert calculator.pricing == mock_pricing
        mock_pricing_class.assert_called_once()

    def test_calculate_costs_tokens(self):
        """Test cost calculation for token usage."""
        usage_data = {
            "model": "gpt-4o",
            "usage_type": "tokens",
            "input_tokens": 1000,
            "output_tokens": 500,
        }

        with patch.object(self.calculator, "calculate_token_cost") as mock_token_cost:
            mock_token_cost.return_value = {"total": 0.06}

            result = self.calculator.calculate_costs(usage_data)

            assert result == {"total": 0.06}
            mock_token_cost.assert_called_once_with("gpt-4o", 1000, 500)

    def test_calculate_costs_images(self):
        """Test cost calculation for image usage."""
        usage_data = {
            "model": "dall-e-3",
            "usage_type": "images",
            "num_images": 5,
            "image_size": "1024x1024",
        }

        with patch.object(self.calculator, "calculate_image_cost") as mock_image_cost:
            mock_image_cost.return_value = {"total": 0.20}

            result = self.calculator.calculate_costs(usage_data)

            assert result == {"total": 0.20}
            mock_image_cost.assert_called_once_with("dall-e-3", 5, "1024x1024")

    def test_calculate_costs_audio(self):
        """Test cost calculation for audio usage."""
        usage_data = {
            "model": "whisper-1",
            "usage_type": "audio",
            "duration_seconds": 300,
        }

        with patch.object(self.calculator, "calculate_audio_cost") as mock_audio_cost:
            mock_audio_cost.return_value = {"total": 0.018}

            result = self.calculator.calculate_costs(usage_data)

            assert result == {"total": 0.018}
            mock_audio_cost.assert_called_once_with("whisper-1", 300)

    def test_calculate_costs_requests_fallback(self):
        """Test cost calculation fallback for requests."""
        usage_data = {
            "model": "unknown-model",
            "usage_type": "requests",
            "num_requests": 10,
        }

        result = self.calculator.calculate_costs(usage_data)

        expected = {
            "total": 0.01,
            "unit_price": 0.001,
            "breakdown": {"requests": 10},
        }
        assert result == expected

    def test_calculate_costs_default_requests(self):
        """Test cost calculation default to requests when no usage type."""
        usage_data = {"model": "unknown-model", "num_requests": 5}

        result = self.calculator.calculate_costs(usage_data)

        expected = {
            "total": 0.005,
            "unit_price": 0.001,
            "breakdown": {"requests": 5},
        }
        assert result == expected

    def test_calculate_token_cost_success(self):
        """Test successful token cost calculation."""
        mock_pricing_info = {
            "input": 0.0025,
            "output": 0.01,
        }

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_token_cost("gpt-4o", 1000, 500)

            expected = {
                "total": 0.0075,
                "input_cost": 0.0025,
                "output_cost": 0.005,
                "unit_price": 0.004999999999999999,
                "breakdown": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "input_cost": 0.0025,
                    "output_cost": 0.005,
                },
            }
            assert result == expected

    def test_calculate_token_cost_no_pricing(self):
        """Test token cost calculation with no pricing found."""
        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = None

            result = self.calculator.calculate_token_cost("unknown-model", 1000, 500)

            expected = {
                "total": 0.0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "unit_price": 0.0,
                "breakdown": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "input_cost": 0.0,
                    "output_cost": 0.0,
                },
            }
            assert result == expected

    def test_calculate_token_cost_exception_handling(self):
        """Test token cost calculation exception handling."""
        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.side_effect = Exception("Pricing error")

            result = self.calculator.calculate_token_cost("gpt-4o", 1000, 500)

            expected = {
                "total": 0.0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "unit_price": 0.0,
                "breakdown": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "input_cost": 0.0,
                    "output_cost": 0.0,
                },
            }
            assert result == expected

    def test_calculate_token_cost_zero_tokens(self):
        """Test token cost calculation with zero tokens."""
        mock_pricing_info = {"input": 0.0025, "output": 0.01}

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_token_cost("gpt-4o", 0, 0)

            assert result["total"] == 0.0
            assert result["input_cost"] == 0.0
            assert result["output_cost"] == 0.0

    def test_calculate_image_cost_success(self):
        """Test successful image cost calculation."""
        mock_pricing_info = {"per_unit": 0.04}

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_image_cost("dall-e-3", 5, "1024x1024")

            expected = {
                "total": 0.20,
                "unit_price": 0.04,
                "breakdown": {
                    "num_images": 5,
                    "image_size": "1024x1024",
                    "unit_price": 0.04,
                },
            }
            assert result == expected

    def test_calculate_image_cost_no_pricing(self):
        """Test image cost calculation with no pricing found."""
        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = None

            result = self.calculator.calculate_image_cost("dall-e-3", 5, "1024x1024")

            expected = {
                "total": 0.0,
                "unit_price": 0.0,
                "breakdown": {
                    "num_images": 5,
                    "image_size": "1024x1024",
                    "unit_price": 0.0,
                },
            }
            assert result == expected

    def test_calculate_image_cost_no_per_unit(self):
        """Test image cost calculation with no per_unit pricing."""
        mock_pricing_info = {"input": 0.01}

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_image_cost("dall-e-3", 5, "1024x1024")

            expected = {
                "total": 0.0,
                "unit_price": 0.0,
                "breakdown": {
                    "num_images": 5,
                    "image_size": "1024x1024",
                    "unit_price": 0.0,
                },
            }
            assert result == expected

    def test_calculate_audio_cost_success(self):
        """Test successful audio cost calculation."""
        mock_pricing_info = {"per_unit": 0.006}

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_audio_cost("whisper-1", 300)

            expected = {
                "total": 0.03,
                "unit_price": 0.006,
                "breakdown": {
                    "duration_seconds": 300,
                    "duration_minutes": 5.0,
                    "unit_price_per_minute": 0.006,
                },
            }
            assert result == expected

    def test_calculate_audio_cost_no_pricing(self):
        """Test audio cost calculation with no pricing found."""
        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = None

            result = self.calculator.calculate_audio_cost("whisper-1", 300)

            expected = {
                "total": 0.0,
                "unit_price": 0.0,
                "breakdown": {
                    "duration_seconds": 300,
                    "duration_minutes": 5.0,
                    "unit_price_per_minute": 0.0,
                },
            }
            assert result == expected

    def test_calculate_audio_cost_exception_handling(self):
        """Test audio cost calculation exception handling."""
        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.side_effect = Exception("Pricing error")

            result = self.calculator.calculate_audio_cost("whisper-1", 300)

            expected = {
                "total": 0.0,
                "unit_price": 0.0,
                "breakdown": {
                    "duration_seconds": 300,
                    "duration_minutes": 5.0,
                    "unit_price_per_minute": 0.0,
                },
            }
            assert result == expected

    def test_empty_token_cost_response(self):
        """Test empty token cost response."""
        result = OpenAICostCalculator._empty_token_cost_response(1000, 500)

        expected = {
            "total": 0.0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "unit_price": 0.0,
            "breakdown": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "input_cost": 0.0,
                "output_cost": 0.0,
            },
        }
        assert result == expected

    def test_empty_image_cost_response(self):
        """Test empty image cost response."""
        result = OpenAICostCalculator._empty_image_cost_response(5, "1024x1024")

        expected = {
            "total": 0.0,
            "unit_price": 0.0,
            "breakdown": {
                "num_images": 5,
                "image_size": "1024x1024",
                "unit_price": 0.0,
            },
        }
        assert result == expected

    def test_empty_audio_cost_response(self):
        """Test empty audio cost response."""
        result = OpenAICostCalculator._empty_audio_cost_response(300)

        expected = {
            "total": 0.0,
            "unit_price": 0.0,
            "breakdown": {
                "duration_seconds": 300,
                "duration_minutes": 5.0,
                "unit_price_per_minute": 0.0,
            },
        }
        assert result == expected

    def test_calculate_token_cost_only_input(self):
        """Test token cost calculation with only input tokens."""
        mock_pricing_info = {"input": 0.0025, "output": 0.01}

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_token_cost("gpt-4o", 1000, 0)

            assert result["input_cost"] == 0.0025
            assert result["output_cost"] == 0.0
            assert result["total"] == 0.0025

    def test_calculate_token_cost_only_output(self):
        """Test token cost calculation with only output tokens."""
        mock_pricing_info = {"input": 0.0025, "output": 0.01}

        with patch.object(self.calculator.pricing, "get_model_pricing") as mock_pricing:
            mock_pricing.return_value = mock_pricing_info

            result = self.calculator.calculate_token_cost("gpt-4o", 0, 500)

            assert result["input_cost"] == 0.0
            assert result["output_cost"] == 0.005
            assert result["total"] == 0.005

    def test_integration_with_pricing_module(self):
        """Test integration with actual pricing module."""
        calculator = OpenAICostCalculator()
        result = calculator.calculate_token_cost("nonexistent-model", 1000, 500)

        assert isinstance(result, dict)
        assert "total" in result
        assert "breakdown" in result
