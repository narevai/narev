from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from pipeline.config import PipelineConfig
from pipeline.stages.load import LoadStage


class TestLoadStage:
    """Test LoadStage."""

    @pytest.fixture
    def config(self):
        return PipelineConfig(
            load_config={
                "batch_size": 500,
                "write_disposition": "merge",
                "primary_key": ["id"],
                "merge_key": [
                    "x_provider_id",
                    "charge_period_start",
                    "charge_period_end",
                ],
            }
        )

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def load_stage(self, config, mock_db):
        return LoadStage(config, mock_db)

    @pytest.fixture
    def base_context(self):
        return {
            "transformed_records": [
                {
                    "id": "record-1",
                    "x_provider_id": "provider-1",
                    "charge_period_start": datetime(2023, 1, 1, tzinfo=UTC),
                    "charge_period_end": datetime(2023, 1, 2, tzinfo=UTC),
                    "billing_currency": "USD",
                    "billed_cost": 10.0,
                }
            ],
            "failed_records": [],
            "pipeline_run_id": "test-run-123",
            "raw_billing_ids": ["raw-1", "raw-2"],
        }

    @pytest.mark.asyncio
    async def test_validate_input_success(self, load_stage, base_context):
        await load_stage.validate_input(base_context)

    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self, load_stage):
        context = {"transformed_records": []}

        with pytest.raises(ValueError, match="Missing required context fields"):
            await load_stage.validate_input(context)

    @pytest.mark.asyncio
    async def test_validate_input_missing_record_fields(self, load_stage):
        context = {
            "transformed_records": [
                {"id": "record-1"}  # Missing required fields
            ],
            "failed_records": [],
        }

        with pytest.raises(ValueError, match="Missing required billing data fields"):
            await load_stage.validate_input(context)

    @pytest.mark.asyncio
    async def test_execute_empty_records(self, load_stage):
        context = {
            "transformed_records": [],
            "failed_records": [],
            "pipeline_run_id": "test-run-123",
        }

        result = await load_stage.execute(context)

        assert result.success is True
        assert result.records_processed == 0
        assert result.stage_name == "load"
        assert result.data["loaded_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_success(self, load_stage, base_context):
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_load_info.has_failed_jobs = False
        mock_load_info.jobs = []
        mock_pipeline.run.return_value = mock_load_info

        with (
            patch.object(load_stage, "_create_pipeline", return_value=mock_pipeline),
            patch.object(load_stage, "_mark_raw_records_as_processed") as mock_mark,
        ):
            result = await load_stage.execute(base_context)

            assert result.success is True
            assert result.records_processed == 1
            assert result.data["loaded_count"] == 1
            mock_mark.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_failures(self, load_stage, base_context):
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_load_info.has_failed_jobs = True
        mock_job = Mock()
        mock_job.failed = True
        mock_job.job_id = "job-123"
        mock_job.exception = "Test failure"
        mock_load_info.jobs = [mock_job]
        mock_pipeline.run.return_value = mock_load_info

        with patch.object(load_stage, "_create_pipeline", return_value=mock_pipeline):
            result = await load_stage.execute(base_context)

            # With 1 failed job out of 1 record, success depends on failure threshold
            assert len(result.errors) > 0
            assert "Test failure" in result.errors[0]["error"]

    def test_prepare_records_for_dlt(self, load_stage):
        records = [
            {
                "id": "record-1",
                "charge_period_start": "2023-01-01T00:00:00Z",
                "billed_cost": Decimal("10.50"),
                "tags": {"key": "value"},
                "some_field": "test",
            }
        ]

        prepared = load_stage._prepare_records_for_dlt(records)

        assert len(prepared) == 1
        record = prepared[0]
        assert isinstance(record["charge_period_start"], datetime)
        assert isinstance(record["billed_cost"], float)
        assert record["billed_cost"] == 10.5
        assert isinstance(record["tags"], str)

    def test_prepare_records_invalid_date(self, load_stage):
        records = [{"id": "record-1", "charge_period_start": "invalid-date"}]

        prepared = load_stage._prepare_records_for_dlt(records)

        assert len(prepared) == 1
        assert (
            prepared[0]["charge_period_start"] == "invalid-date"
        )  # Should remain as string

    @pytest.mark.asyncio
    async def test_mark_raw_records_as_processed_success(self, load_stage):
        context = {"raw_billing_ids": ["raw-1", "raw-2"]}

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 2
        load_stage.db.query.return_value = mock_query

        with patch("app.models.raw_billing_data.RawBillingData"):
            await load_stage._mark_raw_records_as_processed(context, "run-123")

            load_stage.db.query.assert_called_once()
            load_stage.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_raw_records_as_processed_failure(self, load_stage):
        context = {"raw_billing_ids": ["raw-1", "raw-2"]}

        load_stage.db.query.side_effect = Exception("Database error")

        with patch("app.models.raw_billing_data.RawBillingData"):
            # Should not raise exception
            await load_stage._mark_raw_records_as_processed(context, "run-123")

            load_stage.db.rollback.assert_called_once()

    def test_create_pipeline(self, load_stage):
        with patch("pipeline.config.PipelineConfig.get_dlt_pipeline") as mock_get:
            mock_pipeline = Mock()
            mock_get.return_value = mock_pipeline

            result = load_stage._create_pipeline()

            assert result == mock_pipeline
            mock_get.assert_called_once()

    def test_load_stage_initialization(self, config, mock_db):
        stage = LoadStage(config, mock_db)

        assert stage.batch_size == 500
        assert stage.write_disposition == "merge"
        assert stage.primary_key == ["id"]
        assert stage.merge_key == [
            "x_provider_id",
            "charge_period_start",
            "charge_period_end",
        ]

    def test_get_progress(self, load_stage):
        context = {
            "transformed_records": [{"id": "1"}, {"id": "2"}],
            "loaded_count": 1,
            "failed_count": 1,
        }

        progress = load_stage.get_progress(context)

        assert progress["stage"] == "load"
        assert progress["records_total"] == 2
        assert progress["records_loaded"] == 1
        assert progress["records_failed"] == 1
