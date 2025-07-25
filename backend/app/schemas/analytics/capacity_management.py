"""
Capacity management schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class UnusedCapacityData(BaseModel):
    """Single unused capacity reservation data point."""

    provider_name: str = Field(..., description="Provider name")
    billing_account_id: str = Field(..., description="Billing account ID")
    commitment_discount_id: str = Field(..., description="Capacity reservation ID")
    commitment_discount_status: str = Field(
        ..., description="Capacity reservation status"
    )
    total_billed_cost: float = Field(..., description="Total billed cost")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    first_charge_date: str | None = Field(None, description="First charge date")
    last_charge_date: str | None = Field(None, description="Last charge date")


class ProviderBreakdown(BaseModel):
    """Provider breakdown summary."""

    provider_name: str = Field(..., description="Provider name")
    total_cost: float = Field(..., description="Total cost for this provider")
    reservation_count: int = Field(..., description="Number of unused reservations")
    charge_count: int = Field(..., description="Number of charges")
    unique_accounts: int = Field(..., description="Number of unique accounts")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class UnusedCapacitySummary(BaseModel):
    """Summary statistics for unused capacity analysis."""

    total_unused_reservations: int = Field(
        ..., description="Total number of unused reservations"
    )
    total_unused_cost: float = Field(
        ..., description="Total cost of unused reservations"
    )
    total_charges: int = Field(..., description="Total number of charges")
    unique_providers: int = Field(..., description="Number of unique providers")
    unique_accounts: int = Field(..., description="Number of unique accounts")
    cost_impact: float = Field(..., description="Financial impact of unused capacity")
    provider_breakdown: list[ProviderBreakdown] = Field(
        ..., description="Breakdown by provider"
    )


class UnusedCapacityFilters(BaseModel):
    """Applied filters for unused capacity analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    billing_account_id: str | None = Field(
        None, description="Billing account ID filter"
    )


class UnusedCapacityResponse(BaseModel):
    """Response for unused capacity identification."""

    status: str = Field(..., description="Response status")
    data: list[UnusedCapacityData] | None = Field(
        None, description="Unused capacity data"
    )
    summary: UnusedCapacitySummary | None = Field(
        None, description="Summary statistics"
    )
    filters: UnusedCapacityFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class StatusBreakdown(BaseModel):
    """Status breakdown summary."""

    status: str = Field(..., description="Capacity reservation status")
    total_cost: float = Field(..., description="Total cost for this status")
    charge_count: int = Field(..., description="Number of charges for this status")
    unique_reservations: int = Field(
        ..., description="Number of unique reservations for this status"
    )
    cost_percentage: float = Field(..., description="Percentage of total cost")


class CapacityReservationData(BaseModel):
    """Single capacity reservation data point."""

    status: str = Field(..., description="Capacity reservation status")
    provider_name: str = Field(..., description="Provider name")
    billing_account_id: str = Field(..., description="Billing account ID")
    total_billed_cost: float = Field(..., description="Total billed cost")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    unique_reservations: int = Field(..., description="Number of unique reservations")


class CapacityReservationSummary(BaseModel):
    """Summary statistics for capacity reservation analysis."""

    total_compute_cost: float = Field(..., description="Total compute cost")
    total_charges: int = Field(..., description="Total number of charges")
    reservation_utilization_percentage: float = Field(
        ..., description="Reservation utilization percentage"
    )
    cost_with_reservations: float = Field(
        ..., description="Cost with capacity reservations"
    )
    cost_without_reservations: float = Field(
        ..., description="Cost without capacity reservations"
    )
    total_reservations: int = Field(..., description="Total number of reservations")
    status_breakdown: list[StatusBreakdown] = Field(
        ..., description="Breakdown by status"
    )


class CapacityReservationFilters(BaseModel):
    """Applied filters for capacity reservation analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    billing_account_id: str | None = Field(
        None, description="Billing account ID filter"
    )


class CapacityReservationAnalysisResponse(BaseModel):
    """Response for capacity reservation analysis."""

    status: str = Field(..., description="Response status")
    data: list[CapacityReservationData] | None = Field(
        None, description="Capacity reservation data"
    )
    summary: CapacityReservationSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: CapacityReservationFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
