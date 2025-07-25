"""
Tests for PipelineRepository - Fixed after our changes
"""

from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.pipeline_run import PipelineRun
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.sync import SyncRunInfo, SyncRunMetrics


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def pipeline_repo(mock_db):
    """PipelineRepository instance with mocked DB."""
    return PipelineRepository(mock_db)


@pytest.fixture
def sample_pipeline_run():
    """Sample pipeline run."""
    run_id = str(uuid4())
    provider_id = str(uuid4())
    return Mock(
        spec=PipelineRun,
        id=run_id,  # Keep as string
        provider_id=provider_id,  # Keep as string
        status="completed",
        started_at=datetime(2025, 7, 20, 9, 30, 0),
        completed_at=datetime(2025, 7, 20, 9, 33, 0),
        duration_seconds=180.5,
        records_extracted=100,
        records_transformed=95,
        records_loaded=95,
        records_failed=5,
        error_message=None,
    )


class TestPipelineRepositoryInit:
    """Test repository initialization."""

    def test_init(self, mock_db):
        """Test repository initialization."""
        repo = PipelineRepository(mock_db)
        assert repo.db == mock_db


class TestGetRecentPipelineRuns:
    """Test get_recent_pipeline_runs method - now returns SyncRunInfo models."""

    def test_get_recent_pipeline_runs_basic(
        self, pipeline_repo, mock_db, sample_pipeline_run
    ):
        """Test fetching recent pipeline runs - now with JOIN and SyncRunInfo."""
        # Mock the query result for JOIN (PipelineRun, provider_name, provider_display_name)
        mock_query_results = [
            (sample_pipeline_run, "Test Provider", "Test Provider Display")
        ]

        # Setup mock query chain for JOIN
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_query_results

        # Execute
        result = pipeline_repo.get_recent_pipeline_runs()

        # Assert - should return list of SyncRunInfo models
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], SyncRunInfo)
        # Convert UUID back to string for comparison
        assert str(result[0].id) == sample_pipeline_run.id
        assert result[0].provider_name == "Test Provider Display"
        assert result[0].status == "completed"
        mock_query.outerjoin.assert_called_once()  # Should JOIN with Provider

    def test_get_recent_pipeline_runs_with_provider_filter(
        self, pipeline_repo, mock_db
    ):
        """Test with provider_id filter."""
        provider_id = str(uuid4())

        # Setup mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Execute
        result = pipeline_repo.get_recent_pipeline_runs(provider_id=provider_id)

        # Assert
        assert result == []
        mock_query.filter.assert_called_once()

    def test_get_recent_pipeline_runs_with_custom_limit(self, pipeline_repo, mock_db):
        """Test with custom limit."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = pipeline_repo.get_recent_pipeline_runs(limit=5)

        mock_query.limit.assert_called_with(5)
        assert result == []


class TestGetPipelineRuns:
    """Test get_pipeline_runs method - now returns tuple[list[SyncRunInfo], int]."""

    def test_get_pipeline_runs_basic(self, pipeline_repo, mock_db, sample_pipeline_run):
        """Test paginated pipeline runs."""
        mock_query_results = [
            (sample_pipeline_run, "Provider Name", "Provider Display")
        ]

        # Setup mock for main query (with JOIN)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_query_results

        # Setup mock for count query (separate query without JOIN)
        mock_count_query = Mock()
        mock_count_query.count.return_value = 1
        # Need to handle multiple query() calls
        mock_db.query.side_effect = [mock_query, mock_count_query]

        # Execute
        runs, total = pipeline_repo.get_pipeline_runs(skip=0, limit=10)

        # Assert
        assert isinstance(runs, list)
        assert len(runs) == 1
        assert isinstance(runs[0], SyncRunInfo)
        assert total == 1
        assert runs[0].provider_name == "Provider Display"
        # Convert UUID to string for comparison
        assert str(runs[0].id) == sample_pipeline_run.id

    def test_get_pipeline_runs_with_filters(self, pipeline_repo, mock_db):
        """Test with multiple filters."""
        # Setup main query mock
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Setup count query mock
        mock_count_query = Mock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.count.return_value = 0

        # Handle multiple query() calls
        mock_db.query.side_effect = [mock_query, mock_count_query]

        # Execute with filters
        runs, total = pipeline_repo.get_pipeline_runs(
            provider_id=str(uuid4()),
            status="completed",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        # Assert
        assert runs == []
        assert total == 0
        # Should have filters applied
        mock_query.filter.assert_called()
        mock_count_query.filter.assert_called()


class TestGetPipelineRun:
    """Test get_pipeline_run method - returns dict for details."""

    def test_get_pipeline_run_found(self, pipeline_repo, mock_db, sample_pipeline_run):
        """Test getting run by ID."""
        run_id = str(uuid4())

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pipeline_run

        result = pipeline_repo.get_pipeline_run(run_id)

        assert isinstance(result, dict)
        assert result["id"] == sample_pipeline_run.id
        assert result["status"] == "completed"
        assert "provider_name" in result

    def test_get_pipeline_run_not_found(self, pipeline_repo, mock_db):
        """Test getting non-existent run."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = pipeline_repo.get_pipeline_run(str(uuid4()))

        assert result is None


class TestGetRunMetrics:
    """Test get_run_metrics method - returns SyncRunMetrics."""

    def test_get_run_metrics_found(self, pipeline_repo, mock_db, sample_pipeline_run):
        """Test getting metrics for existing run."""
        run_id = str(uuid4())

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pipeline_run

        result = pipeline_repo.get_run_metrics(run_id)

        assert isinstance(result, SyncRunMetrics)
        assert result.duration_seconds == sample_pipeline_run.duration_seconds
        assert result.records_processed == sample_pipeline_run.records_extracted

    def test_get_run_metrics_not_found(self, pipeline_repo, mock_db):
        """Test getting metrics for non-existent run."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = pipeline_repo.get_run_metrics(str(uuid4()))

        assert result is None


class TestGetStatistics:
    """Test get_statistics method - now with provider and daily stats."""

    @patch("sqlalchemy.case")
    def test_get_statistics_basic(self, mock_case, pipeline_repo, mock_db):
        """Test getting basic statistics."""
        # Mock the main query result
        mock_result = Mock()
        mock_result.total_runs = 10
        mock_result.completed_runs = 8
        mock_result.failed_runs = 1
        mock_result.running_runs = 1
        mock_result.cancelled_runs = 0
        mock_result.total_extracted = 1000
        mock_result.avg_duration = 150.5

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result

        # Mock the private methods
        with patch.object(pipeline_repo, "_get_provider_stats", return_value=[]):
            with patch.object(pipeline_repo, "_get_daily_stats", return_value=[]):
                result = pipeline_repo.get_statistics()

        # Assert
        assert isinstance(result, dict)
        assert result["total_runs"] == 10
        assert result["successful_runs"] == 8
        assert result["success_rate"] == 80.0
        assert "provider_stats" in result
        assert "daily_stats" in result

    @patch("sqlalchemy.case")
    def test_get_statistics_with_filters(self, mock_case, pipeline_repo, mock_db):
        """Test statistics with filters."""
        provider_id = str(uuid4())
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)

        # Mock main query result
        mock_result = Mock()
        mock_result.total_runs = 5
        mock_result.completed_runs = 4
        mock_result.failed_runs = 1
        mock_result.running_runs = 0
        mock_result.cancelled_runs = 0
        mock_result.total_extracted = 500
        mock_result.avg_duration = 120.0

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result

        # Mock private methods
        with patch.object(pipeline_repo, "_get_provider_stats", return_value=[]):
            with patch.object(pipeline_repo, "_get_daily_stats", return_value=[]):
                result = pipeline_repo.get_statistics(
                    provider_id=provider_id, start_date=start_date, end_date=end_date
                )

        assert result["total_runs"] == 5
        assert result["success_rate"] == 80.0


class TestPrivateStatsMethods:
    """Test private statistics methods."""

    @patch("sqlalchemy.case")
    def test_get_provider_stats(self, mock_case, pipeline_repo, mock_db):
        """Test _get_provider_stats method."""
        # Mock query results
        mock_results = [
            Mock(
                provider_id=str(uuid4()),
                provider_name="Provider A",
                provider_display_name="Provider A Display",
                total_runs=5,
                successful_runs=4,
                failed_runs=1,
                total_records=100,
                avg_duration=60.0,
            )
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_results

        result = pipeline_repo._get_provider_stats(None, None)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["provider_name"] == "Provider A Display"
        assert result[0]["success_rate"] == 80.0

    @patch("sqlalchemy.case")
    def test_get_daily_stats(self, mock_case, pipeline_repo, mock_db):
        """Test _get_daily_stats method."""
        # Mock query results with date parsing
        mock_results = [
            Mock(
                date="2025-01-01",  # String date from func.date()
                total_runs=3,
                successful_runs=2,
                failed_runs=1,
                total_records=50,
                avg_duration=45.0,
            )
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results

        result = pipeline_repo._get_daily_stats(None, None, None)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0]["date"], datetime)
        assert result[0]["total_runs"] == 3


class TestCRUDOperations:
    """Test CRUD operations."""

    def test_create_pipeline_run_success(
        self, pipeline_repo, mock_db, sample_pipeline_run
    ):
        """Test creating pipeline run."""
        result = pipeline_repo.create(sample_pipeline_run)

        mock_db.add.assert_called_once_with(sample_pipeline_run)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_pipeline_run)
        assert result == sample_pipeline_run

    def test_create_pipeline_run_with_error(
        self, pipeline_repo, mock_db, sample_pipeline_run
    ):
        """Test create with database error."""
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            pipeline_repo.create(sample_pipeline_run)

        mock_db.rollback.assert_called_once()

    def test_update_run_status_success(
        self, pipeline_repo, mock_db, sample_pipeline_run
    ):
        """Test updating run status."""
        run_id = str(uuid4())

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pipeline_run

        result = pipeline_repo.update_run_status(run_id, "completed")

        assert result is True
        mock_db.commit.assert_called_once()

    def test_update_run_status_not_found(self, pipeline_repo, mock_db):
        """Test updating non-existent run."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = pipeline_repo.update_run_status(str(uuid4()), "completed")

        assert result is False
        mock_db.commit.assert_not_called()


class TestLegacyMethods:
    """Test methods that didn't change much."""

    def test_get_by_id(self, pipeline_repo, mock_db, sample_pipeline_run):
        """Test get by ID."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pipeline_run

        result = pipeline_repo.get_by_id(str(uuid4()))

        assert result == sample_pipeline_run

    def test_get_running_runs(self, pipeline_repo, mock_db, sample_pipeline_run):
        """Test getting running runs."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_pipeline_run]

        result = pipeline_repo.get_running_runs()

        assert result == [sample_pipeline_run]
        mock_query.filter.assert_called_once()

    def test_delete_old_runs(self, pipeline_repo, mock_db):
        """Test deleting old runs."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.delete.return_value = 5

        result = pipeline_repo.delete_old_runs(older_than_days=30)

        assert result == 5
        mock_db.commit.assert_called_once()
