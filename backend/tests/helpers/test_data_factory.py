"""
Test data factory for creating consistent test data
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any


class TestDataFactory:
    """Factory class for creating test data objects."""

    @staticmethod
    def create_provider_data(
        provider_id: str = "test-provider-1",
        name: str = "test-openai",
        provider_type: str = "openai",
        **overrides,
    ) -> dict[str, Any]:
        """Create provider test data."""
        data = {
            "id": provider_id,
            "name": name,
            "provider_type": provider_type,
            "display_name": f"Test {provider_type.title()} Provider",
            "api_key_encrypted": "encrypted-test-key",
            "api_endpoint": f"https://api.{provider_type}.com",
            "is_active": True,
            "is_validated": True,
            "additional_config": {"organization_id": "org-test123"},
        }
        data.update(overrides)
        return data

    @staticmethod
    def create_billing_data(
        billing_id: str = "billing-test-1",
        provider_id: str = "provider-1",
        service_name: str = "GPT-4",
        cost: float = 10.50,
        **overrides,
    ) -> dict[str, Any]:
        """Create billing data for tests."""
        now = datetime.now(UTC)

        data = {
            "id": billing_id,
            "x_provider_id": provider_id,
            "provider_name": "Test Provider",
            "publisher_name": "Test Publisher",
            "invoice_issuer_name": "Test Issuer",
            "billed_cost": Decimal(str(cost)),
            "effective_cost": Decimal(str(cost)),
            "list_cost": Decimal(str(cost * 1.2)),
            "contracted_cost": Decimal(str(cost)),
            "billing_account_id": "account-1",
            "billing_account_name": "Test Account",
            "billing_account_type": "cloud",
            "billing_period_start": now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ),
            "billing_period_end": (
                now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=30)
            ),
            "charge_period_start": now,
            "charge_period_end": now + timedelta(hours=1),
            "billing_currency": "USD",
            "service_name": service_name,
            "service_category": "AI and Machine Learning",
            "charge_category": "Usage",
            "charge_description": f"{service_name} API usage",
            "sku_id": f"{service_name.lower().replace('-', '')}-tokens",
            "consumed_quantity": Decimal("1000"),
            "consumed_unit": "tokens",
            "tags": {"environment": "test", "team": "engineering"},
        }
        data.update(overrides)
        return data

    @staticmethod
    def create_pipeline_run_data(
        run_id: str = "test-run-1",
        provider_id: str = "provider-1",
        status: str = "completed",
        **overrides,
    ) -> dict[str, Any]:
        """Create pipeline run data for tests."""
        now = datetime.now(UTC)

        data = {
            "id": run_id,
            "provider_id": provider_id,
            "status": status,
            "started_at": now - timedelta(minutes=30),
            "completed_at": now
            if status in ["completed", "failed", "cancelled"]
            else None,
            "execution_time_seconds": 1800
            if status in ["completed", "failed"]
            else None,
            "records_processed": 1000 if status == "completed" else 0,
            "error_message": "Test error" if status == "failed" else None,
            "config": {"sync_type": "full", "batch_size": 100},
        }
        data.update(overrides)
        return data

    @staticmethod
    def create_multiple_billing_records(
        count: int = 10,
        provider_id: str = "provider-1",
        services: list | None = None,
    ) -> list:
        """Create multiple billing records for testing."""
        if services is None:
            services = ["GPT-4", "GPT-3.5", "DALL-E", "Whisper"]

        records = []
        now = datetime.now(UTC)

        for i in range(count):
            service = services[i % len(services)]
            cost = 5.0 + (i * 2.5)

            data = TestDataFactory.create_billing_data(
                billing_id=f"billing-test-{i}",
                provider_id=provider_id,
                service_name=service,
                cost=cost,
                charge_period_start=now - timedelta(days=count - i),
                charge_period_end=now - timedelta(days=count - i) + timedelta(hours=1),
                consumed_quantity=Decimal(str(100 * (i + 1))),
            )
            records.append(data)

        return records

    @staticmethod
    def create_analytics_test_data(
        days: int = 30, services: list | None = None
    ) -> list:
        """Create test data optimized for analytics testing."""
        if services is None:
            services = ["GPT-4", "GPT-3.5", "DALL-E", "Whisper", "Embeddings"]

        records = []
        now = datetime.now(UTC)

        for day in range(days):
            for service_idx, service in enumerate(services):
                # Vary costs to create interesting analytics patterns
                base_cost = 10.0 + (service_idx * 5.0)
                daily_variation = (day % 7) * 2.0  # Weekly pattern
                cost = base_cost + daily_variation

                data = TestDataFactory.create_billing_data(
                    billing_id=f"analytics-{day}-{service_idx}",
                    service_name=service,
                    cost=cost,
                    charge_period_start=now - timedelta(days=days - day),
                    charge_period_end=now
                    - timedelta(days=days - day)
                    + timedelta(hours=1),
                    consumed_quantity=Decimal(
                        str(cost * 10)
                    ),  # Quantity correlates with cost
                    tags={
                        "environment": "production" if day % 2 == 0 else "development",
                        "team": f"team-{service_idx % 3}",
                        "region": ["us-east-1", "us-west-2", "eu-west-1"][day % 3],
                    },
                )
                records.append(data)

        return records

    @staticmethod
    def create_export_test_data(formats: list = None) -> dict[str, Any]:
        """Create test data for export functionality testing."""
        if formats is None:
            formats = ["csv", "json", "focus", "parquet"]

        # Create diverse data to test all export scenarios
        records = []

        # Record with all fields populated
        records.append(
            TestDataFactory.create_billing_data(
                billing_id="export-complete-1", service_name="GPT-4", cost=25.50
            )
        )

        # Record with minimal fields
        minimal_data = TestDataFactory.create_billing_data(
            billing_id="export-minimal-1", service_name="GPT-3.5", cost=5.00
        )
        # Remove optional fields
        minimal_data["tags"] = {}
        minimal_data["additional_config"] = {}
        records.append(minimal_data)

        # Record with special characters (test CSV escaping)
        special_data = TestDataFactory.create_billing_data(
            billing_id="export-special-1",
            service_name='Service with "quotes" and, commas',
            cost=15.75,
        )
        records.append(special_data)

        return {
            "records": records,
            "expected_formats": formats,
            "test_scenarios": ["complete", "minimal", "special_chars"],
        }
