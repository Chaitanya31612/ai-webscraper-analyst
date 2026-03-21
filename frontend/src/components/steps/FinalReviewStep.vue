<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Loader2,
  RefreshCw,
  XCircle,
} from 'lucide-vue-next'
import { batchService } from '@/services/batchService'
import { companyService } from '@/services/companyService'
import type { CompanyListItem } from '@/types/api'
import CompanyDetailDrawer from './CompanyDetailDrawer.vue'

const props = defineProps<{
  batchId: string | null
}>()

const emit = defineEmits<{ (e: 'next'): void }>()

const isLoading = ref(false)
const isRefreshing = ref(false)
const updatingCompanyId = ref<number | null>(null)
const errorMessage = ref<string | null>(null)
const companies = ref<CompanyListItem[]>([])
const drawerOpen = ref(false)
const selectedCompany = ref<CompanyListItem | null>(null)

const hasCompanies = computed(() => companies.value.length > 0)

function getPriority(company: CompanyListItem): 'High' | 'Medium' | 'Low' {
  if (company.status === 'deciding' || company.status === 'error') return 'High'
  if (company.decision === 'manual_review') return 'High'
  if (typeof company.confidence !== 'number') return 'High'
  if (company.confidence < 0.65) return 'High'
  if (company.confidence < 0.85) return 'Medium'
  return 'Low'
}

function priorityClass(priority: 'High' | 'Medium' | 'Low'): string {
  if (priority === 'High') return 'text-[var(--color-danger)] bg-[rgba(244,63,94,0.08)]'
  if (priority === 'Medium') return 'text-[rgba(245,158,11,1)] bg-[rgba(245,158,11,0.12)]'
  return 'text-[var(--color-accent)] bg-[rgba(52,211,153,0.12)]'
}

function aiDecisionLabel(company: CompanyListItem): string {
  if (company.status === 'deciding') return 'Evaluating'
  if (company.decision === 'accept') return 'Accept'
  if (company.decision === 'reject') return 'Reject'
  if (company.decision === 'manual_review') return 'Manual Review'
  if (company.status === 'error') return 'Error'
  return 'Not available'
}

function aiDecisionClass(company: CompanyListItem): string {
  if (company.status === 'deciding') return 'text-[rgba(245,158,11,1)] bg-[rgba(245,158,11,0.12)]'
  if (company.decision === 'accept') return 'text-[var(--color-accent)] bg-[rgba(52,211,153,0.12)]'
  if (company.decision === 'reject') return 'text-[var(--color-danger)] bg-[rgba(244,63,94,0.1)]'
  if (company.decision === 'manual_review') return 'text-[var(--color-info)] bg-[rgba(129,140,248,0.12)]'
  if (company.status === 'error') return 'text-[var(--color-danger)] bg-[rgba(244,63,94,0.08)]'
  return 'text-[var(--color-text-muted)] bg-[var(--color-bg-alt)]'
}

const reviewRows = computed(() => {
  const priorityOrder: Record<'High' | 'Medium' | 'Low', number> = {
    High: 0,
    Medium: 1,
    Low: 2,
  }

  const relevant = companies.value.filter((company) => {
    return !!company.profile || !!company.decision || !!company.reasoning || company.status === 'deciding'
  })

  return [...relevant].sort((a, b) => {
    const pa = getPriority(a)
    const pb = getPriority(b)
    if (priorityOrder[pa] !== priorityOrder[pb]) {
      return priorityOrder[pa] - priorityOrder[pb]
    }
    return a.company_name.localeCompare(b.company_name)
  })
})

const priorityCounts = computed(() => {
  const counts = { high: 0, medium: 0, low: 0 }
  for (const company of reviewRows.value) {
    const p = getPriority(company)
    if (p === 'High') counts.high++
    if (p === 'Medium') counts.medium++
    if (p === 'Low') counts.low++
  }
  return counts
})

const finalDecisionCounts = computed(() => {
  return {
    // Count companies where final_decision is set (either by user or auto-initialized from AI)
    accept: reviewRows.value.filter((c) => c.final_decision === 'accept').length,
    reject: reviewRows.value.filter((c) => c.final_decision === 'reject').length,
  }
})

const canProceed = computed(() => reviewRows.value.length > 0)

/**
 * After loading, auto-initialize final_decision from AI decision for any company
 * that doesn't already have a final decision saved.
 * Only applies to clear accept/reject decisions — manual_review stays unset.
 */
async function autoInitFinalDecisions(loadedCompanies: CompanyListItem[]) {
  const toInit = loadedCompanies.filter(
    (c) => !c.final_decision && (c.decision === 'accept' || c.decision === 'reject')
  )
  if (!toInit.length) return

  // Optimistically update local state immediately so counts update without waiting for API
  const now = new Date().toISOString()
  for (const company of toInit) {
    setLocalCompany({
      ...company,
      final_decision: company.decision as 'accept' | 'reject',
      final_decided_at: now,
    })
  }

  // Persist to backend in parallel (fire-and-forget — failures don't block the UI)
  await Promise.allSettled(
    toInit.map((c) =>
      companyService.setFinalDecision(c.id, c.decision as 'accept' | 'reject')
    )
  )
}

async function loadData() {
  if (!props.batchId) return

  isLoading.value = true
  errorMessage.value = null
  try {
    const loaded = await batchService.getCompanies(props.batchId)
    companies.value = loaded
    // Auto-default final decision to AI decision for companies without one
    await autoInitFinalDecisions(loaded)
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string })?.message || 'Failed to load final review data.'
  } finally {
    isLoading.value = false
  }
}

async function refreshData() {
  if (!props.batchId || isRefreshing.value) return
  isRefreshing.value = true
  errorMessage.value = null
  try {
    companies.value = await batchService.getCompanies(props.batchId)
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string })?.message || 'Failed to refresh final review data.'
  } finally {
    isRefreshing.value = false
  }
}

function setLocalCompany(updated: CompanyListItem) {
  const index = companies.value.findIndex((item) => item.id === updated.id)
  if (index >= 0) {
    companies.value[index] = updated
  }
}

async function setFinalDecision(company: CompanyListItem, decision: 'accept' | 'reject') {
  if (updatingCompanyId.value === company.id) return

  const previousDecision = company.final_decision
  const previousDecidedAt = company.final_decided_at

  const now = new Date().toISOString()
  setLocalCompany({
    ...company,
    final_decision: decision,
    final_decided_at: now,
  })

  updatingCompanyId.value = company.id
  errorMessage.value = null
  try {
    const updated = await companyService.setFinalDecision(company.id, decision)
    setLocalCompany(updated)
  } catch (error: unknown) {
    setLocalCompany({
      ...company,
      final_decision: previousDecision,
      final_decided_at: previousDecidedAt,
    })
    errorMessage.value = (error as { message?: string })?.message || 'Failed to save final decision.'
  } finally {
    updatingCompanyId.value = null
  }
}

function openDrawer(company: CompanyListItem) {
  selectedCompany.value = company
  drawerOpen.value = true
}

function closeDrawer() {
  drawerOpen.value = false
}

onMounted(loadData)
watch(() => props.batchId, loadData)
</script>

<template>
  <div class="flex flex-col h-full gap-4">
    <div
      v-if="isLoading"
      class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-3"
    >
      <Loader2 :size="28" class="animate-spin text-[var(--color-primary)]" />
      <p class="text-sm text-[var(--color-text-secondary)] m-0">Loading final review data…</p>
    </div>

    <div
      v-else-if="!hasCompanies || !reviewRows.length"
      class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-3"
    >
      <AlertCircle :size="24" class="text-[var(--color-text-muted)]" />
      <p class="text-base font-semibold text-[var(--color-text)] m-0">No companies ready for final review.</p>
      <p class="text-sm text-[var(--color-text-secondary)] max-w-[420px] leading-relaxed m-0">
        Run Accept/Reject first to generate AI decisions, then finalize outcomes here.
      </p>
    </div>

    <template v-else>
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs text-[var(--color-text-muted)] m-0">
          Review AI decisions, inspect reasoning, and set the final human decision.
        </p>
        <button
          @click="refreshData"
          :disabled="isRefreshing"
          class="w-8 h-8 flex items-center justify-center rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all disabled:opacity-50"
          title="Refresh now"
        >
          <RefreshCw :size="14" :class="isRefreshing ? 'animate-spin' : ''" />
        </button>
      </div>

      <div class="flex-1 border border-[var(--color-border)] rounded-[var(--radius-md)] bg-[var(--color-surface)] overflow-auto">
        <table class="w-full border-collapse text-sm" style="min-width: 1180px;">
          <thead>
            <tr class="sticky top-0 z-10 bg-[var(--color-bg-alt)] border-b border-[var(--color-border)]">
              <th class="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:220px">Company Name</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:140px">Review Priority</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:120px">AI Decision</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:360px">AI Reasoning</th>
              <th class="px-3 py-3 text-left text-xs font-semibold text-[var(--color-text-secondary)]" style="min-width:220px">Final Decision</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="company in reviewRows"
              :key="company.id"
              class="border-b border-[var(--color-border)] hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer"
              @click="openDrawer(company)"
            >
              <td class="px-4 py-3">
                <p class="text-sm font-semibold text-[var(--color-text)] m-0 mb-0.5 truncate max-w-[220px]">
                  {{ company.company_name }}
                </p>
                <p class="text-[0.7rem] text-[var(--color-text-muted)] m-0">
                  {{ company.country || '—' }}
                </p>
              </td>

              <td class="px-3 py-3">
                <span
                  :class="[
                    'inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full',
                    priorityClass(getPriority(company)),
                  ]"
                >
                  {{ getPriority(company) }}
                </span>
              </td>

              <td class="px-3 py-3">
                <span
                  :class="[
                    'inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full',
                    aiDecisionClass(company),
                  ]"
                >
                  {{ aiDecisionLabel(company) }}
                </span>
              </td>

              <td class="px-3 py-3">
                <p v-if="company.reasoning" class="text-xs text-[var(--color-text-secondary)] m-0 line-clamp-3 max-w-[380px]">
                  {{ company.reasoning }}
                </p>
                <span v-else class="text-xs text-[var(--color-text-muted)]">No reasoning provided</span>
              </td>

              <td class="px-3 py-3">
                <div class="flex items-center gap-2" @click.stop>
                  <button
                    @click="setFinalDecision(company, 'accept')"
                    :disabled="updatingCompanyId === company.id"
                    :class="[
                      'px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold border transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
                      company.final_decision === 'accept'
                        ? 'bg-[rgba(52,211,153,0.14)] text-[var(--color-accent)] border-[rgba(52,211,153,0.45)]'
                        : 'bg-transparent text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]',
                    ]"
                  >
                    <CheckCircle2 :size="12" class="inline-block mr-1" />
                    Accept
                  </button>
                  <button
                    @click="setFinalDecision(company, 'reject')"
                    :disabled="updatingCompanyId === company.id"
                    :class="[
                      'px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold border transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
                      company.final_decision === 'reject'
                        ? 'bg-[rgba(244,63,94,0.12)] text-[var(--color-danger)] border-[rgba(244,63,94,0.45)]'
                        : 'bg-transparent text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-danger)] hover:text-[var(--color-danger)]',
                    ]"
                  >
                    <XCircle :size="12" class="inline-block mr-1" />
                    Reject
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="sticky bottom-0 bg-[var(--color-bg)] border-t border-[var(--color-border)] pt-3 pb-1 flex flex-col gap-3">
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-3 text-[var(--color-text-muted)]">
            <span>High: {{ priorityCounts.high }}</span>
            <span>Medium: {{ priorityCounts.medium }}</span>
            <span>Low: {{ priorityCounts.low }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-[var(--color-accent)] font-semibold">Final Accept: {{ finalDecisionCounts.accept }}</span>
            <span class="text-[var(--color-danger)] font-semibold">Final Reject: {{ finalDecisionCounts.reject }}</span>
          </div>
        </div>

        <p v-if="errorMessage" class="flex items-center gap-1.5 text-xs text-[var(--color-danger)] font-medium m-0">
          <AlertCircle :size="12" />{{ errorMessage }}
        </p>

        <div class="flex items-center justify-end">
          <button
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
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
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
</style>
