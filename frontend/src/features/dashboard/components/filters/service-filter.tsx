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

interface ServiceFilterProps {
  value: string[]
  onChange: (value: string[]) => void
}

export function ServiceFilter({ value, onChange }: ServiceFilterProps) {
  const [open, setOpen] = useState(false)
  const [services, setServices] = useState<string[]>([])
  const { getAvailableServices, loading } = useAnalytics()
  const [hasInitialized, setHasInitialized] = useState(false)

  useEffect(() => {
    const fetchServices = async () => {
      const response = await getAvailableServices()
      if (response?.data) {
        // response.data is an array of { service_name, provider_name, ... }
        const uniqueServices = Array.from(
          new Set(response.data.map((s) => s.service_name))
        )
        setServices(uniqueServices)
      }
    }
    fetchServices()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleServiceToggle = (serviceName: string) => {
    const newValue = value.includes(serviceName)
      ? value.filter((s) => s !== serviceName)
      : [...value, serviceName]
    onChange(newValue)
  }

  const handleSelectAll = () => {
    onChange(services)
  }

  const displayText = () => {
    if (loading) return 'Loading...'
    if (value.length === 0) return 'All Services'
    if (value.length === services.length) return 'All Services'
    return `${value.length} Service${value.length === 1 ? '' : 's'} Selected`
  }

  const handleClearAll = () => {
    onChange([])
  }

  useEffect(() => {
    if (
      !hasInitialized &&
      !loading &&
      services.length > 0 &&
      value.length === 0
    ) {
      onChange(services)
      setHasInitialized(true)
    }
  }, [hasInitialized, loading, services, value, onChange])

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
          <CommandInput placeholder='Search services...' />
          <CommandList>
            <CommandEmpty>
              {loading ? 'Loading services...' : 'No services found.'}
            </CommandEmpty>
            {!loading && services.length > 0 && (
              <CommandGroup>
                <div className='flex items-center justify-between border-b px-2 py-1.5 text-sm'>
                  <span className='font-medium'>
                    Services ({services.length})
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
                {services.map((serviceName) => (
                  <CommandItem
                    key={serviceName}
                    onSelect={() => handleServiceToggle(serviceName)}
                    className='flex cursor-pointer items-center space-x-2'
                  >
                    <Checkbox
                      checked={value.includes(serviceName)}
                      onChange={() => handleServiceToggle(serviceName)}
                    />
                    <div className='flex flex-1 flex-col'>
                      <span className='text-sm'>{serviceName}</span>
                    </div>
                    <Check
                      className={cn(
                        'h-4 w-4',
                        value.includes(serviceName)
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
