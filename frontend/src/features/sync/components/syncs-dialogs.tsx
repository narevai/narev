import { toast } from 'sonner'
import { showSubmittedData } from '@/utils/show-submitted-data'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { useSyncs } from '../context/syncs-context'
import { SyncsMutateDrawer } from './syncs-mutate-drawer'

export function SyncsDialogs() {
  const {
    open,
    setOpen,
    currentRow,
    setCurrentRow,
    cancelSyncRun,
    retrySyncRun,
  } = useSyncs()

  return (
    <>
      <SyncsMutateDrawer
        key='sync-trigger'
        open={open === 'trigger'}
        onOpenChange={() => setOpen('trigger')}
      />

      {currentRow && (
        <>
          <SyncsMutateDrawer
            key={`sync-details-${currentRow.id}`}
            open={open === 'details'}
            onOpenChange={() => {
              setOpen('details')
              setTimeout(() => {
                setCurrentRow(null)
              }, 500)
            }}
            currentRow={currentRow}
          />

          <ConfirmDialog
            key='sync-cancel'
            destructive
            open={open === 'cancel'}
            onOpenChange={(isOpen) => {
              setOpen(isOpen ? 'cancel' : null)
              if (!isOpen) {
                setTimeout(() => {
                  setCurrentRow(null)
                }, 500)
              }
            }}
            handleConfirm={async () => {
              try {
                // Check if the sync is still cancellable
                if (!['running', 'pending'].includes(currentRow.status)) {
                  toast.error('Cannot cancel sync run', {
                    description: `Sync is in "${currentRow.status}" state and cannot be cancelled.`,
                  })
                  setOpen(null)
                  setTimeout(() => {
                    setCurrentRow(null)
                  }, 500)
                  return
                }

                await cancelSyncRun(currentRow.id)
                setOpen(null)
                setTimeout(() => {
                  setCurrentRow(null)
                }, 500)
              } catch (_) {
                toast.error('Failed to cancel sync run', {
                  description:
                    'The sync may have already completed or is not in a cancellable state.',
                })
              }
            }}
            className='max-w-md'
            title={`Cancel sync run: ${currentRow.id}?`}
            desc={
              <>
                You are about to cancel the sync run with ID{' '}
                <strong>{currentRow.id}</strong>. <br />
                This will stop the current synchronization process.
              </>
            }
            confirmText='Cancel Sync'
          />

          <ConfirmDialog
            key='sync-retry'
            open={open === 'retry'}
            onOpenChange={() => {
              setOpen('retry')
              setTimeout(() => {
                setCurrentRow(null)
              }, 500)
            }}
            handleConfirm={async () => {
              try {
                await retrySyncRun(currentRow.id)
                setOpen(null)
                setTimeout(() => {
                  setCurrentRow(null)
                }, 500)
                showSubmittedData(
                  currentRow,
                  'The following sync run has been retried:'
                )
              } catch (_) {
                // Error is already handled in the hook with toast
              }
            }}
            className='max-w-md'
            title={`Retry sync run: ${currentRow.id}?`}
            desc={
              <>
                You are about to retry the failed sync run with ID{' '}
                <strong>{currentRow.id}</strong>. <br />
                This will start a new synchronization with the same parameters.
              </>
            }
            confirmText='Retry Sync'
          />
        </>
      )}
    </>
  )
}
