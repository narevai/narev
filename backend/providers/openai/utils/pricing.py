# providers/openai/pricing.py
"""
OpenAI Pricing Information - Updated January 2025
"""

import re
from decimal import Decimal


class OpenAIPricing:
    """OpenAI pricing information and calculators."""

    # Token-based pricing (price per 1M tokens)
    TOKEN_PRICING = {
        # GPT-4.1 models (NEW)
        "gpt-4.1": (Decimal("2.00"), Decimal("8.00"), "USD"),
        "gpt-4.1-2025-04-14": (Decimal("2.00"), Decimal("8.00"), "USD"),
        # GPT-4.1 mini (NEW)
        "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60"), "USD"),
        "gpt-4.1-mini-2025-04-14": (Decimal("0.40"), Decimal("1.60"), "USD"),
        # GPT-4.1 nano (NEW)
        "gpt-4.1-nano": (Decimal("0.10"), Decimal("0.40"), "USD"),
        "gpt-4.1-nano-2025-04-14": (Decimal("0.10"), Decimal("0.40"), "USD"),
        # GPT-4.5 preview (NEW)
        "gpt-4.5-preview": (Decimal("75.00"), Decimal("150.00"), "USD"),
        "gpt-4.5-preview-2025-02-27": (Decimal("75.00"), Decimal("150.00"), "USD"),
        # GPT-4o models (UPDATED)
        "gpt-4o": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-2024-11-20": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-2024-08-06": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-2024-05-13": (Decimal("5.00"), Decimal("15.00"), "USD"),
        # GPT-4o audio preview (NEW)
        "gpt-4o-audio-preview": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-audio-preview-2025-06-03": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-audio-preview-2024-12-17": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-audio-preview-2024-10-01": (Decimal("2.50"), Decimal("10.00"), "USD"),
        # GPT-4o realtime preview (UPDATED)
        "gpt-4o-realtime-preview": (Decimal("5.00"), Decimal("20.00"), "USD"),
        "gpt-4o-realtime-preview-2025-06-03": (
            Decimal("5.00"),
            Decimal("20.00"),
            "USD",
        ),
        "gpt-4o-realtime-preview-2024-12-17": (
            Decimal("5.00"),
            Decimal("20.00"),
            "USD",
        ),
        "gpt-4o-realtime-preview-2024-10-01": (
            Decimal("5.00"),
            Decimal("20.00"),
            "USD",
        ),
        # GPT-4o mini
        "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60"), "USD"),
        "gpt-4o-mini-2024-07-18": (Decimal("0.15"), Decimal("0.60"), "USD"),
        # GPT-4o mini audio preview (NEW)
        "gpt-4o-mini-audio-preview": (Decimal("0.15"), Decimal("0.60"), "USD"),
        "gpt-4o-mini-audio-preview-2024-12-17": (
            Decimal("0.15"),
            Decimal("0.60"),
            "USD",
        ),
        # GPT-4o mini realtime preview (NEW)
        "gpt-4o-mini-realtime-preview": (Decimal("0.60"), Decimal("2.40"), "USD"),
        "gpt-4o-mini-realtime-preview-2024-12-17": (
            Decimal("0.60"),
            Decimal("2.40"),
            "USD",
        ),
        # o1 models (NEW)
        "o1": (Decimal("15.00"), Decimal("60.00"), "USD"),
        "o1-2024-12-17": (Decimal("15.00"), Decimal("60.00"), "USD"),
        "o1-preview-2024-09-12": (Decimal("15.00"), Decimal("60.00"), "USD"),
        # o1 pro (NEW)
        "o1-pro": (Decimal("150.00"), Decimal("600.00"), "USD"),
        "o1-pro-2025-03-19": (Decimal("150.00"), Decimal("600.00"), "USD"),
        # o3 models (NEW)
        "o3": (Decimal("2.00"), Decimal("8.00"), "USD"),
        "o3-2025-04-16": (Decimal("2.00"), Decimal("8.00"), "USD"),
        # o3 pro (NEW)
        "o3-pro": (Decimal("20.00"), Decimal("80.00"), "USD"),
        "o3-pro-2025-06-10": (Decimal("20.00"), Decimal("80.00"), "USD"),
        # o3 deep research (NEW)
        "o3-deep-research": (Decimal("10.00"), Decimal("40.00"), "USD"),
        "o3-deep-research-2025-06-26": (Decimal("10.00"), Decimal("40.00"), "USD"),
        # o4 mini (NEW)
        "o4-mini": (Decimal("1.10"), Decimal("4.40"), "USD"),
        "o4-mini-2025-04-16": (Decimal("1.10"), Decimal("4.40"), "USD"),
        # o4 mini deep research (NEW)
        "o4-mini-deep-research": (Decimal("2.00"), Decimal("8.00"), "USD"),
        "o4-mini-deep-research-2025-06-26": (Decimal("2.00"), Decimal("8.00"), "USD"),
        # o3 mini (NEW)
        "o3-mini": (Decimal("1.10"), Decimal("4.40"), "USD"),
        "o3-mini-2025-01-31": (Decimal("1.10"), Decimal("4.40"), "USD"),
        # o1 mini (NEW)
        "o1-mini": (Decimal("1.10"), Decimal("4.40"), "USD"),
        "o1-mini-2024-09-12": (Decimal("1.10"), Decimal("4.40"), "USD"),
        # Codex mini (NEW)
        "codex-mini-latest": (Decimal("1.50"), Decimal("6.00"), "USD"),
        # Search models (NEW)
        "gpt-4o-mini-search-preview": (Decimal("0.15"), Decimal("0.60"), "USD"),
        "gpt-4o-mini-search-preview-2025-03-11": (
            Decimal("0.15"),
            Decimal("0.60"),
            "USD",
        ),
        "gpt-4o-search-preview": (Decimal("2.50"), Decimal("10.00"), "USD"),
        "gpt-4o-search-preview-2025-03-11": (Decimal("2.50"), Decimal("10.00"), "USD"),
        # Computer use (NEW)
        "computer-use-preview": (Decimal("3.00"), Decimal("12.00"), "USD"),
        "computer-use-preview-2025-03-11": (Decimal("3.00"), Decimal("12.00"), "USD"),
        # GPT Image 1 (NEW) - tylko input
        "gpt-image-1": (Decimal("5.00"), Decimal("0.00"), "USD"),
        # ChatGPT-4o (NEW)
        "chatgpt-4o-latest": (Decimal("5.00"), Decimal("15.00"), "USD"),
        # GPT-4 Turbo (existing)
        "gpt-4-turbo": (Decimal("10.00"), Decimal("30.00"), "USD"),
        "gpt-4-turbo-2024-04-09": (Decimal("10.00"), Decimal("30.00"), "USD"),
        "gpt-4-0125-preview": (Decimal("10.00"), Decimal("30.00"), "USD"),
        "gpt-4-1106-preview": (Decimal("10.00"), Decimal("30.00"), "USD"),
        "gpt-4-1106-vision-preview": (Decimal("10.00"), Decimal("30.00"), "USD"),
        # GPT-4 (existing)
        "gpt-4": (Decimal("30.00"), Decimal("60.00"), "USD"),
        "gpt-4-0613": (Decimal("30.00"), Decimal("60.00"), "USD"),
        "gpt-4-0314": (Decimal("30.00"), Decimal("60.00"), "USD"),
        "gpt-4-32k": (Decimal("60.00"), Decimal("120.00"), "USD"),
        # GPT-3.5 Turbo (updated)
        "gpt-3.5-turbo": (Decimal("0.50"), Decimal("1.50"), "USD"),
        "gpt-3.5-turbo-0125": (Decimal("0.50"), Decimal("1.50"), "USD"),
        "gpt-3.5-turbo-1106": (Decimal("1.00"), Decimal("2.00"), "USD"),
        "gpt-3.5-turbo-0613": (Decimal("1.50"), Decimal("2.00"), "USD"),
        "gpt-3.5-0301": (Decimal("1.50"), Decimal("2.00"), "USD"),
        "gpt-3.5-turbo-instruct": (Decimal("1.50"), Decimal("2.00"), "USD"),
        "gpt-3.5-turbo-16k-0613": (Decimal("3.00"), Decimal("4.00"), "USD"),
        # Embedding models (updated)
        "text-embedding-3-large": (Decimal("0.13"), Decimal("0.00"), "USD"),
        "text-embedding-3-small": (Decimal("0.02"), Decimal("0.00"), "USD"),
        "text-embedding-ada-002": (Decimal("0.10"), Decimal("0.00"), "USD"),
        # Other models
        "davinci-002": (Decimal("2.00"), Decimal("2.00"), "USD"),
        "babbage-002": (Decimal("0.40"), Decimal("0.40"), "USD"),
    }

    # Audio token pricing (price per 1M tokens) - UPDATED
    AUDIO_TOKEN_PRICING = {
        "gpt-4o-audio-preview-2025-06-03": (Decimal("40.00"), Decimal("80.00"), "USD"),
        "gpt-4o-audio-preview-2024-12-17": (Decimal("40.00"), Decimal("80.00"), "USD"),
        "gpt-4o-audio-preview-2024-10-01": (
            Decimal("100.00"),
            Decimal("200.00"),
            "USD",
        ),
        "gpt-4o-mini-audio-preview-2024-12-17": (
            Decimal("10.00"),
            Decimal("20.00"),
            "USD",
        ),
        "gpt-4o-realtime-preview-2024-12-17": (
            Decimal("40.00"),
            Decimal("80.00"),
            "USD",
        ),
        "gpt-4o-realtime-preview-2025-06-03": (
            Decimal("40.00"),
            Decimal("80.00"),
            "USD",
        ),
        "gpt-4o-realtime-preview-2024-10-01": (
            Decimal("100.00"),
            Decimal("200.00"),
            "USD",
        ),
        "gpt-4o-mini-realtime-preview-2024-12-17": (
            Decimal("10.00"),
            Decimal("20.00"),
            "USD",
        ),
    }

    # Image token pricing (price per 1M tokens) - NEW
    IMAGE_TOKEN_PRICING = {
        "gpt-image-1": (Decimal("10.00"), Decimal("40.00"), "USD"),
    }

    # Non-token based pricing - UPDATED
    NON_TOKEN_PRICING = {
        # Image generation - UPDATED
        "dall-e-3": {
            "price": Decimal("0.040"),
            "currency": "USD",
            "unit": "images",
        },  # 1024x1024 standard
        "dall-e-3-hd": {
            "price": Decimal("0.080"),
            "currency": "USD",
            "unit": "images",
        },  # 1024x1024 HD
        "dall-e-2": {
            "price": Decimal("0.020"),
            "currency": "USD",
            "unit": "images",
        },  # 1024x1024
        # GPT Image 1 pricing (NEW)
        "gpt-image-1-low": {
            "price": Decimal("0.011"),
            "currency": "USD",
            "unit": "images",
        },  # 1024x1024 low
        "gpt-image-1-medium": {
            "price": Decimal("0.042"),
            "currency": "USD",
            "unit": "images",
        },  # 1024x1024 medium
        "gpt-image-1-high": {
            "price": Decimal("0.167"),
            "currency": "USD",
            "unit": "images",
        },  # 1024x1024 high
        # Audio transcription/synthesis - UPDATED
        "whisper-1": {"price": Decimal("0.006"), "currency": "USD", "unit": "minutes"},
        "tts-1": {
            "price": Decimal("15.00"),
            "currency": "USD",
            "unit": "1m_characters",
        },
        "tts-1-hd": {
            "price": Decimal("30.00"),
            "currency": "USD",
            "unit": "1m_characters",
        },
        # New transcription models (token-based but also estimated per minute)
        "gpt-4o-transcribe": {
            "price": Decimal("0.006"),
            "currency": "USD",
            "unit": "minutes",
        },
        "gpt-4o-mini-transcribe": {
            "price": Decimal("0.003"),
            "currency": "USD",
            "unit": "minutes",
        },
        "gpt-4o-mini-tts": {
            "price": Decimal("0.015"),
            "currency": "USD",
            "unit": "minutes",
        },
        # Built-in tools (NEW)
        "code-interpreter": {
            "price": Decimal("0.03"),
            "currency": "USD",
            "unit": "containers",
        },
        "file-search-storage": {
            "price": Decimal("0.10"),
            "currency": "USD",
            "unit": "gb_days",
        },
        "file-search-tool": {
            "price": Decimal("2.50"),
            "currency": "USD",
            "unit": "1k_calls",
        },
        "web-search-gpt4": {
            "price": Decimal("25.00"),
            "currency": "USD",
            "unit": "1k_calls",
        },
        "web-search-o3": {
            "price": Decimal("10.00"),
            "currency": "USD",
            "unit": "1k_calls",
        },
    }

    FLEX_PRICING = {
        "o3-2025-04-16": (Decimal("1.00"), Decimal("4.00"), "USD"),
        "o4-mini-2025-04-16": (Decimal("0.55"), Decimal("2.20"), "USD"),
    }

    # Regex patterns for free models
    FREE_MODEL_PATTERNS = [
        r"^text-moderation.*",
        r"^omni-moderation.*",
    ]

    @classmethod
    def _is_free_model(cls, model_id: str) -> bool:
        """Check if model is free based on regex patterns."""
        for pattern in cls.FREE_MODEL_PATTERNS:
            if re.match(pattern, model_id):
                return True
        return False

    @classmethod
    def get_token_pricing(
        cls, model_id: str, flex_processing: bool = False
    ) -> tuple[Decimal, Decimal, str] | None:
        """Get token pricing: (input_per_1m, output_per_1m, currency)"""
        # Check flex processing first if enabled
        if flex_processing and model_id in cls.FLEX_PRICING:
            return cls.FLEX_PRICING[model_id]

        # Check text tokens
        if model_id in cls.TOKEN_PRICING:
            return cls.TOKEN_PRICING[model_id]
        # Check audio tokens
        if model_id in cls.AUDIO_TOKEN_PRICING:
            return cls.AUDIO_TOKEN_PRICING[model_id]
        # Check image tokens
        if model_id in cls.IMAGE_TOKEN_PRICING:
            return cls.IMAGE_TOKEN_PRICING[model_id]
        return None

    @classmethod
    def calculate_token_cost(
        cls,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        flex_processing: bool = False,
    ) -> dict[str, Decimal]:
        """Calculate cost for token usage."""
        pricing = cls.get_token_pricing(model_id, flex_processing)
        if not pricing:
            return {
                "input_cost": Decimal("0"),
                "output_cost": Decimal("0"),
                "total_cost": Decimal("0"),
                "currency": "USD",
            }

        input_price_per_1m, output_price_per_1m, currency = pricing

        input_cost = (
            Decimal(str(input_tokens)) / Decimal("1000000")
        ) * input_price_per_1m
        output_cost = (
            Decimal(str(output_tokens)) / Decimal("1000000")
        ) * output_price_per_1m

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "currency": currency,
            "flex_processing": flex_processing,
        }

    @classmethod
    def get_non_token_pricing(cls, model_id: str) -> dict | None:
        """Get non-token pricing info."""
        # Check explicit pricing first
        if model_id in cls.NON_TOKEN_PRICING:
            return cls.NON_TOKEN_PRICING[model_id]

        # Check if it's a free model
        if cls._is_free_model(model_id):
            return {"price": Decimal("0.00"), "currency": "USD", "unit": "requests"}

        return None

    @classmethod
    def estimate_non_token_cost(
        cls, model_id: str, usage_data: dict
    ) -> dict[str, Decimal]:
        """Estimate cost for non-token models."""
        pricing = cls.get_non_token_pricing(model_id)
        if not pricing:
            return {"total_cost": Decimal("0"), "currency": "USD"}

        price = pricing["price"]
        unit = pricing["unit"]
        currency = pricing["currency"]

        if unit == "images":
            quantity = usage_data.get("num_images", 0)
        elif unit == "minutes":
            seconds = usage_data.get("num_seconds", 0)
            quantity = seconds / 60 if seconds > 0 else 0
        elif unit == "1m_characters":
            requests = usage_data.get("num_model_requests", 0)
            # Estimate 200 chars per request
            quantity = (requests * 200) / 1000000 if requests > 0 else 0
        elif unit == "containers":
            quantity = usage_data.get("num_containers", 0)
        elif unit == "gb_days":
            quantity = usage_data.get("storage_gb_days", 0)
        elif unit == "1k_calls":
            quantity = usage_data.get("num_calls", 0) / 1000
        else:
            quantity = usage_data.get("num_model_requests", 0)

        total_cost = Decimal(str(quantity)) * price

        return {"total_cost": total_cost, "currency": currency}

    @classmethod
    def is_token_based_model(cls, model_id: str) -> bool:
        """Check if model uses token-based pricing."""
        return (
            model_id in cls.TOKEN_PRICING
            or model_id in cls.AUDIO_TOKEN_PRICING
            or model_id in cls.IMAGE_TOKEN_PRICING
            or model_id in cls.FLEX_PRICING
        )

    @classmethod
    def supports_flex_processing(cls, model_id: str) -> bool:
        """Check if model supports flex processing."""
        return model_id in cls.FLEX_PRICING

    @classmethod
    def get_all_supported_models(cls) -> list[str]:
        """Get all models with pricing data."""
        all_models = (
            list(cls.TOKEN_PRICING.keys())
            + list(cls.AUDIO_TOKEN_PRICING.keys())
            + list(cls.IMAGE_TOKEN_PRICING.keys())
            + list(cls.NON_TOKEN_PRICING.keys())
            + list(cls.FLEX_PRICING.keys())
        )
        return sorted(set(all_models))

    @classmethod
    def get_stats(cls) -> dict[str, int]:
        """Get simple pricing stats."""
        return {
            "text_token_models": len(cls.TOKEN_PRICING),
            "audio_token_models": len(cls.AUDIO_TOKEN_PRICING),
            "image_token_models": len(cls.IMAGE_TOKEN_PRICING),
            "non_token_models": len(cls.NON_TOKEN_PRICING),
            "flex_models": len(cls.FLEX_PRICING),
            "total_models": len(cls.get_all_supported_models()),
        }

    @classmethod
    def get_model_pricing(
        cls, model_id: str, flex_processing: bool = False
    ) -> dict[str, Decimal] | None:
        """Get pricing info for mapper compatibility."""
        # Token-based pricing
        token_pricing = cls.get_token_pricing(model_id, flex_processing)
        if token_pricing:
            input_price, output_price, currency = token_pricing
            return {
                "input": input_price
                / 1000,  # Convert to per 1K tokens for backward compatibility
                "output": output_price / 1000,
                "currency": currency,
                "flex_processing": flex_processing,
            }

        # Non-token pricing (including free models via regex)
        non_token = cls.get_non_token_pricing(model_id)
        if non_token:
            return {
                "per_unit": non_token["price"],
                "unit": non_token["unit"],
                "currency": non_token["currency"],
            }

        return None
