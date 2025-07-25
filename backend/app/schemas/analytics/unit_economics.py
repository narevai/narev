"""
Unit economics calculation schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class UnitEconomicsData(BaseModel):
    """Single unit economics data point."""

    charge_period_date: str = Field(..., description="Date of the charge period")
    cost_per_unit: float = Field(..., description="Cost per unit (e.g., per GB)")
    total_cost: float = Field(..., description="Total cost for the day")
    total_quantity: float = Field(..., description="Total quantity consumed")
    consumed_unit: str = Field(..., description="Unit of measurement")
    record_count: int = Field(..., description="Number of records")


class UnitEconomicsSummary(BaseModel):
    """Summary statistics for unit economics analysis."""

    total_days: int = Field(..., description="Total number of days analyzed")
    total_cost: float = Field(..., description="Total cost across all days")
    total_quantity: float = Field(..., description="Total quantity across all days")
    average_cost_per_unit: float = Field(..., description="Average cost per unit")
    unit_type: str = Field(..., description="Type of unit analyzed")


class UnitEconomicsFilters(BaseModel):
    """Applied filters for unit economics analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    unit_type: str = Field(..., description="Unit type filter")
    charge_description_filter: str = Field(..., description="Charge description filter")


class UnitEconomicsResponse(BaseModel):
    """Response for unit economics calculation."""

    status: str = Field(..., description="Response status")
    data: list[UnitEconomicsData] | None = Field(
        None, description="Unit economics data"
    )
    summary: UnitEconomicsSummary | None = Field(None, description="Summary statistics")
    filters: UnitEconomicsFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
