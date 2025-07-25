import { TrendingUp, TrendingDown } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts'
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
import { AreaChartProps } from '@/features/dashboard/components/charts/types'

export function GenericAreaChart({
  data,
  dataKeys = ['value'],
  loading = false,
  error = null,
  height = 350,
  className = '',
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
  fillOpacity = 0.4,
  areaType = 'natural',
  stacked = true,
  angle = 0,
}: AreaChartProps & { angle?: number }) {
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

  // Filter out dataKeys that are all zeros
  const nonZeroKeys = dataKeys.filter((key) =>
    data.some((d) => Number(d[key]) !== 0)
  )

  // Use a fixed palette of CSS variables for colors
  const palette = [
    'var(--chart-1)',
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

  // Normalize key for SVG id (lowercase, alphanumeric only)
  const normalizeKey = (key: string) =>
    key.replace(/[^a-zA-Z0-9]/g, '').toLowerCase()

  // Ensure every data object has all nonZeroKeys, defaulting to 0 if missing
  const normalizedData = data.map((d) =>
    nonZeroKeys.reduce((acc, key) => ({ ...acc, [key]: d[key] ?? 0 }), { ...d })
  )

  const chartConfig = nonZeroKeys.reduce((config, key, index) => {
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
          <AreaChart
            accessibilityLayer
            data={normalizedData}
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
            <defs>
              {nonZeroKeys.map((key, index) => (
                <linearGradient
                  key={key}
                  id={`fill${normalizeKey(key)}`}
                  x1='0'
                  y1='0'
                  x2='0'
                  y2='1'
                >
                  <stop
                    offset='5%'
                    stopColor={palette[index % palette.length]}
                    stopOpacity={0.8}
                  />
                  <stop
                    offset='95%'
                    stopColor={palette[index % palette.length]}
                    stopOpacity={0.1}
                  />
                </linearGradient>
              ))}
            </defs>
            {nonZeroKeys.map((key, index) => (
              <Area
                key={key}
                dataKey={key}
                type={areaType}
                fill={`url(#fill${normalizeKey(key)})`}
                fillOpacity={fillOpacity}
                stroke={palette[index % palette.length]}
                stackId={stacked ? 'a' : undefined} // Conditional stacking
              />
            ))}
          </AreaChart>
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
