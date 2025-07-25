// hooks/use-analytics.ts
import { useState } from 'react'
import { toast } from 'sonner'
import {
  analytics,
  ListUseCasesResponse,
  ResourceRateResponse,
  ResourceUsageResponse,
  UnitEconomicsResponse,
  VirtualCurrencyTargetResponse,
  EffectiveCostByCurrencyResponse,
  VirtualCurrencyPurchaseResponse,
  ContractedSavingsResponse,
  TagCoverageResponse,
  SKUMeteredCostsResponse,
  ServiceCategoryBreakdownResponse,
  CapacityReservationAnalysisResponse,
  UnusedCapacityResponse,
  RefundsBySubaccountResponse,
  RecurringCommitmentChargesResponse,
  ServiceCostAnalysisResponse,
  SpendingByBillingPeriodResponse,
  ServiceCostByRegionResponse,
  ServiceCostBySubaccountResponse,
  ServiceCostTrendResponse,
  ApplicationCostTrendResponse,
  AnalyticsHealthCheckResponse,
  AnalyticsDateRangeParams,
  AnalyticsProviderParams,
  AnalyticsServiceParams,
  AnalyticsRegionParams,
  ConnectedProvidersResponse,
  AvailableServicesResponse,
} from '@/lib/api'

export function useAnalytics() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getConnectedProviders =
    async (): Promise<ConnectedProvidersResponse | null> => {
      try {
        setLoading(true)
        setError(null)

        const { data, error } = await analytics.getConnectedProviders()
        if (error) throw new Error('Failed to get connected providers')

        return data as ConnectedProvidersResponse
      } catch (_) {
        const errorMessage = 'Failed to load connected providers'
        setError(errorMessage)
        toast.error(errorMessage, {
          description: 'Unable to load connected provider data.',
        })
        return null
      } finally {
        setLoading(false)
      }
    }

  // Health check
  const checkHealth =
    async (): Promise<AnalyticsHealthCheckResponse | null> => {
      try {
        setLoading(true)
        setError(null)

        const { data, error } = await analytics.health()
        if (error) throw new Error('Analytics health check failed')

        return data as AnalyticsHealthCheckResponse
      } catch (_) {
        const errorMessage = 'Failed to check analytics health'
        setError(errorMessage)
        toast.error(errorMessage, {
          description: 'Unable to verify analytics service status.',
        })
        return null
      } finally {
        setLoading(false)
      }
    }

  // Use cases
  const getUseCases = async (params?: {
    persona?: string
    capability?: string
  }): Promise<ListUseCasesResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.listUseCases(params)
      if (error) throw new Error('Failed to fetch use cases')

      return data as ListUseCasesResponse
    } catch (_) {
      const errorMessage = 'Failed to load analytics use cases'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load available analytics capabilities.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Resource analysis
  const getResourceRate = async (
    params: AnalyticsRegionParams
  ): Promise<ResourceRateResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.resourceRate(params)
      if (error) throw new Error('Failed to calculate resource rate')

      return data as ResourceRateResponse
    } catch (_) {
      const errorMessage = 'Failed to calculate resource rate'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to analyze resource rate data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getResourceUsage = async (
    params: AnalyticsRegionParams
  ): Promise<ResourceUsageResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.resourceUsage(params)
      if (error) throw new Error('Failed to get resource usage')

      return data as ResourceUsageResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze resource usage'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load resource usage data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Economics and pricing
  const getUnitEconomics = async (
    params: AnalyticsDateRangeParams & {
      unit_type?: string
      charge_description_filter?: string
    }
  ): Promise<UnitEconomicsResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.unitEconomics(params)
      if (error) throw new Error('Failed to calculate unit economics')

      return data as UnitEconomicsResponse
    } catch (_) {
      const errorMessage = 'Failed to calculate unit economics'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to analyze unit cost data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getVirtualCurrencyTarget = async (
    params: AnalyticsDateRangeParams & {
      pricing_currency?: string
      limit?: number
    }
  ): Promise<VirtualCurrencyTargetResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.virtualCurrencyTarget(params)
      if (error) throw new Error('Failed to analyze virtual currency target')

      return data as VirtualCurrencyTargetResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze virtual currency usage'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load virtual currency target data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getEffectiveCostByCurrency = async (
    params: AnalyticsDateRangeParams & {
      include_exchange_rates?: boolean
    }
  ): Promise<EffectiveCostByCurrencyResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.effectiveCostByCurrency(params)
      if (error) throw new Error('Failed to analyze effective cost by currency')

      return data as EffectiveCostByCurrencyResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze costs by currency'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load currency cost analysis.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getVirtualCurrencyPurchases = async (
    params: AnalyticsDateRangeParams & {
      pricing_unit?: string
      group_by?: string
    }
  ): Promise<VirtualCurrencyPurchaseResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.virtualCurrencyPurchases(params)
      if (error) throw new Error('Failed to analyze virtual currency purchases')

      return data as VirtualCurrencyPurchaseResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze virtual currency purchases'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load purchase data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getContractedSavings = async (
    params: AnalyticsDateRangeParams & {
      commitment_type?: string
    }
  ): Promise<ContractedSavingsResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.contractedSavings(params)
      if (error) throw new Error('Failed to analyze contracted savings')

      return data as ContractedSavingsResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze contracted savings'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load savings data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Governance and optimization
  const getTagCoverage = async (
    params: AnalyticsProviderParams & {
      required_tags?: string[]
    }
  ): Promise<TagCoverageResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.tagCoverage(params)
      if (error) throw new Error('Failed to analyze tag coverage')

      return data as TagCoverageResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze tag coverage'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load tag coverage data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getSkuMeteredCosts = async (
    params: AnalyticsProviderParams & {
      sku_id?: string
      limit?: number
    }
  ): Promise<SKUMeteredCostsResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.skuMeteredCosts(params)
      if (error) throw new Error('Failed to analyze SKU metered costs')

      return data as SKUMeteredCostsResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze SKU costs'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load SKU cost data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getServiceCategoryBreakdown = async (
    params: AnalyticsProviderParams & {
      service_category?: string
    }
  ): Promise<ServiceCategoryBreakdownResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.serviceCategoryBreakdown(params)
      if (error) throw new Error('Failed to get service category breakdown')

      return data as ServiceCategoryBreakdownResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze service categories'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load service category breakdown.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Capacity and reservations
  const getCapacityReservationAnalysis = async (
    params: AnalyticsProviderParams & {
      billing_account_id?: string
    }
  ): Promise<CapacityReservationAnalysisResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } =
        await analytics.capacityReservationAnalysis(params)
      if (error) throw new Error('Failed to analyze capacity reservations')

      return data as CapacityReservationAnalysisResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze capacity reservations'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load capacity reservation data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getUnusedCapacity = async (
    params: AnalyticsProviderParams & {
      billing_account_id?: string
    }
  ): Promise<UnusedCapacityResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.unusedCapacity(params)
      if (error) throw new Error('Failed to identify unused capacity')

      return data as UnusedCapacityResponse
    } catch (_) {
      const errorMessage = 'Failed to identify unused capacity'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load unused capacity data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Financial reporting
  const getRefundsBySubaccount = async (
    params: AnalyticsProviderParams & {
      billing_account_id?: string
      service_category?: string
    }
  ): Promise<RefundsBySubaccountResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.refundsBySubaccount(params)
      if (error) throw new Error('Failed to get refunds by subaccount')

      return data as RefundsBySubaccountResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze refunds by subaccount'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load refund data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getRecurringCommitmentCharges = async (
    params: AnalyticsDateRangeParams & {
      commitment_discount_type?: string
      charge_frequency?: string
    }
  ): Promise<RecurringCommitmentChargesResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.recurringCommitmentCharges(params)
      if (error) throw new Error('Failed to get recurring commitment charges')

      return data as RecurringCommitmentChargesResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze recurring charges'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load recurring commitment data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Service cost analysis
  const getServiceCostAnalysis = async (
    params: AnalyticsProviderParams & {
      service_name: string
      sub_account_id?: string
    }
  ): Promise<ServiceCostAnalysisResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.serviceCostAnalysis(params)
      if (error) throw new Error('Failed to analyze service costs')

      return data as ServiceCostAnalysisResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze service costs'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load service cost analysis.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getSpendingByBillingPeriod = async (
    params: AnalyticsDateRangeParams & {
      provider_name: string
      service_category?: string
      billing_account_id?: string
    }
  ): Promise<SpendingByBillingPeriodResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.spendingByBillingPeriod(params)
      if (error) throw new Error('Failed to get spending by billing period')

      return data as SpendingByBillingPeriodResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze spending by billing period'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load billing period data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getServiceCostsByRegion = async (
    params: AnalyticsServiceParams & {
      region_id?: string
    }
  ): Promise<ServiceCostByRegionResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.serviceCostsByRegion(params)
      if (error) throw new Error('Failed to analyze service costs by region')

      return data as ServiceCostByRegionResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze costs by region'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load regional cost data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getServiceCostsBySubaccount = async (
    params: AnalyticsDateRangeParams & {
      sub_account_id: string
      provider_name: string
      service_name?: string
    }
  ): Promise<ServiceCostBySubaccountResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.serviceCostsBySubaccount(params)
      if (error) throw new Error('Failed to get service costs by subaccount')

      return data as ServiceCostBySubaccountResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze costs by subaccount'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load subaccount cost data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Trend analysis
  const getServiceCostTrends = async (
    params: AnalyticsServiceParams
  ): Promise<ServiceCostTrendResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.serviceCostTrends(params)
      if (error) throw new Error('Failed to analyze service cost trends')

      return data as ServiceCostTrendResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze service cost trends'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load cost trend data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  const getApplicationCostTrends = async (
    params: AnalyticsDateRangeParams & {
      application_tag: string
      service_name?: string
    }
  ): Promise<ApplicationCostTrendResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await analytics.applicationCostTrends(params)
      if (error) throw new Error('Failed to get application cost trends')

      return data as ApplicationCostTrendResponse
    } catch (_) {
      const errorMessage = 'Failed to analyze application cost trends'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load application trend data.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  // Get available services
  const getAvailableServices =
    async (): Promise<AvailableServicesResponse | null> => {
      try {
        setLoading(true)
        setError(null)

        const { data, error } = await analytics.getAvailableServices()
        if (error) throw new Error('Failed to fetch available services')

        return data as AvailableServicesResponse
      } catch (_) {
        const errorMessage = 'Failed to load available services'
        setError(errorMessage)
        toast.error(errorMessage, {
          description: 'Unable to load available services.',
        })
        return null
      } finally {
        setLoading(false)
      }
    }

  return {
    // State
    loading,
    error,

    //Providers
    getConnectedProviders,

    // Health
    checkHealth,

    // Use cases
    getUseCases,

    // Resource analysis
    getResourceRate,
    getResourceUsage,

    // Economics and pricing
    getUnitEconomics,
    getVirtualCurrencyTarget,
    getEffectiveCostByCurrency,
    getVirtualCurrencyPurchases,
    getContractedSavings,

    // Governance and optimization
    getTagCoverage,
    getSkuMeteredCosts,
    getServiceCategoryBreakdown,

    // Capacity and reservations
    getCapacityReservationAnalysis,
    getUnusedCapacity,

    // Financial reporting
    getRefundsBySubaccount,
    getRecurringCommitmentCharges,

    // Service cost analysis
    getServiceCostAnalysis,
    getSpendingByBillingPeriod,
    getServiceCostsByRegion,
    getServiceCostsBySubaccount,

    // Trend analysis
    getServiceCostTrends,
    getApplicationCostTrends,

    // Services
    getAvailableServices,
  }
}
