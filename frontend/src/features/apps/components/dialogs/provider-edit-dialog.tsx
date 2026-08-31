import { useState, useEffect } from 'react'
import type {
  AuthField,
  AuthMethod,
  Provider,
  ProviderInstance,
  StandardField,
  UpdateProviderRequest,
} from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'

const MASK_PLACEHOLDER = '••••••••'

interface ProviderEditDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  provider: Provider | null
  providerInstance: ProviderInstance | null
  onUpdate: (id: string, data: UpdateProviderRequest) => Promise<void>
}

export function ProviderEditDialog({
  open,
  onOpenChange,
  provider,
  providerInstance,
  onUpdate,
}: ProviderEditDialogProps) {
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [selectedAuthMethod, setSelectedAuthMethod] = useState<string>('')
  const [maskedFields, setMaskedFields] = useState<Set<string>>(new Set())

  // Initialize form data when provider instance changes
  useEffect(() => {
    if (!providerInstance || !provider) return

    const initialData: Record<string, string> = {}
    const masked = new Set<string>()

    // Set basic fields
    if (providerInstance.name) {
      initialData.name = providerInstance.name
    }
    if (providerInstance.display_name) {
      initialData.display_name = providerInstance.display_name
    }
    if (providerInstance.api_endpoint) {
      initialData.api_endpoint = providerInstance.api_endpoint
    }

    // Set auth method - server doesn't return auth_config for security
    setSelectedAuthMethod(provider.default_auth_method)

    // Get the selected auth method configuration
    const authMethodConfig = provider.supported_auth_methods.find(
      (m) => m.method === provider.default_auth_method
    )

    // Set placeholders for sensitive auth fields so users know they can update them
    if (authMethodConfig?.fields) {
      Object.entries(authMethodConfig.fields).forEach(
        ([fieldName, field]: [string, unknown]) => {
          const typedField = field as AuthField

          if (typedField.type === 'group' && typedField.fields) {
            // Handle grouped fields (like AWS)
            Object.entries(typedField.fields).forEach(
              ([subFieldName, subField]: [string, unknown]) => {
                const subTypedField = subField as AuthField
                const fieldKey = `auth_${subFieldName}`

                // Mask sensitive fields (password, key, secret, token)
                if (
                  subTypedField.type === 'password' ||
                  subFieldName.toLowerCase().includes('key') ||
                  subFieldName.toLowerCase().includes('secret') ||
                  subFieldName.toLowerCase().includes('token') ||
                  subFieldName.toLowerCase().includes('password') ||
                  subFieldName.toLowerCase().includes('credential')
                ) {
                  initialData[fieldKey] = MASK_PLACEHOLDER
                  masked.add(fieldKey)
                }
              }
            )
          } else {
            // Handle direct fields
            const fieldKey = `auth_${fieldName}`

            // Mask sensitive fields (password, key, secret, token, or json_upload)
            if (
              typedField.type === 'password' ||
              typedField.type === 'json_upload' ||
              fieldName.toLowerCase().includes('key') ||
              fieldName.toLowerCase().includes('secret') ||
              fieldName.toLowerCase().includes('token') ||
              fieldName.toLowerCase().includes('password') ||
              fieldName.toLowerCase().includes('credential')
            ) {
              initialData[fieldKey] = MASK_PLACEHOLDER
              masked.add(fieldKey)
            }
          }
        }
      )
    }

    // Set additional config fields
    const additionalConfig = providerInstance.additional_config as Record<
      string,
      unknown
    > | null
    if (additionalConfig) {
      Object.entries(additionalConfig).forEach(([key, value]) => {
        initialData[`config_${key}`] = String(value)
      })
    }

    setFormData(initialData)
    setMaskedFields(masked)
  }, [providerInstance, provider, open])

  if (!provider || !providerInstance) return null

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Remove from masked fields when user starts editing
    if (maskedFields.has(field)) {
      setMaskedFields((prev) => {
        const newSet = new Set(prev)
        newSet.delete(field)
        return newSet
      })
    }
  }

  const handleFocus = (field: string) => {
    // Clear masked placeholder on focus
    if (maskedFields.has(field)) {
      setFormData((prev) => ({ ...prev, [field]: '' }))
    }
  }

  const handleSubmit = () => {
    const authMethod = selectedAuthMethod || provider.default_auth_method

    // Get the selected auth method configuration
    const selectedAuth = provider.supported_auth_methods.find(
      (method) => method.method === authMethod
    )

    // Build auth_config only if user entered new values
    const authConfig: Record<string, string | Record<string, string> | object> =
      {
        method: authMethod,
      }
    let hasAuthChanges = false

    // Handle different auth field structures
    if (selectedAuth?.fields) {
      Object.entries(selectedAuth.fields).forEach(
        ([fieldName, field]: [string, unknown]) => {
          const typedField = field as AuthField
          if (typedField.type === 'group' && typedField.fields) {
            // Handle grouped fields (like AWS)
            const groupData: Record<string, string> = {}
            Object.keys(typedField.fields).forEach((subFieldName) => {
              const fieldKey = `auth_${subFieldName}`
              const formValue = formData[fieldKey]
              // Only include if user entered a value (not masked)
              if (formValue && formValue !== MASK_PLACEHOLDER) {
                groupData[subFieldName] = formValue
                hasAuthChanges = true
              }
            })
            if (Object.keys(groupData).length > 0) {
              authConfig[fieldName] = groupData
            }
          } else {
            // Handle direct fields
            const fieldKey = `auth_${fieldName}`
            const formValue = formData[fieldKey]
            // Only include if user entered a value (not masked)
            if (formValue && formValue !== MASK_PLACEHOLDER) {
              // Handle JSON fields
              if (typedField.type === 'json_upload') {
                try {
                  authConfig[fieldName] = JSON.parse(formValue)
                } catch {
                  authConfig[fieldName] = formValue
                }
              } else {
                authConfig[fieldName] = formValue
              }
              hasAuthChanges = true
            }
          }
        }
      )
    }

    // Build additional_config
    const additionalConfig: Record<string, string> = {}
    let hasConfigChanges = false
    Object.keys(formData).forEach((key) => {
      if (key.startsWith('config_')) {
        const configKey = key.replace('config_', '')
        additionalConfig[configKey] = formData[key]
        hasConfigChanges = true
      }
    })

    // Build update data - only include changed fields
    const updateData: UpdateProviderRequest = {}

    if (formData.name && formData.name !== providerInstance.name) {
      updateData.name = formData.name
    }
    if (
      formData.display_name &&
      formData.display_name !== providerInstance.display_name
    ) {
      updateData.display_name = formData.display_name
    }
    if (
      formData.api_endpoint &&
      formData.api_endpoint !== providerInstance.api_endpoint
    ) {
      updateData.api_endpoint = formData.api_endpoint
    }
    if (hasAuthChanges) {
      updateData.auth_config = authConfig
    }
    if (hasConfigChanges) {
      updateData.additional_config = additionalConfig
    }

    onUpdate(providerInstance.id, updateData)
  }

  const renderField = (
    fieldName: string,
    field: AuthField,
    prefix: string = ''
  ) => {
    const fieldKey = prefix ? `${prefix}_${fieldName}` : fieldName
    const isMasked = maskedFields.has(fieldKey)
    const value = formData[fieldKey] || ''

    if (field.type === 'json_upload') {
      return (
        <div key={fieldKey} className='space-y-2'>
          <Label htmlFor={fieldKey} className='text-sm font-medium'>
            {field.description}
            {field.required && <span className='ml-1 text-red-500'>*</span>}
          </Label>
          <Textarea
            id={fieldKey}
            placeholder={
              isMasked ? MASK_PLACEHOLDER : field.placeholder || 'No change'
            }
            value={value}
            onChange={(e) => handleInputChange(fieldKey, e.target.value)}
            onFocus={() => handleFocus(fieldKey)}
            className='font-mono text-sm'
            rows={8}
          />
          {isMasked && (
            <p className='text-muted-foreground text-xs'>
              Leave as is to keep existing value, or enter new value to update
            </p>
          )}
        </div>
      )
    }

    return (
      <div key={fieldKey} className='space-y-2'>
        <Label htmlFor={fieldKey} className='text-sm font-medium'>
          {field.description}
          {field.required && <span className='ml-1 text-red-500'>*</span>}
        </Label>
        <Input
          id={fieldKey}
          type={field.type === 'password' && !isMasked ? 'password' : 'text'}
          placeholder={
            isMasked ? MASK_PLACEHOLDER : field.placeholder || 'No change'
          }
          value={value}
          onChange={(e) => handleInputChange(fieldKey, e.target.value)}
          onFocus={() => handleFocus(fieldKey)}
        />
        {isMasked && (
          <p className='text-muted-foreground text-xs'>
            Leave as is to keep existing value, or enter new value to update
          </p>
        )}
      </div>
    )
  }

  const renderAuthFields = (authMethod: AuthMethod) => {
    if (!authMethod?.fields) return null

    return Object.entries(authMethod.fields).map(
      ([fieldName, field]: [string, unknown]) => {
        const typedField = field as AuthField
        // Handle grouped fields (like AWS)
        if (typedField.type === 'group' && typedField.fields) {
          return (
            <div key={fieldName} className='space-y-4'>
              <div className='space-y-3'>
                {Object.entries(typedField.fields).map(
                  ([subFieldName, subField]: [string, unknown]) =>
                    renderField(subFieldName, subField as AuthField, 'auth')
                )}
              </div>
            </div>
          )
        }

        // Handle direct fields
        return renderField(fieldName, field as AuthField, 'auth')
      }
    )
  }

  const renderConfigFields = () => {
    const allFields = [...provider.required_config, ...provider.optional_config]

    return allFields.map((fieldName) => {
      const fieldType =
        (
          provider.configuration_schema?.field_types as Record<string, string>
        )?.[fieldName] || 'string'
      const description =
        (
          provider.configuration_schema?.field_descriptions as Record<
            string,
            string
          >
        )?.[fieldName] || fieldName
      const placeholder =
        (
          provider.configuration_schema?.field_placeholders as Record<
            string,
            string
          >
        )?.[fieldName] || ''
      const options = (
        provider.configuration_schema?.field_options as Record<
          string,
          { value: string; label: string }[]
        >
      )?.[fieldName]
      const isRequired = provider.required_config.includes(fieldName)

      return (
        <div key={fieldName} className='space-y-2'>
          <Label
            htmlFor={`config_${fieldName}`}
            className='text-sm font-medium'
          >
            {description}
            {isRequired && <span className='ml-1 text-red-500'>*</span>}
          </Label>
          {fieldType === 'select' && options ? (
            <Select
              value={formData[`config_${fieldName}`] || ''}
              onValueChange={(value) =>
                handleInputChange(`config_${fieldName}`, value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder={`Select ${fieldName}`} />
              </SelectTrigger>
              <SelectContent>
                {options.map((option: { value: string; label: string }) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              id={`config_${fieldName}`}
              type='text'
              placeholder={placeholder}
              value={formData[`config_${fieldName}`] || ''}
              onChange={(e) =>
                handleInputChange(`config_${fieldName}`, e.target.value)
              }
            />
          )}
        </div>
      )
    })
  }

  const renderAuthMethodContent = (authMethod: AuthMethod) => {
    return (
      <div className='space-y-6'>
        {/* Basic Configuration */}
        <div className='space-y-4'>
          <h3 className='font-semibold'>Varne Configuration</h3>
          <div className='space-y-3'>
            {Object.entries(
              provider.configuration_schema?.standard_fields || {}
            ).map(([fieldName, field]: [string, StandardField]) => {
              // Disable the 'name' field as it's the unique identifier
              const isNameField = fieldName === 'name'
              return (
                <div key={fieldName} className='space-y-2'>
                  <Label htmlFor={fieldName} className='text-sm font-medium'>
                    {field.description}
                    {field.required && (
                      <span className='ml-1 text-red-500'>*</span>
                    )}
                    {isNameField && (
                      <span className='text-muted-foreground ml-2 text-xs'>
                        (cannot be changed)
                      </span>
                    )}
                  </Label>
                  <Input
                    id={fieldName}
                    type='text'
                    placeholder={field.placeholder}
                    value={formData[fieldName] || ''}
                    onChange={(e) =>
                      handleInputChange(fieldName, e.target.value)
                    }
                    disabled={isNameField}
                    className={
                      isNameField ? 'cursor-not-allowed opacity-60' : ''
                    }
                  />
                </div>
              )
            })}
          </div>
        </div>

        <Separator />

        {/* Auth Fields */}
        <h3 className='font-semibold'>App Configuration</h3>
        <div className='space-y-4'>{renderAuthFields(authMethod)}</div>

        {/* Provider-Specific Configuration */}
        {(provider.required_config.length > 0 ||
          provider.optional_config.length > 0) && (
          <>
            <div className='space-y-4'>
              <div className='space-y-3'>{renderConfigFields()}</div>
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='max-h-[80vh] overflow-y-auto sm:max-w-[600px]'>
        <DialogHeader>
          <DialogTitle className='flex items-center gap-3'>
            <div className='bg-muted flex size-10 items-center justify-center rounded-lg p-2'>
              {provider.logo}
            </div>
            Edit {provider.display_name}
          </DialogTitle>
          <DialogDescription>
            Update your {provider.display_name} provider configuration
          </DialogDescription>
        </DialogHeader>

        <div className='space-y-6 py-4'>
          {/* Authentication Methods */}
          {provider.supported_auth_methods.length === 1 ? (
            // Single auth method
            renderAuthMethodContent(provider.supported_auth_methods[0])
          ) : (
            // Multiple auth methods - use tabs
            <Tabs
              value={selectedAuthMethod || provider.default_auth_method}
              onValueChange={setSelectedAuthMethod}
            >
              <TabsList
                className='grid w-full'
                style={{
                  gridTemplateColumns: `repeat(${provider.supported_auth_methods.length}, 1fr)`,
                }}
              >
                {provider.supported_auth_methods.map((method) => (
                  <TabsTrigger key={method.method} value={method.method}>
                    {method.display_name}
                  </TabsTrigger>
                ))}
              </TabsList>
              {provider.supported_auth_methods.map((method) => (
                <TabsContent
                  key={method.method}
                  value={method.method}
                  className='mt-4'
                >
                  {renderAuthMethodContent(method)}
                </TabsContent>
              ))}
            </Tabs>
          )}
        </div>

        <DialogFooter>
          <Button variant='outline' onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Update</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
