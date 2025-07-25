from unittest.mock import Mock

import pytest

from pipeline.config import PipelineConfig
from pipeline.stages.base import BaseStage, StageResult


class MockStage(BaseStage):
    """Mock stage for testing."""

    async def execute(self, context):
        return StageResult(
            stage_name=self.stage_name,
            success=True,
            records_processed=10,
            records_failed=0,
            duration_seconds=1.0,
            errors=[],
            data={},
        )

    async def validate_input(self, context):
        if "error" in context:
            raise ValueError("Test validation error")


class TestStageResult:
    """Test StageResult dataclass."""

    def test_stage_result_creation(self):
        result = StageResult(
            stage_name="test",
            success=True,
            records_processed=100,
            records_failed=5,
            duration_seconds=10.5,
            errors=[{"error": "test error"}],
            data={"test": "data"},
        )

        assert result.stage_name == "test"
        assert result.success is True
        assert result.records_processed == 100
        assert result.records_failed == 5
        assert result.duration_seconds == 10.5
        assert len(result.errors) == 1
        assert result.data["test"] == "data"

    def test_to_dict(self):
        result = StageResult(
            stage_name="test",
            success=True,
            records_processed=50,
            records_failed=2,
            duration_seconds=5.0,
            errors=[{"error": f"error {i}"} for i in range(15)],
            data={"other_data": [1, 2, 3], "summary": "test"},
        )

        result_dict = result.to_dict()

        assert result_dict["stage_name"] == "test"
        assert result_dict["success"] is True
        assert result_dict["records_processed"] == 50
        assert result_dict["records_failed"] == 2
        assert result_dict["duration_seconds"] == 5.0
        assert len(result_dict["errors"]) == 10  # Limited to 10
        assert result_dict["data_summary"]["other_data"] == 3
        assert result_dict["data_summary"]["summary"] == "test"


class TestBaseStage:
    """Test BaseStage abstract class."""

    @pytest.fixture
    def config(self):
        return PipelineConfig(
            extract_config={"batch_size": 50, "max_retries": 2},
            fail_fast=True,
            max_errors_percentage=10.0,
        )

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def stage(self, config, mock_db):
        return MockStage(config, mock_db)

    def test_stage_initialization(self, stage, config, mock_db):
        assert stage.config == config
        assert stage.db == mock_db
        assert stage.stage_name == "mock"
        assert stage.errors == []

    def test_get_batch_size(self, stage):
        assert (
            stage.get_batch_size() == 100
        )  # Default because stage_name is 'mock' not 'extract'

    def test_get_max_retries(self, stage):
        assert stage.get_max_retries() == 3  # Default

    def test_get_retry_delay(self, stage):
        assert stage.get_retry_delay() == 1.0

    def test_add_error(self, stage):
        stage.add_error({"error": "test error"})

        assert len(stage.errors) == 1
        assert stage.errors[0]["error"] == "test error"
        assert stage.errors[0]["stage"] == "mock"

    def test_create_batches(self, stage):
        items = list(range(125))
        batches = stage.create_batches(items)

        assert len(batches) == 2  # 100, 25 (default batch size is 100)
        assert len(batches[0]) == 100
        assert len(batches[1]) == 25

    @pytest.mark.asyncio
    async def test_run_success(self, stage):
        context = {"test": "data"}

        result = await stage.run(context)

        assert result.success is True
        assert result.stage_name == "mock"
        assert result.records_processed == 10

    @pytest.mark.asyncio
    async def test_run_validation_failure(self, stage):
        context = {"error": True}

        result = await stage.run(context)

        assert result.success is False
        assert "validation error" in result.errors[0]["error"]
