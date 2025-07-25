import type { CreateProviderRequest, Provider } from '@/lib/api'
import { ProviderDialog } from './provider-dialog'

interface ProviderDialogManagerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  provider: Provider | null
  onConnect: (data: CreateProviderRequest) => Promise<void>
}

export function ProviderDialogManager(props: ProviderDialogManagerProps) {
  return <ProviderDialog {...props} />
}
