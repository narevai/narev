// hooks/use-providers.ts
import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  CreateProviderRequest,
  DeleteProviderResponse,
  Provider,
  ProviderInstance,
  ProviderTypeInfo,
  providers,
  ProviderTypesResponse,
  ListProvidersResponse,
  UpdateProviderRequest,
} from '@/lib/api'
import { PROVIDER_ICONS } from '@/lib/providerIcons'

export function useProviders() {
  const [providerTypes, setProviderTypes] = useState<ProviderTypeInfo[]>([])
  const [providerInstances, setProviderInstances] = useState<
    ProviderInstance[]
  >([])
  const [providersList, setProvidersList] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProviderTypes = async () => {
    try {
      const { data, error } = await providers.getTypes()
      if (error) throw new Error('Failed to fetch provider types')

      const typedData = data as ProviderTypesResponse
      return typedData.providers || []
    } catch (err) {
      toast.error('Failed to fetch provider types', {
        description: 'Unable to load available provider configurations.',
      })
      throw err
    }
  }

  const fetchProviderInstances = async () => {
    try {
      const { data, error } = await providers.list()
      if (error) throw new Error('Failed to fetch provider instances')

      return (data as ListProvidersResponse) || []
    } catch (err) {
      toast.error('Failed to fetch provider instances', {
        description: 'Unable to load your configured providers.',
      })
      throw err
    }
  }

  const fetchAllProviders = async () => {
    try {
      setLoading(true)
      setError(null)

      const [types, instances] = await Promise.all([
        fetchProviderTypes(),
        fetchProviderInstances(),
      ])

      setProviderTypes(types)
      setProviderInstances(instances)

      // Create a map of provider instances by type for quick lookup
      const instancesByType = new Map<string, ProviderInstance[]>()
      instances.forEach((instance) => {
        const existing = instancesByType.get(instance.provider_type) || []
        instancesByType.set(instance.provider_type, [...existing, instance])
      })

      // Map provider types to the display format, enriching with instance data
      const mappedProviders = types.map((providerInfo): Provider => {
        const typeInstances =
          instancesByType.get(providerInfo.provider_type) || []
        const hasConnectedInstance = typeInstances.some(
          (instance) => instance.is_active
        )

        return {
          // Basic display info (for backward compatibility)
          name: providerInfo.display_name,
          logo:
            PROVIDER_ICONS[
              providerInfo.provider_type as keyof typeof PROVIDER_ICONS
            ] || PROVIDER_ICONS.default,
          connected: hasConnectedInstance,
          desc: providerInfo.description,

          // Full configuration data from ProviderTypeInfo
          provider_type: providerInfo.provider_type,
          display_name: providerInfo.display_name,
          description: providerInfo.description,
          supported_auth_methods: providerInfo.supported_auth_methods,
          default_auth_method: providerInfo.default_auth_method,
          required_config: providerInfo.required_config,
          optional_config: providerInfo.optional_config,
          configuration_schema: providerInfo.configuration_schema,
          capabilities: providerInfo.capabilities,
          status: providerInfo.status,
          version: providerInfo.version,
        }
      })

      setProvidersList(mappedProviders)
    } catch (_) {
      const errorMessage = 'Failed to load providers'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Please check your connection and try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllProviders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const createProvider = async (data: CreateProviderRequest) => {
    try {
      const { data: result, error } = await providers.create(data)
      if (error) throw new Error('Failed to create provider')

      // Refresh the provider instances after creation
      await fetchAllProviders()

      toast.success('Provider created successfully')
      return result
    } catch (error) {
      toast.error('Failed to create provider', {
        description: 'Unable to create the provider configuration.',
      })
      throw error
    }
  }

  const updateProvider = async (id: string, data: UpdateProviderRequest) => {
    try {
      const { data: result, error } = await providers.update(id, data)
      if (error) throw new Error('Failed to update provider')

      // Refresh the provider instances after update
      await fetchAllProviders()

      toast.success('Provider updated successfully')
      return result
    } catch (error) {
      toast.error('Failed to update provider', {
        description: 'Unable to save changes to the provider.',
      })
      throw error
    }
  }

  const deleteProvider = async (id: string) => {
    try {
      const { data, error } = await providers.delete(id)
      if (error) throw new Error('Failed to delete provider')

      // Refresh the provider instances after deletion
      await fetchAllProviders()

      toast.success('Provider deleted successfully')
      return data as DeleteProviderResponse
    } catch (error) {
      toast.error('Failed to delete provider', {
        description: 'Unable to remove the provider configuration.',
      })
      throw error
    }
  }

  const testProvider = async (id: string) => {
    try {
      const { data, error } = await providers.test(id)
      if (error) throw new Error('Failed to test provider')

      toast.success('Provider test completed')
      return data
    } catch (error) {
      toast.error('Failed to test provider', {
        description: 'Unable to verify provider connection.',
      })
      throw error
    }
  }

  const getProvider = async (id: string) => {
    try {
      const { data, error } = await providers.get(id)
      if (error) throw new Error('Failed to get provider')
      return data
    } catch (error) {
      toast.error('Failed to get provider', {
        description: 'Unable to load provider details.',
      })
      throw error
    }
  }

  const getAuthFields = async (providerType: string, authMethod?: string) => {
    try {
      const { data, error } = await providers.getAuthFields(
        providerType,
        authMethod
      )
      if (error) throw new Error('Failed to get auth fields')
      return data
    } catch (error) {
      toast.error('Failed to get auth fields', {
        description: 'Unable to load authentication configuration options.',
      })
      throw error
    }
  }

  const refreshProviders = () => {
    return fetchAllProviders()
  }

  return {
    // Main provider list (for backward compatibility)
    providers: providersList,

    // Separate access to types and instances
    providerTypes,
    providerInstances,

    // State
    loading,
    error,

    // Actions
    createProvider,
    updateProvider,
    deleteProvider,
    testProvider,
    getProvider,
    getAuthFields,
    refreshProviders,
  }
}
