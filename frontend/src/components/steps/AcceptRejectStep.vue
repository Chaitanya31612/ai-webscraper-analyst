<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  XCircle,
  Clock3,
  ArrowRight,
} from 'lucide-vue-next'
import { batchService } from '@/services/batchService'
import type {
  BatchStatusResponse,
  CompanyListItem,
  CriteriaUpdate,
} from '@/types/api'
import CriteriaModal from './CriteriaModal.vue'
import CompanyDetailDrawer from './CompanyDetailDrawer.vue'

const props = defineProps<{
  batchId: string | null
}>()

const emit = defineEmits<{ (e: 'next'): void }>()

const isLoading = ref(false)
const isRefreshing = ref(false)
const isSavingCriteria = ref(false)
const isInitiating = ref(false)
const autoRefresh = ref(false)
const showCriteriaModal = ref(false)
const decisionRequested = ref(false)
const companies = ref<CompanyListItem[]>([])
const batchStatus = ref<BatchStatusResponse | null>(null)
const criteria = ref<CriteriaUpdate>({})
const errorMessage = ref<string | null>(null)
const drawerOpen = ref(false)
const selectedCompany = ref<CompanyListItem | null>(null)

const hasCompanies = computed(() => companies.value.length > 0)

const acceptedCount = computed(() => companies.value.filter((c) => c.decision === 'accept').length)
const rejectedCount = computed(() => companies.value.filter((c) => c.decision === 'reject').length)
const reviewCount = computed(() => companies.value.filter((c) => c.decision === 'manual_review').length)
const decidingCount = computed(() => companies.value.filter((c) => c.status === 'deciding').length)
const decisionReadyCount = computed(() => {
  return companies.value.filter((c) => c.status === 'complete' && !!c.profile).length
})
const undecidedCount = computed(() => {
  return companies.value.filter((c) => c.status === 'complete' && !c.decision && c.profile).length
})
const evaluatingCount = computed(() => decidingCount.value + undecidedCount.value)

const totalTracked = computed(() => {
  return acceptedCount.value + rejectedCount.value + reviewCount.value + evaluatingCount.value
})

const pctAccepted = computed(() => (totalTracked.value ? (acceptedCount.value / totalTracked.value) * 100 : 0))
const pctRejected = computed(() => (totalTracked.value ? (rejectedCount.value / totalTracked.value) * 100 : 0))
const pctEvaluating = computed(() => (totalTracked.value ? (evaluatingCount.value / totalTracked.value) * 100 : 0))
const pctReview = computed(() => (totalTracked.value ? (reviewCount.value / totalTracked.value) * 100 : 0))

const criteriaConfigured = computed(() => {
  return [
    criteria.value.accept_products,
    criteria.value.reject_products,
    criteria.value.ideal_functional_profile,
    criteria.value.reject_functions,
  ].some((value) => (value ?? '').trim().length > 0)
})

const canInitiate = computed(() => {
  return Boolean(props.batchId) &&
    criteriaConfigured.value &&
    decisionReadyCount.value > 0 &&
    !isInitiating.value
})

const hasDecisions = computed(() => {
  return acceptedCount.value + rejectedCount.value + reviewCount.value > 0
})

const canNext = computed(() => {
  return acceptedCount.value + rejectedCount.value + reviewCount.value > 0
})

const shouldPoll = computed(() => {
  return autoRefresh.value &&
    decisionRequested.value &&
    (undecidedCount.value > 0 || decidingCount.value > 0) &&
    !!props.batchId
})

function parseCriteria(raw: Record<string, unknown> | null | undefined): CriteriaUpdate {
  if (!raw) return {}
  return {
    accept_products: typeof raw.accept_products === 'string' ? raw.accept_products : undefined,
    reject_products: typeof raw.reject_products === 'string' ? raw.reject_products : undefined,
    ideal_functional_profile:
      typeof raw.ideal_functional_profile === 'string' ? raw.ideal_functional_profile : undefined,
    reject_functions: typeof raw.reject_functions === 'string' ? raw.reject_functions : undefined,
  }
}

function setData(companiesData: CompanyListItem[], statusData: BatchStatusResponse) {
  companies.value = companiesData
  batchStatus.value = statusData
  criteria.value = parseCriteria(statusData.criteria)

  const hasDecisionActivity = companiesData.some((company) => company.status === 'deciding' || !!company.decision)
  if (hasDecisionActivity) {
    decisionRequested.value = true
  }
}

async function loadData() {
  if (!props.batchId) return

  isLoading.value = true
  errorMessage.value = null
  try {
    const [companiesData, statusData] = await Promise.all([
      batchService.getCompanies(props.batchId),
      batchService.getStatus(props.batchId),
    ])
    setData(companiesData, statusData)
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string })?.message || 'Failed to load companies.'
  } finally {
    isLoading.value = false
  }
}

async function refreshData() {
  if (!props.batchId || isRefreshing.value) return

  isRefreshing.value = true
  try {
    const [companiesData, statusData] = await Promise.all([
      batchService.getCompanies(props.batchId),
      batchService.getStatus(props.batchId),
    ])
    setData(companiesData, statusData)

    if (decisionRequested.value && undecidedCount.value === 0 && decidingCount.value === 0) {
      autoRefresh.value = false
    }
  } catch {
    // keep silent during polling retries
  } finally {
    isRefreshing.value = false
  }
}

onMounted(loadData)
watch(() => props.batchId, loadData)

let pollTimer: ReturnType<typeof setInterval> | null = null

watch(shouldPoll, (enabled) => {
  if (enabled) {
    pollTimer = setInterval(refreshData, 3000)
    return
  }
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function saveCriteria(payload: CriteriaUpdate) {
  if (!props.batchId) return

  isSavingCriteria.value = true
  errorMessage.value = null
  try {
    const response = await batchService.saveCriteria(props.batchId, payload)
    criteria.value = parseCriteria(response.criteria || null)
    showCriteriaModal.value = false
    await refreshData()
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string })?.message || 'Failed to save criteria.'
  } finally {
    isSavingCriteria.value = false
  }
}

async function initiateDecisions() {
  if (!props.batchId || !canInitiate.value) return

  isInitiating.value = true
  errorMessage.value = null
  try {
    await batchService.triggerDecisions(props.batchId)
    decisionRequested.value = true
    autoRefresh.value = true
    await refreshData()
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string })?.message || 'Failed to initiate decisions.'
  } finally {
    isInitiating.value = false
  }
}

function cleanDomain(url: string): string {
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}

function profileText(company: CompanyListItem, field: string): string {
  if (!company.profile) return ''
  const value = (company.profile as Record<string, unknown>)[field]
  return typeof value === 'string' ? value : ''
}

function productsText(company: CompanyListItem): string {
  if (!company.profile) return ''
  const products = (company.profile as Record<string, unknown>).products_services
  if (!Array.isArray(products)) return ''
  const names = products
    .map((item) => (typeof item === 'object' && item ? (item as { name?: unknown }).name : ''))
    .filter((value): value is string => typeof value === 'string' && value.length > 0)
  return names.slice(0, 4).join(', ')
}

function decisionLabel(company: CompanyListItem): string {
  if (company.status === 'deciding') return 'Evaluating'
  if (company.decision === 'accept') return 'Accepted'
  if (company.decision === 'reject') return 'Rejected'
  if (company.decision === 'manual_review') return 'Manual Review'
  if (company.status === 'error') return 'Error'
  return 'Start analysis'
}

function decisionClass(company: CompanyListItem): string {
  if (company.status === 'deciding') return 'chip-evaluating'
  if (company.decision === 'accept') return 'chip-accepted'
  if (company.decision === 'reject') return 'chip-rejected'
  if (company.decision === 'manual_review') return 'chip-review'
  if (company.status === 'error') return 'chip-error'
  return 'chip-pending'
}

function rowClass(company: CompanyListItem): string {
  if (company.decision === 'accept') return 'row-accepted'
  if (company.decision === 'reject') return 'row-rejected'
  if (company.status === 'deciding') return 'row-evaluating'
  return ''
}

function openDrawer(company: CompanyListItem) {
  selectedCompany.value = company
  drawerOpen.value = true
}

function closeDrawer() {
  drawerOpen.value = false
}
</script>

<template>
  <div class="flex flex-col h-full gap-4">
    <div
      v-if="isLoading"
      class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-3"
    >
      <Loader2 :size="28" class="animate-spin text-[var(--color-primary)]" />
      <p class="text-sm text-[var(--color-text-secondary)] m-0">Loading Accept/Reject data…</p>
    </div>

    <div
      v-else-if="!hasCompanies"
      class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-3"
    >
      <AlertCircle :size="24" class="text-[var(--color-text-muted)]" />
      <p class="text-base font-semibold text-[var(--color-text)] m-0">No companies found.</p>
      <p class="text-sm text-[var(--color-text-secondary)] max-w-[380px] leading-relaxed m-0">
        Complete the web search step first so AI profiles are available for Accept/Reject decisions.
      </p>
    </div>

    <template v-else>
      <div class="flex items-center gap-3 justify-between">
        <p class="text-xs text-[var(--color-text-muted)] m-0">
          Analyze companies for comparability using configured Accept/Reject criteria.
        </p>
        <div class="flex items-center gap-3">
          <span
            v-if="acceptedCount === 0 && decisionRequested"
            class="text-xs font-semibold text-[var(--color-text-muted)] bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-full px-2.5 py-1"
          >
            No AI accepted companies
          </span>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <span class="text-xs text-[var(--color-text-muted)] font-medium">Auto-updates</span>
            <button
              @click="autoRefresh = !autoRefresh"
              :class="[
                'relative w-9 h-5 rounded-full border-2 transition-all duration-200 cursor-pointer focus:outline-none',
                autoRefresh
                  ? 'bg-[var(--color-primary)] border-[var(--color-primary)]'
                  : 'bg-[var(--color-bg-alt)] border-[var(--color-border)]',
              ]"
              :aria-pressed="autoRefresh"
            >
              <span
                :class="[
                  'absolute top-[1px] left-[1px] w-3.5 h-3.5 rounded-full bg-white shadow-sm transition-transform duration-200',
                  autoRefresh ? 'translate-x-[16px]' : 'translate-x-0',
                ]"
              />
            </button>
          </label>

          <button
            @click="refreshData"
            :disabled="isRefreshing"
            class="w-8 h-8 flex items-center justify-center rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all disabled:opacity-50"
            title="Refresh now"
          >
            <RefreshCw :size="14" :class="isRefreshing ? 'animate-spin' : ''" />
          </button>
        </div>
      </div>

      <div class="flex-1 border border-[var(--color-border)] rounded-[var(--radius-md)] bg-[var(--color-surface)] overflow-auto">
        <table class="w-full border-collapse text-sm" style="min-width: 1240px;">
          <thead>
            <tr class="sticky top-0 z-10 bg-[var(--color-bg-alt)] border-b border-[var(--color-border)]">
              <th class="w-10 px-3 py-3 text-center text-xs font-semibold text-[var(--color-text-muted)]">#</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:220px">Company</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:140px">Status</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:220px">Products/Services</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:180px">Functional Profile</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:160px">Independence</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:240px">Custom Comment</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(company, index) in companies"
              :key="company.id"
              @click="openDrawer(company)"
              :class="['border-b border-[var(--color-border)] hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer', rowClass(company)]"
            >
              <td class="px-3 py-3 text-center text-xs text-[var(--color-text-muted)]">{{ index + 1 }}</td>

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

              <td class="px-3 py-3">
                <span
                  :class="[
                    'inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full',
                    decisionClass(company),
                  ]"
                >
                  <Loader2 v-if="company.status === 'deciding'" :size="11" class="animate-spin" />
                  <CheckCircle2 v-else-if="company.decision === 'accept'" :size="11" />
                  <XCircle v-else-if="company.decision === 'reject'" :size="11" />
                  <AlertCircle v-else-if="company.status === 'error'" :size="11" />
                  <Clock3 v-else :size="11" />
                  {{ decisionLabel(company) }}
                </span>
              </td>

              <td class="px-3 py-3">
                <p v-if="productsText(company)" class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-2 max-w-[220px]">
                  {{ productsText(company) }}
                </p>
                <div v-else-if="company.status === 'deciding'" class="h-3 w-36 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>

              <td class="px-3 py-3">
                <p v-if="profileText(company, 'functional_profile')" class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-2 max-w-[180px]">
                  {{ profileText(company, 'functional_profile') }}
                </p>
                <div v-else-if="company.status === 'deciding'" class="h-3 w-24 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>

              <td class="px-3 py-3">
                <p v-if="profileText(company, 'company_size')" class="text-xs text-[var(--color-text-secondary)] m-0">
                  {{ profileText(company, 'company_size') }}
                </p>
                <span v-else class="text-xs text-[var(--color-text-muted)]">No information indicated</span>
              </td>

              <td class="px-3 py-3">
                <p v-if="company.reasoning" class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-2 max-w-[260px]">
                  {{ company.reasoning }}
                </p>
                <div v-else-if="company.status === 'deciding'" class="h-3 w-40 rounded bg-gradient-to-r from-[var(--color-bg-alt)] via-[var(--color-border)] to-[var(--color-bg-alt)] shimmer"></div>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="sticky bottom-0 bg-[var(--color-bg)] border-t border-[var(--color-border)] pt-3 pb-1 flex flex-col gap-3">
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <span class="text-xs text-[var(--color-text-muted)] font-medium">
              PROGRESS (INCLUDED COMPANIES: {{ companies.length }})
            </span>
            <div class="flex items-center gap-3 text-xs">
              <span v-if="rejectedCount > 0" class="flex items-center gap-1 text-[var(--color-danger)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[var(--color-danger)] inline-block" />
                Rejected ({{ rejectedCount }})
              </span>
              <span v-if="acceptedCount > 0" class="flex items-center gap-1 text-[var(--color-accent)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[var(--color-accent)] inline-block" />
                Accepted ({{ acceptedCount }})
              </span>
              <span v-if="evaluatingCount > 0" class="flex items-center gap-1 text-[rgba(245,158,11,1)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[rgba(245,158,11,1)] inline-block" />
                Evaluating ({{ evaluatingCount }})
              </span>
              <span v-if="reviewCount > 0" class="flex items-center gap-1 text-[rgba(129,140,248,1)] font-medium">
                <span class="w-2 h-2 rounded-full bg-[rgba(129,140,248,1)] inline-block" />
                Review ({{ reviewCount }})
              </span>
            </div>
          </div>

          <div class="relative h-1.5 rounded-full bg-[var(--color-bg-alt)] border border-[var(--color-border)] overflow-hidden">
            <div
              class="absolute left-0 top-0 h-full bg-[var(--color-danger)] transition-all duration-500"
              :style="{ width: `${pctRejected}%` }"
            />
            <div
              class="absolute top-0 h-full bg-[var(--color-accent)] transition-all duration-500"
              :style="{ left: `${pctRejected}%`, width: `${pctAccepted}%` }"
            />
            <div
              class="absolute top-0 h-full bg-[rgba(245,158,11,1)] transition-all duration-500"
              :style="{ left: `${pctRejected + pctAccepted}%`, width: `${pctEvaluating}%` }"
            />
            <div
              class="absolute top-0 h-full bg-[rgba(129,140,248,1)] transition-all duration-500"
              :style="{ left: `${pctRejected + pctAccepted + pctEvaluating}%`, width: `${pctReview}%` }"
            />
          </div>
        </div>

        <p v-if="errorMessage" class="flex items-center gap-1.5 text-xs text-[var(--color-danger)] font-medium m-0">
          <AlertCircle :size="12" />{{ errorMessage }}
        </p>

        <div class="flex items-center gap-3 justify-end">
          <button
            @click="showCriteriaModal = true"
            class="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] text-sm font-semibold text-[var(--color-text)] cursor-pointer transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)]"
          >
            {{ criteriaConfigured ? 'Update Accept/Reject Criteria' : 'Set Accept/Reject Criteria' }}
          </button>

          <button
            @click="initiateDecisions"
            :disabled="!canInitiate"
            class="flex items-center gap-2 px-5 py-2 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-sm font-semibold cursor-pointer font-sans border-none transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="isInitiating || (autoRefresh && undecidedCount > 0)" :size="14" class="animate-spin" />
            {{ isInitiating ? 'Initiating…' : hasDecisions ? 'Re-run Accept/Reject' : 'Initiate Accept/Reject' }}
          </button>

          <button
            @click="emit('next')"
            :disabled="!canNext"
            class="flex items-center gap-2 px-5 py-2 rounded-[var(--radius-sm)] text-sm font-semibold cursor-pointer font-sans border-none transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            :class="canNext
              ? 'bg-[var(--color-accent)] text-white hover:opacity-90 hover:shadow-[0_4px_12px_rgba(52,211,153,0.3)]'
              : 'bg-[var(--color-bg-alt)] text-[var(--color-text-muted)] border border-[var(--color-border)]'"
          >
            Next Step
            <ArrowRight :size="14" />
          </button>
        </div>
      </div>
    </template>

    <CriteriaModal
      :open="showCriteriaModal"
      :initial-criteria="criteria"
      :saving="isSavingCriteria"
      @close="showCriteriaModal = false"
      @save="saveCriteria"
    />

    <CompanyDetailDrawer
      :company="selectedCompany"
      :open="drawerOpen"
      :show-footer-actions="false"
      @close="closeDrawer"
      @update-url="closeDrawer"
      @remove-results="closeDrawer"
    />
  </div>
</template>

<style scoped>
.chip-pending {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.chip-evaluating {
  color: rgba(245, 158, 11, 1);
  background: rgba(245, 158, 11, 0.12);
}

.chip-accepted {
  color: var(--color-accent);
  background: rgba(52, 211, 153, 0.12);
}

.chip-rejected {
  color: var(--color-danger);
  background: rgba(244, 63, 94, 0.1);
}

.chip-review {
  color: rgba(129, 140, 248, 1);
  background: rgba(129, 140, 248, 0.12);
}

.chip-error {
  color: var(--color-danger);
  background: rgba(244, 63, 94, 0.08);
}

.row-accepted {
  background: rgba(52, 211, 153, 0.08);
}

.row-rejected {
  background: rgba(244, 63, 94, 0.06);
}

.row-evaluating {
  background: rgba(245, 158, 11, 0.08);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.shimmer {
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
</style>
