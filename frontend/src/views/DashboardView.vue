<script setup lang="ts">
/**
 * DashboardView — Main app home after login.
 *
 * Layout: Left sidebar (AppSidebar) + content area.
 * Features:
 *  - Welcome card with user greeting and "Start Benchmarking" CTA
 *  - Quick links / feature cards section
 */
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/AppSidebar.vue'
import { useSidebar } from '@/composables/useSidebar'

const authStore = useAuthStore()
const router = useRouter()
const { collapsed } = useSidebar()

function startBenchmarking() {
  router.push('/benchmark')
}
</script>

<template>
  <div class="app-layout">
    <AppSidebar />

    <main
      id="dashboard-main"
      :class="[
        'flex-1 transition-all duration-300 ease-in-out',
        collapsed ? 'ml-[60px]' : 'ml-[220px]',
        'px-10 pt-12 pb-16 max-w-[1100px]',
      ]"
    >
      <!-- Welcome Hero -->
      <section class="dashboard__welcome fade-in-up">
        <div class="dashboard__welcome-text">
          <h1 class="dashboard__greeting">
            Welcome back, {{ authStore.user?.full_name?.split(' ')[0] || 'there' }} 👋
          </h1>
          <p class="dashboard__subtext">
            Your AI-powered web analysis workspace. Choose an action below to get started.
          </p>
        </div>
      </section>

      <!-- Feature cards grid -->
      <section class="dashboard__cards fade-in-up fade-in-up-delay-1">
        <!-- Benchmarking Analysis card -->
        <button class="dashboard__feature-card" @click="startBenchmarking" id="card-benchmarking">
          <div class="dashboard__card-header">
            <div class="dashboard__card-icon dashboard__card-icon--primary">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
            </div>
            <svg class="dashboard__card-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
            </svg>
          </div>
          <h2 class="dashboard__card-title">Benchmarking Analysis</h2>
          <p class="dashboard__card-desc">
            Upload company data, scrape their websites with AI, and automatically classify them with accept/reject decisions.
          </p>
          <div class="dashboard__card-cta">
            Start benchmarking
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
            </svg>
          </div>
        </button>

        <!-- More features coming soon -->
        <div class="dashboard__feature-card dashboard__feature-card--muted" id="card-coming-soon-reports">
          <div class="dashboard__card-header">
            <div class="dashboard__card-icon dashboard__card-icon--muted">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <span class="dashboard__card-badge">Coming soon</span>
          </div>
          <h2 class="dashboard__card-title">Reports & Exports</h2>
          <p class="dashboard__card-desc">
            Generate structured Excel and JSON reports from your completed analysis runs.
          </p>
        </div>

        <div class="dashboard__feature-card dashboard__feature-card--muted" id="card-coming-soon-settings">
          <div class="dashboard__card-header">
            <div class="dashboard__card-icon dashboard__card-icon--muted">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
              </svg>
            </div>
            <span class="dashboard__card-badge">Coming soon</span>
          </div>
          <h2 class="dashboard__card-title">AI Configuration</h2>
          <p class="dashboard__card-desc">
            Manage AI provider settings, acceptance criteria, and scraping parameters.
          </p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ---- Shared app layout (sidebar + content) ---- */
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

/* ---- Welcome section ---- */
.dashboard__welcome {
  margin-bottom: 2.5rem;
}

.dashboard__greeting {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.dashboard__subtext {
  font-size: 1rem;
  color: var(--color-text-secondary);
}

/* ---- Feature cards grid ---- */
.dashboard__cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.dashboard__feature-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
}

.dashboard__feature-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--color-primary-glow);
  opacity: 0;
  transition: opacity 0.22s ease;
  border-radius: inherit;
  pointer-events: none;
}

.dashboard__feature-card:not(.dashboard__feature-card--muted):hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--color-primary);
  transform: translateY(-2px);
}

.dashboard__feature-card:not(.dashboard__feature-card--muted):hover::after {
  opacity: 1;
}

.dashboard__feature-card--muted {
  cursor: default;
  opacity: 0.65;
}

.dashboard__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dashboard__card-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dashboard__card-icon--primary {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.dashboard__card-icon--muted {
  background: var(--color-bg-alt);
  color: var(--color-text-muted);
}

.dashboard__card-arrow {
  color: var(--color-text-muted);
  transition: transform 0.2s ease, color 0.2s ease;
}

.dashboard__feature-card:not(.dashboard__feature-card--muted):hover .dashboard__card-arrow {
  transform: translateX(4px);
  color: var(--color-primary);
}

.dashboard__card-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.6rem;
  background: var(--color-bg-alt);
  border: 1px solid var(--color-border);
  border-radius: 99px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.dashboard__card-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
  margin: 0;
}

.dashboard__card-desc {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.55;
  flex: 1;
}

.dashboard__card-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-primary);
  padding-top: 0.25rem;
}

@media (max-width: 768px) {
  .dashboard__greeting {
    font-size: 1.5rem;
  }
}
</style>
