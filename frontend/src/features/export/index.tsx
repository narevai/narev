import { useState } from 'react'
import {
  IconDownload,
  IconFileTypeCsv,
  IconFileTypeXls,
  IconSortAscendingLetters,
  IconSortDescendingLetters,
} from '@tabler/icons-react'
import type { ExportBillingParams } from '@/lib/api'
import { useExport } from '@/hooks/use-export'
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
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

type ExportFormat = {
  id: string
  name: string
  description: string
  format: 'csv' | 'xlsx'
  icon: React.ReactNode
}

const exportFormats: ExportFormat[] = [
  {
    id: 'csv',
    name: 'CSV Export',
    description: 'Export billing data in CSV format for spreadsheet analysis',
    format: 'csv',
    icon: <IconFileTypeCsv size={24} />,
  },
  {
    id: 'xlsx',
    name: 'Excel Export',
    description: 'Export billing data in Excel format with advanced formatting',
    format: 'xlsx',
    icon: <IconFileTypeXls size={24} />,
  },
]

export default function Export() {
  const [sort, setSort] = useState<'ascending' | 'descending'>('ascending')
  const [searchTerm, setSearchTerm] = useState('')

  const { loading, exportAndDownloadBilling } = useExport()

  const filteredFormats = exportFormats
    .sort((a, b) =>
      sort === 'ascending'
        ? a.name.localeCompare(b.name)
        : b.name.localeCompare(a.name)
    )
    .filter(
      (format) =>
        format.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        format.description.toLowerCase().includes(searchTerm.toLowerCase())
    )

  const handleExport = async (format: ExportFormat) => {
    try {
      const params: ExportBillingParams = { format: format.format }
      const filename = `billing-export-${new Date().toISOString().split('T')[0]}.${format.format}`
      await exportAndDownloadBilling(params, filename)
    } catch (_) {
      // Error handling is done in the hook
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
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Export Data</h1>
          <p className='text-muted-foreground'>
            Download your billing data in various formats for analysis and
            reporting
          </p>
        </div>

        <div className='my-4 flex items-end justify-between sm:my-0 sm:items-center'>
          <div className='flex flex-col gap-4 sm:my-4 sm:flex-row'>
            <Input
              placeholder='Filter export formats...'
              className='h-9 w-40 lg:w-[250px]'
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <Select
            value={sort}
            onValueChange={(value: 'ascending' | 'descending') =>
              setSort(value)
            }
          >
            <SelectTrigger className='w-16'>
              <SelectValue>
                <IconSortAscendingLetters size={18} />
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
            {Array.from({ length: 2 }).map((_, i) => (
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
            {filteredFormats.map((format) => (
              <li
                key={format.id}
                className='rounded-lg border p-4 transition-shadow hover:shadow-md'
              >
                <div className='mb-8 flex items-center justify-between'>
                  <div className='bg-muted flex size-10 items-center justify-center rounded-lg p-2'>
                    {format.icon}
                  </div>
                  <Button
                    variant='outline'
                    size='sm'
                    disabled={loading}
                    onClick={() => handleExport(format)}
                    className='gap-2'
                  >
                    <IconDownload size={14} />
                    Export
                  </Button>
                </div>
                <div>
                  <h2 className='mb-1 font-semibold'>{format.name}</h2>
                  <p className='line-clamp-2 text-gray-500'>
                    {format.description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}

        {!loading && filteredFormats.length === 0 && (
          <div className='py-12 text-center'>
            <p className='text-muted-foreground'>
              {searchTerm
                ? 'No export formats match your search'
                : 'No export formats available'}
            </p>
          </div>
        )}
      </Main>
    </>
  )
}
