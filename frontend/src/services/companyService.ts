/**
 * Company Service
 *
 * API methods for company data:
 *   GET  /companies/{id}                Full company detail
 *   GET  /batches/{batch_id}/companies  List companies in batch
 *   GET  /batches/{batch_id}/results    Aggregated results summary
 *   GET  /batches/{batch_id}/export     Download Excel export
 */

import apiClient from './api'
import type {
  CompanyDetail,
  CompanyListItem,
  BatchResultsSummary,
  FinalDecisionUpdateRequest,
} from '@/types/api'

export const companyService = {
  /**
   * Get full company detail with AI analysis.
   */
  async getDetail(companyId: number): Promise<CompanyDetail> {
    const { data } = await apiClient.get<CompanyDetail>(`/companies/${companyId}`)
    return data
  },

  /**
   * Set final human accept/reject decision for one company.
   */
  async setFinalDecision(
    companyId: number,
    finalDecision: 'accept' | 'reject' | null,
  ): Promise<CompanyListItem> {
    const payload: FinalDecisionUpdateRequest = { final_decision: finalDecision }
    const { data } = await apiClient.patch<CompanyListItem>(
      `/companies/${companyId}/final-decision`,
      payload,
    )
    return data
  },

  /**
   * List companies in a batch with optional filters.
   */
  async listByBatch(
    batchId: string,
    filters?: { status?: string; decision?: string },
  ): Promise<CompanyListItem[]> {
    const { data } = await apiClient.get<CompanyListItem[]>(
      `/companies/batch/${batchId}`,
      { params: filters },
    )
    return data
  },

  /**
   * Get aggregated results summary for a batch.
   */
  async getResults(batchId: string): Promise<BatchResultsSummary> {
    const { data } = await apiClient.get<BatchResultsSummary>(`/batches/${batchId}/results`)
    return data
  },

  /**
   * Download batch results as Excel file.
   */
  async exportExcel(batchId: string): Promise<void> {
    const response = await apiClient.get(`/companies/batch/${batchId}/export`, {
      responseType: 'blob',
    })
    // Create a temporary download link and click it
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `batch_${batchId}_results.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  /**
   * Re-scrape and re-analyse a single company (resets it to PENDING).
   */
  async rescrapeCompany(companyId: number): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>(`/companies/${companyId}/rescrape`)
    return data
  },
}
