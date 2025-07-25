import { TrendingUp, TrendingDown } from 'lucide-react'
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
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
} from '@/components/ui/chart'
import { LineChartProps } from '@/features/dashboard/components/charts/types'

export function GenericLineChart({
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
  strokeWidth = 2,
  showDots = false,
  lineType = 'natural',
  angle = 0,
}: LineChartProps & { angle?: number }) {
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

  const chartConfig = {
    [dataKey]: {
      label: dataKey,
      color: 'var(--primary)',
    },
  } satisfies ChartConfig

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
          <LineChart
            accessibilityLayer
            data={data}
            margin={{ top: 20, right: 5, left: 5, bottom: 32 }}
          >
            {showGrid && (
              <CartesianGrid vertical={false} stroke='hsl(var(--border))' />
            )}
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
              stroke='hsl(var(--muted-foreground))'
              fontSize={12}
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <Line
              dataKey={dataKey}
              type={lineType}
              stroke={`var(--color-${dataKey})`}
              strokeWidth={strokeWidth}
              dot={showDots}
            />
          </LineChart>
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

  return <div className='h-full w-full'>{chartContent}</div>
}
