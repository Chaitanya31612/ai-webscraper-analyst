/**
 * Benchmark Pinia Store
 *
 * Holds the state for the active benchmarking session across all steps.
 * - companies[] lives here as the editable "source of truth"
 * - batchId is set after a successful POST /api/batches/upload
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface CompanyRow {
  /** Temporary client-side id (not the DB id) */
  _id: number
  company_name: string
  website: string
  country: string
  industry: string
  bvd_id: string
  /** Validation error map: field -> message */
  errors: Record<string, string>
}

let _nextId = 1

export function makeRow(partial: Partial<Omit<CompanyRow, '_id' | 'errors'>> = {}): CompanyRow {
  return {
    _id: _nextId++,
    company_name: partial.company_name ?? '',
    website: partial.website ?? '',
    country: partial.country ?? '',
    industry: partial.industry ?? '',
    bvd_id: partial.bvd_id ?? '',
    errors: {},
  }
}

export const useBenchmarkStore = defineStore('benchmark', () => {
  const batchId = ref<string | null>(null)
  const batchFilename = ref<string | null>(null)
  const totalCompanies = ref(0)
  const companies = ref<CompanyRow[]>([])

  function setCompanies(rows: CompanyRow[]) {
    companies.value = rows
  }

  function addRow() {
    companies.value.push(makeRow())
  }

  function deleteRow(id: number) {
    companies.value = companies.value.filter(r => r._id !== id)
  }

  function updateField(id: number, field: keyof Omit<CompanyRow, '_id' | 'errors'>, value: string) {
    const row = companies.value.find(r => r._id === id)
    if (row) {
      row[field] = value
      // Clear the error for this field on edit
      delete row.errors[field]
    }
  }

  function setBatch(id: string, filename: string, total: number) {
    batchId.value = id
    batchFilename.value = filename
    totalCompanies.value = total
  }

  function reset() {
    batchId.value = null
    batchFilename.value = null
    totalCompanies.value = 0
    companies.value = []
    _nextId = 1
  }

  return {
    batchId,
    batchFilename,
    totalCompanies,
    companies,
    setCompanies,
    addRow,
    deleteRow,
    updateField,
    setBatch,
    reset,
  }
})
