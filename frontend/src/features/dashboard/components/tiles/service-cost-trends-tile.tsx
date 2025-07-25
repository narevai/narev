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

interface ServiceCostTrendsTileProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
  }
}

export function ServiceCostTrendsTile({ filters }: ServiceCostTrendsTileProps) {
  const { getServiceCostTrends, getUseCases } = useAnalytics()
  const [data, setData] = useState<Record<string, number | string>[]>([])
  const [serviceNames, setServiceNames] = useState<string[]>([])
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
        service_name: string
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
      // Calculate total cost per service across all months
      const serviceTotals: Record<string, number> = {}
      trendData.forEach((d) => {
        serviceTotals[d.service_name] =
          (serviceTotals[d.service_name] || 0) + (d.total_effective_cost || 0)
      })
      // Get top 10 services by total cost
      const topServices = Object.entries(serviceTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([service]) => service)
      // Build stacked data: [{ month_name, service1: cost, ..., Other: cost }]
      const monthMap: Record<string, Record<string, number>> = {}
      trendData.forEach((d) => {
        if (!monthMap[d.month_name]) monthMap[d.month_name] = {}
        const key = topServices.includes(d.service_name)
          ? d.service_name
          : 'Other'
        monthMap[d.month_name][key] =
          (monthMap[d.month_name][key] || 0) + (d.total_effective_cost || 0)
      })
      const allKeys = [...topServices, 'Other']
      // Filter out months outside the selected date range
      const startDate = new Date(filters.dateRange.start_date)
      const endDate = new Date(filters.dateRange.end_date)
      // months is an array of month_name (YYYY-MM)
      const monthsInRange = months.filter((month) => {
        // Parse as first day of month
        const [year, monthNum] = month.split('-').map(Number)
        const monthDate = new Date(year, monthNum - 1, 1)
        return monthDate >= startDate && monthDate <= endDate
      })
      // Use monthsInRange instead of months
      // Build stacked data: [{ month_name, service1: cost, ..., Other: cost }]
      const stacked = monthsInRange.map((month) => {
        const entry: Record<string, number | string> = { month_name: month }
        allKeys.forEach((s) => {
          entry[s] = monthMap[month]?.[s] || 0
        })
        return entry
      })
      setData(stacked)
      setServiceNames(allKeys)
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
            name: 'Service Cost Trends by Service',
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
            {meta?.name || 'Service Cost Trends by Service'}
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
          dataKeys={serviceNames}
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
