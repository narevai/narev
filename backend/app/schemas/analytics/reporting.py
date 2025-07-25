"""
Reporting schemas
"""

from pydantic import BaseModel, Field

from .base import UseCaseMetadata


class TagCoverageOverall(BaseModel):
    """Overall tag coverage statistics."""

    cost_coverage_percentage: float = Field(
        ..., description="Percentage of cost that is tagged"
    )
    resource_coverage_percentage: float = Field(
        ..., description="Percentage of resources that are tagged"
    )
    total_tagged_cost: float = Field(..., description="Total cost of tagged resources")
    total_cost: float = Field(..., description="Total cost of all resources")
    total_tagged_resources: int = Field(..., description="Number of tagged resources")
    total_resources: int = Field(..., description="Total number of resources")


class TagCoverageByProvider(BaseModel):
    """Tag coverage statistics by provider."""

    provider_name: str = Field(..., description="Provider name")
    tagged_cost: float = Field(..., description="Tagged cost for this provider")
    total_cost: float = Field(..., description="Total cost for this provider")
    tagged_resources: int = Field(..., description="Tagged resources for this provider")
    total_resources: int = Field(..., description="Total resources for this provider")
    cost_coverage_percentage: float = Field(
        ..., description="Cost coverage percentage for this provider"
    )
    resource_coverage_percentage: float = Field(
        ..., description="Resource coverage percentage for this provider"
    )


class SpecificTagAnalysis(BaseModel):
    """Analysis for specific required tags."""

    tag_name: str = Field(..., description="Tag name")
    tagged_cost: float = Field(..., description="Cost of resources with this tag")
    tagged_resources: int = Field(..., description="Number of resources with this tag")
    cost_coverage_percentage: float = Field(
        ..., description="Percentage of total cost covered by this tag"
    )
    resource_coverage_percentage: float = Field(
        ..., description="Percentage of total resources covered by this tag"
    )


class TagCoverageData(BaseModel):
    """Tag coverage analysis data."""

    overall_coverage: TagCoverageOverall = Field(
        ..., description="Overall coverage statistics"
    )
    coverage_by_provider: list[TagCoverageByProvider] = Field(
        ..., description="Coverage by provider"
    )
    specific_tag_analysis: list[SpecificTagAnalysis] = Field(
        ..., description="Analysis of specific tags"
    )


class TagCoverageSummary(BaseModel):
    """Summary statistics for tag coverage analysis."""

    overall_cost_coverage: float = Field(
        ..., description="Overall cost coverage percentage"
    )
    overall_resource_coverage: float = Field(
        ..., description="Overall resource coverage percentage"
    )
    total_providers: int = Field(..., description="Number of providers analyzed")
    tags_analyzed: int = Field(..., description="Number of specific tags analyzed")
    untagged_cost: float = Field(..., description="Total untagged cost")
    untagged_resources: int = Field(..., description="Number of untagged resources")


class TagCoverageFilters(BaseModel):
    """Applied filters for tag coverage analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    required_tags: list[str] = Field(..., description="Required tags to analyze")


class TagCoverageResponse(BaseModel):
    """Response for tag coverage analysis."""

    status: str = Field(..., description="Response status")
    data: TagCoverageData | None = Field(None, description="Tag coverage data")
    summary: TagCoverageSummary | None = Field(None, description="Summary statistics")
    filters: TagCoverageFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class SKUMeteredCostsData(BaseModel):
    """Single SKU metered costs data point."""

    provider_name: str = Field(..., description="Provider name")
    charge_period_start: str = Field(..., description="Charge period start")
    charge_period_end: str = Field(..., description="Charge period end")
    sku_id: str = Field(..., description="SKU ID")
    sku_price_id: str | None = Field(None, description="SKU price ID")
    pricing_unit: str | None = Field(None, description="Pricing unit")
    list_unit_price: float = Field(..., description="List unit price")
    total_pricing_quantity: float = Field(..., description="Total pricing quantity")
    total_list_cost: float = Field(..., description="Total list cost")
    total_effective_cost: float = Field(..., description="Total effective cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_effective_cost: float = Field(..., description="Average effective cost")
    cost_per_unit: float = Field(..., description="Cost per unit")


class PricingUnitBreakdown(BaseModel):
    """Pricing unit breakdown."""

    pricing_unit: str = Field(..., description="Pricing unit")
    total_cost: float = Field(..., description="Total cost for this unit")
    total_quantity: float = Field(..., description="Total quantity for this unit")
    charge_count: int = Field(..., description="Number of charges for this unit")
    unique_skus: int = Field(..., description="Number of unique SKUs for this unit")
    avg_cost_per_unit: float = Field(..., description="Average cost per unit")


class SKUMeteredCostsSummary(BaseModel):
    """Summary statistics for SKU metered costs analysis."""

    total_skus: int = Field(..., description="Total number of unique SKUs")
    total_cost: float = Field(..., description="Total cost across all SKUs")
    total_quantity: float = Field(..., description="Total quantity across all SKUs")
    unique_pricing_units: int = Field(..., description="Number of unique pricing units")
    date_range_days: int = Field(
        ..., description="Number of days in the analysis period"
    )
    pricing_unit_breakdown: list[PricingUnitBreakdown] = Field(
        ..., description="Breakdown by pricing unit"
    )


class SKUMeteredCostsFilters(BaseModel):
    """Applied filters for SKU metered costs analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    sku_id: str | None = Field(None, description="SKU ID filter")
    provider_name: str | None = Field(None, description="Provider name filter")
    limit: int = Field(..., description="Result limit")


class SKUMeteredCostsResponse(BaseModel):
    """Response for SKU metered costs analysis."""

    status: str = Field(..., description="Response status")
    data: list[SKUMeteredCostsData] | None = Field(
        None, description="SKU metered costs data"
    )
    summary: SKUMeteredCostsSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: SKUMeteredCostsFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class ServiceCategoryData(BaseModel):
    """Single service category data point."""

    provider_name: str = Field(..., description="Provider name")
    billing_currency: str | None = Field(None, description="Billing currency")
    charge_period_start: str = Field(..., description="Charge period start date")
    service_category: str = Field(..., description="Service category")
    service_subcategory: str = Field(..., description="Service subcategory")
    total_billed_cost: float = Field(..., description="Total billed cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_billed_cost: float = Field(..., description="Average billed cost")


class CategoryBreakdown(BaseModel):
    """Category breakdown summary."""

    service_category: str = Field(..., description="Service category")
    total_cost: float = Field(..., description="Total cost for this category")
    charge_count: int = Field(..., description="Number of charges for this category")
    unique_subcategories: int = Field(..., description="Number of unique subcategories")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class ServiceCategorySummary(BaseModel):
    """Summary statistics for service category analysis."""

    total_cost: float = Field(..., description="Total cost across all categories")
    total_charges: int = Field(..., description="Total number of charges")
    unique_categories: int = Field(..., description="Number of unique categories")
    unique_subcategories: int = Field(..., description="Number of unique subcategories")
    unique_providers: int = Field(..., description="Number of unique providers")
    category_breakdown: list[CategoryBreakdown] = Field(
        ..., description="Breakdown by category"
    )


class ServiceCategoryFilters(BaseModel):
    """Applied filters for service category analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    service_category: str | None = Field(None, description="Service category filter")


class ServiceCategoryBreakdownResponse(BaseModel):
    """Response for service category breakdown."""

    status: str = Field(..., description="Response status")
    data: list[ServiceCategoryData] | None = Field(
        None, description="Service category data"
    )
    summary: ServiceCategorySummary | None = Field(
        None, description="Summary statistics"
    )
    filters: ServiceCategoryFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class RefundData(BaseModel):
    """Single refund data point."""

    provider_name: str = Field(..., description="Provider name")
    billing_account_id: str = Field(..., description="Billing account ID")
    service_category: str = Field(..., description="Service category")
    sub_account_id: str = Field(..., description="Sub account ID")
    sub_account_name: str = Field(..., description="Sub account name")
    total_billed_cost: float = Field(..., description="Total refund amount")
    refund_count: int = Field(..., description="Number of refunds")
    earliest_refund: str | None = Field(None, description="Earliest refund date")
    latest_refund: str | None = Field(None, description="Latest refund date")
    avg_refund_amount: float = Field(..., description="Average refund amount")


class SubaccountBreakdown(BaseModel):
    """Subaccount breakdown summary."""

    sub_account_id: str = Field(..., description="Sub account ID")
    sub_account_name: str = Field(..., description="Sub account name")
    total_refund_amount: float = Field(..., description="Total refund amount")
    refund_count: int = Field(..., description="Number of refunds")
    unique_service_categories: int = Field(
        ..., description="Number of unique service categories"
    )
    unique_providers: int = Field(..., description="Number of unique providers")
    refund_percentage: float = Field(..., description="Percentage of total refunds")


class RefundsSummary(BaseModel):
    """Summary statistics for refunds analysis."""

    total_refund_amount: float = Field(..., description="Total refund amount")
    total_refund_count: int = Field(..., description="Total number of refunds")
    unique_subaccounts: int = Field(..., description="Number of unique subaccounts")
    unique_service_categories: int = Field(
        ..., description="Number of unique service categories"
    )
    unique_providers: int = Field(..., description="Number of unique providers")
    avg_refund_per_subaccount: float = Field(
        ..., description="Average refund per subaccount"
    )
    subaccount_breakdown: list[SubaccountBreakdown] = Field(
        ..., description="Breakdown by subaccount"
    )


class RefundsFilters(BaseModel):
    """Applied filters for refunds analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str | None = Field(None, description="Provider name filter")
    billing_account_id: str | None = Field(
        None, description="Billing account ID filter"
    )
    service_category: str | None = Field(None, description="Service category filter")


class RefundsBySubaccountResponse(BaseModel):
    """Response for refunds by subaccount report."""

    status: str = Field(..., description="Response status")
    data: list[RefundData] | None = Field(None, description="Refund data")
    summary: RefundsSummary | None = Field(None, description="Summary statistics")
    filters: RefundsFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class RecurringChargeData(BaseModel):
    """Single recurring charge data point."""

    billing_period_start: str = Field(..., description="Billing period start")
    commitment_discount_id: str = Field(..., description="Commitment discount ID")
    commitment_discount_name: str = Field(..., description="Commitment discount name")
    commitment_discount_type: str = Field(..., description="Commitment discount type")
    charge_frequency: str = Field(..., description="Charge frequency")
    total_billed_cost: float = Field(..., description="Total billed cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_charge_amount: float = Field(..., description="Average charge amount")
    min_effective_cost: float = Field(..., description="Minimum effective cost")
    max_effective_cost: float = Field(..., description="Maximum effective cost")


class CommitmentTypeBreakdown(BaseModel):
    """Commitment type breakdown summary."""

    commitment_discount_type: str = Field(..., description="Commitment discount type")
    total_cost: float = Field(..., description="Total cost for this type")
    charge_count: int = Field(..., description="Number of charges")
    unique_commitments: int = Field(..., description="Number of unique commitments")
    billing_periods: int = Field(..., description="Number of billing periods")
    avg_cost_per_period: float = Field(..., description="Average cost per period")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class RecurringChargesSummary(BaseModel):
    """Summary statistics for recurring charges analysis."""

    total_recurring_cost: float = Field(..., description="Total recurring cost")
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_commitments: int = Field(..., description="Number of unique commitments")
    unique_commitment_types: int = Field(
        ..., description="Number of unique commitment types"
    )
    billing_periods: int = Field(..., description="Number of billing periods")
    avg_cost_per_period: float = Field(..., description="Average cost per period")
    commitment_type_breakdown: list[CommitmentTypeBreakdown] = Field(
        ..., description="Breakdown by commitment type"
    )


class RecurringChargesFilters(BaseModel):
    """Applied filters for recurring charges analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    commitment_discount_type: str | None = Field(
        None, description="Commitment discount type filter"
    )
    charge_frequency: str = Field(..., description="Charge frequency filter")


class RecurringCommitmentChargesResponse(BaseModel):
    """Response for recurring commitment charges report."""

    status: str = Field(..., description="Response status")
    data: list[RecurringChargeData] | None = Field(
        None, description="Recurring charge data"
    )
    summary: RecurringChargesSummary | None = Field(
        None, description="Summary statistics"
    )
    filters: RecurringChargesFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")


class SpendingData(BaseModel):
    """Single spending data point."""

    provider_name: str = Field(..., description="Provider name")
    billing_account_name: str = Field(..., description="Billing account name")
    billing_account_id: str = Field(..., description="Billing account ID")
    billing_currency: str = Field(..., description="Billing currency")
    billing_period_start: str = Field(..., description="Billing period start")
    service_category: str = Field(..., description="Service category")
    service_name: str = Field(..., description="Service name")
    total_billed_cost: float = Field(..., description="Total billed cost")
    charge_count: int = Field(..., description="Number of charges")
    avg_billed_cost: float = Field(..., description="Average billed cost")
    min_billed_cost: float = Field(..., description="Minimum billed cost")
    max_billed_cost: float = Field(..., description="Maximum billed cost")


class SpendingPeriodBreakdown(BaseModel):
    """Spending period breakdown summary."""

    billing_period: str = Field(..., description="Billing period")
    total_cost: float = Field(..., description="Total cost for this period")
    charge_count: int = Field(..., description="Number of charges")
    unique_service_categories: int = Field(
        ..., description="Number of unique service categories"
    )
    unique_billing_accounts: int = Field(
        ..., description="Number of unique billing accounts"
    )
    cost_percentage: float = Field(..., description="Percentage of total cost")


class SpendingCategoryBreakdown(BaseModel):
    """Spending service category breakdown summary."""

    service_category: str = Field(..., description="Service category")
    total_cost: float = Field(..., description="Total cost for this category")
    charge_count: int = Field(..., description="Number of charges")
    billing_periods: int = Field(..., description="Number of billing periods")
    unique_services: int = Field(..., description="Number of unique services")
    cost_percentage: float = Field(..., description="Percentage of total cost")


class SpendingSummary(BaseModel):
    """Summary statistics for spending analysis."""

    total_spending: float = Field(..., description="Total spending")
    total_charge_count: int = Field(..., description="Total number of charges")
    unique_billing_periods: int = Field(
        ..., description="Number of unique billing periods"
    )
    unique_service_categories: int = Field(
        ..., description="Number of unique service categories"
    )
    unique_billing_accounts: int = Field(
        ..., description="Number of unique billing accounts"
    )
    avg_spending_per_period: float = Field(
        ..., description="Average spending per period"
    )
    period_breakdown: list[SpendingPeriodBreakdown] = Field(
        ..., description="Breakdown by period"
    )
    service_category_breakdown: list[SpendingCategoryBreakdown] = Field(
        ..., description="Breakdown by service category"
    )


class SpendingFilters(BaseModel):
    """Applied filters for spending analysis."""

    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    provider_name: str = Field(..., description="Provider name filter")
    service_category: str | None = Field(None, description="Service category filter")
    billing_account_id: str | None = Field(
        None, description="Billing account ID filter"
    )


class SpendingByBillingPeriodResponse(BaseModel):
    """Response for spending by billing period report."""

    status: str = Field(..., description="Response status")
    data: list[SpendingData] | None = Field(None, description="Spending data")
    summary: SpendingSummary | None = Field(None, description="Summary statistics")
    filters: SpendingFilters | None = Field(None, description="Applied filters")
    message: str | None = Field(None, description="Error message if status is error")
    metadata: UseCaseMetadata | None = Field(None, description="Use case metadata")
