import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useProviders } from '@/hooks/use-providers'
import type { SyncRunInfo } from '@/hooks/use-syncs'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { SelectDropdown } from '@/components/select-dropdown'
import { DateRangeFilter } from '@/features/dashboard/components/filters/date-range-filter'
import type { DateRange } from '@/features/dashboard/components/filters/types'
import { useSyncs } from '../context/syncs-context'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentRow?: SyncRunInfo
}

const formSchema = z.object({
  provider_id: z.string().optional(),
  date_range: z.object({
    start_date: z.string(),
    end_date: z.string(),
  }),
})
type SyncTriggerForm = z.infer<typeof formSchema>

export function SyncsMutateDrawer({ open, onOpenChange, currentRow }: Props) {
  const isViewingDetails = !!currentRow
  const { triggerSync } = useSyncs()
  const { providerInstances } = useProviders()

  // Calculate default date range (last 30 days)
  const getDefaultDateRange = (): DateRange => {
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)

    return {
      start_date: thirtyDaysAgo.toISOString(),
      end_date: today.toISOString(),
    }
  }

  const form = useForm<SyncTriggerForm>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      provider_id: '',
      date_range: getDefaultDateRange(),
    },
  })

  const onSubmit = async (data: SyncTriggerForm) => {
    try {
      // Convert form data to API format
      const syncRequest = {
        provider_id: data.provider_id || undefined,
        start_date: data.date_range.start_date,
        end_date: data.date_range.end_date,
        days_back: null, // Remove days_back from API request
      }

      await triggerSync(syncRequest)
      onOpenChange(false)
      form.reset()
    } catch (_) {
      // Error handling is done in the hook with toast notifications
    }
  }

  if (isViewingDetails) {
    // Read-only view for sync run details
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className='flex flex-col'>
          <SheetHeader className='text-left'>
            <SheetTitle>Sync Run Details</SheetTitle>
            <SheetDescription>
              Detailed information about sync run {currentRow.id}
            </SheetDescription>
          </SheetHeader>

          <div className='flex-1 space-y-4 px-4'>
            <div className='grid grid-cols-2 gap-4'>
              <div>
                <label className='text-sm font-medium'>Status</label>
                <p className='text-muted-foreground text-sm'>
                  {currentRow.status}
                </p>
              </div>
              <div>
                <label className='text-sm font-medium'>Provider</label>
                <p className='text-muted-foreground text-sm'>
                  {currentRow.provider_name || 'Unknown'}
                </p>
              </div>
              <div>
                <label className='text-sm font-medium'>Started At</label>
                <p className='text-muted-foreground text-sm'>
                  {new Date(currentRow.started_at).toLocaleString()}
                </p>
              </div>
              <div>
                <label className='text-sm font-medium'>Duration</label>
                <p className='text-muted-foreground text-sm'>
                  {currentRow.duration_seconds
                    ? `${currentRow.duration_seconds}s`
                    : 'N/A'}
                </p>
              </div>
              <div>
                <label className='text-sm font-medium'>Records Processed</label>
                <p className='text-muted-foreground text-sm'>
                  {currentRow.records_processed || 'N/A'}
                </p>
              </div>
              <div>
                <label className='text-sm font-medium'>Records Created</label>
                <p className='text-muted-foreground text-sm'>
                  {currentRow.records_created || 'N/A'}
                </p>
              </div>
            </div>

            {currentRow.error_message && (
              <div>
                <label className='text-destructive text-sm font-medium'>
                  Error Message
                </label>
                <p className='text-muted-foreground bg-destructive/10 rounded p-2 text-sm'>
                  {currentRow.error_message}
                </p>
              </div>
            )}
          </div>

          <SheetFooter className='gap-2'>
            <SheetClose asChild>
              <Button variant='outline'>Close</Button>
            </SheetClose>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    )
  }

  // Form for triggering new sync
  return (
    <Sheet
      open={open}
      onOpenChange={(v) => {
        onOpenChange(v)
        form.reset({
          provider_id: '',
          date_range: getDefaultDateRange(),
        })
      }}
    >
      <SheetContent className='flex flex-col'>
        <SheetHeader className='text-left'>
          <SheetTitle>Trigger Sync</SheetTitle>
          <SheetDescription>
            Start a new data synchronization. Leave fields empty to sync all
            providers with default settings.
          </SheetDescription>
        </SheetHeader>
        <Form {...form}>
          <form
            id='sync-trigger-form'
            onSubmit={form.handleSubmit(onSubmit)}
            className='flex-1 space-y-5 px-4'
          >
            <FormField
              control={form.control}
              name='provider_id'
              render={({ field }) => (
                <FormItem className='space-y-1'>
                  <FormLabel>Provider (Optional)</FormLabel>
                  <SelectDropdown
                    defaultValue={field.value}
                    onValueChange={field.onChange}
                    placeholder='Select provider (all if empty)'
                    items={providerInstances.map((provider) => ({
                      label: provider.display_name || provider.provider_type,
                      value: provider.id,
                    }))}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name='date_range'
              render={({ field }) => (
                <FormItem className='space-y-1'>
                  <FormLabel>Date Range</FormLabel>
                  <DateRangeFilter
                    value={field.value}
                    onChange={field.onChange}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>
        <SheetFooter className='gap-2'>
          <SheetClose asChild>
            <Button variant='outline'>Cancel</Button>
          </SheetClose>
          <Button form='sync-trigger-form' type='submit'>
            Trigger Sync
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
