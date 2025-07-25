// hooks/use-syncs.ts
import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  syncs,
  SyncTriggerRequest,
  SyncTriggerResponse,
  SyncStatusResponse,
  SyncRunsResponse,
  SyncRunDetails,
  SyncActionResponse,
  SyncStatisticsResponse,
  SyncHealthCheckResponse,
} from '@/lib/api'

type SyncRunInfo = SyncStatusResponse['runs'][0]
type SyncRun = SyncRunsResponse['runs'][0]
type SyncRunSummary = SyncStatusResponse['summary']
type SyncStats = SyncStatisticsResponse

export function useSyncs() {
  const [syncStatus, setSyncStatus] = useState<SyncStatusResponse | null>(null)
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([])
  const [syncStats, setSyncStats] = useState<SyncStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSyncStatus = async (params?: {
    provider_id?: string
    limit?: number
  }) => {
    try {
      const { data, error } = await syncs.getStatus(params)
      if (error) throw new Error('Failed to fetch sync status')

      return data as SyncStatusResponse
    } catch (err) {
      toast.error('Failed to fetch sync status', {
        description: 'Unable to load current sync status information.',
      })
      throw err
    }
  }

  const fetchSyncRuns = async (params?: {
    skip?: number
    limit?: number
    provider_id?: string
    status?: string
    start_date?: string
    end_date?: string
  }) => {
    try {
      const { data, error } = await syncs.getRuns(params)
      if (error) throw new Error('Failed to fetch sync runs')

      const typedData = data as SyncRunsResponse
      return typedData.runs || []
    } catch (err) {
      toast.error('Failed to fetch sync runs', {
        description: 'Unable to load sync run history.',
      })
      throw err
    }
  }

  const fetchSyncStats = async (params?: {
    provider_id?: string
    days?: number
  }) => {
    try {
      const { data, error } = await syncs.getStats(params)
      if (error) throw new Error('Failed to fetch sync statistics')

      return (data as SyncStatisticsResponse) || null
    } catch (err) {
      toast.error('Failed to fetch sync statistics', {
        description: 'Unable to load sync performance metrics.',
      })
      throw err
    }
  }

  const fetchAllSyncData = async (params?: {
    provider_id?: string
    limit?: number
    days?: number
  }) => {
    try {
      setLoading(true)
      setError(null)

      const [status, runs, stats] = await Promise.all([
        fetchSyncStatus({
          provider_id: params?.provider_id,
          limit: params?.limit,
        }),
        fetchSyncRuns({
          provider_id: params?.provider_id,
          limit: params?.limit || 50,
        }),
        fetchSyncStats({
          provider_id: params?.provider_id,
          days: params?.days,
        }),
      ])

      setSyncStatus(status)
      setSyncRuns(runs)
      setSyncStats(stats)
    } catch (_) {
      const errorMessage = 'Failed to load sync data'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Please check your connection and try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllSyncData()
  }, [])

  const triggerSync = async (data: SyncTriggerRequest) => {
    try {
      const { data: result, error } = await syncs.trigger(data)
      if (error) throw new Error('Failed to trigger sync')

      // Refresh sync data after triggering
      await fetchAllSyncData()

      toast.success('Sync triggered successfully')
      return result as SyncTriggerResponse
    } catch (error) {
      toast.error('Failed to trigger sync', {
        description: 'Unable to start the synchronization process.',
      })
      throw error
    }
  }

  const getSyncRun = async (run_id: string) => {
    try {
      const { data, error } = await syncs.getRun(run_id)
      if (error) throw new Error('Failed to get sync run details')

      return data as SyncRunDetails
    } catch (error) {
      toast.error('Failed to get sync run details', {
        description: 'Unable to load detailed sync run information.',
      })
      throw error
    }
  }

  const cancelSyncRun = async (run_id: string) => {
    try {
      const { data, error } = await syncs.cancelRun(run_id)
      if (error) throw new Error('Failed to cancel sync run')

      // Refresh sync data after canceling
      await fetchAllSyncData()

      toast.success('Sync run canceled successfully')
      return data as SyncActionResponse
    } catch (error) {
      toast.error('Failed to cancel sync run', {
        description: 'Unable to cancel the running synchronization.',
      })
      throw error
    }
  }

  const retrySyncRun = async (run_id: string) => {
    try {
      const { data, error } = await syncs.retryRun(run_id)
      if (error) throw new Error('Failed to retry sync run')

      // Refresh sync data after retrying
      await fetchAllSyncData()

      toast.success('Sync run retried successfully')
      return data as SyncActionResponse
    } catch (error) {
      toast.error('Failed to retry sync run', {
        description: 'Unable to retry the failed synchronization.',
      })
      throw error
    }
  }

  const getPipelineGraph = async (params?: { format?: string }) => {
    try {
      const { data, error } = await syncs.getPipelineGraph(params)
      if (error) throw new Error('Failed to get pipeline graph')

      return data
    } catch (error) {
      toast.error('Failed to get pipeline graph', {
        description:
          'Unable to load the synchronization pipeline visualization.',
      })
      throw error
    }
  }

  const checkSyncHealth = async () => {
    try {
      const { data, error } = await syncs.health()
      if (error) throw new Error('Failed to check sync health')

      return data as SyncHealthCheckResponse
    } catch (error) {
      toast.error('Failed to check sync health', {
        description: 'Unable to verify sync service status.',
      })
      throw error
    }
  }

  const refreshSyncData = (params?: {
    provider_id?: string
    limit?: number
    days?: number
  }) => {
    return fetchAllSyncData(params)
  }

  return {
    // Main sync data - updated structure
    syncStatus,
    syncRuns,
    syncStats,

    // Convenience getters for common data
    recentRuns: syncStatus?.runs || [],
    summary: syncStatus?.summary || null,

    // State
    loading,
    error,

    // Actions
    triggerSync,
    getSyncRun,
    cancelSyncRun,
    retrySyncRun,
    getPipelineGraph,
    checkSyncHealth,

    // Data fetching
    fetchSyncStatus,
    fetchSyncRuns,
    fetchSyncStats,
    refreshSyncData,
  }
}

export type { SyncRunInfo, SyncRun, SyncRunSummary, SyncStats }
