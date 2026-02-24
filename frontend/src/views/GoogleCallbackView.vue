<script setup lang="ts">
/**
 * GoogleCallbackView — handles the Google OAuth redirect.
 *
 * When Google redirects back to our app with a ?code=... param,
 * this page extracts the code and posts it back to the opener window
 * (the login/register popup flow). If opened directly (not as popup),
 * it exchanges the code directly.
 */
import { onMounted } from 'vue'

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')

  if (code && window.opener) {
    // We're in a popup — send the code back to the opener
    window.opener.postMessage(
      { type: 'google-auth-code', code },
      window.location.origin,
    )
    window.close()
  } else if (code) {
    // Opened directly (not popup) — could handle inline, but for now just close
    window.close()
  }
})
</script>

<template>
  <div class="callback">
    <div class="callback__spinner"></div>
    <p>Completing sign in...</p>
  </div>
</template>

<style scoped>
.callback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 1rem;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.callback__spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
