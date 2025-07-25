import { createFileRoute } from '@tanstack/react-router'
import Tasks from '@/features/sync'

export const Route = createFileRoute('/_authenticated/integrations/sync/')({
  component: Tasks,
})
