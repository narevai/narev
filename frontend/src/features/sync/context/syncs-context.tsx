import React, { useState } from 'react'
import useDialogState from '@/hooks/use-dialog-state'
import { useProviders } from '@/hooks/use-providers'
import { useSyncs as useSyncsHook } from '@/hooks/use-syncs'
import type { SyncRunInfo } from '@/hooks/use-syncs'

type SyncsDialogType = 'trigger' | 'details' | 'cancel' | 'retry'

interface SyncsContextType {
  // Dialog state
  open: SyncsDialogType | null
  setOpen: (str: SyncsDialogType | null) => void
  currentRow: SyncRunInfo | null
  setCurrentRow: React.Dispatch<React.SetStateAction<SyncRunInfo | null>>

  // Sync data and actions from the hook
  syncStatus: ReturnType<typeof useSyncsHook>['syncStatus']
  syncRuns: ReturnType<typeof useSyncsHook>['syncRuns']
  syncStats: ReturnType<typeof useSyncsHook>['syncStats']
  recentRuns: ReturnType<typeof useSyncsHook>['recentRuns']
  summary: ReturnType<typeof useSyncsHook>['summary']
  loading: ReturnType<typeof useSyncsHook>['loading']
  error: ReturnType<typeof useSyncsHook>['error']

  // Provider data
  providerInstances: ReturnType<typeof useProviders>['providerInstances']

  // Actions
  triggerSync: ReturnType<typeof useSyncsHook>['triggerSync']
  getSyncRun: ReturnType<typeof useSyncsHook>['getSyncRun']
  cancelSyncRun: ReturnType<typeof useSyncsHook>['cancelSyncRun']
  retrySyncRun: ReturnType<typeof useSyncsHook>['retrySyncRun']
  getPipelineGraph: ReturnType<typeof useSyncsHook>['getPipelineGraph']
  checkSyncHealth: ReturnType<typeof useSyncsHook>['checkSyncHealth']
  refreshSyncData: ReturnType<typeof useSyncsHook>['refreshSyncData']
}

const SyncsContext = React.createContext<SyncsContextType | null>(null)

interface Props {
  children: React.ReactNode
}

export default function SyncsProvider({ children }: Props) {
  const [open, setOpen] = useDialogState<SyncsDialogType>(null)
  const [currentRow, setCurrentRow] = useState<SyncRunInfo | null>(null)

  // Get all sync data and actions from the hook
  const syncHookData = useSyncsHook()
  const { providerInstances } = useProviders()

  return (
    <SyncsContext.Provider
      value={{
        open,
        setOpen,
        currentRow,
        setCurrentRow,
        providerInstances,
        ...syncHookData,
      }}
    >
      {children}
    </SyncsContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useSyncs = () => {
  const syncsContext = React.useContext(SyncsContext)

  if (!syncsContext) {
    throw new Error('useSyncs has to be used within <SyncsContext>')
  }

  return syncsContext
}
