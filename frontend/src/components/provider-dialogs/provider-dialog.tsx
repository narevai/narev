import { useState } from 'react'
import type { AuthField, AuthMethod, Provider, StandardField } from '@/lib/api'
import type { CreateProviderRequest } from '@/lib/api'
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

interface ProviderDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  provider: Provider | null
  onConnect: (data: CreateProviderRequest) => Promise<void>
}

export function ProviderDialog({
  open,
  onOpenChange,
  provider,
  onConnect,
}: ProviderDialogProps) {
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [selectedAuthMethod, setSelectedAuthMethod] = useState<string>('')

  if (!provider) return null

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = () => {
    const authMethod = selectedAuthMethod || provider.default_auth_method

    // Get the selected auth method configuration
    const selectedAuth = provider.supported_auth_methods.find(
      (method) => method.method === authMethod
    )

    // Build auth_config based on the auth method structure
    const authConfig: Record<string, string | Record<string, string> | object> =
      {
        method: authMethod,
      }

    // Handle different auth field structures
    if (selectedAuth?.fields) {
      Object.entries(selectedAuth.fields).forEach(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ([fieldName, field]: [string, any]) => {
          const typedField = field as AuthField
          if (typedField.type === 'group' && typedField.fields) {
            // Handle grouped fields (like AWS primary/secondary)
            const groupData: Record<string, string> = {}
            Object.keys(typedField.fields).forEach((subFieldName) => {
              const formValue = formData[`auth_${subFieldName}`]
              if (formValue) {
                groupData[subFieldName] = formValue
              }
            })
            if (Object.keys(groupData).length > 0) {
              authConfig[fieldName] = groupData
            }
          } else {
            // Handle direct fields (like Azure, GCP, OpenAI)
            const formValue = formData[`auth_${fieldName}`]
            if (formValue) {
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
            }
          }
        }
      )
    }

    // Build additional_config
    const additionalConfig: Record<string, string> = {}
    Object.keys(formData).forEach((key) => {
      if (key.startsWith('config_')) {
        const configKey = key.replace('config_', '')
        additionalConfig[configKey] = formData[key]
      }
    })

    // Transform form data to match API requirements
    const connectData: CreateProviderRequest = {
      provider_type: provider.provider_type,
      name: formData.name || '',
      display_name: formData.display_name || formData.name || '',
      auth_config: authConfig,
      ...(formData.api_endpoint && { api_endpoint: formData.api_endpoint }),
      ...(Object.keys(additionalConfig).length > 0 && {
        additional_config: additionalConfig,
      }),
    }

    onConnect(connectData)
  }

  const renderField = (
    fieldName: string,
    field: AuthField,
    prefix: string = ''
  ) => {
    const fieldKey = prefix ? `${prefix}_${fieldName}` : fieldName

    if (field.type === 'json_upload') {
      return (
        <div key={fieldKey} className='space-y-2'>
          <Label htmlFor={fieldKey} className='text-sm font-medium'>
            {field.description}
            {field.required && <span className='ml-1 text-red-500'>*</span>}
          </Label>
          <Textarea
            id={fieldKey}
            placeholder={field.placeholder}
            value={formData[fieldKey] || ''}
            onChange={(e) => handleInputChange(fieldKey, e.target.value)}
            className='font-mono text-sm'
            rows={8}
          />
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
          type={field.type === 'password' ? 'password' : 'text'}
          placeholder={field.placeholder}
          value={formData[fieldKey] || ''}
          onChange={(e) => handleInputChange(fieldKey, e.target.value)}
        />
      </div>
    )
  }

  const renderAuthFields = (authMethod: AuthMethod) => {
    if (!authMethod?.fields) return null

    return Object.entries(authMethod.fields).map(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ([fieldName, field]: [string, any]) => {
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

        // Handle direct fields (like Azure, GCP, OpenAI)
        return renderField(fieldName, field, 'auth')
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
          <h3 className='font-semibold'>Narev Configuration</h3>
          <div className='space-y-3'>
            {Object.entries(
              provider.configuration_schema?.standard_fields || {}
            ).map(([fieldName, field]: [string, StandardField]) => (
              <div key={fieldName} className='space-y-2'>
                <Label htmlFor={fieldName} className='text-sm font-medium'>
                  {field.description}
                  {field.required && (
                    <span className='ml-1 text-red-500'>*</span>
                  )}
                </Label>
                <Input
                  id={fieldName}
                  type='text'
                  placeholder={field.placeholder}
                  value={formData[fieldName] || ''}
                  onChange={(e) => handleInputChange(fieldName, e.target.value)}
                />
              </div>
            ))}
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
            Connect {provider.display_name}
          </DialogTitle>
          <DialogDescription>
            Configure your {provider.display_name} provider connection
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
              defaultValue={provider.default_auth_method}
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
          <Button onClick={handleSubmit}>Connect</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
