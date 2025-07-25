import { useEffect, useState } from 'react'
import { Info } from 'lucide-react'
import { useAnalytics } from '@/hooks/use-analytics'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { GenericAreaChart } from '@/features/dashboard/components/charts'

interface SpendingByProviderTrendsTileProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
  }
}

export function SpendingByProviderTrendsTile({
  filters,
}: SpendingByProviderTrendsTileProps) {
  const { getServiceCostTrends, getUseCases } = useAnalytics()
  const [data, setData] = useState<Record<string, number | string>[]>([])
  const [providerNames, setProviderNames] = useState<string[]>([])
  const [meta, setMeta] = useState<{ name: string; context: string } | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [metaLoading, setMetaLoading] = useState(false)

  useEffect(() => {
    const fetchTrends = async () => {
      setLoading(true)
      const params = {
        start_date: filters.dateRange.start_date,
        end_date: filters.dateRange.end_date,
      }
      const response = await getServiceCostTrends(params)
      type TrendData = {
        month_name: string
        provider_name: string
        total_effective_cost: number
      }
      let trendData = (response?.data as TrendData[]) || []
      // Filter by selected providers if any are selected
      if (filters.providers && filters.providers.length > 0) {
        trendData = trendData.filter((d) =>
          filters.providers.includes(d.provider_name)
        )
      }
      // Get all unique months in order (YYYY-MM)
      const months = Array.from(
        new Set(trendData.map((d) => d.month_name))
      ).sort()
      // Get all unique providers
      const providers = Array.from(
        new Set(trendData.map((d) => d.provider_name))
      )
      setProviderNames(providers)
      // Filter out months outside the selected date range
      const startDate = new Date(filters.dateRange.start_date)
      const endDate = new Date(filters.dateRange.end_date)
      const monthsInRange = months.filter((month) => {
        const [year, monthNum] = month.split('-').map(Number)
        const monthDate = new Date(year, monthNum - 1, 1)
        return monthDate >= startDate && monthDate <= endDate
      })
      // Build stacked data: [{ month_name, provider1: cost, provider2: cost, ... }]
      const monthMap: Record<string, Record<string, number>> = {}
      trendData.forEach((d) => {
        if (!monthMap[d.month_name]) monthMap[d.month_name] = {}
        monthMap[d.month_name][d.provider_name] = d.total_effective_cost
      })
      // Use monthsInRange instead of months
      const stacked = monthsInRange.map((month) => {
        const entry: Record<string, number | string> = { month_name: month }
        providers.forEach((p) => {
          entry[p] = monthMap[month]?.[p] || 0
        })
        return entry
      })
      setData(stacked)
      setLoading(false)
    }
    fetchTrends()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.dateRange.start_date,
    filters.dateRange.end_date,
    filters.providers,
  ])

  useEffect(() => {
    const fetchMeta = async () => {
      setMetaLoading(true)
      const useCases = await getUseCases()
      if (useCases && Array.isArray(useCases.use_cases)) {
        type UseCase = { endpoint: string; name: string; context: string }
        const trendsUseCase = (useCases.use_cases as UseCase[]).find(
          (uc) => uc.endpoint === '/analytics/service-cost-trends'
        )
        if (trendsUseCase) {
          setMeta({
            name: 'Spending Over Time by Provider',
            context: trendsUseCase.context,
          })
        }
      }
      setMetaLoading(false)
    }
    fetchMeta()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Card>
      <CardHeader>
        <div className='flex items-center gap-2'>
          <CardTitle>
            {meta?.name || 'Spending Over Time by Provider'}
          </CardTitle>
          {meta?.context && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    tabIndex={0}
                    className='text-muted-foreground cursor-pointer'
                  >
                    <Info className='h-4 w-4' aria-label='Info' />
                  </span>
                </TooltipTrigger>
                <TooltipContent
                  side='right'
                  className='max-w-xs whitespace-pre-line'
                >
                  {meta.context}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </CardHeader>
      <CardContent className='pl-2'>
        <GenericAreaChart
          data={data}
          dataKeys={providerNames}
          xAxisKey='month_name'
          tickFormatter={(value: unknown) =>
            `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
          }
          showCard={false}
          stacked={true}
          height={300}
          loading={loading || metaLoading}
          angle={-30}
        />
      </CardContent>
    </Card>
  )
}
