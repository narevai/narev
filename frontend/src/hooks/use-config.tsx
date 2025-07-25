import { useState } from 'react'
import { toast } from 'sonner'
import { config, GetConfigResponse } from '@/lib/api'

export function useConfig() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getConfig = async (): Promise<GetConfigResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await config.get()
      if (error) throw new Error('Failed to fetch config')

      return data as GetConfigResponse
    } catch (_) {
      const errorMessage = 'Failed to load config'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to load application configuration.',
      })
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    error,
    getConfig,
  }
}

export default useConfig
