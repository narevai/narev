import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from pipeline.config import PipelineConfig
from pipeline.stages.extract import ExtractStage


class TestExtractStage:
    """Test ExtractStage."""

    @pytest.fixture
    def config(self):
        return PipelineConfig(
            dlt_pipeline_name="test_pipeline",
            dlt_dataset_name="test",
            dlt_destination="sqlite",
        )

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def extract_stage(self, config, mock_db):
        return ExtractStage(config, mock_db)

    @pytest.fixture
    def base_context(self):
        mock_provider = Mock()
        mock_provider.get_sources.return_value = [
            {"name": "test_source", "source_type": "rest_api"}
        ]

        return {
            "provider": mock_provider,
            "provider_id": str(uuid.uuid4()),
            "start_date": datetime(2023, 1, 1, tzinfo=UTC),
            "end_date": datetime(2023, 1, 31, tzinfo=UTC),
            "provider_config": {"provider_type": "test", "name": "test_provider"},
            "pipeline_run_id": str(uuid.uuid4()),
            "sources": [{"name": "test_source", "source_type": "rest_api"}],
        }

    @pytest.mark.asyncio
    async def test_validate_input_success(self, extract_stage, base_context):
        await extract_stage.validate_input(base_context)

    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self, extract_stage):
        context = {"provider": Mock()}

        with pytest.raises(ValueError, match="Missing required context fields"):
            await extract_stage.validate_input(context)

    def test_get_sources_from_context(self, extract_stage, base_context):
        sources = extract_stage._get_sources(
            base_context,
            base_context["provider"],
            base_context["start_date"],
            base_context["end_date"],
        )

        assert sources == base_context["sources"]

    def test_extract_context_fields(self, extract_stage, base_context):
        fields = extract_stage._extract_context_fields(base_context)

        assert len(fields) == 6
        assert fields[0] == base_context["provider_id"]
        assert fields[1] == base_context["provider"]

    @pytest.mark.asyncio
    async def test_execute_no_sources(self, extract_stage, base_context):
        base_context["sources"] = []
        base_context["provider"].get_sources.return_value = []

        result = await extract_stage.execute(base_context)

        assert result.success is True
        assert result.records_processed == 0
        assert result.stage_name == "extract"
        assert result.data["extraction_summary"]["total_sources"] == 0

    @pytest.mark.asyncio
    async def test_save_raw_response_dlt(self, extract_stage):
        mock_pipeline = Mock()
        extracted_data = [{"id": 1, "data": "test"}]

        raw_id = await extract_stage._save_raw_response_dlt(
            provider_id="provider_123",
            provider_config={"provider_type": "test"},
            source_config={
                "name": "test_source",
                "source_type": "rest_api",
                "params": {"param1": "value1"},
            },
            extracted_data=extracted_data,
            start_date=datetime(2023, 1, 1, tzinfo=UTC),
            end_date=datetime(2023, 1, 31, tzinfo=UTC),
            pipeline_run_id="run_123",
            pipeline=mock_pipeline,
        )

        assert raw_id is not None
        mock_pipeline.run.assert_called_once()

        call_args = mock_pipeline.run.call_args
        raw_record = call_args[0][0][0]

        assert raw_record["provider_id"] == "provider_123"
        assert raw_record["source_name"] == "test_source"
        assert raw_record["record_count"] == 1
        assert raw_record["processed"] is False
