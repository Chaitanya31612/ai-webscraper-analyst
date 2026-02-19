<script setup lang="ts">
// DashboardView — empty shell, to be built out in Phase 2
</script>

<template>
  <div class="min-h-screen bg-neutral-950 text-white">
    <header class="border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold tracking-tight">AI Scraper Dashboard</h1>
      <router-link
        to="/"
        class="text-sm text-neutral-500 hover:text-white transition-colors"
      >
        ← Home
      </router-link>
    </header>
    <main class="p-6">
      <div class="border border-dashed border-neutral-700 rounded-xl p-12 text-center">
        <p class="text-neutral-500">Dashboard content will be built here.</p>
      </div>
    </main>
  </div>
</template>
