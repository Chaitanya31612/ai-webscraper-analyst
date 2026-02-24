/**
 * Batch Store — manages batch state across the application.
 *
 * Handles:
 *  - List of all batches (dashboard)
 *  - Current active batch (upload → verify → process → results flow)
 *  - Polling for real-time status updates
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { batchService } from '@/services/batchService'
import type {
  BatchUploadResponse,
  BatchStatusResponse,
  BatchListItem,
  BatchConfirmRequest,
} from '@/types/api'

export const useBatchStore = defineStore('batch', () => {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const batches = ref<BatchListItem[]>([])
  const currentBatch = ref<BatchUploadResponse | null>(null)
  const currentStatus = ref<BatchStatusResponse | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------
  const isProcessing = computed(() => {
    const status = currentStatus.value?.status
    return status === 'processing' || status === 'scraping' || status === 'analyzing'
  })

  const isComplete = computed(() => currentStatus.value?.status === 'complete')

  const progressPercent = computed(() => {
    if (!currentStatus.value) return 0
    const { counts, total_companies } = currentStatus.value
    if (total_companies === 0) return 0
    return Math.round(((counts.complete + counts.error) / total_companies) * 100)
  })

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function fetchBatches(skip = 0, limit = 20) {
    isLoading.value = true
    error.value = null
    try {
      batches.value = await batchService.list(skip, limit)
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch batches'
    } finally {
      isLoading.value = false
    }
  }

  async function uploadFile(file: File) {
    isLoading.value = true
    error.value = null
    try {
      currentBatch.value = await batchService.upload(file)
      return currentBatch.value
    } catch (e: any) {
      error.value = e.message || 'Upload failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function confirmBatch(batchId: string, payload?: BatchConfirmRequest) {
    isLoading.value = true
    error.value = null
    try {
      await batchService.confirm(batchId, payload)
      // Start polling after confirmation
      startPolling(batchId)
    } catch (e: any) {
      error.value = e.message || 'Failed to confirm batch'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStatus(batchId: string) {
    try {
      currentStatus.value = await batchService.getStatus(batchId)

      // Auto-stop polling when done
      if (
        currentStatus.value.status === 'complete' ||
        currentStatus.value.status === 'error'
      ) {
        stopPolling()
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch status'
    }
  }

  function startPolling(batchId: string, intervalMs = 3000) {
    stopPolling() // Clear any existing
    fetchStatus(batchId) // Immediate first fetch
    pollingInterval.value = setInterval(() => fetchStatus(batchId), intervalMs)
  }

  function stopPolling() {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
  }

  function clearCurrent() {
    currentBatch.value = null
    currentStatus.value = null
    stopPolling()
  }

  return {
    // State
    batches,
    currentBatch,
    currentStatus,
    isLoading,
    error,
    // Computed
    isProcessing,
    isComplete,
    progressPercent,
    // Actions
    fetchBatches,
    uploadFile,
    confirmBatch,
    fetchStatus,
    startPolling,
    stopPolling,
    clearCurrent,
  }
})
