"""
OpenAI to FOCUS 1.2 Mapper
"""

import logging
from datetime import UTC, datetime
from typing import Any

from focus.mappers.base import (
    AccountInfo,
    BaseFocusMapper,
    ChargeInfo,
    CostInfo,
    ResourceInfo,
    ServiceInfo,
    TimeInfo,
    UsageInfo,
)

from .utils.cost_calculator import OpenAICostCalculator

logger = logging.getLogger(__name__)


class OpenAIFocusMapper(BaseFocusMapper):
    """
    OpenAI usage data to FOCUS 1.2 mapper.

    Handles record splitting for input/output tokens and cost calculation.
    """

    def __init__(self, provider_config: dict[str, Any]):
        """Initialize OpenAI mapper with cost calculator."""
        super().__init__(provider_config)
        self.cost_calculator = OpenAICostCalculator()
        self.organization_id = provider_config.get("organization_id", "")

    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate OpenAI usage record structure."""
        if not isinstance(record, dict) or not record:
            return False

        # Skip buckets (should be processed separately)
        if record.get("object") == "bucket":
            return False

        # Check required fields
        required_fields = ["object", "model", "api_key_id"]
        has_required = all(field in record for field in required_fields)

        # Check if has meaningful usage data
        has_usage = any(
            [
                record.get("input_tokens", 0) > 0,
                record.get("output_tokens", 0) > 0,
                record.get("num_images", 0) > 0,
                record.get("num_seconds", 0) > 0,
                record.get("num_model_requests", 0) > 0,
            ]
        )

        return has_required and has_usage

    def _split_record(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Split OpenAI record into input/output token records if needed.
        Override of base method to handle OpenAI token splitting.
        """
        # Check if this is token-based usage with both input and output
        input_tokens = record.get("input_tokens", 0)
        output_tokens = record.get("output_tokens", 0)

        if input_tokens > 0 and output_tokens > 0:
            records = []

            # Create input tokens record
            if input_tokens > 0:
                input_record = record.copy()
                input_record["_openai_token_type"] = "input"
                input_record["_openai_token_count"] = input_tokens
                records.append(input_record)

            # Create output tokens record
            if output_tokens > 0:
                output_record = record.copy()
                output_record["_openai_token_type"] = "output"
                output_record["_openai_token_count"] = output_tokens
                records.append(output_record)

            return records

        # Return single record for other cases
        return [record]

    def _get_costs(self, record: dict[str, Any]) -> CostInfo:
        """Extract cost information from OpenAI record."""
        model = record["model"]

        # Check if this is a split token record
        if "_openai_token_type" in record:
            token_type = record["_openai_token_type"]
            token_count = record["_openai_token_count"]

            # Calculate cost for specific token type
            if token_type == "input":
                costs = self.cost_calculator.calculate_token_cost(
                    model, input_tokens=token_count, output_tokens=0
                )
            else:  # output
                costs = self.cost_calculator.calculate_token_cost(
                    model, input_tokens=0, output_tokens=token_count
                )
        else:
            # Calculate costs for entire usage
            usage_data = self._build_usage_data(record)
            costs = self.cost_calculator.calculate_costs(usage_data)

        total_cost = self.safe_decimal(costs["total"])

        return CostInfo(
            billed_cost=total_cost,
            effective_cost=total_cost,
            list_cost=total_cost,
            contracted_cost=total_cost,
            currency="USD",
        )

    def _get_account_info(self, record: dict[str, Any]) -> AccountInfo:
        """Extract account information from OpenAI record."""
        api_key_id = record["api_key_id"]

        billing_account_id = (
            f"openai_org_{self.organization_id}"
            if self.organization_id
            else "openai_org_unknown"
        )
        billing_account_name = (
            f"OpenAI Organization {self.organization_id}"
            if self.organization_id
            else "OpenAI Organization"
        )

        return AccountInfo(
            billing_account_id=billing_account_id,
            billing_account_name=billing_account_name,
            billing_account_type="BillingAccount",
            sub_account_id=api_key_id,
            sub_account_name=f"API Key: ...{api_key_id[-8:]}",
            sub_account_type="APIKey",
        )

    def _get_time_periods(self, record: dict[str, Any]) -> TimeInfo:
        """Extract time periods from OpenAI record."""
        # Check for bucket times
        bucket_start = record.get("bucket_start_time") or record.get("start_time")
        bucket_end = record.get("bucket_end_time") or record.get("end_time")

        if bucket_start and bucket_end:
            try:
                charge_start = datetime.fromtimestamp(bucket_start, tz=UTC)
                charge_end = datetime.fromtimestamp(bucket_end, tz=UTC)
            except (ValueError, TypeError):
                charge_start = charge_end = datetime.now(UTC)
        else:
            # Fallback to current day
            charge_date = datetime.now(UTC)
            charge_start = charge_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            charge_end = charge_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

        return TimeInfo(charge_period_start=charge_start, charge_period_end=charge_end)

    def _get_service_info(self, record: dict[str, Any]) -> ServiceInfo:
        """Extract service information from OpenAI record."""
        model = record["model"]
        service_name = self._get_service_name(model)
        service_subcategory = self._get_service_subcategory(model)

        return ServiceInfo(
            service_name=service_name,
            service_category="AI and Machine Learning",
            provider_name="OpenAI",
            publisher_name="OpenAI",
            invoice_issuer_name="OpenAI",
            service_subcategory=service_subcategory,
        )

    def _get_charge_info(self, record: dict[str, Any]) -> ChargeInfo:
        """Extract charge information from OpenAI record."""
        model = record["model"]
        service_name = self._get_service_name(model)
        costs = self._get_costs(record)

        # Build description and quantity based on usage type
        if "_openai_token_type" in record:
            # Split token record
            token_type = record["_openai_token_type"]
            token_count = record["_openai_token_count"]
            description = (
                f"OpenAI {service_name} ({model}): "
                f"{token_count:,} {token_type} tokens - ${costs.billed_cost:.6f}"
            )
            pricing_quantity = self.safe_decimal(token_count)
            pricing_unit = "tokens"
        else:
            # Regular record
            usage_type = self._determine_usage_type(record)

            if usage_type == "tokens":
                total_tokens = record.get("input_tokens", 0) + record.get(
                    "output_tokens", 0
                )
                description = f"OpenAI {service_name} ({model}): {total_tokens:,} tokens - ${costs.billed_cost:.6f}"
                pricing_quantity = self.safe_decimal(total_tokens)
                pricing_unit = "tokens"
            elif usage_type == "images":
                num_images = record.get("num_images", 0)
                description = f"OpenAI {service_name} ({model}): {num_images} images - ${costs.billed_cost:.2f}"
                pricing_quantity = self.safe_decimal(num_images)
                pricing_unit = "images"
            elif usage_type == "audio":
                duration = record.get("num_seconds", 0)
                minutes = duration / 60
                description = f"OpenAI {service_name} ({model}): {minutes:.2f} minutes - ${costs.billed_cost:.4f}"
                pricing_quantity = self.safe_decimal(duration)
                pricing_unit = "seconds"
            else:
                num_requests = record.get("num_model_requests", 1)
                description = f"OpenAI {service_name} ({model}): {num_requests} requests - ${costs.billed_cost:.6f}"
                pricing_quantity = self.safe_decimal(num_requests)
                pricing_unit = "requests"

        return ChargeInfo(
            charge_category="Usage",
            charge_description=description,
            charge_frequency="Usage-Based",
            pricing_quantity=pricing_quantity,
            pricing_unit=pricing_unit,
        )

    def _get_resource_info(self, record: dict[str, Any]) -> ResourceInfo | None:
        """Extract resource information from OpenAI record."""
        model = record["model"]

        return ResourceInfo(
            resource_id=model,
            resource_name=f"OpenAI Model: {model}",
            resource_type="AI Model",
        )

    def _get_usage_info(self, record: dict[str, Any]) -> UsageInfo | None:
        """Extract usage information from OpenAI record."""
        if "_openai_token_type" in record:
            # Split token record
            return UsageInfo(
                consumed_quantity=self.safe_decimal(record["_openai_token_count"]),
                consumed_unit="tokens",
            )
        else:
            # Regular record - use same as pricing
            charge_info = self._get_charge_info(record)
            return UsageInfo(
                consumed_quantity=charge_info.pricing_quantity,
                consumed_unit=charge_info.pricing_unit,
            )

    def _get_tags(self, record: dict[str, Any]) -> dict[str, str] | None:
        """Extract tags from OpenAI record."""
        model = record["model"]
        api_key_id = record["api_key_id"]

        tags = {
            "openai_model": model,
            "openai_api_key_id": api_key_id,
            "openai_usage_type": self._determine_usage_type(record),
            "openai_object_type": record.get("object", ""),
        }

        # Add organization if available
        if self.organization_id:
            tags["openai_organization_id"] = self.organization_id

        # Add token type if split record
        if "_openai_token_type" in record:
            tags["openai_token_type"] = record["_openai_token_type"]

        # Add usage-specific tags
        if "input_tokens" in record:
            tags["openai_input_tokens"] = str(record.get("input_tokens", 0))
            tags["openai_output_tokens"] = str(record.get("output_tokens", 0))

        # Add optional fields
        for field in ["project_id", "user_id", "batch"]:
            if field in record and record[field]:
                tags[f"openai_{field}"] = str(record[field])

        return tags

    def _get_provider_extensions(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Extract OpenAI-specific data."""
        extensions = {
            "api_key_id": record["api_key_id"],
            "model": record["model"],
            "usage_type": self._determine_usage_type(record),
            "num_requests": record.get("num_model_requests", 1),
            "object_type": record.get("object", ""),
        }

        # Add token-specific data
        if "_openai_token_type" in record:
            extensions["token_type"] = record["_openai_token_type"]
            extensions[f"{record['_openai_token_type']}_tokens"] = record[
                "_openai_token_count"
            ]
        else:
            if "input_tokens" in record:
                extensions["input_tokens"] = record.get("input_tokens", 0)
                extensions["output_tokens"] = record.get("output_tokens", 0)
            if "num_images" in record:
                extensions["num_images"] = record.get("num_images", 0)
                extensions["image_size"] = record.get("image_size", "1024x1024")
            if "num_seconds" in record:
                extensions["duration_seconds"] = record.get("num_seconds", 0)

        # Add optional fields
        for field in ["project_id", "user_id", "batch"]:
            if field in record and record[field]:
                extensions[field] = record[field]

        return extensions

    # OpenAI-specific helper methods

    def _build_usage_data(self, record: dict[str, Any]) -> dict[str, Any]:
        """Build usage data for cost calculator."""
        return {
            "model": record["model"],
            "usage_type": self._determine_usage_type(record),
            "input_tokens": record.get("input_tokens", 0),
            "output_tokens": record.get("output_tokens", 0),
            "num_images": record.get("num_images", 0),
            "image_size": record.get("image_size", "1024x1024"),
            "duration_seconds": record.get("num_seconds", 0),
            "num_requests": record.get("num_model_requests", 1),
        }

    def _determine_usage_type(self, record: dict[str, Any]) -> str:
        """Determine usage type from record."""
        if "input_tokens" in record or "output_tokens" in record:
            return "tokens"
        elif "num_images" in record:
            return "images"
        elif "num_seconds" in record:
            return "audio"
        else:
            return "requests"

    def _get_service_name(self, model: str) -> str:
        """Get service name from model."""
        service_map = {
            "gpt": "Chat Completions",
            "text-embedding": "Text Embeddings",
            "dall-e": "Image Generation",
            "tts": "Text to Speech",
            "whisper": "Speech to Text",
            "moderation": "Content Moderation",
            "fine-tune": "Fine Tuning",
            "assistant": "Assistants API",
        }

        for prefix, service in service_map.items():
            if model.lower().startswith(prefix):
                return service

        # Fallback patterns
        model_lower = model.lower()
        if "gpt" in model_lower:
            return "Chat Completions"
        elif "embedding" in model_lower:
            return "Text Embeddings"
        elif "dall-e" in model_lower or "dalle" in model_lower:
            return "Image Generation"

        return "OpenAI API"

    def _get_service_subcategory(self, model: str) -> str | None:
        """Get service subcategory from model."""
        model_lower = model.lower()

        if "gpt-4" in model_lower:
            if "mini" in model_lower:
                return "Efficient Models"
            return "Advanced Models"
        elif "gpt-3.5" in model_lower:
            return "Standard Models"
        elif "text-embedding" in model_lower:
            return (
                "Large Embeddings" if "large" in model_lower else "Standard Embeddings"
            )
        elif "dall-e-3" in model_lower:
            return "DALL-E 3"
        elif "dall-e-2" in model_lower:
            return "DALL-E 2"
        elif "tts" in model_lower:
            return "Text-to-Speech"
        elif "whisper" in model_lower:
            return "Speech-to-Text"
        elif "moderation" in model_lower:
            return "Content Moderation"
        elif "o1" in model_lower:
            return "Reasoning Models"

        return None
