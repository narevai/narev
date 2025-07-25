"""
Pipeline Repository
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pipeline_run import PipelineRun
from app.schemas.sync import SyncRunInfo, SyncRunLog, SyncRunMetrics

logger = logging.getLogger(__name__)


class PipelineRepository:
    """Repository for pipeline run operations."""

    def __init__(self, db: Session):
        """Initialize repository."""
        self.db = db

    def get_recent_pipeline_runs(
        self, provider_id: str | None = None, limit: int = 10
    ) -> list[SyncRunInfo]:
        """
        Get recent pipeline runs with provider names.

        Returns:
            List of recent pipeline runs as Pydantic models
        """
        from app.models.provider import Provider

        query = self.db.query(
            PipelineRun,
            Provider.name.label("provider_name"),
            Provider.display_name.label("provider_display_name"),
        ).outerjoin(Provider, PipelineRun.provider_id == Provider.id)

        if provider_id:
            query = query.filter(PipelineRun.provider_id == provider_id)

        results = query.order_by(PipelineRun.started_at.desc()).limit(limit).all()

        return [
            self._to_sync_run_info_with_provider(
                run, provider_name, provider_display_name
            )
            for run, provider_name, provider_display_name in results
        ]

    def get_pipeline_runs(
        self,
        skip: int = 0,
        limit: int = 50,
        provider_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[SyncRunInfo], int]:
        """
        Get pipeline runs with pagination and filters.

        Returns:
            Tuple of (runs, total_count)
        """
        from app.models.provider import Provider

        query = self.db.query(
            PipelineRun,
            Provider.name.label("provider_name"),
            Provider.display_name.label("provider_display_name"),
        ).outerjoin(Provider, PipelineRun.provider_id == Provider.id)

        if provider_id:
            query = query.filter(PipelineRun.provider_id == provider_id)

        if status:
            query = query.filter(PipelineRun.status == status)

        if start_date:
            query = query.filter(PipelineRun.started_at >= start_date)

        if end_date:
            query = query.filter(PipelineRun.started_at <= end_date)

        # Get total count (need to count only PipelineRun records)
        count_query = self.db.query(PipelineRun)
        if provider_id:
            count_query = count_query.filter(PipelineRun.provider_id == provider_id)
        if status:
            count_query = count_query.filter(PipelineRun.status == status)
        if start_date:
            count_query = count_query.filter(PipelineRun.started_at >= start_date)
        if end_date:
            count_query = count_query.filter(PipelineRun.started_at <= end_date)

        total = count_query.count()

        # Get paginated results
        results = (
            query.order_by(PipelineRun.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [
            self._to_sync_run_info_with_provider(
                run, provider_name, provider_display_name
            )
            for run, provider_name, provider_display_name in results
        ], total

    def get_pipeline_run(self, run_id: str) -> dict[str, Any] | None:
        """Get pipeline run by ID - returns dict for detailed view."""
        run = self.db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if not run:
            return None

        return {
            "id": run.id,
            "provider_id": run.provider_id,
            "provider_name": getattr(run, "provider_name", None),
            "status": run.status,
            "run_type": getattr(run, "run_type", "manual"),
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "start_date": getattr(run, "start_date", None),
            "end_date": getattr(run, "end_date", None),
            "error_message": run.error_message,
            "config": getattr(run, "config", None),
        }

    def get_run_logs(self, run_id: str) -> list[SyncRunLog]:
        """Get logs for a pipeline run."""
        # This would typically query a separate logs table
        # For now, returning empty list as placeholder
        return []

    def get_run_metrics(self, run_id: str) -> SyncRunMetrics | None:
        """Get metrics for a pipeline run."""
        run = self.db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if not run:
            return None

        return SyncRunMetrics(
            duration_seconds=run.duration_seconds,
            records_processed=getattr(run, "records_extracted", 0),
            records_created=getattr(run, "records_transformed", 0),
            records_updated=getattr(run, "records_loaded", 0),
            records_skipped=getattr(run, "records_failed", 0),
        )

    def update_run_status(self, run_id: str, status: str) -> bool:
        """Update run status."""
        run = self.db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if not run:
            return False

        try:
            run.status = status
            if status in ["completed", "failed", "cancelled"] and not run.completed_at:
                run.completed_at = datetime.now(UTC)
                if run.started_at:
                    # Ensure started_at is timezone-aware
                    started_at = run.started_at
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=UTC)
                    run.duration_seconds = (
                        run.completed_at - started_at
                    ).total_seconds()

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating run status {run_id}: {e}")
            raise

    def get_statistics(
        self,
        provider_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get pipeline statistics with provider and daily breakdowns."""
        from sqlalchemy import case

        query = self.db.query(
            func.count(PipelineRun.id).label("total_runs"),
            func.sum(case((PipelineRun.status == "completed", 1), else_=0)).label(
                "completed_runs"
            ),
            func.sum(case((PipelineRun.status == "failed", 1), else_=0)).label(
                "failed_runs"
            ),
            func.sum(case((PipelineRun.status == "running", 1), else_=0)).label(
                "running_runs"
            ),
            func.sum(case((PipelineRun.status == "cancelled", 1), else_=0)).label(
                "cancelled_runs"
            ),
            func.sum(PipelineRun.records_extracted).label("total_extracted"),
            func.sum(PipelineRun.records_transformed).label("total_transformed"),
            func.sum(PipelineRun.records_loaded).label("total_loaded"),
            func.sum(PipelineRun.records_failed).label("total_failed"),
            func.avg(PipelineRun.duration_seconds).label("avg_duration"),
        )

        if provider_id:
            query = query.filter(PipelineRun.provider_id == provider_id)

        if start_date:
            query = query.filter(PipelineRun.started_at >= start_date)

        if end_date:
            query = query.filter(PipelineRun.started_at <= end_date)

        result = query.first()

        total_runs = result.total_runs or 0
        completed_runs = result.completed_runs or 0

        # Get provider stats (if not filtering by specific provider)
        provider_stats = []
        if not provider_id:
            provider_stats = self._get_provider_stats(start_date, end_date)

        # Get daily stats
        daily_stats = self._get_daily_stats(provider_id, start_date, end_date)

        return {
            "period_days": (end_date - start_date).days
            if start_date and end_date
            else 30,
            "total_runs": total_runs,
            "successful_runs": completed_runs,
            "failed_runs": result.failed_runs or 0,
            "cancelled_runs": result.cancelled_runs or 0,
            "average_duration_seconds": float(result.avg_duration or 0),
            "total_records_processed": result.total_extracted or 0,
            "success_rate": (completed_runs / total_runs * 100)
            if total_runs > 0
            else 0.0,
            "provider_stats": provider_stats,
            "daily_stats": daily_stats,
        }

    def _get_provider_stats(
        self, start_date: datetime | None, end_date: datetime | None
    ) -> list[dict[str, Any]]:
        """Get statistics grouped by provider."""
        from sqlalchemy import case

        from app.models.provider import Provider

        query = (
            self.db.query(
                PipelineRun.provider_id,
                Provider.name.label("provider_name"),
                Provider.display_name.label("provider_display_name"),
                func.count(PipelineRun.id).label("total_runs"),
                func.sum(case((PipelineRun.status == "completed", 1), else_=0)).label(
                    "successful_runs"
                ),
                func.sum(case((PipelineRun.status == "failed", 1), else_=0)).label(
                    "failed_runs"
                ),
                func.sum(PipelineRun.records_extracted).label("total_records"),
                func.avg(PipelineRun.duration_seconds).label("avg_duration"),
            )
            .join(Provider, PipelineRun.provider_id == Provider.id)
            .group_by(PipelineRun.provider_id, Provider.name, Provider.display_name)
        )

        if start_date:
            query = query.filter(PipelineRun.started_at >= start_date)
        if end_date:
            query = query.filter(PipelineRun.started_at <= end_date)

        results = query.all()

        return [
            {
                "provider_id": r.provider_id,
                "provider_name": r.provider_display_name or r.provider_name,
                "total_runs": r.total_runs,
                "successful_runs": r.successful_runs,
                "failed_runs": r.failed_runs,
                "success_rate": (r.successful_runs / r.total_runs * 100)
                if r.total_runs > 0
                else 0.0,
                "avg_duration_seconds": float(r.avg_duration or 0),
                "total_records_processed": r.total_records or 0,
            }
            for r in results
        ]

    def _get_daily_stats(
        self,
        provider_id: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> list[dict[str, Any]]:
        """Get statistics grouped by day."""
        from sqlalchemy import case

        query = self.db.query(
            func.date(PipelineRun.started_at).label("date"),
            func.count(PipelineRun.id).label("total_runs"),
            func.sum(case((PipelineRun.status == "completed", 1), else_=0)).label(
                "successful_runs"
            ),
            func.sum(case((PipelineRun.status == "failed", 1), else_=0)).label(
                "failed_runs"
            ),
            func.sum(PipelineRun.records_extracted).label("total_records"),
            func.avg(PipelineRun.duration_seconds).label("avg_duration"),
        ).group_by(func.date(PipelineRun.started_at))

        if provider_id:
            query = query.filter(PipelineRun.provider_id == provider_id)
        if start_date:
            query = query.filter(PipelineRun.started_at >= start_date)
        if end_date:
            query = query.filter(PipelineRun.started_at <= end_date)

        results = query.order_by(func.date(PipelineRun.started_at)).all()

        return [
            {
                "date": datetime.strptime(str(r.date), "%Y-%m-%d")
                if isinstance(r.date, str)
                else datetime.combine(r.date, datetime.min.time()),
                "total_runs": r.total_runs,
                "successful_runs": r.successful_runs,
                "failed_runs": r.failed_runs,
                "total_records_processed": r.total_records or 0,
                "avg_duration_seconds": float(r.avg_duration or 0),
            }
            for r in results
        ]

    def _to_sync_run_info(self, run: PipelineRun) -> SyncRunInfo:
        """Convert PipelineRun to SyncRunInfo model."""
        return SyncRunInfo(
            id=run.id,
            provider_id=run.provider_id,
            provider_name=getattr(run, "provider_name", None),
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=run.duration_seconds,
            records_processed=getattr(run, "records_extracted", None),
            records_created=getattr(run, "records_transformed", None),
            records_updated=getattr(run, "records_loaded", None),
            error_message=run.error_message,
        )

    def _to_sync_run_info_with_provider(
        self,
        run: PipelineRun,
        provider_name: str | None,
        provider_display_name: str | None,
    ) -> SyncRunInfo:
        """Convert PipelineRun to SyncRunInfo model with provider name from JOIN."""
        return SyncRunInfo(
            id=run.id,
            provider_id=run.provider_id,
            provider_name=provider_display_name or provider_name,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=run.duration_seconds,
            records_processed=getattr(run, "records_extracted", None),
            records_created=getattr(run, "records_transformed", None),
            records_updated=getattr(run, "records_loaded", None),
            error_message=run.error_message,
        )

    def get_by_id(self, run_id: str) -> PipelineRun | None:
        """Get pipeline run by ID."""
        return self.db.query(PipelineRun).filter(PipelineRun.id == run_id).first()

    def get_by_provider(
        self, provider_id: str, limit: int | None = None
    ) -> list[PipelineRun]:
        """Get pipeline runs by provider."""
        query = (
            self.db.query(PipelineRun)
            .filter(PipelineRun.provider_id == provider_id)
            .order_by(PipelineRun.started_at.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_running_runs(self) -> list[PipelineRun]:
        """Get currently running pipeline runs."""
        return (
            self.db.query(PipelineRun)
            .filter(PipelineRun.status == "running")
            .order_by(PipelineRun.started_at.desc())
            .all()
        )

    def get_failed_runs(
        self, provider_id: str | None = None, limit: int = 20
    ) -> list[PipelineRun]:
        """Get failed pipeline runs."""
        query = self.db.query(PipelineRun).filter(PipelineRun.status == "failed")

        if provider_id:
            query = query.filter(PipelineRun.provider_id == provider_id)

        return query.order_by(PipelineRun.started_at.desc()).limit(limit).all()

    def create(self, pipeline_run: PipelineRun) -> PipelineRun:
        """Create new pipeline run."""
        try:
            self.db.add(pipeline_run)
            self.db.commit()
            self.db.refresh(pipeline_run)
            return pipeline_run
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating pipeline run: {e}")
            raise

    def update(self, run_id: str, update_data: dict[str, Any]) -> PipelineRun | None:
        """Update pipeline run."""
        run = self.get_by_id(run_id)
        if not run:
            return None

        try:
            for key, value in update_data.items():
                if hasattr(run, key):
                    setattr(run, key, value)

            self.db.commit()
            self.db.refresh(run)
            return run
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating pipeline run {run_id}: {e}")
            raise

    def delete_old_runs(
        self, older_than_days: int = 30, keep_failed: bool = True
    ) -> int:
        """Delete old pipeline runs."""
        cutoff_date = datetime.now(UTC) - timedelta(days=older_than_days)

        query = self.db.query(PipelineRun).filter(PipelineRun.started_at < cutoff_date)

        if keep_failed:
            query = query.filter(PipelineRun.status != "failed")

        try:
            count = query.count()
            query.delete()
            self.db.commit()
            logger.info(f"Deleted {count} old pipeline runs")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting old pipeline runs: {e}")
            raise
