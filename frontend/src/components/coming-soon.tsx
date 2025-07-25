import { IconPlanet, IconBrandGithub } from '@tabler/icons-react'

export default function ComingSoon() {
  return (
    <div className='h-svh'>
      <div className='m-auto flex h-full w-full flex-col items-center justify-center gap-4'>
        <IconPlanet size={72} />
        <h1 className='text-4xl leading-tight font-bold'>Coming Soon 👀</h1>
        <p className='text-muted-foreground text-center'>
          This page has not been created yet. <br />
          Stay tuned though!
        </p>

        <a
          href='https://github.com/narevai/narev'
          target='_blank'
          rel='noopener noreferrer'
          className='bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-md px-4 py-2 transition-colors'
        >
          <IconBrandGithub size={18} />
          View on GitHub
        </a>
      </div>
    </div>
  )
}
