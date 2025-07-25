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
import { GenericBarChart } from '@/features/dashboard/components/charts'

interface SpendingByBillingPeriodTileProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
  }
}

export function SpendingByBillingPeriodTile({
  filters,
}: SpendingByBillingPeriodTileProps) {
  const { getSpendingByBillingPeriod, getUseCases } = useAnalytics()
  const [data, setData] = useState<Record<string, string | number>[]>([])
  const [meta, setMeta] = useState<{ name: string; context: string } | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [metaLoading, setMetaLoading] = useState(false)
  const [serviceCategories, setServiceCategories] = useState<string[]>([])

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      let allResults: Array<{
        billing_period_start: string
        service_category: string
        total_billed_cost: number
      }> = []
      for (const provider of filters.providers) {
        const params = {
          start_date: filters.dateRange.start_date,
          end_date: filters.dateRange.end_date,
          provider_name: provider,
        }
        const response = await getSpendingByBillingPeriod(params)
        // console.log('getSpendingByBillingPeriod response', response)
        const periodData = (response?.data as typeof allResults) || []
        allResults = allResults.concat(periodData)
      }

      // Normalize all billing_period_start values to YYYY-MM-DD
      allResults = allResults.map((d) => ({
        ...d,
        billing_period_start: d.billing_period_start.slice(0, 10),
      }))
      // Filter out periods outside the selected date range
      const startDate = new Date(filters.dateRange.start_date)
      const endDate = new Date(filters.dateRange.end_date)
      allResults = allResults.filter((d) => {
        const periodDate = new Date(d.billing_period_start)
        return periodDate >= startDate && periodDate <= endDate
      })

      // Get all unique periods and service categories
      const periods = Array.from(
        new Set(allResults.map((d) => d.billing_period_start))
      ).sort((a, b) => a.localeCompare(b))
      const categories = Array.from(
        new Set(allResults.map((d) => d.service_category))
      )

      // Aggregate data by period and service category
      const periodMap: Record<string, Record<string, string | number>> = {}
      for (const period of periods) {
        periodMap[period] = { period } as Record<string, string | number>
        for (const cat of categories) {
          periodMap[period][cat] = 0
        }
      }
      for (const row of allResults) {
        periodMap[row.billing_period_start][row.service_category] =
          (periodMap[row.billing_period_start][
            row.service_category
          ] as number) + row.total_billed_cost
      }
      // For each period, sort categories by value descending
      const sortedCategories = (() => {
        // Use the first period with data to determine order
        const firstPeriod = periods[0]
        if (!firstPeriod) return categories
        return [...categories].sort(
          (a, b) =>
            (periodMap[firstPeriod][b] as number) -
            (periodMap[firstPeriod][a] as number)
        )
      })()
      const finalData = periods.map((period) => periodMap[period])
      setData(finalData)
      setServiceCategories(sortedCategories)
      setLoading(false)
    }
    fetchData()
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
        const useCase = (useCases.use_cases as UseCase[]).find(
          (uc) => uc.endpoint === '/analytics/spending-by-billing-period'
        )
        if (useCase) {
          setMeta({
            name: useCase.name,
            context: useCase.context,
          })
        }
      }
      setMetaLoading(false)
    }
    fetchMeta()
  }, [])

  return (
    <Card>
      <CardHeader>
        <div className='flex items-center gap-2'>
          <CardTitle>{meta?.name || 'Spending by Billing Period'}</CardTitle>
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
        <GenericBarChart
          data={data}
          xAxisKey='period'
          dataKeys={serviceCategories}
          stacked
          showLegend={false}
          barRadius={0}
          tickFormatter={(value: unknown) =>
            `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
          }
          showCard={false}
          height={300}
          loading={loading || metaLoading}
          angle={-30}
        />
      </CardContent>
    </Card>
  )
}
