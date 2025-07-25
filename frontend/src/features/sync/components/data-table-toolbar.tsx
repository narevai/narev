import { Cross2Icon } from '@radix-ui/react-icons'
import { Table } from '@tanstack/react-table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTableViewOptions } from '../components/data-table-view-options'
import { useSyncs } from '../context/syncs-context'
import { DataTableFacetedFilter } from './data-table-faceted-filter'

interface DataTableToolbarProps<TData> {
  table: Table<TData>
}

// Sync status filter options
const syncStatuses = [
  {
    label: 'Pending',
    value: 'pending',
  },
  {
    label: 'Running',
    value: 'running',
  },
  {
    label: 'Completed',
    value: 'completed',
  },
  {
    label: 'Failed',
    value: 'failed',
  },
  {
    label: 'Cancelled',
    value: 'cancelled',
  },
]

export function DataTableToolbar<TData>({
  table,
}: DataTableToolbarProps<TData>) {
  const isFiltered = table.getState().columnFilters.length > 0
  const { providerInstances } = useSyncs()

  // Create provider filter options from available providers
  const providerOptions =
    providerInstances?.map((provider) => ({
      label: provider.display_name || provider.provider_type,
      value: provider.display_name || provider.provider_type,
    })) || []

  return (
    <div className='flex items-center justify-between'>
      <div className='flex flex-1 flex-col-reverse items-start gap-y-2 sm:flex-row sm:items-center sm:space-x-2'>
        <Input
          placeholder='Filter by provider name...'
          value={
            (table.getColumn('provider_name')?.getFilterValue() as string) ?? ''
          }
          onChange={(event) =>
            table.getColumn('provider_name')?.setFilterValue(event.target.value)
          }
          className='h-8 w-[150px] lg:w-[250px]'
        />
        <div className='flex gap-x-2'>
          {table.getColumn('status') && (
            <DataTableFacetedFilter
              column={table.getColumn('status')}
              title='Status'
              options={syncStatuses}
            />
          )}
          {table.getColumn('provider_name') && providerOptions.length > 0 && (
            <DataTableFacetedFilter
              column={table.getColumn('provider_name')}
              title='Provider'
              options={providerOptions}
            />
          )}
        </div>
        {isFiltered && (
          <Button
            variant='ghost'
            onClick={() => table.resetColumnFilters()}
            className='h-8 px-2 lg:px-3'
          >
            Reset
            <Cross2Icon className='ml-2 h-4 w-4' />
          </Button>
        )}
      </div>
      <DataTableViewOptions table={table} />
    </div>
  )
}
