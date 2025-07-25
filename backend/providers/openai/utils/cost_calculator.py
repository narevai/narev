"""
OpenAI Cost Calculator
Handles cost calculations for various OpenAI services.
"""

import logging
from typing import Any

from .pricing import OpenAIPricing

logger = logging.getLogger(__name__)


class OpenAICostCalculator:
    """Calculator for OpenAI service costs."""

    def __init__(self):
        """
        Initialize the cost calculator.

        Args:
            pricing_provider: Instance of OpenAIPricing or similar pricing provider.
                            If not provided, creates a new OpenAIPricing instance.
        """
        self.pricing = OpenAIPricing()

    def calculate_costs(self, usage_data: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate costs based on OpenAI pricing.

        Args:
            usage_data: Dictionary containing usage information including:
                - model: The model name
                - usage_type: Type of usage (tokens, images, audio, requests)
                - Additional fields based on usage_type

        Returns:
            Dictionary with cost information including total, unit_price, and breakdown
        """
        model = usage_data["model"]
        usage_type = usage_data.get("usage_type", "requests")

        if usage_type == "tokens":
            input_tokens = usage_data.get("input_tokens", 0)
            output_tokens = usage_data.get("output_tokens", 0)
            return self.calculate_token_cost(model, input_tokens, output_tokens)
        elif usage_type == "images":
            num_images = usage_data.get("num_images", 0)
            image_size = usage_data.get("image_size", "1024x1024")
            return self.calculate_image_cost(model, num_images, image_size)
        elif usage_type == "audio":
            duration = usage_data.get("duration_seconds", 0)
            return self.calculate_audio_cost(model, duration)
        else:
            # Request-based fallback
            num_requests = usage_data.get("num_requests", 1)
            return {
                "total": 0.001 * num_requests,
                "unit_price": 0.001,
                "breakdown": {"requests": num_requests},
            }

    def calculate_token_cost(
        self, model: str, input_tokens: int = 0, output_tokens: int = 0
    ) -> dict[str, Any]:
        """
        Calculate cost for token-based usage.

        Args:
            model: The model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary with cost breakdown
        """
        try:
            pricing_info = self.pricing.get_model_pricing(model)

            if not pricing_info:
                logger.warning(f"No pricing found for model: {model}")
                return self._empty_token_cost_response(input_tokens, output_tokens)

            # OpenAIPricing.get_model_pricing() returns pricing per 1K tokens
            input_price_per_1k = pricing_info.get("input", 0)
            output_price_per_1k = pricing_info.get("output", 0)

            # Calculate costs
            input_cost = float(input_tokens) * float(input_price_per_1k) / 1000.0
            output_cost = float(output_tokens) * float(output_price_per_1k) / 1000.0
            total_cost = input_cost + output_cost

            # Calculate average unit price
            total_tokens = input_tokens + output_tokens
            unit_price = total_cost / max(total_tokens, 1) * 1000  # per 1K tokens

            return {
                "total": total_cost,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "unit_price": unit_price,
                "breakdown": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "input_cost": input_cost,
                    "output_cost": output_cost,
                },
            }

        except Exception as e:
            logger.error(f"Error calculating token cost for model {model}: {e}")
            return self._empty_token_cost_response(input_tokens, output_tokens)

    def calculate_image_cost(
        self, model: str, num_images: int, image_size: str
    ) -> dict[str, Any]:
        """
        Calculate cost for image generation.

        Args:
            model: The model name
            num_images: Number of images to generate
            image_size: Size of the images

        Returns:
            Dictionary with cost breakdown
        """
        try:
            pricing_info = self.pricing.get_model_pricing(model)

            if not pricing_info or "per_unit" not in pricing_info:
                logger.warning(f"No image pricing found for model: {model}")
                return self._empty_image_cost_response(num_images, image_size)

            unit_price = float(pricing_info["per_unit"])
            total_cost = unit_price * num_images

            return {
                "total": total_cost,
                "unit_price": unit_price,
                "breakdown": {
                    "num_images": num_images,
                    "image_size": image_size,
                    "unit_price": unit_price,
                },
            }

        except Exception as e:
            logger.error(f"Error calculating image cost for model {model}: {e}")
            return self._empty_image_cost_response(num_images, image_size)

    def calculate_audio_cost(
        self, model: str, duration_seconds: float
    ) -> dict[str, Any]:
        """
        Calculate cost for audio processing.

        Args:
            model: The model name
            duration_seconds: Duration of audio in seconds

        Returns:
            Dictionary with cost breakdown
        """
        try:
            pricing_info = self.pricing.get_model_pricing(model)

            if not pricing_info or "per_unit" not in pricing_info:
                logger.warning(f"No audio pricing found for model: {model}")
                return self._empty_audio_cost_response(duration_seconds)

            unit_price_per_minute = float(pricing_info["per_unit"])
            duration_minutes = duration_seconds / 60
            total_cost = unit_price_per_minute * duration_minutes

            return {
                "total": total_cost,
                "unit_price": unit_price_per_minute,
                "breakdown": {
                    "duration_seconds": duration_seconds,
                    "duration_minutes": duration_minutes,
                    "unit_price_per_minute": unit_price_per_minute,
                },
            }

        except Exception as e:
            logger.error(f"Error calculating audio cost for model {model}: {e}")
            return self._empty_audio_cost_response(duration_seconds)

    @staticmethod
    def _empty_token_cost_response(
        input_tokens: int, output_tokens: int
    ) -> dict[str, Any]:
        """Return empty cost response for token-based usage."""
        return {
            "total": 0.0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "unit_price": 0.0,
            "breakdown": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_cost": 0.0,
                "output_cost": 0.0,
            },
        }

    @staticmethod
    def _empty_image_cost_response(num_images: int, image_size: str) -> dict[str, Any]:
        """Return empty cost response for image generation."""
        return {
            "total": 0.0,
            "unit_price": 0.0,
            "breakdown": {
                "num_images": num_images,
                "image_size": image_size,
                "unit_price": 0.0,
            },
        }

    @staticmethod
    def _empty_audio_cost_response(duration_seconds: float) -> dict[str, Any]:
        """Return empty cost response for audio processing."""
        return {
            "total": 0.0,
            "unit_price": 0.0,
            "breakdown": {
                "duration_seconds": duration_seconds,
                "duration_minutes": duration_seconds / 60,
                "unit_price_per_minute": 0.0,
            },
        }
