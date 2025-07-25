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

interface ServiceCostAnalysisTileProps {
  filters: {
    dateRange: { start_date: string; end_date: string }
    providers: string[]
    services: string[]
  }
}

export function ServiceCostAnalysisTile({
  filters,
}: ServiceCostAnalysisTileProps) {
  const { getServiceCostAnalysis, getUseCases, getAvailableServices } =
    useAnalytics()
  const [data, setData] = useState<
    Array<{ label: string; service: string; provider: string; cost: number }>
  >([])
  const [meta, setMeta] = useState<{ name: string; context: string } | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [metaLoading, setMetaLoading] = useState(false)
  const [serviceProviderMap, setServiceProviderMap] = useState<
    Record<string, string[]>
  >({})

  // Fetch available services and build a map: service_name -> [provider_name]
  useEffect(() => {
    const fetchServiceProviderMap = async () => {
      const response = await getAvailableServices()
      if (response?.data) {
        const map: Record<string, string[]> = {}
        response.data.forEach(
          (item: { service_name: string; provider_name: string }) => {
            if (!map[item.service_name]) map[item.service_name] = []
            map[item.service_name].push(item.provider_name)
          }
        )
        setServiceProviderMap(map)
      }
    }
    fetchServiceProviderMap()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      if (
        !filters.services ||
        filters.services.length === 0 ||
        !filters.providers ||
        filters.providers.length === 0
      ) {
        setData([])
        setLoading(false)
        return
      }
      let allResults: Array<{
        label: string
        service: string
        provider: string
        cost: number
      }> = []
      for (const provider of filters.providers) {
        for (const serviceName of filters.services) {
          // Only fetch if this (service, provider) pair exists in available services
          if (
            !serviceProviderMap[serviceName] ||
            !serviceProviderMap[serviceName].includes(provider)
          )
            continue
          const params = {
            provider_name: provider,
            start_date: filters.dateRange.start_date,
            end_date: filters.dateRange.end_date,
            service_name: serviceName,
          }
          const response = await getServiceCostAnalysis(params)
          type ServiceData = {
            service_name: string
            total_effective_cost: number
          }
          const serviceData = (response?.data as ServiceData[]) || []
          const chartData = serviceData.map((d) => ({
            label: `${d.service_name} (${provider})`,
            service: d.service_name,
            provider,
            cost: d.total_effective_cost,
          }))
          allResults = allResults.concat(chartData)
        }
      }
      // Aggregate by label (service + provider)
      const aggregated: Record<
        string,
        { label: string; service: string; provider: string; cost: number }
      > = {}
      allResults.forEach((item) => {
        if (!aggregated[item.label]) {
          aggregated[item.label] = { ...item }
        } else {
          aggregated[item.label].cost += item.cost
        }
      })
      const finalData = Object.values(aggregated).sort(
        (a, b) => b.cost - a.cost
      )
      setData(finalData)
      setLoading(false)
    }
    fetchData()
  }, [
    filters.dateRange.start_date,
    filters.dateRange.end_date,
    filters.providers,
    filters.services,
    serviceProviderMap,
  ])

  useEffect(() => {
    const fetchMeta = async () => {
      setMetaLoading(true)
      const useCases = await getUseCases()
      if (useCases && Array.isArray(useCases.use_cases)) {
        type UseCase = { endpoint: string; name: string; context: string }
        const useCase = (useCases.use_cases as UseCase[]).find(
          (uc) => uc.endpoint === '/analytics/service-cost-analysis'
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
          <CardTitle>{meta?.name || 'Service Cost Analysis'}</CardTitle>
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
        {!filters.services ||
        filters.services.length === 0 ||
        !filters.providers ||
        filters.providers.length === 0 ? (
          <div className='text-muted-foreground'>
            Please select at least one service and one provider to view cost
            analysis.
          </div>
        ) : (
          <GenericBarChart
            data={data}
            xAxisKey='label'
            dataKey='cost'
            tickFormatter={(value: unknown) =>
              `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
            }
            showCard={false}
            height={300}
            loading={loading || metaLoading}
            angle={-30}
          />
        )}
      </CardContent>
    </Card>
  )
}
