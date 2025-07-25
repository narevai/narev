"""
Billing API Schemas
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BillingSummaryResponse(BaseModel):
    """Response schema for billing summary."""

    total_cost: float
    total_records: int
    start_date: datetime
    end_date: datetime
    currency: str = "USD"
    providers: dict[str, float] = Field(default_factory=dict)
    services: dict[str, float] = Field(default_factory=dict)
    daily_costs: list[dict[str, Any]] = Field(default_factory=list)


class BillingRecord(BaseModel):
    """Individual billing record."""

    id: UUID
    provider_name: str | None = None
    service_name: str | None = None
    effective_cost: float
    billed_cost: float | None = None
    list_cost: float | None = None
    billing_currency: str | None = None
    service_category: str | None = None
    charge_category: str | None = None
    charge_period_start: datetime | None = None
    charge_period_end: datetime | None = None
    resource_name: str | None = None
    tags: dict[str, Any] = Field(default_factory=dict)


class PaginationInfo(BaseModel):
    """Pagination information."""

    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    has_more: bool


class BillingDataResponse(BaseModel):
    """Response schema for paginated billing data."""

    data: list[BillingRecord]
    pagination: PaginationInfo


class ServiceCostBreakdown(BaseModel):
    """Service cost breakdown item."""

    service_name: str
    total_cost: float
    record_count: int
    percentage: float | None = None


class ServiceBreakdownResponse(BaseModel):
    """Response schema for service cost breakdown."""

    services: list[ServiceCostBreakdown]
    total_services: int
    total_cost: float | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


class TrendDataPoint(BaseModel):
    """Single trend data point."""

    date: datetime
    cost: float
    record_count: int | None = None


class CostTrendsResponse(BaseModel):
    """Response schema for cost trends."""

    trends: list[TrendDataPoint]
    group_by: str = Field(..., pattern="^(day|week|month)$")
    total_cost: float | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


class StatisticsResponse(BaseModel):
    """Response schema for billing statistics."""

    total_records: int
    total_cost: float
    average_cost_per_record: float | None = None
    cost_by_provider: dict[str, float] = Field(default_factory=dict)
    cost_by_service: dict[str, float] = Field(default_factory=dict)
    period_start: datetime | None = None
    period_end: datetime | None = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str
    timestamp: str
