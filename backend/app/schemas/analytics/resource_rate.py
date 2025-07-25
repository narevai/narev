"""
Resource rate calculation schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class ResourceRateData(BaseModel):
    """Single resource rate data point."""

    provider_name: str = Field(..., description="Cloud provider name")
    service_name: str = Field(..., description="Service name")
    pricing_unit: str = Field(..., description="Pricing unit")
    region_name: str = Field(..., description="Region name")
    instance_series: str | None = Field(None, description="Instance series")
    total_core_count: int = Field(..., description="Total core count")
    average_effective_core_cost: float = Field(..., description="Average cost per core")


class ResourceRateSummary(BaseModel):
    """Summary statistics for resource rate analysis."""

    total_resources: int = Field(
        ..., description="Total number of resource configurations"
    )
    total_core_count: int = Field(
        ..., description="Total core count across all resources"
    )
    average_cost_per_core: float = Field(
        ..., description="Overall average cost per core"
    )


class ResourceRateFilters(BaseModel):
    """Applied filters for resource rate analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider filter")
    service_name: str | None = Field(None, description="Service filter")
    region_name: str | None = Field(None, description="Region filter")


class ResourceRateResponse(BaseModel):
    """Response for resource rate calculation."""

    status: str = Field(..., description="Response status")
    data: list[ResourceRateData] | None = Field(None, description="Resource rate data")
    summary: ResourceRateSummary | None = Field(None, description="Summary statistics")
    filters: ResourceRateFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
