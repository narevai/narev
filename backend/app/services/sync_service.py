"""
Sync Service Layer
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.provider_repository import ProviderRepository
from app.schemas.sync import (
    DailyStats,
    PaginationInfo,
    ProviderStats,
    SyncActionResponse,
    SyncRunDetails,
    SyncRunsResponse,
    SyncRunSummary,
    SyncStatisticsResponse,
    SyncStatusResponse,
)
from app.services.provider_service import ProviderService
from pipeline.hamilton_orchestrator import HamiltonOrchestrator

logger = logging.getLogger(__name__)


class SyncService:
    """Service layer for sync operations"""

    def __init__(self, db: Session):
        """Initialize sync service."""
        self.db = db
        self.pipeline_repo = PipelineRepository(db)
        self.provider_repo = ProviderRepository(db)
        self.provider_service = ProviderService(db)
        self._orchestrator = None  # Lazy loading

    @property
    def orchestrator(self) -> HamiltonOrchestrator:
        """Get orchestrator instance (lazy loaded)."""
        if self._orchestrator is None:
            self._orchestrator = HamiltonOrchestrator()
        return self._orchestrator

    async def trigger_sync(
        self,
        provider_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        days_back: int | None = None,
    ) -> dict[str, Any]:
        """
        Trigger billing data synchronization.

        Args:
            provider_id: Specific provider to sync (optional)
            start_date: Start date for sync
            end_date: End date for sync
            days_back: Days back from now if dates not specified

        Returns:
            Sync trigger result with run IDs
        """
        logger.info(
            f"Triggering billing sync with parameters: "
            f"provider_id={provider_id}, start_date={start_date}, end_date={end_date}, days_back={days_back}"
        )

        # Determine date range
        start_date, end_date = self._get_date_range(start_date, end_date, days_back)
        logger.info(f"Using date range: {start_date} to {end_date}")

        # Get providers to sync
        providers = await self._get_providers_for_sync(provider_id)
        if not providers:
            raise ValueError("No active providers found for synchronization")

        # Start sync jobs for each provider using Hamilton orchestrator
        results = await self._start_sync_jobs_hamilton(providers, start_date, end_date)

        return {
            "success": len(results["run_ids"]) > 0,
            "message": f"Started sync for {len(results['run_ids'])} providers",
            "pipeline_run_ids": results["run_ids"],
            "providers_synced": len(providers),
            "errors": results["errors"],
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def get_sync_status(
        self, provider_id: UUID | None = None, limit: int = 10
    ) -> SyncStatusResponse:
        """
        Get sync status for providers.

        Args:
            provider_id: Filter by provider
            limit: Number of recent runs

        Returns:
            Sync status response model
        """
        runs = self.pipeline_repo.get_recent_pipeline_runs(
            provider_id=str(provider_id) if provider_id is not None else None,
            limit=limit,
        )

        summary = self._get_sync_summary(runs)

        return SyncStatusResponse(runs=runs, summary=summary)

    def get_sync_runs(
        self,
        skip: int = 0,
        limit: int = 50,
        provider_id: UUID | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> SyncRunsResponse:
        """
        Get sync run history with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Number of records to return
            provider_id: Filter by provider
            status: Filter by status
            start_date: Filter runs from this date
            end_date: Filter runs until this date

        Returns:
            Paginated sync runs response model
        """
        runs, total = self.pipeline_repo.get_pipeline_runs(
            skip=skip,
            limit=limit,
            provider_id=str(provider_id) if provider_id else None,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        pagination = PaginationInfo(
            skip=skip, limit=limit, total=total, has_more=(skip + limit) < total
        )

        return SyncRunsResponse(runs=runs, pagination=pagination)

    def get_sync_run_details(self, run_id: UUID) -> SyncRunDetails | None:
        """
        Get detailed information about specific sync run.

        Args:
            run_id: Pipeline run ID

        Returns:
            Run details model with logs and metrics
        """
        run_data = self.pipeline_repo.get_pipeline_run(str(run_id))
        if not run_data:
            return None

        # Get run logs and metrics
        logs = self.pipeline_repo.get_run_logs(str(run_id))
        metrics = self.pipeline_repo.get_run_metrics(str(run_id))

        return SyncRunDetails(
            id=run_data["id"],
            provider_id=run_data["provider_id"],
            provider_name=run_data.get("provider_name"),
            status=run_data["status"],
            run_type=run_data.get("run_type"),
            started_at=run_data["started_at"],
            completed_at=run_data.get("completed_at"),
            start_date=run_data.get("start_date"),
            end_date=run_data.get("end_date"),
            error_message=run_data.get("error_message"),
            logs=logs,
            metrics=metrics,
            config=run_data.get("config"),
        )

    async def cancel_sync_run(self, run_id: UUID) -> SyncActionResponse | None:
        """
        Cancel running sync job.

        Args:
            run_id: Pipeline run ID

        Returns:
            Cancellation result model
        """
        run_data = self.pipeline_repo.get_pipeline_run(str(run_id))
        if not run_data:
            return None

        if run_data["status"] not in ["pending", "running"]:
            raise ValueError(
                f"Cannot cancel sync run with status: {run_data['status']}"
            )

        try:
            # Try to cancel using orchestrator
            success = await self.orchestrator.cancel_pipeline_run(run_id)

            if success:
                # Update status in database
                self.pipeline_repo.update_run_status(str(run_id), "cancelled")

                return SyncActionResponse(
                    success=True,
                    message="Sync run cancelled successfully",
                    run_id=run_id,
                )
            else:
                return SyncActionResponse(
                    success=False,
                    message="Failed to cancel sync run",
                    run_id=run_id,
                )

        except Exception as e:
            logger.error(f"Error cancelling sync run {run_id}: {e}")
            raise

    async def retry_sync_run(self, run_id: UUID) -> SyncActionResponse | None:
        """
        Retry failed sync run with same parameters.

        Args:
            run_id: Original pipeline run ID

        Returns:
            Retry result model with new run ID
        """
        original_run = self.pipeline_repo.get_pipeline_run(str(run_id))
        if not original_run:
            return None

        if original_run["status"] not in ["failed", "cancelled"]:
            raise ValueError(
                f"Cannot retry sync run with status: {original_run['status']}"
            )

        try:
            # Get original run parameters
            provider_id = UUID(original_run["provider_id"])
            start_date = original_run.get("start_date")
            end_date = original_run.get("end_date")

            result = await self.orchestrator.run_pipeline(
                provider_id=provider_id,
                start_date=start_date,
                end_date=end_date,
                run_type="retry",
            )

            return SyncActionResponse(
                success=True,
                message="Sync run retry has been queued",
                run_id=run_id,
                new_run_id=result["pipeline_run_id"],
            )

        except Exception as e:
            logger.error(f"Error retrying sync run {run_id}: {e}")
            raise

    def get_sync_statistics(
        self,
        provider_id: UUID | None = None,
        days: int = 30,
    ) -> SyncStatisticsResponse:
        """
        Get sync statistics and metrics.

        Args:
            provider_id: Filter by provider
            days: Number of days to analyze

        Returns:
            Sync statistics response model
        """
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            logger.info(
                f"Getting statistics for provider_id={provider_id}, days={days}"
            )

            stats_data = self.pipeline_repo.get_statistics(
                provider_id=str(provider_id) if provider_id else None,
                start_date=start_date,
                end_date=end_date,
            )

            logger.debug(f"Raw stats_data: {stats_data}")

            # Convert provider_stats to ProviderStats models
            provider_stats = []
            for stats in stats_data.get("provider_stats", []):
                try:
                    provider_stats.append(ProviderStats(**stats))
                except Exception as e:
                    logger.error(f"Error creating ProviderStats: {e}, data: {stats}")
                    raise

            # Convert daily_stats to DailyStats models
            daily_stats = []
            for stats in stats_data.get("daily_stats", []):
                try:
                    daily_stats.append(DailyStats(**stats))
                except Exception as e:
                    logger.error(f"Error creating DailyStats: {e}, data: {stats}")
                    raise

            logger.debug(
                f"Converted {len(provider_stats)} provider_stats, {len(daily_stats)} daily_stats"
            )

            return SyncStatisticsResponse(
                period_days=stats_data["period_days"],
                total_runs=stats_data["total_runs"],
                successful_runs=stats_data["successful_runs"],
                failed_runs=stats_data["failed_runs"],
                cancelled_runs=stats_data["cancelled_runs"],
                average_duration_seconds=stats_data["average_duration_seconds"],
                total_records_processed=stats_data["total_records_processed"],
                success_rate=stats_data["success_rate"],
                provider_stats=provider_stats,
                daily_stats=daily_stats,
            )

        except Exception as e:
            logger.error(f"Error in get_sync_statistics: {e}", exc_info=True)
            raise

    async def _get_providers_for_sync(self, provider_id: UUID | None = None) -> list:
        """Get providers that should be synced."""
        if provider_id:
            provider = self.provider_repo.get(provider_id)
            if not provider:
                raise ValueError(f"Provider {provider_id} not found")
            if not provider.is_active:
                raise ValueError(f"Provider {provider_id} is not active")
            return [provider]
        else:
            return self.provider_repo.get_active_providers_for_sync()

    async def _start_sync_jobs_hamilton(
        self, providers: list, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Start sync jobs for multiple providers using Hamilton orchestrator."""
        run_ids = []
        errors = []

        for provider in providers:
            try:
                result = await self.orchestrator.run_pipeline(
                    provider_id=UUID(provider.id),
                    start_date=start_date,
                    end_date=end_date,
                    run_type="manual",
                )
                run_ids.append(result["pipeline_run_id"])

            except Exception as e:
                logger.error(
                    f"Failed to start Hamilton sync for provider {provider.id}: {e}"
                )
                errors.append(
                    {
                        "provider_id": provider.id,
                        "provider_name": provider.name,
                        "error": str(e),
                        "orchestrator": "Hamilton",
                    }
                )

        return {"run_ids": run_ids, "errors": errors}

    def _get_sync_summary(self, runs: list) -> SyncRunSummary:
        """Get summary statistics from pipeline runs."""
        if not runs:
            return SyncRunSummary(
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                running_runs=0,
                success_rate=0.0,
                last_run_status=None,
                last_run_time=None,
            )

        total_runs = len(runs)
        successful_runs = len([r for r in runs if r.status == "completed"])
        failed_runs = len([r for r in runs if r.status == "failed"])
        running_runs = len([r for r in runs if r.status == "running"])

        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0.0

        # Most recent run
        latest_run = runs[0] if runs else None

        return SyncRunSummary(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            running_runs=running_runs,
            success_rate=round(success_rate, 2),
            last_run_status=latest_run.status if latest_run else None,
            last_run_time=latest_run.started_at if latest_run else None,
        )

    def _get_date_range(
        self,
        start_date: datetime | None,
        end_date: datetime | None,
        days_back: int | None = 7,
    ) -> tuple[datetime, datetime]:
        """Get date range for sync operations."""
        if end_date:
            end_date = end_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
        else:
            end_date = datetime.now(UTC).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)

        if not start_date:
            if days_back:
                start_date = end_date - timedelta(days=days_back)
            else:
                start_date = end_date - timedelta(days=7)  # Default 7 days

        return start_date, end_date

    def generate_pipeline_graph(self, output_path: str, format: str = "png") -> str:
        """Generate pipeline DAG visualization."""
        try:
            from pipeline.hamilton_orchestrator import HamiltonOrchestrator

            hamilton_orch = HamiltonOrchestrator()
            return hamilton_orch.visualize_dag(output_path)

        except ImportError:
            raise ValueError(
                "Hamilton not installed. Run: pip install 'sf-hamilton[visualization]'"
            ) from None
        except Exception as e:
            raise ValueError(f"Failed to generate graph: {e}") from e
