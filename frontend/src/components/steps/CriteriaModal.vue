<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { X, Sparkles, Sliders, Loader2, RefreshCw, AlertCircle } from 'lucide-vue-next'
import type { CriteriaUpdate } from '@/types/api'
import { batchService } from '@/services/batchService'

const props = defineProps<{
  open: boolean
  initialCriteria?: CriteriaUpdate | null
  saving?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', payload: CriteriaUpdate): void
}>()

// ── Tabs ───────────────────────────────────────────────────────────────────────
type Tab = 'ai' | 'custom'
const activeTab = ref<Tab>('ai')

// ── Form state ─────────────────────────────────────────────────────────────────
const form = reactive<Required<CriteriaUpdate>>({
  accept_products: '',
  reject_products: '',
  ideal_functional_profile: '',
  reject_functions: '',
})

// ── AI Assistant state ─────────────────────────────────────────────────────────
const aiDescription = ref('')
const isGenerating = ref(false)
const generateError = ref<string | null>(null)

function applyInitialValues() {
  form.accept_products = props.initialCriteria?.accept_products ?? ''
  form.reject_products = props.initialCriteria?.reject_products ?? ''
  form.ideal_functional_profile = props.initialCriteria?.ideal_functional_profile ?? ''
  form.reject_functions = props.initialCriteria?.reject_functions ?? ''
}

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    applyInitialValues()
    generateError.value = null
    // If there are no existing criteria, default to AI tab; else custom
    const hasExisting = Object.values(props.initialCriteria ?? {}).some(v => v?.trim())
    activeTab.value = hasExisting ? 'custom' : 'ai'
  }
})

watch(() => props.initialCriteria, () => {
  if (props.open) applyInitialValues()
}, { deep: true })

// ── AI Generation ──────────────────────────────────────────────────────────────
async function generateCriteria() {
  const desc = aiDescription.value.trim()
  if (!desc) return

  generateError.value = null
  isGenerating.value = true
  try {
    const result = await batchService.generateCriteria(desc)
    form.accept_products = result.accept_products
    form.reject_products = result.reject_products
    form.ideal_functional_profile = result.ideal_functional_profile
    form.reject_functions = result.reject_functions
    // Switch to custom tab so user can see and edit the filled-in fields
    activeTab.value = 'custom'
  } catch (err: unknown) {
    generateError.value = (err as { message?: string })?.message || 'Failed to generate criteria. Please try again.'
  } finally {
    isGenerating.value = false
  }
}

// ── Validation / Save ──────────────────────────────────────────────────────────
const canSave = computed(() => {
  return [
    form.accept_products,
    form.reject_products,
    form.ideal_functional_profile,
    form.reject_functions,
  ].some((value) => value.trim().length > 0)
})

function save() {
  if (!canSave.value || props.saving) return
  emit('save', {
    accept_products: form.accept_products.trim() || undefined,
    reject_products: form.reject_products.trim() || undefined,
    ideal_functional_profile: form.ideal_functional_profile.trim() || undefined,
    reject_functions: form.reject_functions.trim() || undefined,
  })
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-[rgba(15,23,42,0.45)] backdrop-blur-[1px]"
      @click.self="emit('close')"
    >
      <div class="w-full max-w-[860px] max-h-[92vh] overflow-hidden rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)] shadow-[0_30px_60px_rgba(2,6,23,0.28)] flex flex-col">

        <!-- Header -->
        <div class="flex items-start justify-between gap-4 px-6 pt-5 pb-4 border-b border-[var(--color-border)] shrink-0">
          <div>
            <h3 class="text-[1.4rem] font-bold tracking-tight text-[var(--color-text)] m-0">
              Set Accept/Reject Criteria
            </h3>
            <p class="text-sm text-[var(--color-text-secondary)] mt-1 mb-0">
              Define criteria for accepting or rejecting companies in the benchmark analysis.
            </p>
          </div>
          <button
            type="button"
            class="w-8 h-8 rounded-md border border-[var(--color-border)] bg-transparent text-[var(--color-text-muted)] cursor-pointer hover:text-[var(--color-text)] hover:bg-[var(--color-bg-alt)] transition-colors"
            @click="emit('close')"
            aria-label="Close modal"
          >
            <X :size="15" />
          </button>
        </div>

        <!-- Tab bar -->
        <div class="flex gap-1 px-6 pt-4 pb-0 shrink-0">
          <button
            v-for="tab in [
              { key: 'ai', label: 'AI Assistant', icon: Sparkles },
              { key: 'custom', label: 'Custom Strategy', icon: Sliders },
            ]"
            :key="tab.key"
            type="button"
            @click="activeTab = tab.key as Tab"
            :class="[
              'flex items-center gap-1.5 px-4 py-2 rounded-t-[var(--radius-sm)] text-sm font-semibold border border-b-0 cursor-pointer transition-all',
              activeTab === tab.key
                ? 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text)]'
                : 'bg-[var(--color-bg-alt)] border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
            ]"
          >
            <component :is="tab.icon" :size="13" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab body -->
        <div class="flex-1 overflow-y-auto border-t border-[var(--color-border)]">

          <!-- ── AI ASSISTANT TAB ──────────────────────────────────────────── -->
          <div v-if="activeTab === 'ai'" class="px-6 py-5 flex flex-col gap-4">
            <div class="rounded-[var(--radius-sm)] bg-[var(--color-primary-light)] border border-[rgba(79,70,229,0.2)] p-4">
              <p class="text-sm font-semibold text-[var(--color-primary)] m-0 mb-1 flex items-center gap-1.5">
                <Sparkles :size="13" />
                Describe your strategy
              </p>
              <p class="text-xs text-[var(--color-text-muted)] m-0 mb-3">
                Tell the AI about what kinds of companies you want to benchmark. It will generate detailed accept/reject criteria automatically.
              </p>
              <textarea
                v-model="aiDescription"
                rows="4"
                class="w-full resize-none rounded-[var(--radius-sm)] border border-[rgba(79,70,229,0.3)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] focus:shadow-[0_0_0_3px_rgba(79,70,229,0.12)] placeholder:text-[var(--color-text-muted)]"
                placeholder="e.g. Distribution and wholesale of construction materials and electrical products in Europe. We want B2B distributors, not retailers or manufacturers."
              />
              <div class="flex items-center justify-between mt-3">
                <p v-if="generateError" class="flex items-center gap-1.5 text-xs text-[var(--color-danger)] font-medium m-0">
                  <AlertCircle :size="12" />{{ generateError }}
                </p>
                <span v-else class="text-xs text-[var(--color-text-muted)]">
                  The AI will fill in the criteria fields below.
                </span>
                <button
                  type="button"
                  :disabled="!aiDescription.trim() || isGenerating"
                  @click="generateCriteria"
                  class="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-white text-sm font-semibold border-none cursor-pointer transition-all hover:bg-[var(--color-primary-hover)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Loader2 v-if="isGenerating" :size="13" class="animate-spin" />
                  <RefreshCw v-else :size="13" />
                  {{ isGenerating ? 'Generating…' : 'Regenerate Strategy' }}
                </button>
              </div>
            </div>

            <!-- Preview of generated criteria (if any) -->
            <div v-if="form.accept_products || form.reject_products" class="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <div class="rounded-[var(--radius-sm)] border border-[rgba(22,163,74,0.2)] bg-[rgba(22,163,74,0.05)] p-3">
                <p class="text-xs font-semibold text-[var(--color-accent)] m-0 mb-1.5">✓ Accept Criteria (preview)</p>
                <p v-if="form.accept_products" class="text-xs text-[var(--color-text-secondary)] m-0 mb-1">
                  <span class="font-medium">Products:</span> {{ form.accept_products }}
                </p>
                <p v-if="form.ideal_functional_profile" class="text-xs text-[var(--color-text-secondary)] m-0">
                  <span class="font-medium">Profile:</span> {{ form.ideal_functional_profile }}
                </p>
              </div>
              <div class="rounded-[var(--radius-sm)] border border-[rgba(244,63,94,0.2)] bg-[rgba(244,63,94,0.05)] p-3">
                <p class="text-xs font-semibold text-[var(--color-danger)] m-0 mb-1.5">✗ Reject Criteria (preview)</p>
                <p v-if="form.reject_products" class="text-xs text-[var(--color-text-secondary)] m-0 mb-1">
                  <span class="font-medium">Products:</span> {{ form.reject_products }}
                </p>
                <p v-if="form.reject_functions" class="text-xs text-[var(--color-text-secondary)] m-0">
                  <span class="font-medium">Functions:</span> {{ form.reject_functions }}
                </p>
              </div>
            </div>
            <p v-else class="text-xs text-[var(--color-text-muted)] text-center py-4">
              Enter a description and click <strong>Regenerate Strategy</strong> to auto-fill the criteria.
            </p>
          </div>

          <!-- ── CUSTOM STRATEGY TAB ────────────────────────────────────────── -->
          <div v-else class="px-6 py-5">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <section class="rounded-[var(--radius-sm)] border border-[rgba(22,163,74,0.2)] bg-[rgba(22,163,74,0.06)] p-4 flex flex-col gap-4">
                <p class="text-sm font-semibold text-[var(--color-text)] m-0">Accept Criteria</p>

                <div>
                  <label class="block text-sm font-semibold text-[var(--color-text)] mb-2">
                    Ideal Products/Services to Accept
                  </label>
                  <textarea
                    v-model="form.accept_products"
                    rows="4"
                    class="w-full resize-y rounded-[var(--radius-sm)] border border-[rgba(22,163,74,0.28)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[rgba(22,163,74,0.7)] focus:shadow-[0_0_0_3px_rgba(22,163,74,0.12)]"
                    placeholder="Describe the products/services that should be accepted (e.g. construction materials, electric materials)"
                  />
                </div>

                <div>
                  <label class="block text-sm font-semibold text-[var(--color-text)] mb-2">
                    Ideal Functional Profile
                  </label>
                  <textarea
                    v-model="form.ideal_functional_profile"
                    rows="4"
                    class="w-full resize-y rounded-[var(--radius-sm)] border border-[rgba(22,163,74,0.28)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[rgba(22,163,74,0.7)] focus:shadow-[0_0_0_3px_rgba(22,163,74,0.12)]"
                    placeholder="Describe ideal functional profile (e.g. distribution and wholesale)"
                  />
                </div>
              </section>

              <section class="rounded-[var(--radius-sm)] border border-[rgba(244,63,94,0.2)] bg-[rgba(244,63,94,0.06)] p-4 flex flex-col gap-4">
                <p class="text-sm font-semibold text-[var(--color-text)] m-0">Reject Criteria</p>

                <div>
                  <label class="block text-sm font-semibold text-[var(--color-text)] mb-2">
                    Products/Services to Reject
                  </label>
                  <textarea
                    v-model="form.reject_products"
                    rows="4"
                    class="w-full resize-y rounded-[var(--radius-sm)] border border-[rgba(244,63,94,0.28)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[rgba(244,63,94,0.65)] focus:shadow-[0_0_0_3px_rgba(244,63,94,0.12)]"
                    placeholder="Describe the products/services that should be rejected"
                  />
                </div>

                <div>
                  <label class="block text-sm font-semibold text-[var(--color-text)] mb-2">
                    Functions/Activities to Reject
                  </label>
                  <textarea
                    v-model="form.reject_functions"
                    rows="4"
                    class="w-full resize-y rounded-[var(--radius-sm)] border border-[rgba(244,63,94,0.28)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[rgba(244,63,94,0.65)] focus:shadow-[0_0_0_3px_rgba(244,63,94,0.12)]"
                    placeholder="Describe functions/activities that should be rejected"
                  />
                </div>
              </section>
            </div>
          </div>

        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-[var(--color-border)] bg-[var(--color-bg)] flex items-center justify-between gap-3 shrink-0">
          <p v-if="activeTab === 'ai' && form.accept_products" class="text-xs text-[var(--color-text-muted)] m-0">
            ✓ Criteria generated — switch to <button @click="activeTab = 'custom'" class="text-[var(--color-primary)] font-medium border-none bg-transparent cursor-pointer p-0">Custom Strategy</button> to edit.
          </p>
          <span v-else />
          <div class="flex gap-3">
            <button
              type="button"
              class="px-4 py-2 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-transparent text-sm font-semibold text-[var(--color-text-secondary)] cursor-pointer hover:bg-[var(--color-bg-alt)] transition-colors"
              @click="emit('close')"
            >
              Cancel
            </button>
            <button
              type="button"
              :disabled="!canSave || saving"
              @click="save"
              class="px-4 py-2 rounded-[var(--radius-sm)] border-none bg-[var(--color-primary)] text-white text-sm font-semibold cursor-pointer transition-all hover:bg-[var(--color-primary-hover)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ saving ? 'Saving…' : 'Save Criteria' }}
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
  to   { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
