"""
Sync API Schemas
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SyncTriggerRequest(BaseModel):
    """Request schema for triggering sync."""

    provider_id: UUID | None = Field(None, description="Specific provider to sync")
    start_date: datetime | None = Field(None, description="Start date for sync")
    end_date: datetime | None = Field(None, description="End date for sync")
    days_back: int | None = Field(
        30, description="Number of days to sync back", ge=1, le=365
    )


class SyncTriggerResponse(BaseModel):
    """Response for sync trigger endpoint."""

    success: bool
    message: str
    info: str | None = None


class SyncRunSummary(BaseModel):
    """Summary statistics for sync runs."""

    total_runs: int
    successful_runs: int
    failed_runs: int
    running_runs: int
    success_rate: float = Field(..., ge=0, le=100)
    last_run_status: str | None = None
    last_run_time: datetime | None = None


class SyncRunInfo(BaseModel):
    """Basic sync run information."""

    id: UUID
    provider_id: UUID
    provider_name: str | None = None
    status: str = Field(..., pattern="^(pending|running|completed|failed|cancelled)$")
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    records_processed: int | None = None
    records_created: int | None = None
    records_updated: int | None = None
    error_message: str | None = None


class SyncStatusResponse(BaseModel):
    """Response for sync status endpoint."""

    runs: list[SyncRunInfo]
    summary: SyncRunSummary


class PaginationInfo(BaseModel):
    """Pagination information."""

    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    has_more: bool


class SyncRunsResponse(BaseModel):
    """Paginated response for sync runs."""

    runs: list[SyncRunInfo]
    pagination: PaginationInfo


class SyncRunLog(BaseModel):
    """Sync run log entry."""

    timestamp: datetime
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str
    component: str | None = None


class SyncRunMetrics(BaseModel):
    """Metrics for a sync run - only fields with real data."""

    duration_seconds: float | None = None
    records_processed: int | None = None
    records_created: int | None = None
    records_updated: int | None = None
    records_skipped: int | None = None


class SyncRunDetails(BaseModel):
    """Detailed sync run information with logs and metrics."""

    id: UUID
    provider_id: UUID
    provider_name: str | None = None
    status: str = Field(..., pattern="^(pending|running|completed|failed|cancelled)$")
    run_type: str | None = Field(None, pattern="^(manual|scheduled|retry)$")
    started_at: datetime
    completed_at: datetime | None = None
    start_date: datetime | None = None  # Date range being synced
    end_date: datetime | None = None
    error_message: str | None = None

    # Related data
    logs: list[SyncRunLog] = Field(default_factory=list)
    metrics: SyncRunMetrics | None = None

    # Configuration used
    config: dict[str, Any] | None = None


class SyncActionResponse(BaseModel):
    """Response for sync actions (cancel, retry)."""

    success: bool
    message: str
    run_id: UUID
    new_run_id: UUID | None = None  # For retry operations


class ProviderStats(BaseModel):
    """Provider-specific statistics."""

    provider_id: UUID
    provider_name: str | None = None
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    avg_duration_seconds: float | None = None
    total_records_processed: int


class DailyStats(BaseModel):
    """Daily statistics."""

    date: datetime
    total_runs: int
    successful_runs: int
    failed_runs: int
    total_records_processed: int
    avg_duration_seconds: float | None = None


class SyncStatisticsResponse(BaseModel):
    """Response for sync statistics"""

    period_days: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    cancelled_runs: int
    average_duration_seconds: float | None = None
    total_records_processed: int
    success_rate: float = Field(..., ge=0, le=100)

    # Breakdown by provider
    provider_stats: list[ProviderStats] = Field(default_factory=list)

    # Time series data
    daily_stats: list[DailyStats] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str
    timestamp: str
    details: dict[str, Any] | None = None


__all__ = [
    "SyncTriggerRequest",
    "SyncTriggerResponse",
    "SyncRunSummary",
    "SyncRunInfo",
    "SyncStatusResponse",
    "PaginationInfo",
    "SyncRunsResponse",
    "SyncRunLog",
    "SyncRunMetrics",
    "SyncRunDetails",
    "SyncActionResponse",
    "ProviderStats",
    "DailyStats",
    "SyncStatisticsResponse",
    "HealthCheckResponse",
]
