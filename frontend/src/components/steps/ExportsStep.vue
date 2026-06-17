<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Download, FileSpreadsheet, Loader2, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import { companyService } from '@/services/companyService'
import { batchService } from '@/services/batchService'

const props = defineProps<{
  batchId: string | null
}>()

const isDownloading = ref(false)
const downloadError = ref<string | null>(null)
const downloadSuccess = ref(false)
const companyCount = ref(0)
const isLoadingCount = ref(false)

async function loadCount() {
  if (!props.batchId) return
  isLoadingCount.value = true
  try {
    const companies = await batchService.getCompanies(props.batchId)
    // Count only companies that have been fully analysed
    companyCount.value = companies.filter(c => c.status === 'complete').length
  } catch {
    companyCount.value = 0
  } finally {
    isLoadingCount.value = false
  }
}


async function downloadExcel() {
  if (!props.batchId || isDownloading.value) return
  downloadError.value = null
  downloadSuccess.value = false
  isDownloading.value = true
  try {
    await companyService.exportExcel(props.batchId)
    downloadSuccess.value = true
    setTimeout(() => { downloadSuccess.value = false }, 4000)
  } catch (e: unknown) {
    downloadError.value = (e as { message?: string })?.message || 'Download failed. Please try again.'
  } finally {
    isDownloading.value = false
  }
}

onMounted(loadCount)
watch(() => props.batchId, loadCount)
</script>

<template>
  <div class="flex flex-col gap-5">
    <!-- Info banner -->
    <div class="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-bg-alt)] px-4 py-3">
      <p class="text-xs text-[var(--color-text-secondary)] m-0 leading-relaxed">
        The exported Excel contains three sections:
        <strong class="text-[#3B6CB0]">General Info</strong> (company name, country, website),
        <strong class="text-[#2E7D5C]">Business Description</strong> (AI-extracted business profile, products, functional profile),
        and <strong class="text-[#7C3AED]">AI Results</strong> (AI decision, final decision, confidence, reasoning).
      </p>
    </div>

    <!-- Export card -->
    <div class="glass-card flex items-center gap-5 px-6 py-5">
      <!-- Icon -->
      <div class="w-14 h-14 rounded-[var(--radius-md)] bg-[rgba(52,211,153,0.1)] border border-[rgba(52,211,153,0.2)] flex items-center justify-center shrink-0">
        <FileSpreadsheet :size="26" class="text-[var(--color-accent)]" />
      </div>

      <!-- Info -->
      <div class="flex-1 min-w-0">
        <p class="text-sm font-bold text-[var(--color-text)] m-0 mb-0.5">
          Companies with AI Web Analysis
        </p>
        <p class="text-xs text-[var(--color-text-muted)] m-0">
          Excel (.xlsx) — structured with colour-coded section headers
        </p>
        <p v-if="!isLoadingCount" class="text-xs text-[var(--color-text-secondary)] m-0 mt-1">
          <span class="font-semibold">{{ companyCount }}</span> companies analysed
        </p>
        <p v-else class="text-xs text-[var(--color-text-muted)] m-0 mt-1">Loading…</p>
      </div>

      <!-- Download button -->
      <div class="flex flex-col items-end gap-1.5 shrink-0">
        <button
          @click="downloadExcel"
          :disabled="!batchId || isDownloading || companyCount === 0"
          :class="[
            'flex items-center gap-2 px-5 py-2.5 rounded-[var(--radius-sm)] text-sm font-semibold border-none cursor-pointer transition-all',
            downloadSuccess
              ? 'bg-[var(--color-accent)] text-white'
              : 'bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)]',
            (!batchId || companyCount === 0) ? 'opacity-40 cursor-not-allowed' : '',
          ]"
        >
          <Loader2 v-if="isDownloading" :size="14" class="animate-spin" />
          <CheckCircle2 v-else-if="downloadSuccess" :size="14" />
          <Download v-else :size="14" />
          {{ isDownloading ? 'Downloading…' : downloadSuccess ? 'Downloaded!' : 'Download Excel' }}
        </button>

        <p v-if="downloadError" class="flex items-center gap-1 text-[0.7rem] text-[var(--color-danger)] m-0">
          <AlertCircle :size="11" />{{ downloadError }}
        </p>
      </div>
    </div>

    <!-- Column structure preview table -->
    <div class="rounded-[var(--radius-sm)] border border-[var(--color-border)] overflow-hidden">
      <table class="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th colspan="5" class="py-2 text-center font-bold text-white bg-[#3B6CB0] border border-[rgba(255,255,255,0.15)]">
              General Info
            </th>
            <th colspan="5" class="py-2 text-center font-bold text-white bg-[#2E7D5C] border border-[rgba(255,255,255,0.15)]">
              Business Description
            </th>
            <th colspan="4" class="py-2 text-center font-bold text-white bg-[#7C3AED] border border-[rgba(255,255,255,0.15)]">
              AI Results
            </th>
          </tr>
          <tr class="bg-[var(--color-bg-alt)] text-[var(--color-text-secondary)]">
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Company Name</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">BVD ID</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Country</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Website</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Industry</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Source</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Business Description</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Products & Services</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Functional Profile</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Corporate Structure</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">AI Decision</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Final Decision</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">Confidence %</th>
            <th class="px-2 py-1.5 text-left font-semibold border border-[var(--color-border)]">AI Reasoning</th>
          </tr>
        </thead>
        <tbody>
          <tr class="text-[var(--color-text-muted)] italic">
            <td class="px-2 py-2 border border-[var(--color-border)] text-[var(--color-text-secondary)] not-italic font-medium">Acme Corp</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">DE12345678</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">Germany</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">acme.com</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">Distribution</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">acme.com</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">Acme Corp is a leading…</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">Product A; Product B</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">B2B Distributor</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">SMB</td>
            <td class="px-2 py-2 border border-[var(--color-border)] text-[var(--color-accent)] font-semibold not-italic">Accept</td>
            <td class="px-2 py-2 border border-[var(--color-border)] text-[var(--color-accent)] font-semibold not-italic">Accept</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">92%</td>
            <td class="px-2 py-2 border border-[var(--color-border)]">Matches criteria…</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin { animation: spin 1s linear infinite; }
</style>
