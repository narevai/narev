import { useEffect, useState } from 'react'
import { Check, ChevronsUpDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalytics } from '@/hooks/use-analytics'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

interface ProviderFilterProps {
  value: string[]
  onChange: (value: string[]) => void
}

export function ProviderFilter({ value, onChange }: ProviderFilterProps) {
  const [open, setOpen] = useState(false)
  const [providers, setProviders] = useState<string[]>([])
  const { getConnectedProviders, loading } = useAnalytics()
  const [hasInitialized, setHasInitialized] = useState(false)

  useEffect(() => {
    const fetchProviders = async () => {
      const response = await getConnectedProviders()
      if (response?.data) {
        setProviders(response.data)
      }
    }
    fetchProviders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const handleProviderToggle = (providerName: string) => {
    const newValue = value.includes(providerName)
      ? value.filter((p) => p !== providerName)
      : [...value, providerName]
    onChange(newValue)
  }

  const handleSelectAll = () => {
    onChange(providers)
  }

  const displayText = () => {
    if (loading) return 'Loading...'
    if (value.length === 0) return 'All Providers'
    if (value.length === providers.length) return 'All Providers'
    return `${value.length} Provider${value.length === 1 ? '' : 's'} Selected`
  }

  const handleClearAll = () => {
    onChange([])
  }

  useEffect(() => {
    if (
      !hasInitialized &&
      !loading &&
      providers.length > 0 &&
      value.length === 0
    ) {
      onChange(providers)
      setHasInitialized(true)
    }
  }, [hasInitialized, loading, providers, value, onChange])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant='outline'
          role='combobox'
          aria-expanded={open}
          className='min-w-[200px] justify-between'
          disabled={loading}
        >
          {displayText()}
          <ChevronsUpDown className='ml-2 h-4 w-4 shrink-0 opacity-50' />
        </Button>
      </PopoverTrigger>
      <PopoverContent className='w-[300px] p-0' align='start'>
        <Command>
          <CommandInput placeholder='Search providers...' />
          <CommandList>
            <CommandEmpty>
              {loading ? 'Loading providers...' : 'No providers found.'}
            </CommandEmpty>
            {!loading && providers.length > 0 && (
              <CommandGroup>
                <div className='flex items-center justify-between border-b px-2 py-1.5 text-sm'>
                  <span className='font-medium'>
                    Providers ({providers.length})
                  </span>
                  <div className='flex gap-2'>
                    <Button
                      variant='ghost'
                      size='sm'
                      className='hover:text-primary h-auto p-0 text-xs'
                      onClick={handleSelectAll}
                    >
                      Select All
                    </Button>
                    <Button
                      variant='ghost'
                      size='sm'
                      className='hover:text-primary h-auto p-0 text-xs'
                      onClick={handleClearAll}
                    >
                      Clear
                    </Button>
                  </div>
                </div>
                {providers.map((providerName) => (
                  <CommandItem
                    key={providerName}
                    onSelect={() => handleProviderToggle(providerName)}
                    className='flex cursor-pointer items-center space-x-2'
                  >
                    <Checkbox
                      checked={value.includes(providerName)}
                      onChange={() => handleProviderToggle(providerName)}
                    />
                    <div className='flex flex-1 flex-col'>
                      <span className='text-sm'>{providerName}</span>
                    </div>
                    <Check
                      className={cn(
                        'h-4 w-4',
                        value.includes(providerName)
                          ? 'opacity-100'
                          : 'opacity-0'
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
