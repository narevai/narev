import { useState, useEffect } from 'react'
import {
  IconAdjustmentsHorizontal,
  IconSortAscendingLetters,
  IconSortDescendingLetters,
} from '@tabler/icons-react'
import { toast } from 'sonner'
import type { CreateProviderRequest, Provider } from '@/lib/api'
import { useConfig } from '@/hooks/use-config'
import { useProviders } from '@/hooks/use-providers'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProviderDialogManager } from '@/components/provider-dialogs/provider-dialog-manager'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

const appText = new Map<string, string>([
  ['all', 'All Apps'],
  ['connected', 'Connected'],
  ['notConnected', 'Not Connected'],
])

export default function Apps() {
  const [sort, setSort] = useState<'ascending' | 'descending'>('ascending')
  const [appType, setAppType] = useState<'all' | 'connected' | 'notConnected'>(
    'all'
  )
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedApp, setSelectedApp] = useState<Provider | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  const { providers: apps, loading, createProvider } = useProviders()
  const { getConfig } = useConfig()
  const [demoMode, setDemoMode] = useState<boolean>(false)

  useEffect(() => {
    ;(async () => {
      const config = await getConfig()
      const settings = (config as unknown as { settings?: { demo?: unknown } })
        ?.settings
      const demo = settings?.demo
      if (typeof demo === 'boolean') {
        setDemoMode(demo)
      }
    })()
  }, [getConfig])

  const filteredApps = apps
    .sort((a, b) =>
      sort === 'ascending'
        ? a.name.localeCompare(b.name)
        : b.name.localeCompare(a.name)
    )
    .filter((app) =>
      appType === 'connected'
        ? app.connected
        : appType === 'notConnected'
          ? !app.connected
          : true
    )
    .filter((app) => app.name.toLowerCase().includes(searchTerm.toLowerCase()))

  const handleConnectClick = (app: Provider) => {
    if (!app.connected) {
      setSelectedApp(app)
      setDialogOpen(true)
    }
  }

  const handleConnect = async (data: CreateProviderRequest) => {
    try {
      await createProvider(data)
      toast.success('Provider connected successfully!')
      setDialogOpen(false)
      setSelectedApp(null)
    } catch (_) {
      // Error toast is handled in the createProvider function
    }
  }

  const handleDialogClose = (open: boolean) => {
    setDialogOpen(open)
    if (!open) {
      setSelectedApp(null)
    }
  }

  return (
    <>
      <Header>
        <Search />
        <div className='ml-auto flex items-center gap-4'>
          <ThemeSwitch />
        </div>
      </Header>

      <Main fixed>
        {demoMode && (
          <Alert className='mb-6 border-orange-200 bg-orange-50 text-orange-800 dark:border-orange-800 dark:bg-orange-950 dark:text-orange-200'>
            <AlertDescription>
              You're viewing demo data. To connect real providers, please
              disable demo mode in your configuration and follow the{' '}
              <a
                href='https://narev.ai/docs'
                className='underline hover:no-underline'
              >
                setup documentation
              </a>
            </AlertDescription>
          </Alert>
        )}
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>
            Provider Integrations
          </h1>
          <p className='text-muted-foreground'>
            Connect your billing providers to start analyzing costs and usage
          </p>
        </div>

        <div className='my-4 flex items-end justify-between sm:my-0 sm:items-center'>
          <div className='flex flex-col gap-4 sm:my-4 sm:flex-row'>
            <Input
              placeholder='Filter providers...'
              className='h-9 w-40 lg:w-[250px]'
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Select
              value={appType}
              onValueChange={(value: 'all' | 'connected' | 'notConnected') =>
                setAppType(value)
              }
            >
              <SelectTrigger className='w-36'>
                <SelectValue>{appText.get(appType)}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='all'>All Providers</SelectItem>
                <SelectItem value='connected'>Connected</SelectItem>
                <SelectItem value='notConnected'>Not Connected</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Select
            value={sort}
            onValueChange={(value: 'ascending' | 'descending') =>
              setSort(value)
            }
          >
            <SelectTrigger className='w-16'>
              <SelectValue>
                <IconAdjustmentsHorizontal size={18} />
              </SelectValue>
            </SelectTrigger>
            <SelectContent align='end'>
              <SelectItem value='ascending'>
                <div className='flex items-center gap-4'>
                  <IconSortAscendingLetters size={16} />
                  <span>Ascending</span>
                </div>
              </SelectItem>
              <SelectItem value='descending'>
                <div className='flex items-center gap-4'>
                  <IconSortDescendingLetters size={16} />
                  <span>Descending</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Separator className='shadow-sm' />

        {loading ? (
          <div className='grid gap-4 pt-4 md:grid-cols-2 lg:grid-cols-3'>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className='rounded-lg border p-4'>
                <div className='mb-8 flex items-center justify-between'>
                  <Skeleton className='h-10 w-10 rounded-lg' />
                  <Skeleton className='h-8 w-20' />
                </div>
                <div>
                  <Skeleton className='mb-2 h-5 w-32' />
                  <Skeleton className='h-4 w-full' />
                  <Skeleton className='mt-1 h-4 w-3/4' />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <ul className='faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 md:grid-cols-2 lg:grid-cols-3'>
            {filteredApps.map((app) => (
              <li
                key={`${app.provider_type}-${app.name}`}
                className='rounded-lg border p-4 transition-shadow hover:shadow-md'
              >
                <div className='mb-8 flex items-center justify-between'>
                  <div className='bg-muted flex size-10 items-center justify-center rounded-lg p-2'>
                    {app.logo}
                  </div>
                  <Button
                    variant='outline'
                    size='sm'
                    disabled={demoMode && !app.connected}
                    className={`${app.connected ? 'border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900' : ''}`}
                    onClick={() => handleConnectClick(app)}
                  >
                    {app.connected ? 'Connected' : 'Connect'}
                  </Button>
                </div>
                <div>
                  <h2 className='mb-1 font-semibold'>{app.name}</h2>
                  <p className='line-clamp-2 text-gray-500'>{app.desc}</p>
                </div>
              </li>
            ))}
          </ul>
        )}

        {!loading && filteredApps.length === 0 && (
          <div className='py-12 text-center'>
            <p className='text-muted-foreground'>
              {searchTerm || appType !== 'all'
                ? 'No providers match your filters'
                : 'No providers available'}
            </p>
          </div>
        )}
      </Main>

      <ProviderDialogManager
        open={dialogOpen}
        onOpenChange={handleDialogClose}
        provider={selectedApp}
        onConnect={handleConnect}
      />
    </>
  )
}
