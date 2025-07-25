"""
Cost analysis schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class EffectiveCostByCurrencyData(BaseModel):
    """Single effective cost by currency data point."""

    provider_name: str = Field(..., description="Cloud provider name")
    publisher_name: str = Field(..., description="Publisher name")
    service_name: str = Field(..., description="Service name")
    pricing_currency: str = Field(..., description="Pricing currency")
    total_effective_cost: float = Field(..., description="Total effective cost")
    avg_effective_cost: float = Field(..., description="Average effective cost")
    charge_count: int = Field(..., description="Number of charges")
    earliest_charge: str | None = Field(None, description="Earliest charge date")
    latest_charge: str | None = Field(None, description="Latest charge date")


class CurrencyBreakdown(BaseModel):
    """Currency breakdown summary."""

    currency: str = Field(..., description="Currency code")
    total_cost: float = Field(..., description="Total cost in this currency")


class EffectiveCostByCurrencySummary(BaseModel):
    """Summary statistics for effective cost by currency analysis."""

    total_cost: float = Field(..., description="Total cost across all currencies")
    total_charges: int = Field(..., description="Total number of charges")
    unique_currencies: int = Field(..., description="Number of unique currencies")
    unique_services: int = Field(..., description="Number of unique services")
    currency_breakdown: list[CurrencyBreakdown] = Field(
        ..., description="Breakdown by currency"
    )


class EffectiveCostByCurrencyFilters(BaseModel):
    """Applied filters for effective cost by currency analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    include_exchange_rates: bool = Field(
        ..., description="Whether to include exchange rates"
    )


class EffectiveCostByCurrencyResponse(BaseModel):
    """Response for effective cost by currency analysis."""

    status: str = Field(..., description="Response status")
    data: list[EffectiveCostByCurrencyData] | None = Field(
        None, description="Cost by currency data"
    )
    summary: EffectiveCostByCurrencySummary | None = Field(
        None, description="Summary statistics"
    )
    filters: EffectiveCostByCurrencyFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ContractedSavingsData(BaseModel):
    """Single contracted savings data point."""

    service_name: str = Field(..., description="Service name")
    service_subcategory: str = Field(..., description="Service subcategory")
    charge_description: str = Field(..., description="Charge description")
    billing_currency: str | None = Field(None, description="Billing currency")
    pricing_currency: str | None = Field(None, description="Pricing currency")
    contracted_savings_in_billing_currency: float = Field(
        ..., description="Unit savings in billing currency"
    )
    total_savings_amount: float = Field(..., description="Total savings amount")
    total_list_cost: float = Field(..., description="Total list cost")
    total_contracted_cost: float = Field(..., description="Total contracted cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_unit_savings: float = Field(..., description="Average unit savings")
    commitment_discount_type: str = Field(..., description="Commitment discount type")
    commitment_discount_status: str = Field(
        ..., description="Commitment discount status"
    )
    savings_percentage: float = Field(..., description="Savings percentage")


class CommitmentBreakdown(BaseModel):
    """Commitment type breakdown."""

    commitment_type: str = Field(..., description="Commitment type")
    total_savings: float = Field(
        ..., description="Total savings for this commitment type"
    )
    total_list_cost: float = Field(
        ..., description="Total list cost for this commitment type"
    )
    charge_count: int = Field(
        ..., description="Number of charges for this commitment type"
    )
    savings_percentage: float = Field(
        ..., description="Savings percentage for this commitment type"
    )


class ContractedSavingsSummary(BaseModel):
    """Summary statistics for contracted savings analysis."""

    total_savings: float = Field(
        ..., description="Total savings across all commitments"
    )
    total_list_cost: float = Field(..., description="Total list cost")
    total_contracted_cost: float = Field(..., description="Total contracted cost")
    overall_savings_percentage: float = Field(
        ..., description="Overall savings percentage"
    )
    total_charges: int = Field(..., description="Total number of charges")
    commitment_breakdown: list[CommitmentBreakdown] = Field(
        ..., description="Breakdown by commitment type"
    )


class ContractedSavingsFilters(BaseModel):
    """Applied filters for contracted savings analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    commitment_type: str | None = Field(None, description="Commitment type filter")


class ContractedSavingsResponse(BaseModel):
    """Response for contracted savings analysis."""

    status: str = Field(..., description="Response status")
    data: list[ContractedSavingsData] | None = Field(
        None, description="Contracted savings data"
    )
    summary: ContractedSavingsSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: ContractedSavingsFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ServiceCostData(BaseModel):
    """Single service cost data point."""

    billing_period_start: str = Field(..., description="Billing period start")
    provider_name: str = Field(..., description="Provider name")
    sub_account_id: str = Field(..., description="Sub account ID")
    sub_account_name: str = Field(..., description="Sub account name")
    service_name: str = Field(..., description="Service name")
    total_billed_cost: float = Field(..., description="Total billed cost")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_effective_cost: float = Field(..., description="Average effective cost")
    min_effective_cost: float = Field(..., description="Minimum effective cost")
    max_effective_cost: float = Field(..., description="Maximum effective cost")


class PeriodBreakdown(BaseModel):
    """Period breakdown summary."""

    billing_period: str = Field(..., description="Billing period")
    total_cost: float = Field(..., description="Total cost for this period")
    cost_percentage: float = Field(..., description="Percentage of total cost")
    deviation_from_avg: float = Field(..., description="Deviation from average cost")


class ServiceCostSummary(BaseModel):
    """Summary statistics for service cost analysis."""

    total_service_cost: float = Field(..., description="Total service cost")
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_billing_periods: int = Field(
        ..., description="Number of unique billing periods"
    )
    unique_subaccounts: int = Field(..., description="Number of unique subaccounts")
    unique_providers: int = Field(..., description="Number of unique providers")
    avg_cost_per_period: float = Field(..., description="Average cost per period")
    cost_variance: float = Field(..., description="Cost variance (standard deviation)")
    period_breakdown: list[PeriodBreakdown] = Field(
        ..., description="Breakdown by period"
    )


class ServiceCostFilters(BaseModel):
    """Applied filters for service cost analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    service_name: str = Field(..., description="Service name filter")
    provider_name: str | None = Field(None, description="Provider name filter")
    sub_account_id: str | None = Field(None, description="Sub account ID filter")


class ServiceCostAnalysisResponse(BaseModel):
    """Response for service cost analysis."""

    status: str = Field(..., description="Response status")
    data: list[ServiceCostData] | None = Field(None, description="Service cost data")
    summary: ServiceCostSummary | None = Field(None, description="Summary statistics")
    filters: ServiceCostFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ServiceCostByRegionData(BaseModel):
    """Single service cost by region data point."""

    charge_period_start: str = Field(..., description="Charge period start")
    provider_name: str = Field(..., description="Provider name")
    region_id: str = Field(..., description="Region ID")
    region_name: str = Field(..., description="Region name")
    service_name: str = Field(..., description="Service name")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_effective_cost: float = Field(..., description="Average effective cost")
    min_effective_cost: float = Field(..., description="Minimum effective cost")
    max_effective_cost: float = Field(..., description="Maximum effective cost")


class RegionBreakdown(BaseModel):
    """Region breakdown summary."""

    region_id: str = Field(..., description="Region ID")
    region_name: str = Field(..., description="Region name")
    total_cost: float = Field(..., description="Total cost for this region")
    charge_count: int = Field(..., description="Number of charges")
    unique_services: int = Field(..., description="Number of unique services")
    unique_providers: int = Field(..., description="Number of unique providers")
    charge_periods: int = Field(..., description="Number of charge periods")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class ServiceByRegionBreakdown(BaseModel):
    """Service breakdown summary."""

    service_name: str = Field(..., description="Service name")
    total_cost: float = Field(..., description="Total cost for this service")
    charge_count: int = Field(..., description="Number of charges")
    unique_regions: int = Field(..., description="Number of unique regions")
    unique_providers: int = Field(..., description="Number of unique providers")
    charge_periods: int = Field(..., description="Number of charge periods")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class ServiceCostByRegionSummary(BaseModel):
    """Summary statistics for service cost by region analysis."""

    total_cost: float = Field(..., description="Total cost across all regions")
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_regions: int = Field(..., description="Number of unique regions")
    unique_services: int = Field(..., description="Number of unique services")
    unique_providers: int = Field(..., description="Number of unique providers")
    charge_periods: int = Field(..., description="Number of charge periods")
    region_breakdown: list[RegionBreakdown] = Field(
        ..., description="Breakdown by region"
    )
    service_breakdown: list[ServiceByRegionBreakdown] = Field(
        ..., description="Breakdown by service"
    )


class ServiceCostByRegionFilters(BaseModel):
    """Applied filters for service cost by region analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    region_id: str | None = Field(None, description="Region ID filter")
    service_name: str | None = Field(None, description="Service name filter")


class ServiceCostByRegionResponse(BaseModel):
    """Response for service cost by region analysis."""

    status: str = Field(..., description="Response status")
    data: list[ServiceCostByRegionData] | None = Field(
        None, description="Service cost by region data"
    )
    summary: ServiceCostByRegionSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: ServiceCostByRegionFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ServiceCostBySubaccountData(BaseModel):
    """Single service cost by subaccount data point."""

    provider_name: str = Field(..., description="Provider name")
    service_name: str = Field(..., description="Service name")
    sub_account_id: str = Field(..., description="Sub account ID")
    sub_account_name: str = Field(..., description="Sub account name")
    charge_period_start: str = Field(..., description="Charge period start")
    billing_period_start: str | None = Field(None, description="Billing period start")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_effective_cost: float = Field(..., description="Average effective cost")
    min_effective_cost: float = Field(..., description="Minimum effective cost")
    max_effective_cost: float = Field(..., description="Maximum effective cost")


class SubaccountServiceBreakdown(BaseModel):
    """Service breakdown for subaccount."""

    service_name: str = Field(..., description="Service name")
    total_cost: float = Field(..., description="Total cost for this service")
    charge_count: int = Field(..., description="Number of charges")
    charge_periods: int = Field(..., description="Number of charge periods")
    avg_cost_per_period: float = Field(..., description="Average cost per period")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class SubaccountPeriodBreakdown(BaseModel):
    """Period breakdown for subaccount."""

    charge_period: str = Field(..., description="Charge period")
    total_cost: float = Field(..., description="Total cost for this period")
    cost_percentage: float = Field(..., description="Percentage of total cost")
    deviation_from_avg: float = Field(..., description="Deviation from average cost")


class ServiceCostBySubaccountSummary(BaseModel):
    """Summary statistics for service cost by subaccount analysis."""

    total_subaccount_cost: float = Field(
        ..., description="Total cost for the subaccount"
    )
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_services: int = Field(..., description="Number of unique services")
    charge_periods: int = Field(..., description="Number of charge periods")
    avg_cost_per_period: float = Field(..., description="Average cost per period")
    cost_variance: float = Field(..., description="Cost variance (standard deviation)")
    service_breakdown: list[SubaccountServiceBreakdown] = Field(
        ..., description="Breakdown by service"
    )
    period_breakdown: list[SubaccountPeriodBreakdown] = Field(
        ..., description="Breakdown by period"
    )


class ServiceCostBySubaccountFilters(BaseModel):
    """Applied filters for service cost by subaccount analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    sub_account_id: str = Field(..., description="Sub account ID filter")
    provider_name: str = Field(..., description="Provider name filter")
    service_name: str | None = Field(None, description="Service name filter")


class ServiceCostBySubaccountResponse(BaseModel):
    """Response for service cost by subaccount report."""

    status: str = Field(..., description="Response status")
    data: list[ServiceCostBySubaccountData] | None = Field(
        None, description="Service cost by subaccount data"
    )
    summary: ServiceCostBySubaccountSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: ServiceCostBySubaccountFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ServiceCostTrendData(BaseModel):
    """Single service cost trend data point."""

    charge_month: int = Field(..., description="Charge month (1-12)")
    charge_year: int = Field(..., description="Charge year")
    month_name: str = Field(..., description="Month name (YYYY-MM)")
    provider_name: str = Field(..., description="Provider name")
    service_name: str = Field(..., description="Service name")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_effective_cost: float = Field(..., description="Average effective cost")


class MonthlyBreakdown(BaseModel):
    """Monthly breakdown summary."""

    month: str = Field(..., description="Month (YYYY-MM)")
    total_cost: float = Field(..., description="Total cost for this month")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class ServiceTrend(BaseModel):
    """Service trend summary."""

    service_name: str = Field(..., description="Service name")
    total_cost: float = Field(..., description="Total cost across all months")
    months_active: int = Field(..., description="Number of months with activity")
    avg_monthly_cost: float = Field(..., description="Average monthly cost")
    growth_rate_percentage: float = Field(
        ..., description="Month-over-month growth rate percentage"
    )
    cost_percentage: float = Field(..., description="Percentage of total cost")


class ServiceCostTrendSummary(BaseModel):
    """Summary statistics for service cost trend analysis."""

    total_cost: float = Field(..., description="Total cost across all months")
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_months: int = Field(..., description="Number of unique months")
    unique_services: int = Field(..., description="Number of unique services")
    unique_providers: int = Field(..., description="Number of unique providers")
    avg_monthly_cost: float = Field(..., description="Average monthly cost")
    cost_growth_rate: float = Field(
        ..., description="Overall cost growth rate percentage"
    )
    monthly_breakdown: list[MonthlyBreakdown] = Field(
        ..., description="Breakdown by month"
    )
    service_trends: list[ServiceTrend] = Field(
        ..., description="Service trend analysis"
    )


class ServiceCostTrendFilters(BaseModel):
    """Applied filters for service cost trend analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    service_name: str | None = Field(None, description="Service name filter")


class ServiceCostTrendResponse(BaseModel):
    """Response for service cost trend analysis."""

    status: str = Field(..., description="Response status")
    data: list[ServiceCostTrendData] | None = Field(
        None, description="Service cost trend data"
    )
    summary: ServiceCostTrendSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: ServiceCostTrendFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ApplicationCostTrendData(BaseModel):
    """Single application cost trend data point."""

    billing_month: int = Field(..., description="Billing month (1-12)")
    billing_year: int = Field(..., description="Billing year")
    month_name: str = Field(..., description="Month name (YYYY-MM)")
    service_name: str = Field(..., description="Service name")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_effective_cost: float = Field(..., description="Average effective cost")


class ApplicationMonthlyBreakdown(BaseModel):
    """Monthly breakdown for application."""

    month: str = Field(..., description="Month (YYYY-MM)")
    total_cost: float = Field(..., description="Total cost for this month")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class ApplicationServiceTrend(BaseModel):
    """Service trend for application."""

    service_name: str = Field(..., description="Service name")
    total_cost: float = Field(..., description="Total cost across all months")
    months_active: int = Field(..., description="Number of months with activity")
    avg_monthly_cost: float = Field(..., description="Average monthly cost")
    growth_rate_percentage: float = Field(
        ..., description="Month-over-month growth rate percentage"
    )
    cost_percentage: float = Field(
        ..., description="Percentage of total application cost"
    )


class ApplicationCostTrendSummary(BaseModel):
    """Summary statistics for application cost trend analysis."""

    total_application_cost: float = Field(
        ..., description="Total application cost across all months"
    )
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_months: int = Field(..., description="Number of unique months")
    unique_services: int = Field(..., description="Number of unique services")
    avg_monthly_cost: float = Field(..., description="Average monthly cost")
    cost_growth_rate: float = Field(
        ..., description="Overall cost growth rate percentage"
    )
    monthly_breakdown: list[ApplicationMonthlyBreakdown] = Field(
        ..., description="Breakdown by month"
    )
    service_trends: list[ApplicationServiceTrend] = Field(
        ..., description="Service trend analysis"
    )


class ApplicationCostTrendFilters(BaseModel):
    """Applied filters for application cost trend analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    application_tag: str = Field(..., description="Application tag filter")
    service_name: str | None = Field(None, description="Service name filter")


class ApplicationCostTrendResponse(BaseModel):
    """Response for application cost trend report."""

    status: str = Field(..., description="Response status")
    data: list[ApplicationCostTrendData] | None = Field(
        None, description="Application cost trend data"
    )
    summary: ApplicationCostTrendSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: ApplicationCostTrendFilters | None = Field(
        None, description="Applied filters"
    )
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
