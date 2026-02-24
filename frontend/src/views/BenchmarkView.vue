<script setup lang="ts">
/**
 * BenchmarkView — Multi-step Benchmarking Analysis workspace.
 * Uses Tailwind v4 classes and lucide-vue-next icons.
 */
import { ref, computed } from 'vue'
import {
  Home, Upload, Filter, Search, CheckCircle, Users, Download, ArrowRight,
} from 'lucide-vue-next'
import AppSidebar from '@/components/AppSidebar.vue'
import StepNavigator from '@/components/StepNavigator.vue'
import { useSidebar } from '@/composables/useSidebar'

const currentStep = ref(0)
const { collapsed } = useSidebar()

const steps = [
  { label: 'Overview' },
  { label: 'Upload Data' },
  { label: 'Filters' },
  { label: 'Web Search' },
  { label: 'Accept/Reject' },
  { label: 'Human Review' },
  { label: 'Exports' },
]

interface StepMeta {
  title: string
  subtitle: string
  icon: unknown
  iconClass: string
  emptyIcon: string
  emptyText: string
  emptySub: string
}

const stepMeta: StepMeta[] = [
  {
    title: 'Overview',
    subtitle: 'Summary of this benchmark analysis and its current status.',
    icon: Home,
    iconClass: 'bg-[var(--color-primary-light)] text-[var(--color-primary)]',
    emptyIcon: '📊',
    emptyText: 'No analyses yet.',
    emptySub: 'Upload company data to start your first benchmarking run.',
  },
  {
    title: 'Upload Data',
    subtitle: 'Upload an Excel file with your company list to begin analysis.',
    icon: Upload,
    iconClass: 'bg-[rgba(52,211,153,0.12)] text-[var(--color-accent)]',
    emptyIcon: '📁',
    emptyText: 'Data upload coming soon.',
    emptySub: 'This step will allow you to upload an Excel file with company URLs to scrape.',
  },
  {
    title: 'Filters',
    subtitle: 'Configure the acceptance criteria used to classify companies.',
    icon: Filter,
    iconClass: 'bg-[rgba(129,140,248,0.12)] text-[var(--color-info)]',
    emptyIcon: '⚙️',
    emptyText: 'Filter configuration coming soon.',
    emptySub: 'Define industry types, revenue ranges, and other criteria to auto-classify results.',
  },
  {
    title: 'Web Search',
    subtitle: 'AI-powered website scraping status for each company.',
    icon: Search,
    iconClass: 'bg-[var(--color-primary-light)] text-[var(--color-primary)]',
    emptyIcon: '🌐',
    emptyText: 'No scraping runs yet.',
    emptySub: 'Once you upload data and initiate a search, progress will be tracked here per company.',
  },
  {
    title: 'Accept / Reject',
    subtitle: 'Review AI classification decisions and override as needed.',
    icon: CheckCircle,
    iconClass: 'bg-[rgba(52,211,153,0.12)] text-[var(--color-accent)]',
    emptyIcon: '✅',
    emptyText: 'No decisions yet.',
    emptySub: 'AI-generated accept/reject verdicts will appear here after scraping completes.',
  },
  {
    title: 'Human Review',
    subtitle: 'Manually review edge cases flagged by the AI pipeline.',
    icon: Users,
    iconClass: 'bg-[rgba(251,191,36,0.12)] text-[var(--color-warning)]',
    emptyIcon: '👀',
    emptyText: 'No items pending review.',
    emptySub: 'Companies that require manual inspection due to ambiguous data will appear here.',
  },
  {
    title: 'Exports',
    subtitle: 'Download analysis results as Excel or JSON reports.',
    icon: Download,
    iconClass: 'bg-[rgba(129,140,248,0.12)] text-[var(--color-info)]',
    emptyIcon: '📥',
    emptyText: 'No exports available.',
    emptySub: 'Complete an analysis run to generate downloadable reports.',
  },
]

// Safe computed — avoids "Object is possibly undefined" TS errors on index access
const currentMeta = computed(() => stepMeta[currentStep.value] ?? stepMeta[0]!)
</script>

<template>
  <div class="flex min-h-screen bg-[var(--color-bg)]">
    <AppSidebar />

    <!-- Main shell — reacts to sidebar collapse -->
    <div
      :class="[
        'flex flex-col flex-1 min-h-screen transition-all duration-300 ease-in-out',
        collapsed ? 'ml-[60px]' : 'ml-[220px]',
      ]"
    >
      <!-- Sticky top navigation bar -->
      <div
        id="benchmark-nav"
        class="sticky top-0 z-50 bg-[var(--color-surface)] border-b border-[var(--color-border)] shadow-[var(--shadow-sm)]"
      >
        <div class="max-w-[1200px] mx-auto">
          <!-- Analysis title -->
          <div class="flex items-center gap-4 px-6 pt-4 pb-1">
            <h2 class="text-[1.1rem] font-bold text-[var(--color-text)] tracking-tight m-0">
              Benchmarking Analysis
            </h2>
          </div>
          <!-- Step navigator -->
          <StepNavigator :steps="steps" v-model="currentStep" />
        </div>
      </div>

      <!-- Step content area -->
      <main
        id="benchmark-content"
        class="flex-1 px-8 py-10 max-w-[1200px] w-full mx-auto"
      >
        <Transition name="step-fade" mode="out-in">
          <div :key="currentStep" class="flex flex-col gap-6">
            <!-- Step header -->
            <div class="flex items-start gap-4">
              <div
                :class="[
                  'w-12 h-12 rounded-[var(--radius-md)] flex items-center justify-center shrink-0',
                  currentMeta.iconClass,
                ]"
              >
                <component :is="currentMeta.icon" :size="22" />
              </div>
              <div>
                <h3 class="text-[1.25rem] font-bold text-[var(--color-text)] tracking-tight m-0 mb-1">
                  {{ currentMeta.title }}
                </h3>
                <p class="text-sm text-[var(--color-text-secondary)] m-0">
                  {{ currentMeta.subtitle }}
                </p>
              </div>
            </div>

            <!-- Empty state card -->
            <div class="glass-card flex flex-col items-center justify-center text-center px-8 py-16 gap-2">
              <div class="text-[2.5rem] mb-2">{{ currentMeta.emptyIcon }}</div>
              <p class="text-base font-semibold text-[var(--color-text)] m-0">
                {{ currentMeta.emptyText }}
              </p>
              <p class="text-sm text-[var(--color-text-secondary)] max-w-[380px] leading-relaxed mt-1 mb-5">
                {{ currentMeta.emptySub }}
              </p>

              <!-- CTA only on Overview step -->
              <button
                v-if="currentStep === 0"
                id="overview-start-cta"
                @click="currentStep = 1"
                class="inline-flex items-center gap-2 px-5 py-2.5 bg-[var(--color-primary)] text-white border-none rounded-[var(--radius-sm)] text-sm font-semibold cursor-pointer font-sans transition-all duration-200 shadow-[0_2px_8px_rgba(79,70,229,0.25)] hover:bg-[var(--color-primary-hover)] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(79,70,229,0.35)]"
              >
                Upload Data
                <ArrowRight :size="14" />
              </button>
            </div>
          </div>
        </Transition>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Step transition */
.step-fade-enter-active,
.step-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.step-fade-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.step-fade-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}
</style>
