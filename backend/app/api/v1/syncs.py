"""
Sync Management API
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.sync import (
    HealthCheckResponse,
    SyncActionResponse,
    SyncRunDetails,
    SyncRunsResponse,
    SyncStatisticsResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from app.services.sync_service import SyncService

from .deps import get_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/syncs", tags=["syncs"])


@router.post("/trigger")
async def trigger_sync(
    request: SyncTriggerRequest,
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncTriggerResponse:
    """
    Trigger billing data synchronization.

    Starts synchronization job in the background (fire and forget).
    """

    async def run_sync_job():
        """Background sync job with error handling."""
        try:
            logger.info(f"Starting sync job for provider: {request.provider_id}")
            result = await sync_service.trigger_sync(
                provider_id=request.provider_id,
                start_date=request.start_date,
                end_date=request.end_date,
                days_back=request.days_back if request.days_back else 7,
            )
            logger.info(f"Sync job completed successfully: {result}")
        except Exception as e:
            logger.error(f"Sync job failed: {e}", exc_info=True)

    # Fire and forget
    asyncio.create_task(run_sync_job())

    return SyncTriggerResponse(
        success=True,
        message="Sync job has been queued",
        info="Job is running in background",
    )


@router.get("/status")
def get_sync_status(
    provider_id: UUID | None = None,
    limit: int = Query(10, ge=1, le=50, description="Number of providers to return"),
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncStatusResponse:
    """
    Get current sync status for providers.

    Shows recent synchronizations and their status.
    """
    try:
        return sync_service.get_sync_status(provider_id=provider_id, limit=limit)

    except Exception as e:
        # TODO: Fix this - catching all exceptions and returning 500 is bad practice
        # Should handle specific exceptions or fix underlying issues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sync status",
        ) from e


@router.get("/runs")
def get_sync_runs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    provider_id: UUID | None = None,
    status_filter: str | None = Query(
        None,
        alias="status",
        pattern="^(pending|running|completed|failed|cancelled)$",
        description="Filter by sync status",
    ),
    start_date: datetime | None = Query(None, description="Filter runs from this date"),
    end_date: datetime | None = Query(None, description="Filter runs until this date"),
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncRunsResponse:
    """
    Get sync run history with pagination and filters.

    Returns history of all synchronizations with filtering capabilities.
    """
    try:
        return sync_service.get_sync_runs(
            skip=skip,
            limit=limit,
            provider_id=provider_id,
            status=status_filter,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        # TODO: Fix this - catching all exceptions and returning 500 is bad practice
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sync runs",
        ) from e


@router.get("/runs/{run_id}")
def get_sync_run(
    run_id: UUID,
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncRunDetails:
    """
    Get detailed information about specific sync run.

    Returns detailed information about a specific synchronization,
    including logs, errors, and metrics.
    """
    try:
        run_details = sync_service.get_sync_run_details(run_id)

        if not run_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sync run not found"
            )

        return run_details

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sync run details",
        ) from e


@router.post("/runs/{run_id}/cancel")
async def cancel_sync_run(
    run_id: UUID,
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncActionResponse:
    """
    Cancel running sync job.

    Cancels a currently executing synchronization.
    """
    try:
        result = await sync_service.cancel_sync_run(run_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync run not found or cannot be cancelled",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cancelling sync run",
        ) from e


@router.post("/runs/{run_id}/retry")
async def retry_sync_run(
    run_id: UUID,
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncActionResponse:
    """
    Retry failed sync run.

    Retries a failed synchronization with the same parameters.
    """
    try:
        result = await sync_service.retry_sync_run(run_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync run not found or cannot be retried",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrying sync run",
        ) from e


@router.get("/stats")
def get_sync_statistics(
    provider_id: UUID | None = None,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncStatisticsResponse:
    """
    Get sync statistics and metrics.

    Returns synchronization statistics: success rate, average time, etc.
    """
    try:
        return sync_service.get_sync_statistics(provider_id=provider_id, days=days)

    except Exception as e:
        # TODO: Fix this - catching all exceptions and returning 500 is bad practice
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sync statistics",
        ) from e


@router.get("/health")
def sync_health_check() -> HealthCheckResponse:
    """Health check for sync API."""
    return HealthCheckResponse(
        status="healthy",
        service="sync_api",
        timestamp=datetime.now().isoformat(),
    )


@router.get("/pipeline/graph")
async def get_pipeline_graph(
    format: str = Query("png", pattern="^(png|svg|pdf)$"),
    sync_service: SyncService = Depends(get_sync_service),
):
    """Get pipeline DAG visualization."""
    try:
        import os

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"logs/pipeline_dag_{timestamp}.{format}"

        os.makedirs("logs", exist_ok=True)

        # Generate graph
        graph_path = sync_service.generate_pipeline_graph(output_path, format)

        # Verify file exists
        actual_path = graph_path if os.path.exists(graph_path) else output_path

        if not os.path.exists(actual_path):
            raise HTTPException(
                status_code=500, detail=f"Graph file not generated: {actual_path}"
            )

        from fastapi.responses import FileResponse

        return FileResponse(path=actual_path, filename=f"pipeline_dag.{format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
