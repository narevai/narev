import { useEffect, useState, useCallback } from 'react'
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

interface ServiceCategoryBreakdownTileProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
  }
}

export function ServiceCategoryBreakdownTile({
  filters,
}: ServiceCategoryBreakdownTileProps) {
  const { getServiceCategoryBreakdown, getUseCases } = useAnalytics()
  const [data, setData] = useState<Array<{ name: string; cost: number }>>([])
  const [meta, setMeta] = useState<{ name: string; context: string } | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [metaLoading, setMetaLoading] = useState(false)

  const fetchServiceCategoryBreakdown = useCallback(
    async () => {
      if (filters.providers.length === 0) return
      setLoading(true)
      try {
        const serviceData = await getServiceCategoryBreakdown(filters.dateRange)
        if (serviceData?.data) {
          type ServiceData = {
            provider_name: string
            service_category: string
            total_billed_cost: number
          }
          // Filter by selected providers
          const filteredData = (serviceData.data as ServiceData[]).filter(
            (item) => filters.providers.includes(item.provider_name)
          )
          // Aggregate by category
          const categoryTotals: { [key: string]: number } = {}
          filteredData.forEach((item) => {
            const category = item.service_category || 'Unknown'
            categoryTotals[category] =
              (categoryTotals[category] || 0) + (item.total_billed_cost || 0)
          })
          // Transform for chart and KPIs
          const categories = Object.entries(categoryTotals)
            .map(([name, cost]) => ({ name, cost }))
            .sort((a, b) => b.cost - a.cost)
          setData(categories.slice(0, 8))
        }
      } catch (_) {
        // Error already handled
      } finally {
        setLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      filters.dateRange.start_date,
      filters.dateRange.end_date,
      filters.providers,
    ]
  )

  useEffect(() => {
    fetchServiceCategoryBreakdown()
  }, [fetchServiceCategoryBreakdown])

  useEffect(
    () => {
      const fetchMeta = async () => {
        setMetaLoading(true)
        const useCases = await getUseCases()
        if (useCases && Array.isArray(useCases.use_cases)) {
          type UseCase = { endpoint: string; name: string; context: string }
          const useCase = (useCases.use_cases as UseCase[]).find(
            (uc) => uc.endpoint === '/analytics/service-category-breakdown'
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
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  return (
    <Card>
      <CardHeader>
        <div className='flex items-center gap-2'>
          <CardTitle>Spending by Service Category</CardTitle>
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
          xAxisKey='name'
          dataKey='cost'
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
