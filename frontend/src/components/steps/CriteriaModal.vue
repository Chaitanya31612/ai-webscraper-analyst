<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { X } from 'lucide-vue-next'
import type { CriteriaUpdate } from '@/types/api'

const props = defineProps<{
  open: boolean
  initialCriteria?: CriteriaUpdate | null
  saving?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', payload: CriteriaUpdate): void
}>()

const form = reactive<Required<CriteriaUpdate>>({
  accept_products: '',
  reject_products: '',
  ideal_functional_profile: '',
  reject_functions: '',
})

function applyInitialValues() {
  form.accept_products = props.initialCriteria?.accept_products ?? ''
  form.reject_products = props.initialCriteria?.reject_products ?? ''
  form.ideal_functional_profile = props.initialCriteria?.ideal_functional_profile ?? ''
  form.reject_functions = props.initialCriteria?.reject_functions ?? ''
}

watch(() => props.open, (isOpen) => {
  if (isOpen) applyInitialValues()
})

watch(() => props.initialCriteria, () => {
  if (props.open) applyInitialValues()
}, { deep: true })

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
      <div class="w-full max-w-[820px] max-h-[90vh] overflow-hidden rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)] shadow-[0_30px_60px_rgba(2,6,23,0.28)]">
        <div class="flex items-start justify-between gap-4 px-6 pt-5 pb-3 border-b border-[var(--color-border)]">
          <div>
            <h3 class="text-[1.45rem] font-bold tracking-tight text-[var(--color-text)] m-0">
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

        <div class="px-6 py-5 overflow-y-auto max-h-[64vh]">
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

        <div class="px-6 py-4 border-t border-[var(--color-border)] bg-[var(--color-bg)] flex items-center justify-end gap-3">
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
  </Teleport>
</template>
