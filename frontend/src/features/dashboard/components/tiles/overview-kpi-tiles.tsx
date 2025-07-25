import { useEffect, useState } from 'react'
import { DollarSign, Layers } from 'lucide-react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { useAnalytics } from '@/hooks/use-analytics'
import { GenericKpiTile } from '@/features/dashboard/components/charts'

interface OverviewKpiTilesProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
  }
}

type TrendData = {
  service_name: string
  provider_name?: string
  total_effective_cost: number
}

type CatData = {
  service_category: string
  total_effective_cost?: number
  total_billed_cost?: number
  provider_name?: string
}

function getPreviousPeriod(dateRange: {
  start_date: string
  end_date: string
}) {
  const start = new Date(dateRange.start_date)
  const end = new Date(dateRange.end_date)
  const diffMs = end.getTime() - start.getTime()
  const prevEnd = new Date(start.getTime() - 1)
  const prevStart = new Date(start.getTime() - diffMs - 1)
  return {
    start_date: prevStart.toISOString(),
    end_date: prevEnd.toISOString(),
  }
}

export function OverviewKpiTiles({ filters }: OverviewKpiTilesProps) {
  const { getServiceCostTrends, getServiceCategoryBreakdown } = useAnalytics()
  const [totalServiceCost, setTotalServiceCost] = useState(0)
  const [totalServiceCostLoading, setTotalServiceCostLoading] = useState(false)
  const [topService, setTopService] = useState<string | null>(null)
  const [topServiceLoading, setTopServiceLoading] = useState(false)
  const [periodChange, setPeriodChange] = useState<number | null>(null)
  const [periodChangeLoading, setPeriodChangeLoading] = useState(false)
  const [topCategory, setTopCategory] = useState<{
    name: string
    cost: number
  } | null>(null)
  const [topCategoryLoading, setTopCategoryLoading] = useState(false)
  const [activeProviders, setActiveProviders] = useState<number>(0)
  const [activeProvidersLoading, setActiveProvidersLoading] = useState(false)

  // 1. Total Service Cost & Top Service
  useEffect(
    () => {
      const fetchTrends = async () => {
        setTotalServiceCostLoading(true)
        setTopServiceLoading(true)
        const params = {
          start_date: filters.dateRange.start_date,
          end_date: filters.dateRange.end_date,
        }
        const response = await getServiceCostTrends(params)
        const data: TrendData[] =
          response && Array.isArray(response.data) ? response.data : []
        // Filter by selected providers if any are selected
        let filtered = data
        if (filters.providers && filters.providers.length > 0) {
          filtered = data.filter(
            (d) =>
              !d.provider_name || filters.providers.includes(d.provider_name)
          )
        }
        // Total cost
        setTotalServiceCost(
          filtered.reduce((sum, d) => sum + (d.total_effective_cost || 0), 0)
        )
        // Top service
        const serviceTotals: Record<string, number> = {}
        filtered.forEach((d) => {
          serviceTotals[d.service_name] =
            (serviceTotals[d.service_name] || 0) + (d.total_effective_cost || 0)
        })
        const top = Object.entries(serviceTotals).sort((a, b) => b[1] - a[1])[0]
        setTopService(top ? top[0] : null)
        setTotalServiceCostLoading(false)
        setTopServiceLoading(false)
      }
      fetchTrends()
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      filters.dateRange.start_date,
      filters.dateRange.end_date,
      filters.providers,
    ]
  )

  // 2. Period-over-Period Cost Change
  useEffect(() => {
    const fetchPeriodChange = async () => {
      setPeriodChangeLoading(true)
      // Current period
      const params = {
        start_date: filters.dateRange.start_date,
        end_date: filters.dateRange.end_date,
      }
      // Previous period
      const prevPeriod = getPreviousPeriod(filters.dateRange)
      const prevParams = {
        start_date: prevPeriod.start_date,
        end_date: prevPeriod.end_date,
      }
      // Fetch both periods
      const [currResp, prevResp] = await Promise.all([
        getServiceCostTrends(params),
        getServiceCostTrends(prevParams),
      ])
      const currArr: TrendData[] =
        currResp && Array.isArray(currResp.data) ? currResp.data : []
      const prevArr: TrendData[] =
        prevResp && Array.isArray(prevResp.data) ? prevResp.data : []
      const currTotal = currArr.reduce(
        (acc, d) => acc + (d.total_effective_cost || 0),
        0
      )
      const prevTotal = prevArr.reduce(
        (acc, d) => acc + (d.total_effective_cost || 0),
        0
      )
      if (prevTotal === 0) {
        setPeriodChange(null)
      } else {
        setPeriodChange(((currTotal - prevTotal) / prevTotal) * 100)
      }
      setPeriodChangeLoading(false)
    }
    fetchPeriodChange()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.dateRange.start_date,
    filters.dateRange.end_date,
    filters.providers,
  ])

  // 3. Top Service Category Spending
  useEffect(() => {
    const fetchTopCategory = async () => {
      setTopCategoryLoading(true)
      const params = {
        start_date: filters.dateRange.start_date,
        end_date: filters.dateRange.end_date,
      }
      const response = await getServiceCategoryBreakdown(params)
      const data: CatData[] =
        response && Array.isArray(response.data) ? response.data : []
      // Filter by selected providers (must match chart logic)
      let filtered = data
      if (filters.providers && filters.providers.length > 0) {
        filtered = data.filter(
          (d) => d.provider_name && filters.providers.includes(d.provider_name)
        )
      }
      // Aggregate by category using total_billed_cost only
      const categoryTotals: { [key: string]: number } = {}
      filtered.forEach((item) => {
        const category = item.service_category || 'Unknown'
        categoryTotals[category] =
          (categoryTotals[category] || 0) + (item.total_billed_cost || 0)
      })
      // Find top category
      const categories = Object.entries(categoryTotals)
        .map(([name, cost]) => ({ name, cost }))
        .sort((a, b) => b.cost - a.cost)
      const top = categories[0]
      setTopCategory(top ? { name: top.name, cost: top.cost } : null)
      setTopCategoryLoading(false)
    }
    fetchTopCategory()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.dateRange.start_date,
    filters.dateRange.end_date,
    filters.providers,
  ])

  // 5. Number of Active Providers
  useEffect(() => {
    const fetchActiveProviders = async () => {
      setActiveProvidersLoading(true)
      const params = {
        start_date: filters.dateRange.start_date,
        end_date: filters.dateRange.end_date,
      }
      const response = await getServiceCostTrends(params)
      const data: TrendData[] =
        response && Array.isArray(response.data) ? response.data : []
      // Filter by selected providers
      let filtered = data
      if (filters.providers && filters.providers.length > 0) {
        filtered = data.filter(
          (d) => !d.provider_name || filters.providers.includes(d.provider_name)
        )
      }
      // Count unique providers with total_effective_cost > 0
      const providerSet = new Set(
        filtered
          .filter((d) => (d.total_effective_cost || 0) > 0 && d.provider_name)
          .map((d) => d.provider_name)
      )
      setActiveProviders(providerSet.size)
      setActiveProvidersLoading(false)
    }
    fetchActiveProviders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.dateRange.start_date,
    filters.dateRange.end_date,
    filters.providers,
  ])

  return (
    <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
      {/* 2. Total Service Cost */}
      <GenericKpiTile
        title='Total Service Cost'
        value={totalServiceCost}
        subtitle={undefined}
        // We'll render the colored subtitle as a child below
        change={undefined}
        changeValue={periodChange || 0}
        icon={DollarSign}
        valueFormatter={(val) =>
          `$${Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        }
        loading={totalServiceCostLoading || periodChangeLoading}
      >
        {periodChangeLoading ? (
          <span className='text-muted-foreground mt-1 block text-sm'>
            Period-over-Period: ...
          </span>
        ) : periodChange === null ? (
          <span className='text-muted-foreground mt-1 block text-sm'>
            Period-over-Period: N/A
          </span>
        ) : (
          <span
            className={
              (periodChange > 0
                ? 'text-destructive'
                : periodChange < 0
                  ? 'text-green-500'
                  : 'text-muted-foreground') + ' mt-1 flex items-center text-sm'
            }
          >
            {periodChange > 0 && <TrendingUp className='mr-1 h-3 w-3' />}
            {periodChange < 0 && <TrendingDown className='mr-1 h-3 w-3' />}
            Period-over-Period: {periodChange > 0 ? '+' : ''}
            {periodChange.toFixed(2)}%
          </span>
        )}
      </GenericKpiTile>
      {/* 3. Top Service */}
      <GenericKpiTile
        title='Top Service'
        value={topService || 'N/A'}
        change=''
        changeValue={0}
        icon={DollarSign}
        valueFormatter={(val) => String(val)}
        loading={topServiceLoading}
      />
      {/* 4. Top Service Category Spending */}
      <GenericKpiTile
        title='Top Service Category Spending'
        value={topCategory ? topCategory.name : 'N/A'}
        subtitle={
          topCategory
            ? `$${Number(topCategory.cost).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : ''
        }
        change=''
        changeValue={0}
        icon={Layers}
        valueFormatter={(val) => String(val)}
        loading={topCategoryLoading}
      />
      {/* 5. Number of Active Providers */}
      <GenericKpiTile
        title='Active Providers'
        value={activeProviders}
        icon={DollarSign}
        valueFormatter={(val) => String(val)}
        loading={activeProvidersLoading}
      />
    </div>
  )
}
