"""
Tests for sync service
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.sync_service import SyncService


@pytest.fixture
def sync_service(test_db_session):
    """Create sync service instance with test database."""
    return SyncService(test_db_session)


@pytest.fixture
def test_provider(test_db_session):
    """Create a test provider for testing."""

    from app.models.provider import Provider

    # Check if provider already exists
    existing_provider = (
        test_db_session.query(Provider)
        .filter_by(id="550e8400-e29b-41d4-a716-446655440001")
        .first()
    )

    if existing_provider:
        return existing_provider

    # Create unique name using timestamp to avoid conflicts
    import time

    unique_name = f"test-provider-{int(time.time())}"

    provider = Provider(
        id="550e8400-e29b-41d4-a716-446655440001",
        name=unique_name,
        provider_type="openai",
        display_name="Test Provider",
        is_active=True,
    )
    test_db_session.add(provider)
    test_db_session.commit()
    return provider


@pytest.fixture
def sample_pipeline_runs(test_db_session, test_provider):
    """Create sample pipeline runs for testing."""
    from app.models.pipeline_run import PipelineRun

    runs = []
    statuses = ["completed", "running", "failed", "cancelled", "completed"]
    now = datetime.now(UTC)

    for i in range(5):
        run = PipelineRun(
            id=f"550e8400-e29b-41d4-a716-44665544000{i}",
            provider_id="550e8400-e29b-41d4-a716-446655440001",
            pipeline_name="billing_sync",
            run_type="manual",
            status=statuses[i],
            started_at=now - timedelta(hours=i),
            completed_at=now - timedelta(hours=i) + timedelta(minutes=30)
            if statuses[i] in ["completed", "failed", "cancelled"]
            else None,
            duration_seconds=1800
            if statuses[i] in ["completed", "failed", "cancelled"]
            else None,
            records_extracted=1000 * i if statuses[i] == "completed" else 0,
            error_message="Test error" if statuses[i] == "failed" else None,
        )
        runs.append(run)
        test_db_session.add(run)

    test_db_session.commit()
    return runs


@pytest.mark.asyncio
async def test_trigger_sync(sync_service, test_db_session):
    """Test triggering a sync."""
    from uuid import UUID

    with patch.object(sync_service, "_start_sync_jobs_hamilton") as mock_start:
        mock_start.return_value = {
            "run_ids": ["550e8400-e29b-41d4-a716-446655440123"],
            "errors": [],
        }

        with patch.object(
            sync_service, "_get_providers_for_sync"
        ) as mock_get_providers:
            mock_provider = Mock()
            mock_provider.id = "550e8400-e29b-41d4-a716-446655440001"
            mock_get_providers.return_value = [mock_provider]

            result = await sync_service.trigger_sync(
                provider_id=UUID("550e8400-e29b-41d4-a716-446655440001")
            )

            assert result["success"] is True
            assert len(result["pipeline_run_ids"]) == 1
            assert (
                result["pipeline_run_ids"][0] == "550e8400-e29b-41d4-a716-446655440123"
            )
            assert "Started sync for 1 providers" in result["message"]


@pytest.mark.asyncio
async def test_trigger_sync_invalid_provider(sync_service):
    """Test triggering sync with invalid provider."""
    from uuid import UUID

    with pytest.raises(ValueError, match="Provider .* not found"):
        await sync_service.trigger_sync(
            provider_id=UUID("550e8400-e29b-41d4-a716-446655440000")
        )


@pytest.mark.asyncio
async def test_trigger_sync_invalid_type(sync_service):
    """Test triggering sync with no active providers."""
    with patch.object(sync_service, "_get_providers_for_sync") as mock_get_providers:
        mock_get_providers.return_value = []

        with pytest.raises(ValueError, match="No active providers found"):
            await sync_service.trigger_sync()


def test_get_sync_status(sync_service, sample_pipeline_runs):
    """Test getting sync status overview."""
    status = sync_service.get_sync_status()

    assert status.runs is not None
    assert status.summary is not None

    # Should have runs with at least 1 running status
    running_runs = [run for run in status.runs if run.status == "running"]
    assert len(running_runs) == 1

    # Total syncs should be 5
    assert status.summary.total_runs == 5

    # Success rate should be around 40% (2 completed out of 5 total)
    assert 35 <= status.summary.success_rate <= 45


def test_get_sync_runs(sync_service, sample_pipeline_runs):
    """Test getting sync runs with pagination."""
    result = sync_service.get_sync_runs()

    assert result.runs is not None
    assert result.pagination is not None

    assert len(result.runs) == 5
    assert result.pagination.total == 5
    assert result.pagination.skip == 0
    assert result.pagination.limit == 50
    assert result.pagination.has_more is False

    # Runs should be ordered by started_at desc
    run_times = [run.started_at for run in result.runs]
    assert run_times == sorted(run_times, reverse=True)


def test_get_runs_with_filters(sync_service, sample_pipeline_runs):
    """Test getting runs with status filter."""
    result = sync_service.get_sync_runs(status="completed")

    assert len(result.runs) == 2
    assert all(run.status == "completed" for run in result.runs)


def test_get_runs_pagination(sync_service, sample_pipeline_runs):
    """Test runs pagination."""
    # First page
    result = sync_service.get_sync_runs(skip=0, limit=3)
    assert len(result.runs) == 3
    assert result.pagination.skip == 0
    assert result.pagination.limit == 3
    assert result.pagination.has_more is True

    # Second page
    result = sync_service.get_sync_runs(skip=3, limit=3)
    assert len(result.runs) == 2
    assert result.pagination.skip == 3
    assert result.pagination.has_more is False


def test_get_sync_run_details(sync_service, sample_pipeline_runs):
    """Test getting specific run by ID."""
    from uuid import UUID

    run = sync_service.get_sync_run_details(
        UUID("550e8400-e29b-41d4-a716-446655440000")
    )

    assert run is not None
    assert str(run.id) == "550e8400-e29b-41d4-a716-446655440000"
    assert str(run.provider_id) == "550e8400-e29b-41d4-a716-446655440001"
    assert run.status == "completed"


def test_get_sync_run_details_not_found(sync_service):
    """Test getting non-existent run."""
    from uuid import UUID

    run = sync_service.get_sync_run_details(
        UUID("550e8400-e29b-41d4-a716-446655440999")
    )
    assert run is None


@pytest.mark.asyncio
async def test_cancel_sync_run(sync_service, sample_pipeline_runs):
    """Test canceling a running sync."""
    from uuid import UUID

    mock_orchestrator = AsyncMock()
    mock_orchestrator.cancel_pipeline_run.return_value = True
    sync_service._orchestrator = mock_orchestrator

    result = await sync_service.cancel_sync_run(
        UUID("550e8400-e29b-41d4-a716-446655440001")
    )  # This one is running

    assert result.success is True
    assert "cancelled successfully" in result.message
    mock_orchestrator.cancel_pipeline_run.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_completed_sync_run(sync_service, sample_pipeline_runs):
    """Test canceling already completed sync."""
    from uuid import UUID

    with pytest.raises(ValueError, match="Cannot cancel"):
        await sync_service.cancel_sync_run(
            UUID("550e8400-e29b-41d4-a716-446655440000")
        )  # This one is completed


@pytest.mark.asyncio
async def test_cancel_non_existent_sync_run(sync_service):
    """Test canceling non-existent sync."""
    from uuid import UUID

    result = await sync_service.cancel_sync_run(
        UUID("550e8400-e29b-41d4-a716-446655440999")
    )
    assert result is None


@pytest.mark.asyncio
async def test_retry_sync_run(sync_service, sample_pipeline_runs):
    """Test retrying a failed sync."""
    from uuid import UUID

    mock_orchestrator = AsyncMock()
    mock_orchestrator.run_pipeline.return_value = {
        "pipeline_run_id": UUID("550e8400-e29b-41d4-a716-446655440999")
    }
    sync_service._orchestrator = mock_orchestrator

    result = await sync_service.retry_sync_run(
        UUID("550e8400-e29b-41d4-a716-446655440002")
    )  # This one failed

    assert result.new_run_id == UUID("550e8400-e29b-41d4-a716-446655440999")
    assert result.success is True
    assert "retry has been queued" in result.message
    mock_orchestrator.run_pipeline.assert_called_once()


@pytest.mark.asyncio
async def test_retry_running_sync_run(sync_service, sample_pipeline_runs):
    """Test retrying a running sync."""
    from uuid import UUID

    with pytest.raises(ValueError, match="Cannot retry"):
        await sync_service.retry_sync_run(
            UUID("550e8400-e29b-41d4-a716-446655440001")
        )  # This one is running


def test_get_sync_statistics(sync_service, sample_pipeline_runs):
    """Test getting sync statistics."""
    stats = sync_service.get_sync_statistics()

    assert stats.total_runs >= 0
    assert stats.successful_runs >= 0
    assert stats.failed_runs >= 0
    assert stats.cancelled_runs >= 0
    assert stats.success_rate >= 0
    assert stats.total_records_processed >= 0
    assert isinstance(stats.provider_stats, list)
    assert isinstance(stats.daily_stats, list)


def test_get_sync_statistics_empty_database(sync_service):
    """Test getting stats with no runs."""
    stats = sync_service.get_sync_statistics()

    assert stats.total_runs == 0
    assert stats.successful_runs == 0
    assert stats.success_rate == 0


def test_generate_pipeline_graph(sync_service):
    """Test generating pipeline graph visualization."""
    with patch(
        "pipeline.hamilton_orchestrator.HamiltonOrchestrator.visualize_dag"
    ) as mock_visualize:
        mock_visualize.return_value = "/tmp/test_graph.png"

        result = sync_service.generate_pipeline_graph("/tmp/test_graph.png")

        assert result == "/tmp/test_graph.png"
        mock_visualize.assert_called_once_with("/tmp/test_graph.png")


# Test removed - _execute_sync method doesn't exist in current implementation


# Test removed - _stop_running_sync method doesn't exist in current implementation


# Test removed - _validate_sync_type method doesn't exist in current implementation


# Test removed - get_provider_active_runs method doesn't exist in current implementation


# Test removed - get_recent_runs method doesn't exist in current implementation


def test_calculate_success_rate_no_completed_runs(sync_service, test_db_session):
    """Test success rate with no completed runs."""
    from app.models.pipeline_run import PipelineRun

    # Add only running runs
    run = PipelineRun(
        id="running-run",
        provider_id="550e8400-e29b-41d4-a716-446655440001",
        pipeline_name="billing_sync",
        run_type="manual",
        status="running",
        started_at=datetime.now(UTC),
    )
    test_db_session.add(run)
    test_db_session.commit()

    stats = sync_service.get_sync_statistics()
    assert stats.success_rate == 0.0
