import { DateRange } from '@/features/dashboard/components/filters/types'

export interface TabComponentProps {
  className?: string
}

export interface TabMetadata {
  title: string
  description?: string
  lastUpdated?: Date
}

export interface OverviewFilters {
  dateRange: DateRange
  providers: string[]
  services: string[]
}
