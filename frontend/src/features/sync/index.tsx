import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { columns } from './components/columns'
import { DataTable } from './components/data-table'
import { SyncsDialogs } from './components/syncs-dialogs'
import { SyncsPrimaryButtons } from './components/syncs-primary-buttons'
import SyncsProvider from './context/syncs-context'

export default function Syncs() {
  return (
    <SyncsProvider>
      <Header fixed>
        <Search />
        <div className='ml-auto flex items-center space-x-4'>
          <ThemeSwitch />
        </div>
      </Header>

      <Main>
        <div className='mb-2 flex flex-wrap items-center justify-between space-y-2 gap-x-4'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Sync Runs</h2>
            <p className='text-muted-foreground'>
              Monitor and manage your data synchronization runs.
            </p>
          </div>
          <SyncsPrimaryButtons />
        </div>
        <div className='-mx-4 flex-1 overflow-auto px-4 py-1 lg:flex-row lg:space-y-0 lg:space-x-12'>
          <DataTable columns={columns} />
        </div>
      </Main>

      <SyncsDialogs />
    </SyncsProvider>
  )
}
