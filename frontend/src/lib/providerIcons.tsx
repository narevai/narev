import {
  IconBrandOpenai,
  IconBrandAzure,
  IconBrandAws,
  IconBrandGoogle,
  IconServer,
} from '@tabler/icons-react'

export const PROVIDER_ICONS = {
  openai: <IconBrandOpenai />,
  gcp: <IconBrandGoogle />,
  aws: <IconBrandAws />,
  azure: <IconBrandAzure />,

  // Fallback for unknown providers
  default: <IconServer />,
} as const
