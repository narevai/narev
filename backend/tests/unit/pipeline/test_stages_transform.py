import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from focus.models import FocusRecord
from pipeline.config import PipelineConfig
from pipeline.stages.transform import TransformStage


class TestTransformStage:
    """Test TransformStage."""

    @pytest.fixture
    def config(self):
        return PipelineConfig(
            transform_config={
                "batch_size": 100,
                "validate_focus": True,
                "strict_validation": False,
            }
        )

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def transform_stage(self, config, mock_db):
        return TransformStage(config, mock_db)

    @pytest.fixture
    def mock_mapper(self):
        mapper = Mock()
        mapper.map_to_focus.return_value = [
            FocusRecord(
                id=str(uuid.uuid4()),
                x_provider_id="test-provider",
                billed_cost=10.0,
                effective_cost=10.0,
                list_cost=12.0,
                contracted_cost=10.0,
                billing_account_id="account-1",
                billing_account_name="Test Account",
                billing_account_type="cloud",
                billing_period_start=datetime(2023, 1, 1, tzinfo=UTC),
                billing_period_end=datetime(2023, 1, 31, tzinfo=UTC),
                charge_period_start=datetime(2023, 1, 1, tzinfo=UTC),
                charge_period_end=datetime(2023, 1, 2, tzinfo=UTC),
                billing_currency="USD",
                service_name="Test Service",
                service_category="AI and Machine Learning",
                provider_name="Test Provider",
                publisher_name="Test Publisher",
                invoice_issuer_name="Test Issuer",
                charge_category="Usage",
                charge_description="Test charge",
            )
        ]
        return mapper

    @pytest.fixture
    def base_context(self, mock_mapper):
        return {
            "mapper": mock_mapper,
            "raw_records": [{"extracted_data": [{"usage": 100, "cost": 10.0}]}],
            "provider_type": "test_provider",
        }

    @pytest.mark.asyncio
    async def test_validate_input_success(self, transform_stage, base_context):
        await transform_stage.validate_input(base_context)

    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self, transform_stage):
        context = {"mapper": Mock()}

        with pytest.raises(ValueError, match="Missing required context fields"):
            await transform_stage.validate_input(context)

    @pytest.mark.asyncio
    async def test_validate_input_missing_mapper_method(
        self, transform_stage, base_context
    ):
        base_context["mapper"] = Mock()
        del base_context["mapper"].map_to_focus

        with pytest.raises(ValueError, match="Mapper missing required method"):
            await transform_stage.validate_input(base_context)

    @pytest.mark.asyncio
    async def test_execute_empty_records(self, transform_stage, mock_mapper):
        context = {
            "mapper": mock_mapper,
            "raw_records": [],
            "provider_type": "test_provider",
        }

        result = await transform_stage.execute(context)

        assert result.success is True
        assert result.records_processed == 0
        assert result.stage_name == "transform"
        assert result.data["transform_summary"]["transformed"] == 0

    @pytest.mark.asyncio
    async def test_execute_success(self, transform_stage, base_context):
        with patch.object(transform_stage, "_validate_focus_record", return_value=[]):
            result = await transform_stage.execute(base_context)

            assert result.success is True
            assert result.records_processed == 1
            assert len(result.data["focus_records"]) == 1
            assert len(result.data["transformed_records"]) == 1

    def test_transform_batch_success(self, transform_stage, mock_mapper):
        batch = [{"usage": 100, "cost": 10.0}]

        with patch.object(transform_stage, "_validate_focus_record", return_value=[]):
            result = transform_stage._transform_batch(batch, mock_mapper)

            assert len(result["transformed"]) == 1
            assert len(result["failed"]) == 0
            assert result["skipped"] == 0

    def test_transform_batch_mapper_failure(self, transform_stage):
        batch = [{"usage": 100, "cost": 10.0}]
        mock_mapper = Mock()
        mock_mapper.map_to_focus.side_effect = Exception("Mapping failed")

        result = transform_stage._transform_batch(batch, mock_mapper)

        assert len(result["transformed"]) == 0
        assert len(result["failed"]) == 1
        assert "Mapping failed" in result["failed"][0]["error"]

    def test_transform_batch_skip_empty(self, transform_stage):
        batch = [{"usage": 0}]
        mock_mapper = Mock()
        mock_mapper.map_to_focus.return_value = None  # Mapper skips record

        result = transform_stage._transform_batch(batch, mock_mapper)

        assert len(result["transformed"]) == 0
        assert len(result["failed"]) == 0
        assert result["skipped"] == 1

    def test_validate_focus_record_success(self, transform_stage):
        focus_record = FocusRecord(
            id=str(uuid.uuid4()),
            x_provider_id="test-provider",
            billed_cost=10.0,
            effective_cost=10.0,
            list_cost=12.0,
            contracted_cost=10.0,
            billing_account_id="account-1",
            billing_account_name="Test Account",
            billing_account_type="cloud",
            billing_period_start=datetime(2023, 1, 1, tzinfo=UTC),
            billing_period_end=datetime(2023, 1, 31, tzinfo=UTC),
            charge_period_start=datetime(2023, 1, 1, tzinfo=UTC),
            charge_period_end=datetime(2023, 1, 2, tzinfo=UTC),
            billing_currency="USD",
            service_name="Test Service",
            service_category="AI and Machine Learning",
            provider_name="Test Provider",
            publisher_name="Test Publisher",
            invoice_issuer_name="Test Issuer",
            charge_category="Usage",
            charge_description="Test charge",
        )

        errors = transform_stage._validate_focus_record(focus_record)
        assert len(errors) == 0

    def test_validate_focus_record_missing_fields(self, transform_stage):
        # Create record with valid values first, then modify for validation
        focus_record = FocusRecord(
            id=str(uuid.uuid4()),
            x_provider_id="test-provider",
            billed_cost=10.0,  # Start with valid value
            effective_cost=10.0,
            list_cost=12.0,
            contracted_cost=10.0,
            billing_account_id="account-1",  # Start with valid value
            billing_account_name="Test Account",
            billing_account_type="cloud",
            billing_period_start=datetime(2023, 1, 1, tzinfo=UTC),
            billing_period_end=datetime(2023, 1, 31, tzinfo=UTC),
            charge_period_start=datetime(2023, 1, 1, tzinfo=UTC),
            charge_period_end=datetime(2023, 1, 2, tzinfo=UTC),
            billing_currency="USD",
            service_name="Test Service",
            service_category="AI and Machine Learning",
            provider_name="Test Provider",
            publisher_name="Test Publisher",
            invoice_issuer_name="Test Issuer",
            charge_category="Usage",
            charge_description="Test charge",
        )

        # Manually modify fields to simulate validation issues
        focus_record.billed_cost = None
        focus_record.billing_account_id = ""

        errors = transform_stage._validate_focus_record(focus_record)
        assert len(errors) >= 2  # billed_cost and billing_account_id

    def test_validate_focus_record_negative_costs(self, transform_stage):
        focus_record = FocusRecord(
            id=str(uuid.uuid4()),
            x_provider_id="test-provider",
            billed_cost=-10.0,  # Negative cost
            effective_cost=10.0,
            list_cost=12.0,
            contracted_cost=10.0,
            billing_account_id="account-1",
            billing_account_name="Test Account",
            billing_account_type="cloud",
            billing_period_start=datetime(2023, 1, 1, tzinfo=UTC),
            billing_period_end=datetime(2023, 1, 31, tzinfo=UTC),
            charge_period_start=datetime(2023, 1, 1, tzinfo=UTC),
            charge_period_end=datetime(2023, 1, 2, tzinfo=UTC),
            billing_currency="USD",
            service_name="Test Service",
            service_category="AI and Machine Learning",
            provider_name="Test Provider",
            publisher_name="Test Publisher",
            invoice_issuer_name="Test Issuer",
            charge_category="Usage",
            charge_description="Test charge",
        )

        errors = transform_stage._validate_focus_record(focus_record)
        assert any("cannot be negative" in error for error in errors)
