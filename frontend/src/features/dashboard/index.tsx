import { TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Tabs, TabsContent } from '@/components/ui/tabs'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { TopNav } from '@/components/layout/top-nav'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { OverviewTab } from './components/tabs/overview-tab'
import { UnitEconomics } from './components/tabs/unit-economics-tab'

const topNav = [
  {
    title: 'Cloud Cost',
    href: '/',
    isActive: true,
    disabled: false,
  },
  {
    title: 'LLM Cost (coming soon)',
    href: 'dashboard/ai',
    isActive: false,
    disabled: true,
  },
]

//
export default function Dashboard() {
  return (
    <>
      {/* ===== Top Heading ===== */}
      <Header>
        <TopNav links={topNav} />
        <div className='ml-auto flex items-center space-x-4'>
          <Search />
          <ThemeSwitch />
        </div>
      </Header>

      {/* ===== Main ===== */}
      <Main>
        <div className='mb-2 flex items-center justify-between space-y-2'>
          <h1 className='text-2xl font-bold tracking-tight'>
            Cloud Cost Dashboard
          </h1>
        </div>
        <Tabs
          orientation='vertical'
          defaultValue='overview'
          className='space-y-4'
        >
          <div className='w-full overflow-x-auto pb-2'>
            <TabsList>
              <TabsTrigger value='overview'>Overview</TabsTrigger>
              <TabsTrigger
                value='unit-economics'
                disabled
                className='text-muted-foreground'
              >
                Unit Economics (coming soon)
              </TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value='overview'>
            <OverviewTab />
          </TabsContent>
          <TabsContent value='unit-economics'>
            <UnitEconomics />
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}
