<script setup lang="ts">
/**
 * StepNavigator — horizontal multi-step wizard.
 * Uses Tailwind v4 classes and lucide-vue-next icons.
 */
import { Home, Check } from 'lucide-vue-next'

export interface Step {
  label: string
}

const props = defineProps<{
  steps: Step[]
  modelValue: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>()
</script>

<template>
  <div
    id="step-navigator"
    role="tablist"
    aria-label="Analysis steps"
    class="bg-[var(--color-surface)] border-b border-[var(--color-border)] px-6 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
  >
    <div class="flex items-center min-w-max py-3 gap-0">
      <template v-for="(step, index) in steps" :key="index">
        <!-- Step button -->
        <button
          :id="`step-nav-${index}`"
          role="tab"
          :aria-selected="index === modelValue"
          @click="emit('update:modelValue', index)"
          :class="[
            'flex items-center gap-2 px-2 py-1.5 border-none bg-transparent cursor-pointer rounded-md font-sans transition-colors duration-150',
            index !== modelValue && index >= modelValue
              ? 'hover:bg-[var(--color-primary-light)]'
              : '',
          ]"
        >
          <!-- Circle indicator -->
          <div
            :class="[
              'w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-all duration-200',
              index < modelValue
                ? 'bg-[var(--color-primary)] border-2 border-[var(--color-primary)] text-white'
                : index === modelValue
                  ? 'bg-[var(--color-primary)] border-2 border-[var(--color-primary)] text-white shadow-[0_0_0_4px_var(--color-primary-glow)]'
                  : 'bg-[var(--color-bg-alt)] border-2 border-[var(--color-border)] text-[var(--color-text-muted)]',
            ]"
          >
            <!-- Completed: checkmark -->
            <Check v-if="index < modelValue" :size="12" stroke-width="3" />
            <!-- First step: home icon -->
            <Home v-else-if="index === 0" :size="12" stroke-width="2.5" />
            <!-- Others: number -->
            <span v-else class="text-[0.7rem] font-bold leading-none">{{ index }}</span>
          </div>

          <!-- Label -->
          <span
            :class="[
              'text-[0.8rem] whitespace-nowrap transition-colors duration-150',
              index === modelValue
                ? 'text-[var(--color-primary)] font-bold'
                : index < modelValue
                  ? 'text-[var(--color-text-secondary)] font-medium'
                  : 'text-[var(--color-text-muted)] font-medium',
            ]"
          >{{ step.label }}</span>
        </button>

        <!-- Connector line -->
        <div
          v-if="index < steps.length - 1"
          :class="[
            'h-0.5 min-w-6 max-w-12 flex-1 shrink-0 rounded-sm transition-colors duration-300',
            index < modelValue
              ? 'bg-[var(--color-primary)] opacity-60'
              : 'bg-[var(--color-border)]',
          ]"
        />
      </template>
    </div>
  </div>
</template>
