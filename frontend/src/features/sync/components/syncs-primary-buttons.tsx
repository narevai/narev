import { IconRefresh, IconHeartbeat, IconGitBranch } from '@tabler/icons-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useSyncs } from '../context/syncs-context'

export function SyncsPrimaryButtons() {
  const { setOpen, checkSyncHealth, refreshSyncData, loading } = useSyncs()

  const handleHealthCheck = async () => {
    try {
      const healthData = await checkSyncHealth()

      // Show success toast with health status
      toast.success('Health check completed', {
        description: `Service status: ${healthData.status || 'Healthy'}`,
      })
    } catch (_) {
      // Error handling is already done in the hook
    }
  }

  const handleRefresh = async () => {
    try {
      await refreshSyncData()
    } catch (_) {
      // Error handling is done in the hook
    }
  }

  return (
    <div className='flex gap-2'>
      <Button
        variant='outline'
        className='space-x-1'
        onClick={handleHealthCheck}
        disabled={loading}
      >
        <span>Health Check</span> <IconHeartbeat size={18} />
      </Button>

      <Button
        variant='outline'
        className='space-x-1'
        onClick={handleRefresh}
        disabled={loading}
      >
        <span>Refresh</span> <IconRefresh size={18} />
      </Button>

      <Button
        className='space-x-1'
        onClick={() => setOpen('trigger')}
        disabled={loading}
      >
        <span>Trigger Sync</span> <IconGitBranch size={18} />
      </Button>
    </div>
  )
}
