"""
Resource usage quantification schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class ResourceUsageData(BaseModel):
    """Single resource usage data point."""

    provider_name: str = Field(..., description="Provider name")
    service_name: str = Field(..., description="Service name")
    pricing_unit: str = Field(..., description="Pricing unit")
    region_name: str = Field(..., description="Region name")
    instance_series: str = Field(..., description="Instance series")
    total_core_count: int = Field(..., description="Total core count")
    resource_count: int = Field(..., description="Number of resources")
    avg_core_count: float = Field(..., description="Average core count per resource")
    min_core_count: int = Field(..., description="Minimum core count")
    max_core_count: int = Field(..., description="Maximum core count")


class InstanceSeriesBreakdown(BaseModel):
    """Instance series breakdown."""

    instance_series: str = Field(..., description="Instance series")
    total_cores: int = Field(..., description="Total cores for this series")
    resource_count: int = Field(..., description="Number of resources")
    unique_regions: int = Field(..., description="Number of unique regions")
    unique_services: int = Field(..., description="Number of unique services")
    avg_cores_per_resource: float = Field(..., description="Average cores per resource")
    core_percentage: float = Field(..., description="Percentage of total cores")


class RegionUsageBreakdown(BaseModel):
    """Region usage breakdown."""

    region_name: str = Field(..., description="Region name")
    total_cores: int = Field(..., description="Total cores in this region")
    resource_count: int = Field(..., description="Number of resources")
    unique_instance_series: int = Field(
        ..., description="Number of unique instance series"
    )
    unique_services: int = Field(..., description="Number of unique services")
    avg_cores_per_resource: float = Field(..., description="Average cores per resource")
    core_percentage: float = Field(..., description="Percentage of total cores")


class ResourceUsageSummary(BaseModel):
    """Summary statistics for resource usage analysis."""

    total_core_count: int = Field(
        ..., description="Total core count across all resources"
    )
    total_resources: int = Field(..., description="Total number of resources")
    unique_instance_series: int = Field(
        ..., description="Number of unique instance series"
    )
    unique_services: int = Field(..., description="Number of unique services")
    unique_regions: int = Field(..., description="Number of unique regions")
    avg_cores_per_resource: float = Field(..., description="Average cores per resource")
    instance_series_breakdown: list[InstanceSeriesBreakdown] = Field(
        ..., description="Breakdown by instance series"
    )
    region_breakdown: list[RegionUsageBreakdown] = Field(
        ..., description="Breakdown by region"
    )


class ResourceUsageFilters(BaseModel):
    """Applied filters for resource usage analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    service_name: str | None = Field(None, description="Service name filter")
    region_name: str | None = Field(None, description="Region name filter")


class ResourceUsageResponse(BaseModel):
    """Response for resource usage quantification."""

    status: str = Field(..., description="Response status")
    data: list[ResourceUsageData] | None = Field(
        None, description="Resource usage data"
    )
    summary: ResourceUsageSummary | None = Field(None, description="Summary statistics")
    filters: ResourceUsageFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
