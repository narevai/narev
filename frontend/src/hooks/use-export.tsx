import { useState } from 'react'
import { toast } from 'sonner'
import {
  ExportBillingParams,
  ExportHealthCheckResponse,
  exportApi,
} from '@/lib/api'

export function useExport() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const exportBilling = async (params?: ExportBillingParams) => {
    try {
      setLoading(true)
      setError(null)

      const { data, error, filename } = await exportApi.billing(params) // Add filename
      if (error) throw new Error(error) // Use the actual error message

      toast.success('Billing data exported successfully')
      return { data, filename } // Return both data and filename
    } catch (err) {
      const errorMessage = 'Failed to export billing data'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to export billing information. Please try again.',
      })
      throw err
    } finally {
      setLoading(false)
    }
  }

  const healthCheck = async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await exportApi.health()
      if (error) throw new Error('Export health check failed')

      return data as ExportHealthCheckResponse
    } catch (err) {
      const errorMessage = 'Export health check failed'
      setError(errorMessage)
      toast.error(errorMessage, {
        description: 'Unable to verify export service status.',
      })
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Helper function to download file from blob response
  const downloadFile = (
    data: unknown,
    filename: string,
    format: 'csv' | 'xlsx' = 'csv'
  ) => {
    try {
      const mimeType =
        format === 'csv'
          ? 'text/csv'
          : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

      // Handle different data types
      let blobData: string | ArrayBuffer | Blob
      if (typeof data === 'string') {
        blobData = data
      } else if (data instanceof Blob) {
        blobData = data
      } else if (data instanceof ArrayBuffer) {
        blobData = data
      } else {
        // Convert other types to string (e.g., if it's JSON)
        blobData =
          typeof data === 'object' ? JSON.stringify(data) : String(data)
      }

      const blob =
        blobData instanceof Blob
          ? blobData
          : new Blob([blobData], { type: mimeType })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      toast.error('Failed to download file', {
        description: 'Unable to save the exported data.',
      })
      throw err
    }
  }

  // Combined function to export and download billing data
  const exportAndDownloadBilling = async (
    params?: ExportBillingParams,
    filename?: string
  ) => {
    const result = await exportBilling(params) // result now has { data, filename }
    const format = params?.format || 'csv'
    const defaultFilename = `billing-export-${new Date().toISOString().split('T')[0]}.${format}`

    // Use server-provided filename if available, otherwise use provided or default
    const finalFilename = filename || result.filename || defaultFilename

    downloadFile(result.data, finalFilename, format)
    return result.data
  }

  return {
    // State
    loading,
    error,

    // Actions
    exportBilling,
    healthCheck,
    downloadFile,
    exportAndDownloadBilling,
  }
}
