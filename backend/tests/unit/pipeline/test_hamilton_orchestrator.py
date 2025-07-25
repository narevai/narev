import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from pipeline.config import PipelineConfig
from pipeline.hamilton_orchestrator import HamiltonOrchestrator
from pipeline.stages.base import StageResult


class TestHamiltonOrchestrator:
    """Test Hamilton pipeline orchestrator."""

    @pytest.fixture
    def pipeline_config(self):
        """Create test pipeline configuration."""
        return PipelineConfig(
            name="test_pipeline",
            version="1.0.0",
            extract_config={"batch_size": 100},
            transform_config={"batch_size": 50},
            load_config={"batch_size": 200},
        )

    @pytest.fixture
    def orchestrator(self, pipeline_config):
        """Create Hamilton orchestrator instance."""
        return HamiltonOrchestrator(pipeline_config)

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_provider_config(self):
        """Create sample provider configuration."""
        return {
            "provider_type": "openai",
            "name": "test_provider",
            "api_key": "test_key",
        }

    def test_orchestrator_initialization(self, pipeline_config):
        """Test orchestrator initializes correctly."""
        orchestrator = HamiltonOrchestrator(pipeline_config)

        assert orchestrator.config == pipeline_config
        assert orchestrator.driver is not None
        assert orchestrator.encryption_service is not None

    def test_orchestrator_default_config(self):
        """Test orchestrator with default configuration."""
        orchestrator = HamiltonOrchestrator()

        assert orchestrator.config is not None
        assert orchestrator.config.name == "billing_pipeline"

    def test_get_dag_structure(self, orchestrator):
        """Test DAG structure retrieval."""
        # Mock the driver methods to avoid Hamilton node sorting issues
        with (
            patch.object(orchestrator.driver, "list_available_variables") as mock_list,
            patch.object(orchestrator.driver, "what_is_upstream_of") as mock_upstream,
        ):
            mock_list.return_value = ["node1", "node2", "pipeline_result"]
            mock_upstream.return_value = ["node1"]

            dag_structure = orchestrator.get_dag_structure()

            assert "nodes" in dag_structure
            assert "dependencies" in dag_structure
            assert "execution_order" in dag_structure
            assert len(dag_structure["nodes"]) == 3

    @patch("os.path.exists")
    def test_visualize_dag_success(self, mock_exists, orchestrator):
        """Test DAG visualization success."""
        mock_exists.return_value = True

        with patch.object(orchestrator.driver, "visualize_execution") as mock_viz:
            result = orchestrator.visualize_dag("test.png")

            assert result == "test.png"
            mock_viz.assert_called_once()

    def test_visualize_dag_missing_dependency(self, orchestrator):
        """Test DAG visualization with missing dependencies."""
        with patch.object(
            orchestrator.driver, "visualize_execution", side_effect=ImportError
        ):
            with pytest.raises(ImportError):
                orchestrator.visualize_dag()

    @pytest.mark.asyncio
    async def test_run_pipeline_success(
        self, orchestrator, mock_db_session, sample_provider_config
    ):
        """Test successful pipeline execution."""
        provider_id = uuid.uuid4()
        start_date = datetime.now(UTC)
        end_date = datetime.now(UTC)

        # Mock successful stage results
        StageResult(
            stage_name="extract",
            success=True,
            records_processed=100,
            records_failed=0,
            duration_seconds=10.0,
            errors=[],
            data={},
        )
        StageResult(
            stage_name="transform",
            success=True,
            records_processed=100,
            records_failed=0,
            duration_seconds=5.0,
            errors=[],
            data={},
        )
        StageResult(
            stage_name="load",
            success=True,
            records_processed=100,
            records_failed=0,
            duration_seconds=8.0,
            errors=[],
            data={},
        )

        expected_pipeline_result = {
            "pipeline_run_id": str(uuid.uuid4()),
            "provider_id": str(provider_id),
            "status": "completed",
            "stages": {
                "extract": {
                    "success": True,
                    "records_processed": 100,
                    "records_failed": 0,
                    "duration": 10.0,
                    "errors": [],
                },
                "transform": {
                    "success": True,
                    "records_processed": 100,
                    "records_failed": 0,
                    "duration": 5.0,
                    "errors": [],
                },
                "load": {
                    "success": True,
                    "records_processed": 100,
                    "records_failed": 0,
                    "duration": 8.0,
                    "errors": [],
                },
            },
            "totals": {
                "total_records_processed": 100,
                "total_records_failed": 0,
                "total_duration": 23.0,
                "stages_completed": 3,
                "stages_failed": 0,
            },
        }

        with (
            patch.object(orchestrator, "_initialize_pipeline") as mock_init,
            patch.object(orchestrator, "_execute_hamilton_sync") as mock_execute,
            patch.object(orchestrator, "_finalize_pipeline") as mock_finalize,
        ):
            mock_init.return_value = (sample_provider_config, Mock())
            mock_execute.return_value = {"pipeline_result": expected_pipeline_result}
            mock_finalize.return_value = None

            result = await orchestrator.run_pipeline(provider_id, start_date, end_date)

            assert result["status"] == "completed"
            assert result["provider_id"] == str(provider_id)
            mock_init.assert_called_once()
            mock_execute.assert_called_once()
            mock_finalize.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_pipeline_failure(self, orchestrator, sample_provider_config):
        """Test pipeline execution with failure."""
        provider_id = uuid.uuid4()
        start_date = datetime.now(UTC)
        end_date = datetime.now(UTC)

        with (
            patch.object(
                orchestrator,
                "_initialize_pipeline",
                side_effect=Exception("Test error"),
            ),
            patch.object(orchestrator, "_handle_pipeline_error") as mock_handle_error,
        ):
            with pytest.raises(Exception, match="Test error"):
                await orchestrator.run_pipeline(provider_id, start_date, end_date)

            mock_handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_pipeline_with_intermediate_results(
        self, orchestrator, sample_provider_config
    ):
        """Test pipeline execution with intermediate results."""
        provider_id = uuid.uuid4()
        start_date = datetime.now(UTC)
        end_date = datetime.now(UTC)

        mock_extract_result = StageResult(
            stage_name="extract",
            success=True,
            records_processed=100,
            records_failed=0,
            duration_seconds=10.0,
            errors=[],
            data={},
        )

        mock_results = {
            "pipeline_result": {"status": "completed"},
            "extract_stage_result": mock_extract_result,
            "transform_stage_result": mock_extract_result,
            "load_stage_result": mock_extract_result,
            "extract_summary": {"stage": "extract", "success": True},
            "transform_summary": {"stage": "transform", "success": True},
            "load_summary": {"stage": "load", "success": True},
            "pipeline_summary": {"all_successful": True},
        }

        with (
            patch.object(orchestrator, "_initialize_pipeline") as mock_init,
            patch.object(
                orchestrator, "_execute_hamilton_with_intermediates"
            ) as mock_execute,
        ):
            mock_init.return_value = (sample_provider_config, Mock())
            mock_execute.return_value = mock_results

            result = await orchestrator.run_pipeline_with_intermediate_results(
                provider_id, start_date, end_date
            )

            assert "pipeline_result" in result
            assert "stage_results" in result
            assert "summaries" in result

    def test_execute_hamilton_sync(self, orchestrator):
        """Test synchronous Hamilton execution."""
        inputs = {
            "provider_id": uuid.uuid4(),
            "start_date": datetime.now(UTC),
            "end_date": datetime.now(UTC),
            "pipeline_run_id": uuid.uuid4(),
            "provider_config": {"provider_type": "test"},
            "pipeline_config": PipelineConfig(),
            "db_session": Mock(),
        }

        expected_result = {"pipeline_result": {"status": "completed"}}

        with patch.object(orchestrator.driver, "execute") as mock_execute:
            mock_execute.return_value = expected_result

            result = orchestrator._execute_hamilton_sync(inputs)

            assert result == expected_result
            mock_execute.assert_called_once_with(
                ["pipeline_result"], inputs=inputs, overrides={}
            )

    def test_execute_hamilton_sync_error(self, orchestrator):
        """Test synchronous Hamilton execution with error."""
        inputs = {"test": "input"}

        with patch.object(
            orchestrator.driver, "execute", side_effect=Exception("Execution failed")
        ):
            with pytest.raises(Exception, match="Execution failed"):
                orchestrator._execute_hamilton_sync(inputs)

    @pytest.mark.asyncio
    async def test_initialize_pipeline_success(
        self, orchestrator, mock_db_session, sample_provider_config
    ):
        """Test successful pipeline initialization."""
        provider_id = uuid.uuid4()
        pipeline_run_id = uuid.uuid4()
        start_date = datetime.now(UTC)
        end_date = datetime.now(UTC)

        mock_pipeline_run = Mock()

        with (
            patch.object(orchestrator, "_get_provider_config") as mock_get_config,
            patch.object(orchestrator, "_create_pipeline_run") as mock_create_run,
        ):
            mock_get_config.return_value = sample_provider_config
            mock_create_run.return_value = mock_pipeline_run

            config, run = await orchestrator._initialize_pipeline(
                mock_db_session,
                provider_id,
                pipeline_run_id,
                "incremental",
                start_date,
                end_date,
            )

            assert config == sample_provider_config
            assert run == mock_pipeline_run

    @pytest.mark.asyncio
    async def test_initialize_pipeline_no_config(self, orchestrator, mock_db_session):
        """Test pipeline initialization with missing provider config."""
        provider_id = uuid.uuid4()
        pipeline_run_id = uuid.uuid4()
        start_date = datetime.now(UTC)
        end_date = datetime.now(UTC)

        with patch.object(orchestrator, "_get_provider_config", return_value=None):
            with pytest.raises(ValueError, match="Provider .* not found"):
                await orchestrator._initialize_pipeline(
                    mock_db_session,
                    provider_id,
                    pipeline_run_id,
                    "incremental",
                    start_date,
                    end_date,
                )

    def test_utcnow(self, orchestrator):
        """Test UTC now helper method."""
        now = orchestrator._utcnow()

        assert isinstance(now, datetime)
        assert now.tzinfo == UTC

    def test_ensure_timezone_aware(self, orchestrator):
        """Test timezone awareness helper method."""
        # Test with None
        assert orchestrator._ensure_timezone_aware(None) is None

        # Test with naive datetime
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        aware_dt = orchestrator._ensure_timezone_aware(naive_dt)
        assert aware_dt.tzinfo == UTC

        # Test with already aware datetime
        already_aware = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = orchestrator._ensure_timezone_aware(already_aware)
        assert result == already_aware
