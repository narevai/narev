import { createFileRoute } from '@tanstack/react-router'
import Export from '@/features/export'

export const Route = createFileRoute('/_authenticated/integrations/export/')({
  component: Export,
})
