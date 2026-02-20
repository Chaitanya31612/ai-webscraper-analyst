<script setup lang="ts">
/**
 * DashboardView — placeholder for the main app experience.
 * Requires authentication to access.
 */
import { useAuthStore } from '@/stores/auth'
import AppHeader from './AppHeader.vue'

const authStore = useAuthStore()
</script>

<template>
  <div class="page">
    <AppHeader />

    <main class="dashboard">
      <div class="dashboard__container">
        <h1 class="dashboard__title">
          Welcome, {{ authStore.user?.full_name || 'User' }} 👋
        </h1>
        <p class="dashboard__subtitle">
          Your AI Scraper dashboard is coming soon. For now, you're successfully authenticated!
        </p>

        <div class="dashboard__card glass-card">
          <h2 class="dashboard__card-title">Account Info</h2>
          <div class="dashboard__info-grid">
            <div class="dashboard__info-item">
              <span class="dashboard__info-label">Email</span>
              <span class="dashboard__info-value">{{ authStore.user?.email }}</span>
            </div>
            <div class="dashboard__info-item">
              <span class="dashboard__info-label">Auth Provider</span>
              <span class="dashboard__info-value">{{ authStore.user?.auth_provider }}</span>
            </div>
            <div class="dashboard__info-item">
              <span class="dashboard__info-label">Joined</span>
              <span class="dashboard__info-value">{{ new Date(authStore.user?.created_at || '').toLocaleDateString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg);
}

.dashboard {
  padding: 6rem 2rem 3rem;
  max-width: 800px;
  margin: 0 auto;
}

.dashboard__title {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 0.5rem;
}

.dashboard__subtitle {
  color: var(--color-text-secondary);
  font-size: 1rem;
  margin-bottom: 2rem;
}

.dashboard__card {
  padding: 2rem;
}

.dashboard__card-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
}

.dashboard__info-grid {
  display: grid;
  gap: 1rem;
}

.dashboard__info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
}

.dashboard__info-item:last-child {
  border-bottom: none;
}

.dashboard__info-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.dashboard__info-value {
  font-size: 0.9rem;
  color: var(--color-text);
}
</style>
