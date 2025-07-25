export interface BaseChartProps {
  data: Array<Record<string, unknown>>
  loading?: boolean
  error?: string | null
  height?: number
  className?: string
  dataKey?: string
  xAxisKey?: string
  showGrid?: boolean
  tickFormatter?: (value: number | string) => string
  title?: string
  description?: string
  trendingText?: string
  trendingPercentage?: number
  footerDescription?: string
  showCard?: boolean
  angle?: number // X axis label rotation angle
}

export interface BarChartProps extends BaseChartProps {
  barRadius?: number
  showValues?: boolean
  dataKeys?: string[]
  stacked?: boolean
}

export interface LineChartProps extends BaseChartProps {
  strokeWidth?: number
  showDots?: boolean
  lineType?:
    | 'basis'
    | 'basisClosed'
    | 'basisOpen'
    | 'linear'
    | 'linearClosed'
    | 'natural'
    | 'monotoneX'
    | 'monotoneY'
    | 'monotone'
    | 'step'
    | 'stepBefore'
    | 'stepAfter'
}
export interface AreaChartProps extends BaseChartProps {
  dataKeys?: string[]
  showGradient?: boolean
  fillOpacity?: number
  areaType?:
    | 'basis'
    | 'basisClosed'
    | 'basisOpen'
    | 'linear'
    | 'linearClosed'
    | 'natural'
    | 'monotoneX'
    | 'monotoneY'
    | 'monotone'
    | 'step'
    | 'stepBefore'
    | 'stepAfter'
  stacked?: boolean // Add this prop
}
