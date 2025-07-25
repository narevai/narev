"""
Export API Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BillingExportRequest(BaseModel):
    """Billing export request parameters."""

    format: str = Field(
        ..., pattern="^(csv|xlsx)$", description="Export format (files only)"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(
        10000, ge=1, le=50000, description="Number of records to export (max 50k)"
    )

    # Date filters
    start_date: datetime | None = None
    end_date: datetime | None = None

    # Filters
    provider_id: UUID | None = None
    service_name: str | None = Field(None, max_length=255)
    service_category: str | None = Field(
        None,
        pattern="^(AI and Machine Learning|Analytics|Compute|Databases|Networking|Storage|Security|Other)$",
    )
    charge_category: str | None = Field(
        None,
        pattern="^(Usage|Purchase|Tax|Credit|Adjustment)$",
    )
    min_cost: float | None = Field(None, ge=0)
    max_cost: float | None = Field(None, ge=0)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str
    timestamp: str
