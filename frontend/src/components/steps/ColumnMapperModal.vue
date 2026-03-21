<script setup lang="ts">
/**
 * ColumnMapperModal — Shown after an Excel file is parsed.
 *
 * Two steps:
 *   Step 1: Column Mapping  — Map Excel columns to target fields
 *   Step 2: Preview         — Show first 5 rows; confirm import
 *
 * AI Mapper: Uses string similarity scoring to auto-assign mappings.
 */
import { ref, computed, watch } from 'vue'
import { X, Sparkles, ChevronRight, Loader2, AlertCircle } from 'lucide-vue-next'
import { makeRow, type CompanyRow } from '@/stores/benchmark'

// ── Target fields ──────────────────────────────────────────────────────────────
interface TargetField {
  key: keyof Omit<CompanyRow, '_id' | 'errors'>
  label: string
  required?: boolean
}

const TARGET_FIELDS: TargetField[] = [
  { key: 'company_name', label: 'Company Name', required: true },
  { key: 'website',      label: 'Website',      required: true },
  { key: 'country',      label: 'Country' },
  { key: 'industry',     label: 'Industry' },
  { key: 'bvd_id',       label: 'BVD ID' },
]

// ── AI mapping aliases ─────────────────────────────────────────────────────────
// Each key is a target field, value is list of strings that strongly suggest that mapping
const AI_ALIASES: Record<string, string[]> = {
  company_name: ['company', 'name', 'company name', 'firm', 'organization', 'business name'],
  website:      ['website', 'url', 'web', 'site', 'link', 'homepage', 'address', 'web address', 'internet'],
  country:      ['country', 'nation', 'location', 'territory', 'region', 'state'],
  industry:     ['industry', 'sector', 'business type', 'category', 'classification'],
  bvd_id:       ['bvd', 'database id', 'id number', 'identifier', 'code'],
}

// ── Props / emits ──────────────────────────────────────────────────────────────
const props = defineProps<{
  open: boolean
  /** Raw Excel rows (array of objects with arbitrary string keys) */
  rawRows: Record<string, unknown>[]
  filename: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'import', rows: CompanyRow[]): void
}>()

// ── State ──────────────────────────────────────────────────────────────────────
type Step = 'mapping' | 'preview'
const currentStep = ref<Step>('mapping')
const isAiMapping = ref(false)
const mappingError = ref<string | null>(null)

/** Maps each Excel column header → selected target field key (or '' for unmapped) */
const columnMappings = ref<Record<string, string>>({})

// ── Computed helpers ───────────────────────────────────────────────────────────

/** All unique column headers from the raw data */
const excelColumns = computed(() => {
  const first = props.rawRows[0]
  if (!first) return []
  return Object.keys(first)
})

/** Sample value for a column (first non-empty value from top rows) */
function sampleValue(col: string): string {
  for (const row of props.rawRows.slice(0, 5)) {
    const v = String(row[col] ?? '').trim()
    if (v && v !== 'undefined' && v !== 'nan') return v
  }
  return '—'
}

/** Currently mapped fields (to prevent duplicate mappings in dropdowns) */
const mappedFields = computed(() => new Set(Object.values(columnMappings.value).filter(Boolean)))

// ── Initialize / reset on open ─────────────────────────────────────────────────
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    currentStep.value = 'mapping'
    mappingError.value = null
    // Reset mappings
    const initial: Record<string, string> = {}
    for (const col of excelColumns.value) initial[col] = ''
    columnMappings.value = initial
    // Auto-run AI mapper on open
    runAiMapper()
  }
})

// ── AI Mapper (client-side fuzzy matching) ─────────────────────────────────────
function similarity(a: string, b: string): number {
  a = a.toLowerCase().replace(/[^a-z0-9\s]/g, '')
  b = b.toLowerCase().replace(/[^a-z0-9\s]/g, '')
  if (a === b) return 1
  if (b.includes(a) || a.includes(b)) return 0.9
  // Word overlap scoring
  const aWords = new Set(a.split(/\s+/))
  const bWords = new Set(b.split(/\s+/))
  const intersection = [...aWords].filter(w => bWords.has(w)).length
  return intersection / Math.max(aWords.size, bWords.size)
}

function runAiMapper() {
  isAiMapping.value = true
  const newMappings: Record<string, string> = {}
  const usedTargets = new Set<string>()

  for (const col of excelColumns.value) {
    let bestField = ''
    let bestScore = 0.25 // Minimum confidence threshold

    for (const [fieldKey, aliases] of Object.entries(AI_ALIASES)) {
      if (usedTargets.has(fieldKey)) continue
      // Score against header vs each alias
      const scores = aliases.map(alias => similarity(col, alias))
      const maxScore = Math.max(...scores)
      if (maxScore > bestScore) {
        bestScore = maxScore
        bestField = fieldKey
      }
    }

    if (bestField) usedTargets.add(bestField)
    newMappings[col] = bestField
  }

  columnMappings.value = newMappings
  isAiMapping.value = false
}

// ── Validation — require at least Company Name and Website are mapped ──────────
const requiredMapped = computed(() => {
  const vals = Object.values(columnMappings.value)
  return vals.includes('company_name') && vals.includes('website')
})

// ── Build preview rows ─────────────────────────────────────────────────────────
const previewRows = computed((): CompanyRow[] => {
  return props.rawRows.slice(0, 5).map(raw => {
    const partial: Partial<Omit<CompanyRow, '_id' | 'errors'>> = {}
    for (const [col, fieldKey] of Object.entries(columnMappings.value)) {
      if (!fieldKey) continue
      partial[fieldKey as keyof typeof partial] = String(raw[col] ?? '').trim()
    }
    return makeRow(partial)
  })
})

// ── All mapped rows for final import ──────────────────────────────────────────
const allMappedRows = computed((): CompanyRow[] => {
  return props.rawRows.map(raw => {
    const partial: Partial<Omit<CompanyRow, '_id' | 'errors'>> = {}
    for (const [col, fieldKey] of Object.entries(columnMappings.value)) {
      if (!fieldKey) continue
      partial[fieldKey as keyof typeof partial] = String(raw[col] ?? '').trim()
    }
    return makeRow(partial)
  })
})

function goToPreview() {
  if (!requiredMapped.value) {
    mappingError.value = 'Please map "Company Name" and "Website" before continuing.'
    return
  }
  mappingError.value = null
  currentStep.value = 'preview'
}

function confirmImport() {
  emit('import', allMappedRows.value)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-[rgba(15,23,42,0.5)] backdrop-blur-[2px]"
      @click.self="emit('close')"
    >
      <div class="w-full max-w-[900px] max-h-[90vh] flex flex-col rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)] shadow-[0_30px_60px_rgba(2,6,23,0.32)]">

        <!-- Header -->
        <div class="flex items-center justify-between gap-4 px-6 pt-5 pb-4 border-b border-[var(--color-border)] shrink-0">
          <div>
            <h3 class="text-lg font-bold text-[var(--color-text)] m-0">Map Columns</h3>
            <p class="text-sm text-[var(--color-text-secondary)] m-0 mt-0.5">
              {{ filename }} — match Excel columns to the required fields
            </p>
          </div>
          <!-- Step indicator -->
          <div class="flex items-center gap-2 text-xs font-medium text-[var(--color-text-muted)]">
            <span :class="currentStep === 'mapping' ? 'text-[var(--color-primary)] font-semibold' : ''">1 Column Mapping</span>
            <ChevronRight :size="12" />
            <span :class="currentStep === 'preview' ? 'text-[var(--color-primary)] font-semibold' : ''">2 Preview Data</span>
          </div>
          <button
            type="button"
            class="w-8 h-8 rounded-md border border-[var(--color-border)] bg-transparent text-[var(--color-text-muted)] cursor-pointer hover:text-[var(--color-danger)] hover:border-[var(--color-danger)] transition-colors"
            @click="emit('close')"
          >
            <X :size="15" />
          </button>
        </div>

        <!-- ── STEP 1: COLUMN MAPPING ──────────────────────────────────────── -->
        <div v-if="currentStep === 'mapping'" class="flex flex-1 overflow-hidden">

          <!-- Left: Excel columns -->
          <div class="flex-1 overflow-y-auto border-r border-[var(--color-border)] p-4">
            <div class="flex items-center justify-between mb-3">
              <p class="text-xs font-semibold text-[var(--color-text-secondary)] m-0 uppercase tracking-wide">
                Excel Columns ({{ excelColumns.length }})
              </p>
              <button
                type="button"
                @click="runAiMapper"
                :disabled="isAiMapping"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-xs font-semibold border-none cursor-pointer transition-all hover:bg-[var(--color-primary-hover)] disabled:opacity-60"
              >
                <Loader2 v-if="isAiMapping" :size="11" class="animate-spin" />
                <Sparkles v-else :size="11" />
                {{ isAiMapping ? 'Mapping…' : 'Auto-Map' }}
              </button>
            </div>

            <div class="flex flex-col gap-2">
              <div
                v-for="col in excelColumns"
                :key="col"
                class="flex items-center gap-3 p-2.5 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-bg-alt)] hover:border-[var(--color-primary-light)] transition-colors"
              >
                <!-- Column info -->
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-[var(--color-text)] m-0 truncate">{{ col }}</p>
                  <p class="text-xs text-[var(--color-text-muted)] m-0 truncate mt-0.5 font-mono">{{ sampleValue(col) }}</p>
                </div>

                <!-- Arrow -->
                <ChevronRight :size="13" class="text-[var(--color-text-muted)] shrink-0" />

                <!-- Target field dropdown -->
                <select
                  v-model="columnMappings[col]"
                  class="w-40 shrink-0 text-xs rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] cursor-pointer"
                >
                  <option value="">Not mapped</option>
                  <option
                    v-for="field in TARGET_FIELDS"
                    :key="field.key"
                    :value="field.key"
                    :disabled="mappedFields.has(field.key) && columnMappings[col] !== field.key"
                  >
                    {{ field.label }}{{ field.required ? ' *' : '' }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Right: Target fields legend -->
          <div class="w-52 shrink-0 overflow-y-auto p-4 bg-[var(--color-bg-alt)]">
            <p class="text-xs font-semibold text-[var(--color-text-secondary)] m-0 mb-3 uppercase tracking-wide">Target Fields</p>
            <div class="flex flex-col gap-2">
              <div
                v-for="field in TARGET_FIELDS"
                :key="field.key"
                class="flex items-center justify-between"
              >
                <span
                  :class="[
                    'text-xs font-medium',
                    mappedFields.has(field.key) ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-muted)]',
                  ]"
                >
                  {{ field.label }}
                  <span v-if="field.required" class="text-[var(--color-danger)]">*</span>
                </span>
                <span
                  :class="[
                    'text-[0.6rem] px-1.5 py-0.5 rounded-full font-medium',
                    mappedFields.has(field.key)
                      ? 'bg-[rgba(52,211,153,0.15)] text-[var(--color-accent)]'
                      : 'bg-[var(--color-border)] text-[var(--color-text-muted)]',
                  ]"
                >
                  {{ mappedFields.has(field.key) ? '✓ Mapped' : field.required ? 'Required' : 'Optional' }}
                </span>
              </div>
            </div>
            <div class="mt-4 pt-3 border-t border-[var(--color-border)]">
              <p class="text-[0.65rem] text-[var(--color-text-muted)] leading-relaxed m-0">
                Fields marked <span class="text-[var(--color-danger)] font-semibold">*</span> are required. Unmapped columns are skipped.
              </p>
            </div>
          </div>
        </div>

        <!-- ── STEP 2: PREVIEW ─────────────────────────────────────────────── -->
        <div v-else class="flex-1 overflow-y-auto p-4">
          <p class="text-sm text-[var(--color-text-secondary)] mb-3 m-0">
            Preview Data — showing first {{ previewRows.length }} of {{ rawRows.length }} rows.
          </p>
          <div class="overflow-x-auto border border-[var(--color-border)] rounded-[var(--radius-sm)]">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="bg-[var(--color-bg-alt)] border-b border-[var(--color-border)]">
                  <th class="px-3 py-2 text-left text-xs font-semibold text-[var(--color-text-secondary)]">Company Name *</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-[var(--color-text-secondary)]">Website *</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-[var(--color-text-secondary)]">Country</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-[var(--color-text-secondary)]">Industry</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-[var(--color-text-secondary)]">BVD ID</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, i) in previewRows"
                  :key="i"
                  class="border-b border-[var(--color-border)] hover:bg-[var(--color-primary-light)] transition-colors"
                >
                  <td class="px-3 py-2 text-xs text-[var(--color-text)] max-w-[200px] truncate">{{ row.company_name || '—' }}</td>
                  <td class="px-3 py-2 text-xs text-[var(--color-text-muted)] max-w-[180px] truncate">{{ row.website || '—' }}</td>
                  <td class="px-3 py-2 text-xs text-[var(--color-text-muted)]">{{ row.country || '—' }}</td>
                  <td class="px-3 py-2 text-xs text-[var(--color-text-muted)]">{{ row.industry || '—' }}</td>
                  <td class="px-3 py-2 text-xs text-[var(--color-text-muted)] font-mono">{{ row.bvd_id || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="rawRows.length > 5" class="text-xs text-[var(--color-text-muted)] mt-2 text-center m-0">
            … and {{ rawRows.length - 5 }} more rows
          </p>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between gap-3 px-6 py-4 border-t border-[var(--color-border)] bg-[var(--color-bg)] shrink-0">
          <div class="flex items-center gap-2">
            <p v-if="mappingError" class="flex items-center gap-1.5 text-xs text-[var(--color-danger)] font-medium m-0">
              <AlertCircle :size="12" />{{ mappingError }}
            </p>
          </div>
          <div class="flex items-center gap-3">
            <button
              v-if="currentStep === 'preview'"
              type="button"
              @click="currentStep = 'mapping'"
              class="px-4 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-transparent text-sm font-semibold text-[var(--color-text-secondary)] cursor-pointer hover:bg-[var(--color-bg-alt)] transition-colors"
            >
              ← Back
            </button>
            <button
              v-else
              type="button"
              @click="emit('close')"
              class="px-4 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-transparent text-sm font-semibold text-[var(--color-text-secondary)] cursor-pointer hover:bg-[var(--color-bg-alt)] transition-colors"
            >
              Cancel
            </button>

            <button
              v-if="currentStep === 'mapping'"
              type="button"
              @click="goToPreview"
              class="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-sm font-semibold border-none cursor-pointer transition-all hover:bg-[var(--color-primary-hover)]"
            >
              Next →
            </button>
            <button
              v-else
              type="button"
              @click="confirmImport"
              class="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-sm)] bg-[var(--color-accent)] text-white text-sm font-semibold border-none cursor-pointer transition-all hover:opacity-90"
            >
              Import {{ rawRows.length }} rows →
            </button>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin { animation: spin 1s linear infinite; }
</style>
