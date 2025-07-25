import { TrendingUp, TrendingDown } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from '@/components/ui/chart'
import { BarChartProps } from '@/features/dashboard/components/charts/types'

export function GenericBarChart({
  data,
  loading = false,
  error = null,
  height = 350,
  className = '',
  dataKey = 'value',
  xAxisKey = 'name',
  showGrid = true,
  tickFormatter = (value) =>
    `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
  title,
  description,
  trendingText,
  trendingPercentage,
  footerDescription,
  showCard = false,
  angle = 0,
  dataKeys: propDataKeys,
  stacked = false,
  showLegend = true,
}: BarChartProps & {
  angle?: number
  dataKeys?: string[]
  stacked?: boolean
  showLegend?: boolean
}) {
  if (loading) {
    return (
      <div
        className={`flex items-center justify-center h-[${height}px] ${className}`}
      >
        <div className='text-muted-foreground animate-pulse'>
          Loading chart...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div
        className={`flex items-center justify-center h-[${height}px] ${className}`}
      >
        <div className='text-destructive'>Error loading chart: {error}</div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div
        className={`flex items-center justify-center h-[${height}px] ${className}`}
      >
        <div className='text-muted-foreground'>No data available</div>
      </div>
    )
  }

  // Determine which keys to use for bars
  const dataKeys =
    propDataKeys && propDataKeys.length > 0 ? propDataKeys : [dataKey]

  // Use a fixed palette of CSS variables for colors
  const palette = [
    'var(--primary)', // First bar uses primary color
    'var(--chart-2)',
    'var(--chart-3)',
    'var(--chart-4)',
    'var(--chart-5)',
    'var(--chart-6)',
    'var(--chart-7)',
    'var(--chart-8)',
    'var(--chart-9)',
    'var(--chart-10)',
  ]

  // Chart config for legend/colors
  const chartConfig = dataKeys.reduce((config, key, index) => {
    config[key] = {
      label: key,
      color: palette[index % palette.length],
    }
    return config
  }, {} as ChartConfig)

  const chartContent = (
    <>
      {showCard && title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent className={showCard ? '' : 'p-0'}>
        <ChartContainer config={chartConfig} className={`${className} w-full`}>
          <BarChart
            accessibilityLayer
            data={data}
            margin={{ top: 20, right: 5, left: 5, bottom: 32 }}
          >
            {showGrid && <CartesianGrid vertical={false} />}
            <XAxis
              dataKey={xAxisKey}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={(value) =>
                typeof value === 'string' && value.length > 8
                  ? value.slice(0, 8) + '…'
                  : value
              }
              angle={angle}
              textAnchor={angle !== 0 ? 'end' : 'middle'}
              stroke='hsl(var(--muted-foreground))'
              fontSize={12}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickFormatter={tickFormatter}
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            {dataKeys.length > 1 && showLegend && (
              <ChartLegend content={<ChartLegendContent />} />
            )}
            {dataKeys.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                stackId={stacked ? 'a' : undefined}
                fill={palette[index % palette.length]}
                radius={dataKeys.length === 1 && !stacked ? 8 : 0}
              />
            ))}
          </BarChart>
        </ChartContainer>
      </CardContent>
      {showCard && (trendingText || footerDescription) && (
        <CardFooter className='flex-col items-start gap-2 text-sm'>
          {trendingText && trendingPercentage !== undefined && (
            <div className='flex gap-2 leading-none font-medium'>
              {trendingText}{' '}
              {trendingPercentage > 0 ? (
                <TrendingUp className='h-4 w-4' />
              ) : (
                <TrendingDown className='h-4 w-4' />
              )}
            </div>
          )}
          {footerDescription && (
            <div className='text-muted-foreground leading-none'>
              {footerDescription}
            </div>
          )}
        </CardFooter>
      )}
    </>
  )

  if (showCard) {
    return <Card>{chartContent}</Card>
  }

  return <div>{chartContent}</div>
}
