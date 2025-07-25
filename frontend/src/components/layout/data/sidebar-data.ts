import {
  IconHelp,
  IconLayoutDashboard,
  IconPackages,
  IconSettings,
  IconArrowsExchange,
  IconDownload,
} from '@tabler/icons-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  navGroups: [
    {
      title: 'Analytics',
      items: [
        {
          title: 'Cost Dashboard',
          url: '/',
          icon: IconLayoutDashboard,
        },
      ],
    },
    {
      title: 'Data Connections',
      items: [
        {
          title: 'Connect',
          url: '/integrations/connect',
          icon: IconPackages,
        },
        {
          title: 'Sync',
          url: '/integrations/sync',
          icon: IconArrowsExchange,
        },
        {
          title: 'Export',
          url: '/integrations/export',
          icon: IconDownload,
        },
      ],
    },
    {
      title: 'Other',
      items: [
        {
          title: 'Settings',
          icon: IconSettings,
          url: '/settings',
        },
        {
          title: 'Documentation',
          url: 'https://www.narev.ai/docs/',
          icon: IconHelp,
        },
      ],
    },
  ],
}
