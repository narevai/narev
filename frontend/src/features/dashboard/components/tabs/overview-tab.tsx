import { useState } from 'react'
import { OverviewKpiTiles } from '@/features/dashboard/components/tiles/overview-kpi-tiles'
import { ServiceCategoryBreakdownTile } from '@/features/dashboard/components/tiles/service-category-breakdown-tile'
import { ServiceCostAnalysisTile } from '@/features/dashboard/components/tiles/service-cost-analysis-tile'
import { ServiceCostTrendsTile } from '@/features/dashboard/components/tiles/service-cost-trends-tile'
import { ServiceCostsByRegionTile } from '@/features/dashboard/components/tiles/service-costs-by-region-tile'
import { SpendingByBillingPeriodTile } from '@/features/dashboard/components/tiles/spending-by-billing-period-tile'
import { SpendingByProviderTrendsTile } from '@/features/dashboard/components/tiles/spending-by-provider-trends-tile'
import { OverviewFilters } from './overview-filters'
import {
  OverviewFilters as OverviewFiltersType,
  TabComponentProps,
} from './types'

const defaultFilters: OverviewFiltersType = {
  dateRange: {
    start_date: new Date('2024-07-20T00:00:00.000Z').toISOString(),
    end_date: new Date('2025-07-20T00:00:00.000Z').toISOString(),
  },
  providers: [],
  services: [],
}

export function OverviewTab({ className }: TabComponentProps) {
  {
    /* Cost Overview & Reporting Dashboard
  
  Service Category Breakdown - DONE
  Spending by Billing Period - Done
  Service Cost Trends - Done
  Application Cost Trends
  Service Costs by Region
  Service Costs by Subaccount */
  }
  const [filters, setFilters] = useState<OverviewFiltersType>(defaultFilters)

  return (
    <div className={`space-y-4 ${className || ''}`}>
      <OverviewFilters filters={filters} onFiltersChange={setFilters} />
      <OverviewKpiTiles filters={filters} />
      <div className='grid grid-cols-1 gap-4 lg:grid-cols-2'>
        <ServiceCategoryBreakdownTile filters={filters} />
        <ServiceCostTrendsTile filters={filters} />
        <SpendingByProviderTrendsTile filters={filters} />
        <ServiceCostsByRegionTile filters={filters} />
        <SpendingByBillingPeriodTile filters={filters} />
        <ServiceCostAnalysisTile filters={filters} />
      </div>
    </div>
  )
}
