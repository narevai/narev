import { Label } from '@/components/ui/label'
import { DateRangeFilter } from '@/features/dashboard/components/filters/date-range-filter'
import { ProviderFilter } from '@/features/dashboard/components/filters/provider-filter'
import { ServiceFilter } from '@/features/dashboard/components/filters/service-filter'
import { OverviewFilters as OverviewFiltersType } from '@/features/dashboard/components/tabs/types.ts'

interface OverviewFiltersProps {
  filters: OverviewFiltersType
  onFiltersChange: (filters: OverviewFiltersType) => void
}

export function OverviewFilters({
  filters,
  onFiltersChange,
}: OverviewFiltersProps) {
  return (
    <div className='mb-6'>
      <Label className='mb-3 block text-sm font-medium'>Filters</Label>
      <div className='flex gap-4'>
        <DateRangeFilter
          value={filters.dateRange}
          onChange={(dateRange) => onFiltersChange({ ...filters, dateRange })}
        />
        <ProviderFilter
          value={filters.providers}
          onChange={(providers) => onFiltersChange({ ...filters, providers })}
        />
        <ServiceFilter
          value={filters.services}
          onChange={(services) => onFiltersChange({ ...filters, services })}
        />
      </div>
    </div>
  )
}
