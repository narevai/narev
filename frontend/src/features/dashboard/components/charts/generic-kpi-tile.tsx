// components/tiles/generic-kpi-tile.tsx
import { LucideIcon } from 'lucide-react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface KpiTileProps {
  title: string
  value: string | number
  change?: string
  changeValue?: number
  icon?: LucideIcon
  loading?: boolean
  error?: string | null
  valueFormatter?: (value: string | number) => string
  showTrend?: boolean
  trendDirection?: 'up' | 'down' | 'neutral'
  subtitle?: string
  className?: string
  children?: React.ReactNode
}

export function GenericKpiTile({
  title,
  value,
  change,
  changeValue,
  icon: Icon,
  loading = false,
  error = null,
  valueFormatter = (val) => val.toString(),
  showTrend = true,
  trendDirection,
  subtitle,
  className = '',
  children,
}: KpiTileProps) {
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
          <CardTitle className='text-sm font-medium'>{title}</CardTitle>
          {Icon && <Icon className='text-muted-foreground h-4 w-4' />}
        </CardHeader>
        <CardContent>
          <div className='bg-muted h-8 w-24 animate-pulse rounded text-2xl font-bold'></div>
          <div className='text-muted-foreground bg-muted mt-1 h-4 w-32 animate-pulse rounded text-xs'></div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
          <CardTitle className='text-sm font-medium'>{title}</CardTitle>
          {Icon && <Icon className='text-muted-foreground h-4 w-4' />}
        </CardHeader>
        <CardContent>
          <div className='text-destructive text-2xl font-bold'>Error</div>
          <p className='text-muted-foreground text-xs'>{error}</p>
        </CardContent>
      </Card>
    )
  }

  const autoTrendDirection =
    trendDirection ||
    (changeValue !== undefined
      ? changeValue > 0
        ? 'up'
        : changeValue < 0
          ? 'down'
          : 'neutral'
      : 'neutral')

  const getTrendIcon = () => {
    if (!showTrend) return null

    switch (autoTrendDirection) {
      case 'up':
        return <TrendingUp className='h-3 w-3 text-green-500' />
      case 'down':
        return <TrendingDown className='text-destructive h-3 w-3' />
      default:
        return null
    }
  }

  const getTrendColor = () => {
    switch (autoTrendDirection) {
      case 'up':
        return 'text-green-500'
      case 'down':
        return 'text-destructive'
      default:
        return 'text-muted-foreground'
    }
  }

  return (
    <Card className={className}>
      <CardHeader className='flex flex-row items-start justify-between space-y-0 pb-2'>
        <CardTitle className='text-sm font-medium'>{title}</CardTitle>
        {Icon && <Icon className='text-muted-foreground mt-0.5 h-5 w-5' />}
      </CardHeader>
      <CardContent>
        <div className='text-2xl font-bold'>{valueFormatter(value)}</div>
        {subtitle && (
          <p className='text-muted-foreground mt-1 text-sm'>{subtitle}</p>
        )}
        {change && (
          <div
            className={`mt-1 flex items-center gap-1 text-xs ${getTrendColor()}`}
          >
            {getTrendIcon()}
            <span>{change}</span>
          </div>
        )}
        {children}
      </CardContent>
    </Card>
  )
}
