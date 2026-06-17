<script setup lang="ts">
/**
 * CompanyDetailDrawer — slide-in right panel for Web Search step.
 *
 * Shows full AI-extracted company profile including:
 *   - Data sources & status
 *   - Business description
 *   - Products & services list
 *   - Company profile grid (functional, target market, size, geography)
 *   - Technology indicators & certifications
 *   - Scraped pages
 */
import { computed } from 'vue'
import {
  X, Globe, ExternalLink, CheckCircle2, AlertCircle, Clock,
  Loader2, Database, FileText, Link2, Tag, Shield, Building2,
  Target, MapPin, Cpu, Package,
} from 'lucide-vue-next'
import type { CompanyListItem } from '@/types/api'

const props = defineProps<{
  company: CompanyListItem | null
  open: boolean
  showFooterActions?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updateUrl'): void
  (e: 'removeResults'): void
}>()

// ── Status helpers ────────────────────────────────────────────────────────────
interface StatusConfig {
  label: string
  color: string
  bgColor: string
  icon: unknown
  pulse?: boolean
}

function getStatusConfig(status: string): StatusConfig {
  const map: Record<string, StatusConfig> = {
    pending:   { label: 'Pending',   color: 'text-[var(--color-text-muted)]',    bgColor: 'bg-[var(--color-bg-alt)]',                       icon: Clock },
    scraping:  { label: 'Searching', color: 'text-[var(--color-primary)]',       bgColor: 'bg-[var(--color-primary-light)]',                 icon: Loader2, pulse: true },
    scraped:   { label: 'Scraped',   color: 'text-[var(--color-info)]',          bgColor: 'bg-[rgba(129,140,248,0.12)]',                    icon: Database },
    analyzing: { label: 'Analysing', color: 'text-[rgba(251,146,60,1)]',         bgColor: 'bg-[rgba(251,146,60,0.1)]',                      icon: Loader2, pulse: true },
    deciding:  { label: 'Evaluating', color: 'text-[rgba(245,158,11,1)]',        bgColor: 'bg-[rgba(245,158,11,0.14)]',                     icon: Loader2, pulse: true },
    complete:  { label: 'Analysed',  color: 'text-[var(--color-accent)]',        bgColor: 'bg-[rgba(52,211,153,0.12)]',                     icon: CheckCircle2 },
    error:     { label: 'Error',     color: 'text-[var(--color-danger)]',        bgColor: 'bg-[rgba(244,63,94,0.08)]',                      icon: AlertCircle },
    excluded:  { label: 'Excluded',  color: 'text-[var(--color-text-muted)]',    bgColor: 'bg-[var(--color-bg-alt)]',                       icon: X },
  }
  return map[status] ?? map['pending']!
}

const statusConfig = computed(() =>
  props.company ? getStatusConfig(props.company.status) : getStatusConfig('pending')
)

const sourceLabel = computed(() => {
  if (!props.company) return '—'
  const s = props.company.status
  if (s === 'complete' || s === 'scraped' || s === 'analyzing') return 'Website'
  if (s === 'error') return 'Failed'
  return 'Not analysed'
})

const isAnalysed = computed(() =>
  props.company?.status === 'complete' || props.company?.status === 'scraped'
)

const aiDecisionLabel = computed(() => {
  if (!props.company) return 'Not available'
  if (props.company.status === 'deciding') return 'Evaluating'
  if (props.company.decision === 'accept') return 'Accept'
  if (props.company.decision === 'reject') return 'Reject'
  if (props.company.decision === 'manual_review') return 'Manual Review'
  return 'Not available'
})

const aiDecisionBadge = computed(() => {
  if (!props.company) return 'text-[var(--color-text-muted)] bg-[var(--color-bg-alt)]'
  if (props.company.status === 'deciding') return 'text-[rgba(245,158,11,1)] bg-[rgba(245,158,11,0.14)]'
  if (props.company.decision === 'accept') return 'text-[var(--color-accent)] bg-[rgba(52,211,153,0.12)]'
  if (props.company.decision === 'reject') return 'text-[var(--color-danger)] bg-[rgba(244,63,94,0.1)]'
  if (props.company.decision === 'manual_review') return 'text-[var(--color-info)] bg-[rgba(129,140,248,0.12)]'
  return 'text-[var(--color-text-muted)] bg-[var(--color-bg-alt)]'
})

const aiConfidence = computed(() => {
  const raw = props.company?.confidence
  if (typeof raw !== 'number') return '—'
  return `${Math.round(raw * 100)}%`
})

const finalDecisionLabel = computed(() => {
  if (!props.company?.final_decision) return 'Not set'
  return props.company.final_decision === 'accept' ? 'Accept' : 'Reject'
})

const finalDecisionBadge = computed(() => {
  if (props.company?.final_decision === 'accept') {
    return 'text-[var(--color-accent)] bg-[rgba(52,211,153,0.12)]'
  }
  if (props.company?.final_decision === 'reject') {
    return 'text-[var(--color-danger)] bg-[rgba(244,63,94,0.1)]'
  }
  return 'text-[var(--color-text-muted)] bg-[var(--color-bg-alt)]'
})

// ── Profile computed data ─────────────────────────────────────────────────────
interface ProductService {
  name: string
  description: string
  category: string
  is_core: boolean
}

const profile = computed(() => props.company?.profile as Record<string, unknown> | null)

const businessDescription = computed(() =>
  (profile.value?.business_description as string) || null
)

const products = computed<ProductService[]>(() =>
  (profile.value?.products_services as ProductService[]) || []
)

const functionalProfile = computed(() =>
  (profile.value?.functional_profile as string) || null
)

const targetMarket = computed(() =>
  (profile.value?.target_market as string) || null
)

const companySize = computed(() =>
  (profile.value?.company_size as string) || null
)

const geoPresence = computed<string[]>(() =>
  (profile.value?.geographic_presence as string[]) || []
)

const techIndicators = computed<string[]>(() =>
  (profile.value?.technology_indicators as string[]) || []
)

const certifications = computed<string[]>(() =>
  (profile.value?.certifications as string[]) || []
)

const hasProfile = computed(() => !!profile.value)

const pagesCrawled = computed<string[]>(() =>
  props.company?.pages_crawled || []
)

function cleanUrl(url: string): string {
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}
</script>

<template>
  <!-- Backdrop -->
  <Transition name="backdrop">
    <div
      v-if="open"
      class="fixed inset-0 z-[100] bg-black/40 backdrop-blur-[2px]"
      @click="emit('close')"
    />
  </Transition>

  <!-- Drawer panel -->
  <Transition name="drawer">
    <div
      v-if="open && company"
      id="company-detail-drawer"
      class="fixed top-0 right-0 bottom-0 z-[101] w-[520px] max-w-full flex flex-col bg-[var(--color-surface)] border-l border-[var(--color-border)] shadow-[var(--shadow-lg)] overflow-hidden"
    >
      <!-- ── Header ──────────────────────────────────────────────────────── -->
      <div class="flex items-start gap-3 px-6 pt-5 pb-4 border-b border-[var(--color-border)]">
        <div class="flex-1 min-w-0">
          <h3 class="text-[1rem] font-bold text-[var(--color-text)] m-0 mb-1 leading-tight line-clamp-2">
            {{ company.company_name }}
          </h3>
          <div class="flex items-center gap-3 flex-wrap mt-1">
            <a
              v-if="company.website"
              :href="company.website.startsWith('http') ? company.website : `https://${company.website}`"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline"
            >
              <Globe :size="11" />
              {{ cleanUrl(company.website) }}
              <ExternalLink :size="10" />
            </a>
            <span
              v-if="company.country"
              class="text-xs text-[var(--color-text-muted)] flex items-center gap-1"
            >
              {{ company.country }}
            </span>
            <span
              v-if="company.bvd_id"
              class="text-[0.68rem] font-mono bg-[var(--color-bg-alt)] px-1.5 py-0.5 rounded text-[var(--color-text-muted)] border border-[var(--color-border)]"
            >
              {{ company.bvd_id }}
            </span>
          </div>
        </div>

        <!-- Close -->
        <button
          id="drawer-close"
          @click="emit('close')"
          class="shrink-0 w-8 h-8 flex items-center justify-center rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)] hover:border-[var(--color-primary)] transition-all"
        >
          <X :size="15" />
        </button>
      </div>

      <!-- ── Scrollable body ─────────────────────────────────────────────── -->
      <div class="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-5">

        <!-- DATA SOURCES section ──────────────────────────────────────────── -->
        <section>
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Data Sources
          </p>

          <div class="flex flex-col gap-2">
            <!-- Status row -->
            <div class="flex items-center justify-between py-1.5 px-3 rounded-[var(--radius-sm)] bg-[var(--color-bg-alt)] border border-[var(--color-border)]">
              <span class="text-xs text-[var(--color-text-secondary)] font-medium">Status</span>
              <span
                :class="[
                  'flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full',
                  statusConfig.color,
                  statusConfig.bgColor,
                ]"
              >
                <component
                  :is="statusConfig.icon"
                  :size="11"
                  :class="statusConfig.pulse ? 'animate-spin' : ''"
                />
                {{ statusConfig.label }}
              </span>
            </div>

            <!-- Website validity -->
            <div class="flex items-center justify-between py-1.5 px-3 rounded-[var(--radius-sm)] bg-[var(--color-bg-alt)] border border-[var(--color-border)]">
              <span class="text-xs text-[var(--color-text-secondary)] font-medium flex items-center gap-1.5">
                <Globe :size="12" />
                Website
              </span>
              <span
                :class="[
                  'flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full',
                  isAnalysed
                    ? 'text-[var(--color-accent)] bg-[rgba(52,211,153,0.12)]'
                    : 'text-[var(--color-text-muted)] bg-[var(--color-bg-alt)]',
                ]"
              >
                <CheckCircle2 v-if="isAnalysed" :size="11" />
                <Clock v-else :size="11" />
                {{ isAnalysed ? 'Valid' : 'Pending' }}
              </span>
            </div>

            <!-- Source type -->
            <div class="flex items-center justify-between py-1.5 px-3 rounded-[var(--radius-sm)] bg-[var(--color-bg-alt)] border border-[var(--color-border)]">
              <span class="text-xs text-[var(--color-text-secondary)] font-medium flex items-center gap-1.5">
                <Database :size="12" />
                AI Source
              </span>
              <span class="text-xs font-semibold text-[var(--color-text-secondary)]">
                {{ sourceLabel }}
              </span>
            </div>
          </div>
        </section>

        <!-- BUSINESS DESCRIPTION ───────────────────────────────────────────── -->
        <section v-if="businessDescription">
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Business Description
          </p>
          <div class="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
            <p class="text-xs text-[var(--color-text-secondary)] m-0 leading-relaxed">
              {{ businessDescription }}
            </p>
          </div>
        </section>

        <!-- PRODUCTS & SERVICES ────────────────────────────────────────────── -->
        <section v-if="products.length">
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Products &amp; Services ({{ products.length }})
          </p>
          <div class="flex flex-col gap-2">
            <div
              v-for="(prod, idx) in products"
              :key="idx"
              class="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-2.5"
            >
              <div class="flex items-center gap-2 mb-1">
                <Package :size="12" class="shrink-0 text-[var(--color-primary)]" />
                <span class="text-xs font-semibold text-[var(--color-text)]">{{ prod.name }}</span>
                <span
                  v-if="prod.is_core"
                  class="text-[0.6rem] font-bold uppercase text-[var(--color-accent)] bg-[rgba(52,211,153,0.12)] px-1.5 py-0 rounded-full"
                >
                  Core
                </span>
                <span
                  v-if="prod.category"
                  class="ml-auto text-[0.6rem] font-medium text-[var(--color-text-muted)] bg-[var(--color-bg-alt)] border border-[var(--color-border)] px-1.5 py-0 rounded-full"
                >
                  {{ prod.category }}
                </span>
              </div>
              <p v-if="prod.description" class="text-[0.7rem] text-[var(--color-text-muted)] m-0 ml-5 leading-relaxed">
                {{ prod.description }}
              </p>
            </div>
          </div>
        </section>

        <!-- COMPANY PROFILE GRID ───────────────────────────────────────────── -->
        <section v-if="hasProfile">
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Company Profile
          </p>

          <div class="rounded-[var(--radius-md)] border border-[var(--color-border)] overflow-hidden">
            <div class="grid grid-cols-2 divide-x divide-[var(--color-border)]">
              <!-- Functional Profile -->
              <div class="px-4 py-3 bg-[var(--color-bg-alt)]">
                <div class="flex items-center gap-1.5 mb-1">
                  <Building2 :size="11" class="text-[var(--color-text-muted)]" />
                  <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium">Functional Profile</p>
                </div>
                <span class="text-xs font-semibold text-[var(--color-text)]">
                  {{ functionalProfile || '—' }}
                </span>
              </div>
              <!-- Company Size -->
              <div class="px-4 py-3 bg-[var(--color-bg-alt)]">
                <div class="flex items-center gap-1.5 mb-1">
                  <Building2 :size="11" class="text-[var(--color-text-muted)]" />
                  <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium">Company Size</p>
                </div>
                <span class="text-xs font-semibold text-[var(--color-text)]">
                  {{ companySize || '—' }}
                </span>
              </div>
            </div>
            <div class="grid grid-cols-2 divide-x divide-[var(--color-border)] border-t border-[var(--color-border)]">
              <!-- Target Market -->
              <div class="px-4 py-3 bg-[var(--color-surface)]">
                <div class="flex items-center gap-1.5 mb-1">
                  <Target :size="11" class="text-[var(--color-text-muted)]" />
                  <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium">Target Market</p>
                </div>
                <span class="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                  {{ targetMarket || '—' }}
                </span>
              </div>
              <!-- Industry -->
              <div class="px-4 py-3 bg-[var(--color-surface)]">
                <div class="flex items-center gap-1.5 mb-1">
                  <Database :size="11" class="text-[var(--color-text-muted)]" />
                  <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium">Industry</p>
                </div>
                <span class="text-xs font-semibold text-[var(--color-text)]">
                  {{ company.industry || '—' }}
                </span>
              </div>
            </div>
            <!-- Geographic Presence -->
            <div v-if="geoPresence.length" class="px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-bg-alt)]">
              <div class="flex items-center gap-1.5 mb-1.5">
                <MapPin :size="11" class="text-[var(--color-text-muted)]" />
                <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium">Geographic Presence</p>
              </div>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="geo in geoPresence"
                  :key="geo"
                  class="text-[0.65rem] font-medium text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] px-2 py-0.5 rounded-full"
                >
                  {{ geo }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- TECHNOLOGY INDICATORS ──────────────────────────────────────────── -->
        <section v-if="techIndicators.length">
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Technology Indicators
          </p>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tech in techIndicators"
              :key="tech"
              class="inline-flex items-center gap-1 text-[0.65rem] font-medium text-[var(--color-primary)] bg-[var(--color-primary-light)] border border-[rgba(79,70,229,0.15)] px-2 py-0.5 rounded-full"
            >
              <Cpu :size="10" />
              {{ tech }}
            </span>
          </div>
        </section>

        <!-- CERTIFICATIONS ─────────────────────────────────────────────────── -->
        <section v-if="certifications.length">
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Certifications
          </p>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="cert in certifications"
              :key="cert"
              class="inline-flex items-center gap-1 text-[0.65rem] font-medium text-[var(--color-accent)] bg-[rgba(52,211,153,0.1)] border border-[rgba(52,211,153,0.2)] px-2 py-0.5 rounded-full"
            >
              <Shield :size="10" />
              {{ cert }}
            </span>
          </div>
        </section>

        <!-- AI REASONING (if any — from Stage 2) ──────────────────────────── -->
        <section v-if="company.reasoning">
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            AI Reasoning
          </p>
          <div class="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
            <p class="text-xs text-[var(--color-text-secondary)] m-0 leading-relaxed">
              {{ company.reasoning }}
            </p>
          </div>
        </section>

        <!-- AI DECISION SUMMARY ────────────────────────────────────────────── -->
        <section>
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Decision Summary
          </p>
          <div class="rounded-[var(--radius-md)] border border-[var(--color-border)] overflow-hidden">
            <div class="grid grid-cols-2 divide-x divide-[var(--color-border)]">
              <div class="px-4 py-3 bg-[var(--color-bg-alt)]">
                <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium mb-1">AI Decision</p>
                <span
                  :class="[
                    'inline-flex items-center gap-1 text-[0.7rem] font-semibold px-2 py-0.5 rounded-full',
                    aiDecisionBadge,
                  ]"
                >
                  {{ aiDecisionLabel }}
                </span>
              </div>
              <div class="px-4 py-3 bg-[var(--color-bg-alt)]">
                <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium mb-1">AI Confidence</p>
                <span class="text-xs font-semibold text-[var(--color-text)]">{{ aiConfidence }}</span>
              </div>
            </div>
            <div class="grid grid-cols-2 divide-x divide-[var(--color-border)] border-t border-[var(--color-border)]">
              <div class="px-4 py-3 bg-[var(--color-surface)]">
                <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium mb-1">Final Decision</p>
                <span
                  :class="[
                    'inline-flex items-center gap-1 text-[0.7rem] font-semibold px-2 py-0.5 rounded-full',
                    finalDecisionBadge,
                  ]"
                >
                  {{ finalDecisionLabel }}
                </span>
              </div>
              <div class="px-4 py-3 bg-[var(--color-surface)]">
                <p class="text-[0.68rem] text-[var(--color-text-muted)] m-0 font-medium mb-1">Finalized At</p>
                <span class="text-xs text-[var(--color-text-secondary)]">
                  {{ company.final_decided_at ? new Date(company.final_decided_at).toLocaleString() : '—' }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- SCRAPED PAGES ────────────────────────────────────────────────── -->
        <section>
          <p class="text-[0.68rem] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2.5">
            Scraped Pages
          </p>

          <!-- No pages yet -->
          <div
            v-if="!pagesCrawled.length"
            class="flex flex-col items-center justify-center py-8 gap-2 rounded-[var(--radius-md)] border border-dashed border-[var(--color-border)] bg-[var(--color-bg-alt)]"
          >
            <Globe :size="22" class="text-[var(--color-text-muted)] opacity-40" />
            <p class="text-xs text-[var(--color-text-muted)] m-0">No pages scraped yet.</p>
          </div>

          <!-- Pages list -->
          <div v-else class="flex flex-col gap-2">
            <div
              v-for="pageUrl in pagesCrawled"
              :key="pageUrl"
              class="rounded-[var(--radius-md)] border border-[var(--color-border)] overflow-hidden"
            >
              <div class="flex items-start gap-3 px-4 py-3 bg-[var(--color-surface)]">
                <FileText :size="13" class="mt-0.5 shrink-0 text-[var(--color-text-muted)]" />
                <div class="flex-1 min-w-0">
                  <a
                    :href="pageUrl.startsWith('http') ? pageUrl : `https://${pageUrl}`"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs text-[var(--color-primary)] hover:underline break-all block"
                  >
                    {{ pageUrl }}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>

      <!-- ── Footer actions ─────────────────────────────────────────────── -->
      <div
        v-if="showFooterActions !== false"
        class="px-6 py-4 border-t border-[var(--color-border)] flex items-center gap-3"
      >
        <button
          id="drawer-update-url"
          @click="emit('updateUrl')"
          class="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-transparent text-sm font-medium text-[var(--color-text-secondary)] cursor-pointer font-sans hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all"
        >
          <Link2 :size="14" />
          Update URL
        </button>
        <button
          id="drawer-remove-results"
          @click="emit('removeResults')"
          class="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-[var(--radius-sm)] border border-[rgba(244,63,94,0.3)] bg-transparent text-sm font-medium text-[var(--color-danger)] cursor-pointer font-sans hover:bg-[rgba(244,63,94,0.08)] hover:border-[var(--color-danger)] transition-all"
        >
          <X :size="14" />
          Remove Results
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Backdrop transition */
.backdrop-enter-active,
.backdrop-leave-active {
  transition: opacity 0.2s ease;
}
.backdrop-enter-from,
.backdrop-leave-to {
  opacity: 0;
}

/* Drawer slide-in from right */
.drawer-enter-active {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
}
.drawer-leave-active {
  transition: transform 0.2s ease, opacity 0.15s ease;
}
.drawer-enter-from {
  transform: translateX(40px);
  opacity: 0;
}
.drawer-leave-to {
  transform: translateX(40px);
  opacity: 0;
}

/* Line clamp utility */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
