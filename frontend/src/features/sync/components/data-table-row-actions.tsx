import { DotsHorizontalIcon } from '@radix-ui/react-icons'
import { Row } from '@tanstack/react-table'
import { IconEye, IconRefresh, IconX, IconCopy } from '@tabler/icons-react'
import { toast } from 'sonner'
import type { SyncRunInfo } from '@/hooks/use-syncs'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useSyncs } from '../context/syncs-context'

interface DataTableRowActionsProps<TData> {
  row: Row<TData>
}

export function DataTableRowActions<TData>({
  row,
}: DataTableRowActionsProps<TData>) {
  const syncRun = row.original as SyncRunInfo
  const { setOpen, setCurrentRow } = useSyncs()

  const copyRunId = async () => {
    try {
      await navigator.clipboard.writeText(syncRun.id)
      toast.success('Run ID copied to clipboard')
    } catch (_) {
      toast.error('Failed to copy Run ID')
    }
  }

  const canCancel = syncRun.status === 'running' || syncRun.status === 'pending'
  const canRetry = syncRun.status === 'failed' || syncRun.status === 'cancelled'

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button
          variant='ghost'
          className='data-[state=open]:bg-muted flex h-8 w-8 p-0'
        >
          <DotsHorizontalIcon className='h-4 w-4' />
          <span className='sr-only'>Open menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align='end' className='w-[160px]'>
        <DropdownMenuItem
          onClick={() => {
            setCurrentRow(syncRun)
            setOpen('details')
          }}
        >
          View Details
          <DropdownMenuShortcut>
            <IconEye size={16} />
          </DropdownMenuShortcut>
        </DropdownMenuItem>

        <DropdownMenuItem onClick={copyRunId}>
          Copy Run ID
          <DropdownMenuShortcut>
            <IconCopy size={16} />
          </DropdownMenuShortcut>
        </DropdownMenuItem>

        {(canRetry || canCancel) && <DropdownMenuSeparator />}

        {canRetry && (
          <DropdownMenuItem
            onClick={() => {
              setCurrentRow(syncRun)
              setOpen('retry')
            }}
          >
            Retry Sync
            <DropdownMenuShortcut>
              <IconRefresh size={16} />
            </DropdownMenuShortcut>
          </DropdownMenuItem>
        )}

        {canCancel && (
          <DropdownMenuItem
            onClick={() => {
              setCurrentRow(syncRun)
              setOpen('cancel')
            }}
            className='text-destructive focus:text-destructive'
          >
            Cancel Sync
            <DropdownMenuShortcut>
              <IconX size={16} />
            </DropdownMenuShortcut>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
