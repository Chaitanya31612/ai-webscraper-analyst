<script setup lang="ts">
/**
 * UploadDataStep — Step 1 of the Benchmarking workflow.
 *
 * Two UI states:
 *   - Empty: drag-and-drop zone + "add row" link
 *   - Table: editable rows with sticky action bar
 *
 * Flow:
 *   1. Drop / pick Excel → parse client-side with SheetJS → populate table
 *   2. User can add/edit/delete rows inline
 *   3. "Save & Continue" → re-serialize to xlsx → POST /api/batches/upload → emit('next')
 */
import { ref, computed, onMounted, watch } from 'vue'
import * as XLSX from 'xlsx'
import {
  Upload, Plus, Trash2, ArrowRight, FileSpreadsheet, X, AlertCircle,
  Loader2, FilePlus2,
} from 'lucide-vue-next'
import { useBenchmarkStore, makeRow, type CompanyRow } from '@/stores/benchmark'
import { batchService } from '@/services/batchService'
import ColumnMapperModal from '@/components/steps/ColumnMapperModal.vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  batchId: string | null
}>()

const emit = defineEmits<{ (e: 'uploaded', batchId: string): void }>()

const benchmarkStore = useBenchmarkStore()
const router = useRouter()

/** Reset store + navigate to fresh /benchmark (clears batch ID from URL) */
function newBatch() {
  benchmarkStore.reset()
  router.push('/benchmark')
}

// ── Refs ─────────────────────────────────────────────────────────────────────
const fileInputRef = ref<HTMLInputElement | null>(null)
const tableBodyRef = ref<HTMLElement | null>(null)
const isDragging = ref(false)
const uploadedFilename = ref<string | null>(null)
const saving = ref(false)
const saveError = ref<string | null>(null)
const loadingExisting = ref(false)

// ── Column Mapper Modal state ────────────────────────────────────────────────
const mapperOpen = ref(false)
const rawExcelRows = ref<Record<string, unknown>[]>([])
const mapperFilename = ref('')

const hasRows = computed(() => benchmarkStore.companies.length > 0)

// ── Load existing batch data ──────────────────────────────────────────────────
async function loadExistingBatch() {
  if (!props.batchId || benchmarkStore.companies.length > 0) return
  loadingExisting.value = true
  try {
    const companies = await batchService.getCompanies(props.batchId)
    if (companies.length > 0) {
      const rows = companies.map(c => makeRow({
        company_name: c.company_name,
        website: c.website,
        country: c.country ?? '',
        industry: c.industry ?? '',
        bvd_id: c.bvd_id ?? '',
      }))
      benchmarkStore.setCompanies(rows)
      uploadedFilename.value = benchmarkStore.batchFilename ?? 'Previously uploaded'
    }
  } catch {
    // Silently ignore — user can still upload a new file
  } finally {
    loadingExisting.value = false
  }
}

onMounted(() => {
  loadExistingBatch()
})

watch(() => props.batchId, () => {
  loadExistingBatch()
})

// ── Column config ─────────────────────────────────────────────────────────────
const columns: Array<{ key: keyof Omit<CompanyRow, '_id' | 'errors'>; label: string; required?: boolean; width: string }> = [
  { key: 'company_name', label: 'Company Name', required: true, width: '260px' },
  { key: 'website',      label: 'Website',       required: true, width: '240px' },
  { key: 'country',      label: 'Country',                       width: '140px' },
  { key: 'industry',     label: 'Industry',                      width: '160px' },
  { key: 'bvd_id',       label: 'BVD ID',                        width: '140px' },
]

// ── Excel parsing ─────────────────────────────────────────────────────────────
/** Map of common header aliases → our field names */
const HEADER_MAP: Record<string, keyof Omit<CompanyRow, '_id' | 'errors'>> = {
  'company_name': 'company_name',
  'company name': 'company_name',
  'name': 'company_name',
  'company': 'company_name',
  'website': 'website',
  'url': 'website',
  'web': 'website',
  'country': 'country',
  'industry': 'industry',
  'sector': 'industry',
  'bvd_id': 'bvd_id',
  'bvd id': 'bvd_id',
  'database id': 'bvd_id',
}

function parseExcel(file: File) {
  uploadedFilename.value = file.name

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = e.target?.result
      const wb = XLSX.read(data, { type: 'array' })
      const sheetName = wb.SheetNames[0]
      if (!sheetName) { saveError.value = 'Excel file has no sheets.'; return }
      const ws = wb.Sheets[sheetName]
      if (!ws) { saveError.value = 'Could not read the sheet.'; return }
      const rawRows = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, { defval: '' })

      if (!rawRows.length) {
        saveError.value = 'No data found in the file.'
        return
      }

      // Open the Column Mapper modal — let user confirm/adjust mappings
      rawExcelRows.value = rawRows
      mapperFilename.value = file.name
      mapperOpen.value = true
      saveError.value = null
    } catch {
      saveError.value = 'Could not read the file. Make sure it is a valid .xlsx or .xls file.'
    }
  }
  reader.readAsArrayBuffer(file)
}

/** Called when user confirms import from ColumnMapperModal */
function onMapperImport(rows: CompanyRow[]) {
  mapperOpen.value = false
  benchmarkStore.setCompanies(rows)
  saveError.value = null
}

// ── File input / drag-drop ─────────────────────────────────────────────────
function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) parseExcel(file)
  // Reset so the same file can be re-selected
  input.value = ''
}

function onDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) parseExcel(file)
}

function openFilePicker() {
  fileInputRef.value?.click()
}

// ── Row editing ───────────────────────────────────────────────────────────────
function addRow() {
  benchmarkStore.addRow()
  // Scroll to bottom of table on next tick
  setTimeout(() => {
    tableBodyRef.value?.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, 50)
}

function deleteRow(id: number) {
  benchmarkStore.deleteRow(id)
}

function onCellBlur(id: number, field: keyof Omit<CompanyRow, '_id' | 'errors'>, event: FocusEvent) {
  const el = event.target as HTMLElement
  benchmarkStore.updateField(id, field, el.innerText.trim())
}

function onCellKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    ;(event.target as HTMLElement).blur()
  }
}

// ── Validation ────────────────────────────────────────────────────────────────
function validate(): boolean {
  let valid = true
  for (const row of benchmarkStore.companies) {
    row.errors = {}
    if (!row.company_name.trim()) {
      row.errors['company_name'] = 'Required'
      valid = false
    }
    if (!row.website.trim()) {
      row.errors['website'] = 'Required'
      valid = false
    }
  }
  return valid
}

// ── Save & Continue ───────────────────────────────────────────────────────────
async function saveAndContinue() {
  saveError.value = null
  if (!validate()) {
    saveError.value = 'Please fill in all required fields (Company Name and Website).'
    return
  }
  if (benchmarkStore.companies.length === 0) {
    saveError.value = 'Add at least one company before continuing.'
    return
  }

  saving.value = true
  try {
    // Re-serialise table rows back to xlsx in memory
    const wsData = benchmarkStore.companies.map(r => ({
      company_name: r.company_name,
      website:      r.website,
      country:      r.country,
      industry:     r.industry,
      bvd_id:       r.bvd_id,
    }))
    const ws = XLSX.utils.json_to_sheet(wsData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Companies')
    const xlsxBytes = XLSX.write(wb, { type: 'array', bookType: 'xlsx' })
    const blob = new Blob([xlsxBytes], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    // Create a File object for the service layer
    const file = new File([blob], uploadedFilename.value ?? 'companies.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    const data = await batchService.upload(file)
    benchmarkStore.setBatch(data.batch_id, data.filename, data.total_companies)
    emit('uploaded', data.batch_id)
  } catch (err: unknown) {
    const msg = (err as { message?: string })?.message
    saveError.value = msg || 'Upload failed. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".xlsx,.xls"
      class="hidden"
      @change="onFileChange"
    />

    <!-- Column Mapper Modal — opened after file parse -->
    <ColumnMapperModal
      :open="mapperOpen"
      :raw-rows="rawExcelRows"
      :filename="mapperFilename"
      @close="mapperOpen = false"
      @import="onMapperImport"
    />

    <!-- ── LOADING STATE ──────────────────────────────────────────────── -->
    <div
      v-if="loadingExisting"
      class="flex-1 flex flex-col items-center justify-center min-h-[360px] gap-3"
    >
      <Loader2 :size="28" class="animate-spin text-[var(--color-primary)]" />
      <p class="text-sm text-[var(--color-text-muted)] m-0">Loading batch data…</p>
    </div>

    <!-- ── STATE A: EMPTY DROP ZONE ──────────────────────────────────────── -->
    <div
      v-else-if="!hasRows"
      class="flex-1 flex flex-col items-center justify-center min-h-[360px] p-8"
    >
      <!-- Drop zone -->
      <div
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
        @click="openFilePicker"
        :class="[
          'w-full max-w-[540px] flex flex-col items-center justify-center gap-4',
          'border-2 border-dashed rounded-[var(--radius-lg)] px-10 py-14 cursor-pointer',
          'transition-all duration-200',
          isDragging
            ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] scale-[1.01]'
            : 'border-[var(--color-border)] bg-[var(--color-bg-alt)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)]',
        ]"
      >
        <div class="w-14 h-14 rounded-[var(--radius-md)] bg-[var(--color-primary-light)] text-[var(--color-primary)] flex items-center justify-center">
          <FileSpreadsheet :size="28" />
        </div>
        <div class="text-center">
          <p class="text-base font-semibold text-[var(--color-text)] m-0">
            Drop your Excel file here
          </p>
          <p class="text-sm text-[var(--color-text-muted)] mt-1 m-0">
            or click to browse — accepts <code class="text-[0.78rem] font-mono opacity-80">.xlsx</code> / <code class="text-[0.78rem] font-mono opacity-80">.xls</code>
          </p>
        </div>
        <div class="flex items-center gap-2 px-5 py-2 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-sm font-semibold pointer-events-none">
          <Upload :size="15" />
          Choose File
        </div>
      </div>

      <!-- Manual add -->
      <p class="text-sm text-[var(--color-text-muted)] mt-5">
        or
        <button
          id="upload-add-manually"
          @click="addRow"
          class="text-[var(--color-primary)] font-semibold border-none bg-transparent cursor-pointer p-0 font-sans hover:underline"
        >
          add companies manually
        </button>
      </p>

      <!-- Error -->
      <p v-if="saveError" class="flex items-center gap-1.5 text-sm text-[var(--color-danger)] mt-3 font-medium">
        <AlertCircle :size="14" />{{ saveError }}
      </p>
    </div>

    <!-- ── STATE B: TABLE ────────────────────────────────────────────────── -->
    <div v-else class="flex flex-col flex-1 overflow-hidden">
      <!-- File badge -->
      <div v-if="uploadedFilename" class="flex items-center gap-2 px-1 pb-3">
        <div class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-full px-3 py-1">
          <FileSpreadsheet :size="12" />
          {{ uploadedFilename }}
          <button
            @click="uploadedFilename = null; benchmarkStore.reset(); openFilePicker()"
            class="ml-1 border-none bg-transparent p-0 cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors"
            title="Upload different file"
          >
            <X :size="11" />
          </button>
        </div>
        <button
          @click="openFilePicker"
          class="text-xs text-[var(--color-primary)] border-none bg-transparent cursor-pointer font-medium hover:underline p-0 font-sans"
        >
          Upload different file
        </button>
      </div>

      <!-- Table wrapper -->
      <div class="flex-1 overflow-auto border border-[var(--color-border)] rounded-[var(--radius-md)] bg-[var(--color-surface)]">
        <table class="w-full border-collapse text-sm" style="min-width: 960px;">
          <!-- Sticky header -->
          <thead>
            <tr class="sticky top-0 z-10 bg-[var(--color-bg-alt)] border-b border-[var(--color-border)]">
              <th class="w-10 px-3 py-2.5 text-center text-xs font-semibold text-[var(--color-text-muted)]">#</th>
              <th
                v-for="col in columns"
                :key="col.key"
                :style="{ width: col.width, minWidth: col.width }"
                class="px-3 py-2.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] whitespace-nowrap"
              >
                {{ col.label }}
                <span v-if="col.required" class="text-[var(--color-danger)] ml-0.5">*</span>
              </th>
              <th class="w-10 px-2 py-2.5"></th>
            </tr>
          </thead>

          <tbody ref="tableBodyRef">
            <tr
              v-for="(row, idx) in benchmarkStore.companies"
              :key="row._id"
              class="border-b border-[var(--color-border)] hover:bg-[var(--color-primary-light)] transition-colors group"
            >
              <!-- Row number -->
              <td class="px-3 py-1.5 text-center text-xs text-[var(--color-text-muted)]">{{ idx + 1 }}</td>

              <!-- Editable cells -->
              <td
                v-for="col in columns"
                :key="col.key"
                :style="{ width: col.width, minWidth: col.width }"
                class="px-0 py-0"
              >
                <div
                  :id="`cell-${row._id}-${col.key}`"
                  contenteditable="true"
                  :class="[
                    'w-full px-3 py-2 outline-none text-sm text-[var(--color-text)]',
                    'focus:bg-[var(--color-primary-light)] focus:shadow-[inset_0_0_0_2px_var(--color-primary)]',
                    'rounded-sm min-h-[36px] whitespace-nowrap overflow-hidden',
                    row.errors[col.key]
                      ? 'shadow-[inset_0_0_0_2px_var(--color-danger)] bg-[rgba(244,63,94,0.05)]'
                      : '',
                  ]"
                  @blur="onCellBlur(row._id, col.key, $event)"
                  @keydown="onCellKeydown"
                  :title="row.errors[col.key]"
                >{{ row[col.key] }}</div>
              </td>

              <!-- Delete -->
              <td class="px-2 py-1.5 text-center">
                <button
                  @click="deleteRow(row._id)"
                  class="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center border-none bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-danger)] rounded-md hover:bg-[rgba(244,63,94,0.1)] transition-all"
                  title="Delete row"
                >
                  <Trash2 :size="14" />
                </button>
              </td>
            </tr>

            <!-- Add row inline -->
            <tr class="border-b border-[var(--color-border)]">
              <td colspan="7" class="px-3 py-2">
                <button
                  id="table-add-row"
                  @click="addRow"
                  class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] border-none bg-transparent cursor-pointer font-sans hover:text-[var(--color-primary)] transition-colors p-0"
                >
                  <Plus :size="13" />
                  Add row
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── STICKY ACTION BAR ─────────────────────────────────────────── -->
      <div class="sticky bottom-0 flex items-center gap-3 pt-3 pb-1 bg-[var(--color-bg)] border-t border-[var(--color-border)] mt-3">
        <!-- Company count + New Batch button -->
        <span class="text-xs text-[var(--color-text-muted)] mr-auto flex items-center gap-2">
          {{ benchmarkStore.companies.length }} {{ benchmarkStore.companies.length === 1 ? 'company' : 'companies' }}
          <button
            @click="newBatch"
            title="Start a new batch (clears current data)"
            class="flex items-center gap-1 text-[var(--color-text-muted)] border-none bg-transparent cursor-pointer hover:text-[var(--color-primary)] transition-colors p-0 text-xs font-medium"
          >
            <FilePlus2 :size="13" />
            New Batch
          </button>
        </span>

        <!-- Error message -->
        <div v-if="saveError" class="flex items-center gap-1.5 text-xs text-[var(--color-danger)] font-medium max-w-[280px]">
          <AlertCircle :size="12" class="shrink-0" />
          <span class="truncate">{{ saveError }}</span>
        </div>

        <!-- Add Row -->
        <button
          id="action-add-row"
          @click="addRow"
          class="flex items-center gap-1.5 px-3.5 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-transparent text-sm font-medium text-[var(--color-text-secondary)] cursor-pointer font-sans hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all"
        >
          <Plus :size="14" />
          Add Row
        </button>

        <!-- Upload Excel -->
        <button
          id="action-upload-excel"
          @click="openFilePicker"
          class="flex items-center gap-1.5 px-3.5 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-transparent text-sm font-medium text-[var(--color-text-secondary)] cursor-pointer font-sans hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all"
        >
          <Upload :size="14" />
          Upload Excel
        </button>

        <!-- Save & Continue -->
        <button
          id="action-save-continue"
          @click="saveAndContinue"
          :disabled="saving"
          class="flex items-center gap-2 px-5 py-2 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-sm font-semibold cursor-pointer font-sans border-none transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <span v-if="saving">Uploading…</span>
          <span v-else class="flex items-center gap-2">
            Save & Continue
            <ArrowRight :size="15" />
          </span>
        </button>
      </div>
    </div>
  </div>
</template>
