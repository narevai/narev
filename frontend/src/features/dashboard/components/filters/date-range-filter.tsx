// components/filters/date-range-filter.tsx
import { useState } from 'react'
import { Calendar as CalendarIcon } from 'lucide-react'
import { DateRange } from 'react-day-picker'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { DateRange as DateRangeType } from './types'

interface DateRangeFilterProps {
  value: DateRangeType
  onChange: (range: DateRangeType) => void
}

export function DateRangeFilter({ value, onChange }: DateRangeFilterProps) {
  const [selected, setSelected] = useState<DateRange | undefined>({
    from: new Date(value.start_date),
    to: new Date(value.end_date),
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  const handleSelect = (range: DateRange | undefined) => {
    setSelected(range)

    if (range?.from && range?.to) {
      onChange({
        start_date: range.from.toISOString(),
        end_date: range.to.toISOString(),
      })
    }
  }

  const handleDayClick = (day: Date) => {
    // If we have a complete range and click on any selected date, start fresh
    if (selected?.from && selected?.to) {
      setSelected({ from: day, to: undefined })
    }
  }

  // Get previous month for default view
  const getPreviousMonth = () => {
    const today = new Date()
    return new Date(today.getFullYear(), today.getMonth() - 1, 1)
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant='outline'>
          <CalendarIcon className='mr-2 h-4 w-4' />
          {formatDate(value.start_date)} - {formatDate(value.end_date)}
        </Button>
      </PopoverTrigger>
      <PopoverContent className='w-auto p-0' align='start'>
        <Calendar
          mode='range'
          numberOfMonths={2}
          selected={selected}
          onSelect={handleSelect}
          onDayClick={handleDayClick}
          defaultMonth={getPreviousMonth()}
        />
      </PopoverContent>
    </Popover>
  )
}
