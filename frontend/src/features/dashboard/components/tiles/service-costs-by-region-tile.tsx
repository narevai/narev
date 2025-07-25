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

interface ServiceCostsByRegionTileProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
  }
}

export function ServiceCostsByRegionTile({
  filters,
}: ServiceCostsByRegionTileProps) {
  const { getServiceCostsByRegion, getUseCases } = useAnalytics()
  const [data, setData] = useState<Array<{ region: string; cost: number }>>([])
  const [meta, setMeta] = useState<{ name: string; context: string } | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [metaLoading, setMetaLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      // For now, aggregate by region across all providers
      const params = {
        start_date: filters.dateRange.start_date,
        end_date: filters.dateRange.end_date,
      }
      const response = await getServiceCostsByRegion(params)
      type RegionData = {
        region_id: string
        provider_name: string
        total_effective_cost: number
      }
      let regionData = (response?.data as RegionData[]) || []
      // Filter by selected providers if any are selected
      if (filters.providers && filters.providers.length > 0) {
        regionData = regionData.filter((d) =>
          filters.providers.includes(d.provider_name)
        )
      }
      // Aggregate by region
      const regionTotals: Record<string, number> = {}
      regionData.forEach((d) => {
        regionTotals[d.region_id || 'Unknown'] =
          (regionTotals[d.region_id || 'Unknown'] || 0) +
          (d.total_effective_cost || 0)
      })
      const chartData = Object.entries(regionTotals)
        .map(([region, cost]) => ({ region, cost }))
        .sort((a, b) => b.cost - a.cost)
      setData(chartData.slice(0, 8))
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
          (uc) => uc.endpoint === '/analytics/service-costs-by-region'
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
          <CardTitle>{meta?.name || 'Service Costs by Region'}</CardTitle>
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
          xAxisKey='region'
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
