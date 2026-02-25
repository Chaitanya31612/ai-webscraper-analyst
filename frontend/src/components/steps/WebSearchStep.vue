<script setup lang="ts">
/**
 * WebSearchStep — Step 2 of the Benchmarking workflow.
 *
 * Displays the per-company scraping status table and lets the user
 * initiate AI-powered website analysis.
 *
 * Data flow:
 *   - Receives batchId from BenchmarkView (from URL /benchmark/:batchId)
 *   - Loads companies via GET /api/companies/batch/:batchId
 *   - "Initiate Search" calls POST /api/batches/:batchId/confirm
 *   - Auto-refresh polls GET /api/batches/:batchId/status + companies
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  Search, RefreshCw, ChevronRight, Globe, ArrowRight,
  CheckCircle2, Clock, Loader2, AlertCircle, X, Eye,
} from 'lucide-vue-next'
import { batchService } from '@/services/batchService'
import type { CompanyListItem, BatchStatusResponse } from '@/types/api'
import CompanyDetailDrawer from './CompanyDetailDrawer.vue'

// ── Props / emits ─────────────────────────────────────────────────────────────
const props = defineProps<{
  batchId: string | null
}>()

const emit = defineEmits<{ (e: 'next'): void }>()

// ── Local state ───────────────────────────────────────────────────────────────
const autoRefresh     = ref(false)
const isInitiating    = ref(false)
const isRefreshing    = ref(false)
const isLoading       = ref(false)
const searchStarted   = ref(false)
const searchError     = ref<string | null>(null)
const drawerOpen      = ref(false)
const selectedCompany = ref<CompanyListItem | null>(null)
const companies       = ref<CompanyListItem[]>([])
const batchStatus     = ref<BatchStatusResponse | null>(null)

const hasCompanies = computed(() => companies.value.length > 0)

// ── Status counts for footer bar ──────────────────────────────────────────────
const statusCounts = computed(() => {
  const counts = { pending: 0, scraping: 0, scraped: 0, analyzing: 0, complete: 0, error: 0, excluded: 0 }
  for (const c of companies.value) {
    const s = c.status as keyof typeof counts
    if (s in counts) counts[s]++
  }
  return counts
})

const totalIncluded = computed(() => companies.value.filter(c => c.status !== 'excluded').length)
const totalAnalysed = computed(() => statusCounts.value.complete)
const canProceed    = computed(() => totalAnalysed.value > 0)

// Progress widths for the multi-segment bar
const pctSearching = computed(() => totalIncluded.value === 0 ? 0 : (statusCounts.value.scraping  / totalIncluded.value) * 100)
const pctAnalysing = computed(() => totalIncluded.value === 0 ? 0 : (statusCounts.value.analyzing / totalIncluded.value) * 100)
const pctAnalysed  = computed(() => totalIncluded.value === 0 ? 0 : (statusCounts.value.complete  / totalIncluded.value) * 100)

// Are we currently processing? (auto-stop polling when done)
const isProcessing = computed(() => {
  if (!batchStatus.value) return false
  return batchStatus.value.status === 'processing'
})

// ── Status config map ─────────────────────────────────────────────────────────
interface StatusCfg { label: string; chip: string; icon: unknown; pulse?: boolean }

function getStatus(s: string): StatusCfg {
  const map: Record<string, StatusCfg> = {
    pending:   { label: 'Pending',   chip: 'chip-pending',   icon: Clock },
    scraping:  { label: 'Searching', chip: 'chip-searching', icon: Loader2, pulse: true },
    scraped:   { label: 'Scraped',   chip: 'chip-scraped',   icon: Globe },
    analyzing: { label: 'Analysing', chip: 'chip-analysing', icon: Loader2, pulse: true },
    complete:  { label: 'Analysed',  chip: 'chip-analysed',  icon: CheckCircle2 },
    error:     { label: 'Error',     chip: 'chip-error',     icon: AlertCircle },
    excluded:  { label: 'Excluded',  chip: 'chip-excluded',  icon: X },
  }
  return map[s] ?? map['pending']!
}

// ── Load initial data ─────────────────────────────────────────────────────────
async function loadData() {
  if (!props.batchId) return
  isLoading.value = true
  try {
    const [companiesData, statusData] = await Promise.all([
      batchService.getCompanies(props.batchId),
      batchService.getStatus(props.batchId),
    ])
    companies.value = companiesData
    batchStatus.value = statusData

    // If batch is already processing, start polling
    if (statusData.status === 'processing') {
      searchStarted.value = true
      autoRefresh.value = true
    }
  } catch (e: unknown) {
    searchError.value = (e as { message?: string })?.message || 'Failed to load batch data.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

// Reload when batchId changes
watch(() => props.batchId, loadData)

// ── Auto-refresh polling ──────────────────────────────────────────────────────
let pollTimer: ReturnType<typeof setInterval> | null = null

watch(autoRefresh, (on) => {
  if (on) {
    pollTimer = setInterval(refreshStatus, 5000)
  } else {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = null
  }
})

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

async function refreshStatus() {
  if (!props.batchId || isRefreshing.value) return
  isRefreshing.value = true
  try {
    const [companiesData, statusData] = await Promise.all([
      batchService.getCompanies(props.batchId),
      batchService.getStatus(props.batchId),
    ])
    companies.value = companiesData
    batchStatus.value = statusData

    // Auto-stop polling when processing is done
    if (statusData.status !== 'processing') {
      autoRefresh.value = false
    }
  } catch {
    // Silently ignore polling errors — will retry next interval
  } finally {
    isRefreshing.value = false
  }
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function initiateSearch() {
  if (!props.batchId) {
    searchError.value = 'No batch found. Please upload data first.'
    return
  }
  searchError.value = null
  isInitiating.value = true
  try {
    await batchService.confirm(props.batchId)
    searchStarted.value = true
    autoRefresh.value = true // Start polling automatically
  } catch (e: unknown) {
    searchError.value = (e as { message?: string })?.message || 'Failed to start search.'
  } finally {
    isInitiating.value = false
  }
}

// ── Profile helpers ───────────────────────────────────────────────────────────
function getProfileField(company: CompanyListItem, field: string): string {
  if (!company.profile) return ''
  return (company.profile as Record<string, unknown>)[field] as string || ''
}

function getProductNames(company: CompanyListItem): string[] {
  if (!company.profile) return []
  const products = (company.profile as Record<string, unknown>).products_services as Array<{ name: string }> | undefined
  return products?.map(p => p.name) || []
}

// ── Drawer ────────────────────────────────────────────────────────────────────
function openDrawer(company: CompanyListItem) {
  selectedCompany.value = company
  drawerOpen.value = true
}

function closeDrawer() {
  drawerOpen.value = false
}

function cleanDomain(url: string): string {
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}
</script>

<template>
  <div class="flex flex-col h-full gap-4">

    <!-- ── LOADING STATE ─────────────────────────────────────────────── -->
    <div
      v-if="isLoading"
      class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-3"
    >
      <Loader2 :size="28" class="animate-spin text-[var(--color-primary)]" />
      <p class="text-sm text-[var(--color-text-secondary)] m-0">Loading batch data…</p>
    </div>

    <!-- ── EMPTY STATE — no batch yet ─────────────────────────────────── -->
    <div
      v-else-if="!hasCompanies"
      class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-3"
    >
      <div class="w-14 h-14 rounded-[var(--radius-md)] bg-[var(--color-primary-light)] text-[var(--color-primary)] flex items-center justify-center mb-1">
        <Globe :size="28" />
      </div>
      <p class="text-base font-semibold text-[var(--color-text)] m-0">No companies found.</p>
      <p class="text-sm text-[var(--color-text-secondary)] max-w-[380px] leading-relaxed m-0">
        Go back to Upload Data and upload an Excel file to get started.
      </p>
    </div>

    <!-- ── COMPANY TABLE STATE ────────────────────────────────────────── -->
    <template v-else>

      <!-- Toolbar -->
      <div class="flex items-center gap-3 justify-between">
        <p class="text-xs text-[var(--color-text-muted)] m-0">
          AI-powered website analysis — track progress per company below.
        </p>
        <div class="flex items-center gap-3">
          <!-- Auto-refresh toggle -->
          <label
            id="auto-refresh-toggle"
            class="flex items-center gap-2 cursor-pointer select-none"
          >
            <span class="text-xs text-[var(--color-text-muted)] font-medium">Auto-refresh</span>
            <button
              @click="autoRefresh = !autoRefresh"
              :class="[
                'relative w-9 h-5 rounded-full border-2 transition-all duration-200 cursor-pointer focus:outline-none',
                autoRefresh
                  ? 'bg-[var(--color-primary)] border-[var(--color-primary)]'
                  : 'bg-[var(--color-bg-alt)] border-[var(--color-border)]',
              ]"
              :aria-pressed="autoRefresh"
              :title="autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh (every 5s)'"
            >
              <span
                :class="[
                  'absolute top-[1px] left-[1px] w-3.5 h-3.5 rounded-full bg-white shadow-sm transition-transform duration-200',
                  autoRefresh ? 'translate-x-[16px]' : 'translate-x-0',
                ]"
              />
            </button>
          </label>

          <!-- Manual refresh -->
          <button
            id="manual-refresh-btn"
            @click="refreshStatus"
            :disabled="isRefreshing"
            class="w-8 h-8 flex items-center justify-center rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all disabled:opacity-50"
            title="Refresh now"
          >
            <RefreshCw :size="14" :class="isRefreshing ? 'animate-spin' : ''" />
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="flex-1 border border-[var(--color-border)] rounded-[var(--radius-md)] bg-[var(--color-surface)] overflow-auto">
        <table class="w-full border-collapse text-sm" style="min-width: 1200px;">
          <thead>
            <tr class="sticky top-0 z-10 bg-[var(--color-bg-alt)] border-b border-[var(--color-border)]">
              <th class="w-10 px-3 py-3 text-center text-xs font-semibold text-[var(--color-text-muted)]">#</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:220px">Company</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:110px">Status</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:100px">Source</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:200px">Business</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:200px">Products/Services</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:160px">Functional Profile</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:180px">Structure &amp; Affiliation</th>
              <th class="w-12 px-2 py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(company, idx) in companies"
              :key="company.id"
              @click="openDrawer(company)"
              class="border-b border-[var(--color-border)] hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer group"
            >
              <!-- # -->
              <td class="px-3 py-3 text-center text-xs text-[var(--color-text-muted)]">{{ idx + 1 }}</td>

              <!-- Company name + website -->
              <td class="px-4 py-3">
                <p class="text-sm font-semibold text-[var(--color-text)] m-0 mb-0.5 truncate max-w-[200px]">
                  {{ company.company_name }}
                </p>
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span
                    v-if="company.country"
                    class="text-[0.65rem] font-medium text-[var(--color-text-muted)] bg-[var(--color-bg-alt)] border border-[var(--color-border)] px-1.5 py-px rounded-full"
                  >
                    {{ company.country }}
                  </span>
                  <a
                    v-if="company.website"
                    :href="company.website.startsWith('http') ? company.website : `https://${company.website}`"
                    target="_blank"
                    rel="noopener noreferrer"
                    @click.stop
                    class="text-[0.7rem] text-[var(--color-primary)] hover:underline max-w-[140px] truncate"
                  >
                    {{ cleanDomain(company.website) }}
                  </a>
                </div>
              </td>

              <!-- Status chip -->
              <td class="px-3 py-3">
                <span
                  :class="[
                    'inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full',
                    getStatus(company.status).chip,
                  ]"
                >
                  <component
                    :is="getStatus(company.status).icon"
                    :size="11"
                    :class="getStatus(company.status).pulse ? 'animate-spin' : ''"
                  />
                  {{ getStatus(company.status).label }}
                </span>
              </td>

              <!-- Source -->
              <td class="px-3 py-3">
                <span
                  :class="[
                    'inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full',
                    company.status === 'complete' || company.status === 'scraped'
                      ? 'text-[var(--color-info)] bg-[rgba(129,140,248,0.12)]'
                      : 'text-[var(--color-text-muted)] bg-[var(--color-bg-alt)] border border-[var(--color-border)]',
                  ]"
                >
                  <Globe :size="10" />
                  {{ company.status === 'complete' || company.status === 'scraped' ? 'Website' : '—' }}
                </span>
              </td>

              <!-- Business — description -->
              <td class="px-3 py-3">
                <p
                  v-if="getProfileField(company, 'business_description')"
                  class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-2 max-w-[220px]"
                >
                  {{ getProfileField(company, 'business_description') }}
                </p>
                <!-- Show loading shimmer when processing -->
                <div v-else-if="company.status === 'scraping' || company.status === 'analyzing'" class="flex flex-col gap-1.5">
                  <div class="h-3 w-full rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                  <div class="h-3 w-3/4 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                </div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>

              <!-- Products/Services -->
              <td class="px-3 py-3">
                <div v-if="getProductNames(company).length" class="flex flex-wrap gap-1 max-w-[220px]">
                  <span
                    v-for="name in getProductNames(company).slice(0, 3)"
                    :key="name"
                    class="text-[0.65rem] font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-alt)] border border-[var(--color-border)] px-1.5 py-0.5 rounded-full truncate max-w-[100px]"
                    :title="name"
                  >
                    {{ name }}
                  </span>
                  <span
                    v-if="getProductNames(company).length > 3"
                    class="text-[0.65rem] font-medium text-[var(--color-primary)] bg-[var(--color-primary-light)] px-1.5 py-0.5 rounded-full"
                  >
                    +{{ getProductNames(company).length - 3 }}
                  </span>
                </div>
                <div v-else-if="company.status === 'scraping' || company.status === 'analyzing'" class="flex gap-1.5">
                  <div class="h-5 w-16 rounded-full bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                  <div class="h-5 w-12 rounded-full bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                </div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>

              <!-- Functional Profile -->
              <td class="px-3 py-3">
                <p
                  v-if="getProfileField(company, 'functional_profile')"
                  class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-2 max-w-[180px]"
                >
                  {{ getProfileField(company, 'functional_profile') }}
                </p>
                <div v-else-if="company.status === 'scraping' || company.status === 'analyzing'" class="flex flex-col gap-1.5">
                  <div class="h-3 w-3/4 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                </div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>

              <!-- Structure & Affiliation -->
              <td class="px-3 py-3">
                <template v-if="company.profile">
                  <p class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-1">
                    {{ getProfileField(company, 'company_size') }}
                  </p>
                  <p
                    v-if="getProfileField(company, 'target_market')"
                    class="text-[0.65rem] text-[var(--color-text-muted)] m-0 mt-0.5 line-clamp-1 max-w-[180px]"
                  >
                    {{ getProfileField(company, 'target_market') }}
                  </p>
                </template>
                <div v-else-if="company.status === 'scraping' || company.status === 'analyzing'" class="flex flex-col gap-1.5">
                  <div class="h-3 w-20 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                  <div class="h-3 w-28 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                </div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>

              <!-- Eye / expand -->
              <td class="px-2 py-3 text-center">
                <button
                  @click.stop="openDrawer(company)"
                  class="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all"
                  title="View details"
                >
                  <Eye :size="13" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── Footer bar ──────────────────────────────────────────────── -->
      <div class="sticky bottom-0 bg-[var(--color-bg)] border-t border-[var(--color-border)] pt-3 pb-1 flex flex-col gap-3">

        <!-- Multi-segment progress bar + legend -->
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <span class="text-xs text-[var(--color-text-muted)] font-medium">
              PROGRESS (INCLUDED: {{ totalIncluded }} · TOTAL: {{ companies.length }})
            </span>
            <div class="flex items-center gap-3 text-xs">
              <span v-if="statusCounts.scraping > 0" class="flex items-center gap-1 text-[var(--color-primary)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[var(--color-primary)] inline-block" />
                Searching ({{ statusCounts.scraping }})
              </span>
              <span v-if="statusCounts.analyzing > 0" class="flex items-center gap-1 text-[rgba(251,146,60,1)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[rgba(251,146,60,1)] inline-block" />
                Analysing ({{ statusCounts.analyzing }})
              </span>
              <span v-if="statusCounts.complete > 0" class="flex items-center gap-1 text-[var(--color-accent)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[var(--color-accent)] inline-block" />
                Analysed ({{ statusCounts.complete }})
              </span>
            </div>
          </div>

          <!-- Segmented bar -->
          <div class="relative h-1.5 rounded-full bg-[var(--color-bg-alt)] border border-[var(--color-border)] overflow-hidden">
            <div
              class="absolute left-0 top-0 h-full bg-[var(--color-accent)] rounded-full transition-all duration-500"
              :style="{ width: `${pctAnalysed}%` }"
            />
            <div
              class="absolute top-0 h-full bg-[rgba(251,146,60,1)] rounded-full transition-all duration-500"
              :style="{ left: `${pctAnalysed}%`, width: `${pctAnalysing}%` }"
            />
            <div
              class="absolute top-0 h-full bg-[var(--color-primary)] rounded-full transition-all duration-500"
              :style="{ left: `${pctAnalysed + pctAnalysing}%`, width: `${pctSearching}%` }"
            />
          </div>
        </div>

        <!-- Error -->
        <p v-if="searchError" class="flex items-center gap-1.5 text-xs text-[var(--color-danger)] font-medium m-0">
          <AlertCircle :size="12" />{{ searchError }}
        </p>

        <!-- Action buttons -->
        <div class="flex items-center gap-3 justify-end">
          <!-- Initiate Search — only show before search started -->
          <button
            v-if="!searchStarted"
            id="initiate-search-btn"
            @click="initiateSearch"
            :disabled="isInitiating || !batchId"
            class="flex items-center gap-2 px-5 py-2 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-sm font-semibold cursor-pointer font-sans border-none transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="isInitiating" :size="14" class="animate-spin" />
            <Search v-else :size="14" />
            {{ isInitiating ? 'Starting…' : 'Initiate Search' }}
          </button>

          <!-- Processing indicator — show while actively processing -->
          <span
            v-if="searchStarted && isProcessing"
            class="flex items-center gap-2 text-xs text-[var(--color-primary)] font-medium"
          >
            <Loader2 :size="14" class="animate-spin" />
            Processing…
          </span>

          <!-- Next Step -->
          <button
            id="web-search-next-btn"
            @click="emit('next')"
            :disabled="!canProceed"
            class="flex items-center gap-2 px-5 py-2 rounded-[var(--radius-sm)] text-sm font-semibold cursor-pointer font-sans border-none transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            :class="canProceed
              ? 'bg-[var(--color-accent)] text-white hover:opacity-90 hover:shadow-[0_4px_12px_rgba(52,211,153,0.3)]'
              : 'bg-[var(--color-bg-alt)] text-[var(--color-text-muted)] border border-[var(--color-border)]'"
          >
            Next Step
            <ArrowRight :size="14" />
          </button>
        </div>
      </div>

    </template>

    <!-- ── Detail Drawer ───────────────────────────────────────────────── -->
    <CompanyDetailDrawer
      :company="selectedCompany"
      :open="drawerOpen"
      @close="closeDrawer"
      @update-url="closeDrawer"
      @remove-results="closeDrawer"
    />

  </div>
</template>

<style scoped>
/* ── Status chip variants ── */
.chip-pending {
  color: var(--color-text-muted);
  background: var(--color-bg-alt);
  border: 1px solid var(--color-border);
}
.chip-searching {
  color: var(--color-primary);
  background: var(--color-primary-light);
}
.chip-scraped {
  color: rgba(129, 140, 248, 1);
  background: rgba(129, 140, 248, 0.12);
}
.chip-analysing {
  color: rgba(251, 146, 60, 1);
  background: rgba(251, 146, 60, 0.1);
}
.chip-analysed {
  color: var(--color-accent);
  background: rgba(52, 211, 153, 0.12);
}
.chip-error {
  color: var(--color-danger);
  background: rgba(244, 63, 94, 0.08);
}
.chip-excluded {
  color: var(--color-text-muted);
  background: var(--color-bg-alt);
  border: 1px solid var(--color-border);
}

/* Line clamp */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Spin for icons */
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}

/* Shimmer loading animation */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.shimmer {
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
</style>
