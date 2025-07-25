"""
Virtual currency related schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class VirtualCurrencyTargetData(BaseModel):
    """Single virtual currency target data point."""

    provider_name: str = Field(..., description="Cloud provider name")
    publisher_name: str = Field(..., description="Publisher name")
    service_name: str = Field(..., description="Service name")
    charge_description: str = Field(..., description="Charge description")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    pricing_currency: str = Field(..., description="Pricing currency used")


class VirtualCurrencyTargetSummary(BaseModel):
    """Summary statistics for virtual currency target analysis."""

    total_charges: int = Field(..., description="Total number of charges")
    total_cost: float = Field(..., description="Total cost across all charges")
    unique_services: int = Field(..., description="Number of unique services")
    top_currency: str | None = Field(None, description="Currency with highest cost")
    currencies_found: list[str] = Field(..., description="All currencies found")


class VirtualCurrencyTargetFilters(BaseModel):
    """Applied filters for virtual currency target analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    pricing_currency: str | None = Field(None, description="Pricing currency filter")
    limit: int = Field(..., description="Result limit")


class VirtualCurrencyTargetResponse(BaseModel):
    """Response for virtual currency target analysis."""

    status: str = Field(..., description="Response status")
    data: list[VirtualCurrencyTargetData] | None = Field(
        None, description="Virtual currency target data"
    )
    summary: VirtualCurrencyTargetSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: VirtualCurrencyTargetFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class VirtualCurrencyPurchaseData(BaseModel):
    """Single virtual currency purchase data point."""

    provider_name: str = Field(..., description="Cloud provider name")
    publisher_name: str = Field(..., description="Publisher name")
    charge_description: str = Field(..., description="Charge description")
    pricing_unit: str = Field(..., description="Pricing unit")
    billing_currency: str = Field(..., description="Billing currency")
    total_pricing_quantity: float = Field(..., description="Total pricing quantity")
    total_billed_cost: float = Field(..., description="Total billed cost")
    purchase_count: int = Field(..., description="Number of purchases")
    avg_purchase_cost: float = Field(..., description="Average purchase cost")
    first_purchase: str | None = Field(None, description="First purchase date")
    last_purchase: str | None = Field(None, description="Last purchase date")


class UnitBreakdown(BaseModel):
    """Unit breakdown summary."""

    pricing_unit: str = Field(..., description="Pricing unit")
    total_cost: float = Field(..., description="Total cost for this unit")
    total_quantity: float = Field(..., description="Total quantity for this unit")
    purchase_count: int = Field(..., description="Number of purchases for this unit")


class VirtualCurrencyPurchaseSummary(BaseModel):
    """Summary statistics for virtual currency purchase analysis."""

    total_purchases: int = Field(..., description="Total number of purchases")
    total_cost: float = Field(..., description="Total cost across all purchases")
    total_quantity: float = Field(..., description="Total quantity purchased")
    unique_units: int = Field(..., description="Number of unique pricing units")
    avg_purchase_cost: float = Field(..., description="Average cost per purchase")
    unit_breakdown: list[UnitBreakdown] = Field(
        ..., description="Breakdown by pricing unit"
    )


class VirtualCurrencyPurchaseFilters(BaseModel):
    """Applied filters for virtual currency purchase analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    pricing_unit: str | None = Field(None, description="Pricing unit filter")
    group_by: str = Field(..., description="Grouping method")


class VirtualCurrencyPurchaseResponse(BaseModel):
    """Response for virtual currency purchase analysis."""

    status: str = Field(..., description="Response status")
    data: list[VirtualCurrencyPurchaseData] | None = Field(
        None, description="Virtual currency purchase data"
    )
    summary: VirtualCurrencyPurchaseSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: VirtualCurrencyPurchaseFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
