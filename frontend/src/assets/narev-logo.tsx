import { SVGProps } from 'react'
import { cn } from '@/lib/utils'

export function NarevLogo({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      role='img'
      viewBox='0 0 375 375'
      xmlns='http://www.w3.org/2000/svg'
      id='narev'
      height='24'
      width='24'
      className={cn(
        '[&>path]:fill-foreground [&>path]:stroke-foreground',
        className
      )}
      {...props}
    >
      <title>Narev</title>
      <g transform='translate(169.786252, 199.675084)'>
        <path
          d='M 3.21875 0 L 3.21875 -27.484375 L 12.6875 -27.484375 L 12.6875 -24.578125 L 12.796875 -24.578125 C 15.265625 -27.046875 17.890625 -28.28125 20.671875 -28.28125 C 22.023438 -28.28125 23.375 -28.097656 24.71875 -27.734375 C 26.0625 -27.378906 27.347656 -26.828125 28.578125 -26.078125 C 29.804688 -25.328125 30.804688 -24.265625 31.578125 -22.890625 C 32.347656 -21.515625 32.734375 -19.921875 32.734375 -18.109375 L 32.734375 0 L 23.25 0 L 23.25 -15.53125 C 23.25 -16.957031 22.789062 -18.207031 21.875 -19.28125 C 20.96875 -20.351562 19.78125 -20.890625 18.3125 -20.890625 C 16.882812 -20.890625 15.585938 -20.332031 14.421875 -19.21875 C 13.265625 -18.113281 12.6875 -16.882812 12.6875 -15.53125 L 12.6875 0 Z M 3.21875 0'
          strokeWidth='1'
        />
      </g>
      <path
        d='M 0.00082329 5.000385 L 84.433175 5.000385'
        transform='matrix(0.746252,0,0,0.746252,146.675167,220.57314)'
        strokeWidth='10'
        strokeLinecap='butt'
        strokeLinejoin='miter'
        fill='none'
      />
      <path
        d='M 0.00137009 5.000689 L 82.464973 5.000689'
        transform='matrix(0,0.745878,-0.745878,0,154.171312,163.979447)'
        strokeWidth='10'
        strokeLinecap='butt'
        strokeLinejoin='miter'
        fill='none'
      />
      <path
        d='M 0.00218394 5.000352 L 84.434536 5.000352'
        transform='matrix(-0.746252,0,0,-0.746252,228.153974,154.426835)'
        strokeWidth='10'
        strokeLinecap='butt'
        strokeLinejoin='miter'
        fill='none'
      />
      <path
        d='M 0.00133707 4.998347 L 82.46494 4.998347'
        transform='matrix(0,-0.745878,0.745878,0,220.65856,211.020529)'
        strokeWidth='10'
        strokeLinecap='butt'
        strokeLinejoin='miter'
        fill='none'
      />
    </svg>
  )
}
