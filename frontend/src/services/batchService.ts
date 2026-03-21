/**
 * Batch Service
 *
 * API methods for batch lifecycle:
 *   POST   /batches/upload           Upload Excel
 *   POST   /batches/{id}/confirm     Confirm & start processing
 *   GET    /batches/{id}/status      Poll progress
 *   GET    /batches                  List all batches
 */

import apiClient from './api'
import type {
  BatchUploadResponse,
  BatchStatusResponse,
  BatchConfirmRequest,
  BatchListItem,
  CompanyListItem,
  CriteriaUpdate,
  CriteriaResponse,
} from '@/types/api'

export const batchService = {
  /**
   * Upload an Excel file for parsing (does NOT start processing).
   */
  async upload(file: File): Promise<BatchUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await apiClient.post<BatchUploadResponse>('/batches/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000, // 2 min for large files
    })
    return data
  },

  /**
   * Confirm a batch and start AI processing.
   * Optionally exclude specific company IDs.
   */
  async confirm(batchId: string, payload?: BatchConfirmRequest): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(
      `/batches/${batchId}/confirm`,
      payload ?? {},
    )
    return data
  },

  /**
   * Poll batch processing status.
   */
  async getStatus(batchId: string): Promise<BatchStatusResponse> {
    const { data } = await apiClient.get<BatchStatusResponse>(`/batches/${batchId}/status`)
    return data
  },

  /**
   * Get all companies in a batch with their current status.
   */
  async getCompanies(batchId: string): Promise<CompanyListItem[]> {
    const { data } = await apiClient.get<CompanyListItem[]>(`/companies/batch/${batchId}`)
    return data
  },

  /**
   * Save accept/reject criteria for a batch.
   */
  async saveCriteria(batchId: string, payload: CriteriaUpdate): Promise<CriteriaResponse> {
    const { data } = await apiClient.put<CriteriaResponse>(`/batches/${batchId}/criteria`, payload)
    return data
  },

  /**
   * Trigger Stage 2 accept/reject decisions.
   */
  async triggerDecisions(batchId: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(`/batches/${batchId}/decide`)
    return data
  },

  /**
   * List all batches (paginated newest-first).
   */
  async list(skip = 0, limit = 20): Promise<BatchListItem[]> {
    const { data } = await apiClient.get<BatchListItem[]>('/batches', {
      params: { skip, limit },
    })
    return data
  },
}
