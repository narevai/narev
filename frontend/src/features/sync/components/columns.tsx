import { formatDistanceToNow } from 'date-fns'
import { ColumnDef } from '@tanstack/react-table'
import type { SyncRunInfo } from '@/hooks/use-syncs'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { DataTableColumnHeader } from './data-table-column-header'
import { DataTableRowActions } from './data-table-row-actions'
import { syncStatuses } from './sync-data'

export const columns: ColumnDef<SyncRunInfo>[] = [
  {
    id: 'select',
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && 'indeterminate')
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label='Select all'
        className='translate-y-[2px]'
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label='Select row'
        className='translate-y-[2px]'
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: 'id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Run ID' />
    ),
    cell: ({ row }) => (
      <div className='w-[80px] font-mono text-xs'>
        {row.getValue<string>('id').slice(0, 8)}...
      </div>
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: 'provider_name',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Provider' />
    ),
    cell: ({ row }) => {
      const providerName = row.getValue('provider_name') as string | null
      return (
        <div className='flex space-x-2'>
          <Badge variant='outline'>{providerName || 'Unknown'}</Badge>
        </div>
      )
    },
  },
  {
    accessorKey: 'status',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const status = syncStatuses.find(
        (status) => status.value === row.getValue('status')
      )

      if (!status) {
        return null
      }

      return (
        <div className='flex w-[100px] items-center'>
          <Badge variant={status.variant}>{status.label}</Badge>
        </div>
      )
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id))
    },
  },
  {
    accessorKey: 'started_at',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Started' />
    ),
    cell: ({ row }) => {
      const startedAtString = row.getValue('started_at') as string

      // Parse as UTC by appending 'Z' to treat as GMT
      const startedAt = new Date(startedAtString + 'Z')

      if (isNaN(startedAt.getTime())) {
        return (
          <span className='text-muted-foreground text-xs'>Invalid date</span>
        )
      }

      return (
        <div className='text-muted-foreground text-xs'>
          {formatDistanceToNow(startedAt, { addSuffix: true })}
        </div>
      )
    },
  },
  {
    accessorKey: 'duration_seconds',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Duration' />
    ),
    cell: ({ row }) => {
      const duration = row.getValue('duration_seconds') as number | null
      if (!duration) return <span className='text-muted-foreground'>-</span>

      const minutes = Math.floor(duration / 60)
      const seconds = duration % 60

      return (
        <div className='text-xs'>
          {minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`}
        </div>
      )
    },
  },
  {
    accessorKey: 'records_processed',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Records' />
    ),
    cell: ({ row }) => {
      const processed = row.getValue('records_processed') as number | null
      const created = row.original.records_created || 0
      const updated = row.original.records_updated || 0

      if (!processed) return <span className='text-muted-foreground'>-</span>

      return (
        <div className='text-xs'>
          <div>{processed.toLocaleString()} processed</div>
          {(created > 0 || updated > 0) && (
            <div className='text-muted-foreground'>
              +{created} •{updated}
            </div>
          )}
        </div>
      )
    },
  },
  {
    id: 'actions',
    cell: ({ row }) => <DataTableRowActions row={row} />,
  },
]
