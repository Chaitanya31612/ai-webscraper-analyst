<script setup lang="ts">
// HomeView — Landing page placeholder
// Will be designed in the next phase
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-950 text-white">
    <div class="text-center space-y-4">
      <h1 class="text-5xl font-bold tracking-tight">AI Scraper</h1>
      <p class="text-lg text-neutral-400">Company intelligence, automated.</p>
      <div class="flex gap-4 justify-center pt-4">
        <router-link
          to="/login"
          class="px-6 py-2.5 rounded-lg bg-white text-neutral-950 font-medium hover:bg-neutral-200 transition-colors"
        >
          Sign In
        </router-link>
        <router-link
          to="/dashboard"
          class="px-6 py-2.5 rounded-lg border border-neutral-700 text-neutral-300 font-medium hover:border-neutral-500 hover:text-white transition-colors"
        >
          Dashboard
        </router-link>
      </div>
    </div>
  </div>
</template>
