import type { paths } from '@/types/api'
import createClient from 'openapi-fetch'

// Use VITE_API_URL if set (for dev/Docker), otherwise default to same-origin (for production)
const apiBaseUrl = import.meta.env.VITE_API_URL || ''

export const api = createClient<paths>({
  baseUrl: apiBaseUrl,
})

// /providers endpoints
type ProviderTypesResponse =
  paths['/api/v1/providers/types/info']['get']['responses']['200']['content']['application/json']

type CreateProviderRequest =
  paths['/api/v1/providers']['post']['requestBody']['content']['application/json']

type UpdateProviderRequest =
  paths['/api/v1/providers/{provider_id}']['put']['requestBody']['content']['application/json']

type DeleteProviderResponse =
  paths['/api/v1/providers/{provider_id}']['delete']['responses']['200']['content']['application/json']

type AuthFieldsResponse =
  paths['/api/v1/providers/types/{provider_type}/auth-fields']['get']['responses']['200']['content']['application/json']

type ListProvidersResponse =
  paths['/api/v1/providers']['get']['responses']['200']['content']['application/json']

type GetProviderResponse =
  paths['/api/v1/providers/{provider_id}']['get']['responses']['200']['content']['application/json']

type TestProviderResponse =
  paths['/api/v1/providers/{provider_id}/test']['post']['responses']['200']['content']['application/json']

type HealthCheckResponse =
  paths['/api/v1/providers/health']['get']['responses']['200']['content']['application/json']

type ProviderTypeInfo = ProviderTypesResponse['providers'][0]

type ProviderInstance = ListProvidersResponse[0]

interface Provider extends ProviderTypeInfo {
  // Basic display info
  name: string
  logo: React.ReactNode
  connected: boolean
  desc: string
}

type AuthMethod = ProviderTypeInfo['supported_auth_methods'][0]
type AuthField = {
  required: boolean
  type: string
  placeholder?: string
  description?: string
  fields?: Record<string, AuthField>
}
type ConfigurationSchema = ProviderTypeInfo['configuration_schema']
type StandardField = {
  required: boolean
  type: string
  pattern?: string
  placeholder: string
  description: string
}

// syncs endpoint
type SyncTriggerRequest =
  paths['/api/v1/syncs/trigger']['post']['requestBody']['content']['application/json']

type SyncTriggerResponse =
  paths['/api/v1/syncs/trigger']['post']['responses']['200']['content']['application/json']

type SyncStatusResponse =
  paths['/api/v1/syncs/status']['get']['responses']['200']['content']['application/json']

type SyncRunsResponse =
  paths['/api/v1/syncs/runs']['get']['responses']['200']['content']['application/json']

type SyncRunDetails =
  paths['/api/v1/syncs/runs/{run_id}']['get']['responses']['200']['content']['application/json']

type SyncActionResponse =
  paths['/api/v1/syncs/runs/{run_id}/cancel']['post']['responses']['200']['content']['application/json']

type SyncStatisticsResponse =
  paths['/api/v1/syncs/stats']['get']['responses']['200']['content']['application/json']

type SyncHealthCheckResponse =
  paths['/api/v1/syncs/health']['get']['responses']['200']['content']['application/json']

type ExportBillingResponse =
  paths['/api/v1/export/billing']['get']['responses']['200']['content']['application/json']

type ExportHealthCheckResponse =
  paths['/api/v1/export/health']['get']['responses']['200']['content']['application/json']

type ExportBillingParams = {
  format?: 'csv' | 'xlsx'
  skip?: number
  limit?: number
  start_date?: string
  end_date?: string
  provider_id?: string
  service_name?: string
  service_category?:
    | 'AI and Machine Learning'
    | 'Analytics'
    | 'Compute'
    | 'Databases'
    | 'Networking'
    | 'Storage'
    | 'Security'
    | 'Other'
  charge_category?: 'Usage' | 'Purchase' | 'Tax' | 'Credit' | 'Adjustment'
  min_cost?: number
  max_cost?: number
}

type ListUseCasesResponse =
  paths['/api/v1/analytics/']['get']['responses']['200']['content']['application/json']

type ConnectedProvidersResponse =
  paths['/api/v1/analytics/providers']['get']['responses']['200']['content']['application/json']

type ResourceRateResponse =
  paths['/api/v1/analytics/resource-rate']['get']['responses']['200']['content']['application/json']

type ResourceUsageResponse =
  paths['/api/v1/analytics/resource-usage']['get']['responses']['200']['content']['application/json']

type UnitEconomicsResponse =
  paths['/api/v1/analytics/unit-economics']['get']['responses']['200']['content']['application/json']

type VirtualCurrencyTargetResponse =
  paths['/api/v1/analytics/virtual-currency-target']['get']['responses']['200']['content']['application/json']

type EffectiveCostByCurrencyResponse =
  paths['/api/v1/analytics/effective-cost-by-currency']['get']['responses']['200']['content']['application/json']

type VirtualCurrencyPurchaseResponse =
  paths['/api/v1/analytics/virtual-currency-purchases']['get']['responses']['200']['content']['application/json']

type ContractedSavingsResponse =
  paths['/api/v1/analytics/contracted-savings']['get']['responses']['200']['content']['application/json']

type TagCoverageResponse =
  paths['/api/v1/analytics/tag-coverage']['get']['responses']['200']['content']['application/json']

type SKUMeteredCostsResponse =
  paths['/api/v1/analytics/sku-metered-costs']['get']['responses']['200']['content']['application/json']

type ServiceCategoryBreakdownResponse =
  paths['/api/v1/analytics/service-category-breakdown']['get']['responses']['200']['content']['application/json']

type CapacityReservationAnalysisResponse =
  paths['/api/v1/analytics/capacity-reservation-analysis']['get']['responses']['200']['content']['application/json']

type UnusedCapacityResponse =
  paths['/api/v1/analytics/unused-capacity']['get']['responses']['200']['content']['application/json']

type RefundsBySubaccountResponse =
  paths['/api/v1/analytics/refunds-by-subaccount']['get']['responses']['200']['content']['application/json']

type RecurringCommitmentChargesResponse =
  paths['/api/v1/analytics/recurring-commitment-charges']['get']['responses']['200']['content']['application/json']

type ServiceCostAnalysisResponse =
  paths['/api/v1/analytics/service-cost-analysis']['get']['responses']['200']['content']['application/json']

type SpendingByBillingPeriodResponse =
  paths['/api/v1/analytics/spending-by-billing-period']['get']['responses']['200']['content']['application/json']

type ServiceCostByRegionResponse =
  paths['/api/v1/analytics/service-costs-by-region']['get']['responses']['200']['content']['application/json']

type ServiceCostBySubaccountResponse =
  paths['/api/v1/analytics/service-costs-by-subaccount']['get']['responses']['200']['content']['application/json']

type ServiceCostTrendResponse =
  paths['/api/v1/analytics/service-cost-trends']['get']['responses']['200']['content']['application/json']

type ApplicationCostTrendResponse =
  paths['/api/v1/analytics/application-cost-trends']['get']['responses']['200']['content']['application/json']

type AnalyticsHealthCheckResponse =
  paths['/api/v1/analytics/health']['get']['responses']['200']['content']['application/json']

type AnalyticsDateRangeParams = {
  start_date: string
  end_date: string
}

type AnalyticsProviderParams = AnalyticsDateRangeParams & {
  provider_name?: string
}

type AnalyticsServiceParams = AnalyticsProviderParams & {
  service_name?: string
}

type AnalyticsRegionParams = AnalyticsServiceParams & {
  region_name?: string
}

type AvailableServicesResponse =
  paths['/api/v1/analytics/services']['get']['responses']['200']['content']['application/json']

// Config endpoint
type GetConfigResponse =
  paths['/api/v1/config']['get']['responses']['200']['content']['application/json']

export const config = {
  get: () => api.GET('/api/v1/config'),
}

// Grouped by domain
export const providers = {
  // Health check
  health: () => api.GET('/api/v1/providers/health'),

  // Provider CRUD operations
  list: (params?: { include_inactive?: boolean; provider_type?: string }) =>
    api.GET('/api/v1/providers', {
      params: { query: params },
    }),

  get: (provider_id: string) =>
    api.GET('/api/v1/providers/{provider_id}', {
      params: { path: { provider_id } },
    }),

  create: (data: CreateProviderRequest) =>
    api.POST('/api/v1/providers', { body: data }),

  update: (provider_id: string, data: UpdateProviderRequest) =>
    api.PUT('/api/v1/providers/{provider_id}', {
      params: { path: { provider_id } },
      body: data,
    }),

  delete: (provider_id: string) =>
    api.DELETE('/api/v1/providers/{provider_id}', {
      params: { path: { provider_id } },
    }),

  // Provider testing
  test: (provider_id: string) =>
    api.POST('/api/v1/providers/{provider_id}/test', {
      params: { path: { provider_id } },
    }),

  // Provider types and auth fields
  getTypes: () => api.GET('/api/v1/providers/types/info'),

  getAuthFields: (providerType: string, authMethod?: string) =>
    api.GET('/api/v1/providers/types/{provider_type}/auth-fields', {
      params: {
        path: { provider_type: providerType },
        query: authMethod ? { auth_method: authMethod } : undefined,
      },
    }),
}

export const syncs = {
  // Health check
  health: () => api.GET('/api/v1/syncs/health'),

  // Sync operations
  trigger: (data: SyncTriggerRequest) =>
    api.POST('/api/v1/syncs/trigger', { body: data }),

  getStatus: (params?: { provider_id?: string; limit?: number }) =>
    api.GET('/api/v1/syncs/status', {
      params: { query: params },
    }),

  // Sync runs
  getRuns: (params?: {
    skip?: number
    limit?: number
    provider_id?: string
    status?: string
    start_date?: string
    end_date?: string
  }) =>
    api.GET('/api/v1/syncs/runs', {
      params: { query: params },
    }),

  getRun: (run_id: string) =>
    api.GET('/api/v1/syncs/runs/{run_id}', {
      params: { path: { run_id } },
    }),

  cancelRun: (run_id: string) =>
    api.POST('/api/v1/syncs/runs/{run_id}/cancel', {
      params: { path: { run_id } },
    }),

  retryRun: (run_id: string) =>
    api.POST('/api/v1/syncs/runs/{run_id}/retry', {
      params: { path: { run_id } },
    }),

  // Statistics and pipeline
  getStats: (params?: { provider_id?: string; days?: number }) =>
    api.GET('/api/v1/syncs/stats', {
      params: { query: params },
    }),

  getPipelineGraph: (params?: { format?: string }) =>
    api.GET('/api/v1/syncs/pipeline/graph', {
      params: { query: params },
    }),
}
export const exportApi = {
  // Export billing data
  billing: async (params?: ExportBillingParams) => {
    try {
      const queryParams = new URLSearchParams()
      if (params?.format) queryParams.append('format', params.format)

      const response = await fetch(
        `http://localhost:8000/api/v1/export/billing?${queryParams}`,
        {
          method: 'GET',
        }
      )

      if (!response.ok) {
        return { data: null, error: `Export failed: ${response.status}` }
      }

      const blob = await response.blob()

      const contentDisposition = response.headers.get('content-disposition')
      let filename = null
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=([^;]+)/)
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '')
        }
      }

      return {
        data: blob,
        error: null,
        filename,
      }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Export failed',
      }
    }
  },

  // Export health check
  health: () => api.GET('/api/v1/export/health'),
}

export const analytics = {
  getConnectedProviders: () => api.GET('/api/v1/analytics/providers'),
  // Health check
  health: () => api.GET('/api/v1/analytics/health'),

  // Use cases
  listUseCases: (params?: { persona?: string; capability?: string }) =>
    api.GET('/api/v1/analytics/', {
      params: { query: params },
    }),

  // New endpoint: Get available services
  getAvailableServices: () => api.GET('/api/v1/analytics/services'),

  // Resource analysis
  resourceRate: (params: AnalyticsRegionParams) =>
    api.GET('/api/v1/analytics/resource-rate', {
      params: { query: params },
    }),

  resourceUsage: (params: AnalyticsRegionParams) =>
    api.GET('/api/v1/analytics/resource-usage', {
      params: { query: params },
    }),

  // Economics and pricing
  unitEconomics: (
    params: AnalyticsDateRangeParams & {
      unit_type?: string
      charge_description_filter?: string
    }
  ) =>
    api.GET('/api/v1/analytics/unit-economics', {
      params: { query: params },
    }),

  virtualCurrencyTarget: (
    params: AnalyticsDateRangeParams & {
      pricing_currency?: string
      limit?: number
    }
  ) =>
    api.GET('/api/v1/analytics/virtual-currency-target', {
      params: { query: params },
    }),

  effectiveCostByCurrency: (
    params: AnalyticsDateRangeParams & {
      include_exchange_rates?: boolean
    }
  ) =>
    api.GET('/api/v1/analytics/effective-cost-by-currency', {
      params: { query: params },
    }),

  virtualCurrencyPurchases: (
    params: AnalyticsDateRangeParams & {
      pricing_unit?: string
      group_by?: string
    }
  ) =>
    api.GET('/api/v1/analytics/virtual-currency-purchases', {
      params: { query: params },
    }),

  contractedSavings: (
    params: AnalyticsDateRangeParams & {
      commitment_type?: string
    }
  ) =>
    api.GET('/api/v1/analytics/contracted-savings', {
      params: { query: params },
    }),

  // Governance and optimization
  tagCoverage: (
    params: AnalyticsProviderParams & {
      required_tags?: string[]
    }
  ) =>
    api.GET('/api/v1/analytics/tag-coverage', {
      params: { query: params },
    }),

  skuMeteredCosts: (
    params: AnalyticsProviderParams & {
      sku_id?: string
      limit?: number
    }
  ) =>
    api.GET('/api/v1/analytics/sku-metered-costs', {
      params: { query: params },
    }),

  serviceCategoryBreakdown: (
    params: AnalyticsProviderParams & {
      service_category?: string
    }
  ) =>
    api.GET('/api/v1/analytics/service-category-breakdown', {
      params: { query: params },
    }),

  // Capacity and reservations
  capacityReservationAnalysis: (
    params: AnalyticsProviderParams & {
      billing_account_id?: string
    }
  ) =>
    api.GET('/api/v1/analytics/capacity-reservation-analysis', {
      params: { query: params },
    }),

  unusedCapacity: (
    params: AnalyticsProviderParams & {
      billing_account_id?: string
    }
  ) =>
    api.GET('/api/v1/analytics/unused-capacity', {
      params: { query: params },
    }),

  // Financial reporting
  refundsBySubaccount: (
    params: AnalyticsProviderParams & {
      billing_account_id?: string
      service_category?: string
    }
  ) =>
    api.GET('/api/v1/analytics/refunds-by-subaccount', {
      params: { query: params },
    }),

  recurringCommitmentCharges: (
    params: AnalyticsDateRangeParams & {
      commitment_discount_type?: string
      charge_frequency?: string
    }
  ) =>
    api.GET('/api/v1/analytics/recurring-commitment-charges', {
      params: { query: params },
    }),

  // Service cost analysis
  serviceCostAnalysis: (
    params: AnalyticsProviderParams & {
      service_name: string
      sub_account_id?: string
    }
  ) =>
    api.GET('/api/v1/analytics/service-cost-analysis', {
      params: { query: params },
    }),

  spendingByBillingPeriod: (
    params: AnalyticsDateRangeParams & {
      provider_name: string
      service_category?: string
      billing_account_id?: string
    }
  ) =>
    api.GET('/api/v1/analytics/spending-by-billing-period', {
      params: { query: params },
    }),

  serviceCostsByRegion: (
    params: AnalyticsServiceParams & {
      region_id?: string
    }
  ) =>
    api.GET('/api/v1/analytics/service-costs-by-region', {
      params: { query: params },
    }),

  serviceCostsBySubaccount: (
    params: AnalyticsDateRangeParams & {
      sub_account_id: string
      provider_name: string
      service_name?: string
    }
  ) =>
    api.GET('/api/v1/analytics/service-costs-by-subaccount', {
      params: { query: params },
    }),

  // Trend analysis
  serviceCostTrends: (params: AnalyticsServiceParams) =>
    api.GET('/api/v1/analytics/service-cost-trends', {
      params: { query: params },
    }),

  applicationCostTrends: (
    params: AnalyticsDateRangeParams & {
      application_tag: string
      service_name?: string
    }
  ) =>
    api.GET('/api/v1/analytics/application-cost-trends', {
      params: { query: params },
    }),
}

export type {
  ProviderTypesResponse,
  CreateProviderRequest,
  UpdateProviderRequest,
  DeleteProviderResponse,
  AuthFieldsResponse,
  ListProvidersResponse,
  GetProviderResponse,
  TestProviderResponse,
  HealthCheckResponse,
  ProviderTypeInfo,
  ProviderInstance,
  Provider,
  AuthMethod,
  AuthField,
  ConfigurationSchema,
  StandardField,
  SyncTriggerRequest,
  SyncTriggerResponse,
  SyncStatusResponse,
  SyncRunsResponse,
  SyncRunDetails,
  SyncActionResponse,
  SyncStatisticsResponse,
  SyncHealthCheckResponse,
  ExportBillingResponse,
  ExportHealthCheckResponse,
  ExportBillingParams,
  ConnectedProvidersResponse,
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
  AvailableServicesResponse,
  GetConfigResponse,
}
