<script setup lang="ts">
/**
 * LoginView — Option 1: "Luminous Executive"
 *
 * Clean, centered auth form with:
 * - Glassmorphic card on dot-grid background
 * - Email + password inputs with refined styling
 * - Social login divider
 * - Link to register
 */
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppHeader from './AppHeader.vue'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)

function handleSubmit() {
  isLoading.value = true
  // Simulated login — would integrate with auth store
  setTimeout(() => {
    isLoading.value = false
  }, 1500)
}
</script>

<template>
  <div class="page">
    <AppHeader />

    <main class="auth noise-overlay">
      <!-- Background effects -->
      <div class="auth__grid dot-grid" aria-hidden="true"></div>
      <div class="auth__glow" aria-hidden="true"></div>

      <div class="auth__container fade-in-up">
        <!-- Card -->
        <div class="auth__card glass-card">
          <!-- Header -->
          <div class="auth__header">
            <div class="auth__logo">
              <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
                <rect x="2" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.9"/>
                <rect x="16" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
                <rect x="2" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
                <rect x="16" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.25"/>
              </svg>
            </div>
            <h1 class="auth__title">Welcome back</h1>
            <p class="auth__subtitle">Sign in to your AI Scraper account</p>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleSubmit" class="auth__form" id="login-form">
            <!-- Email -->
            <div class="auth__field">
              <label for="login-email" class="auth__label">Email</label>
              <div class="auth__input-wrapper">
                <svg class="auth__input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                </svg>
                <input
                  id="login-email"
                  v-model="email"
                  type="email"
                  placeholder="name@company.com"
                  required
                  autocomplete="email"
                  class="auth__input"
                />
              </div>
            </div>

            <!-- Password -->
            <div class="auth__field">
              <div class="auth__label-row">
                <label for="login-password" class="auth__label">Password</label>
                <a href="#" class="auth__forgot">Forgot password?</a>
              </div>
              <div class="auth__input-wrapper">
                <svg class="auth__input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input
                  id="login-password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  required
                  autocomplete="current-password"
                  class="auth__input"
                />
                <button
                  type="button"
                  class="auth__toggle-pw"
                  @click="showPassword = !showPassword"
                  :aria-label="showPassword ? 'Hide password' : 'Show password'"
                >
                  <svg v-if="!showPassword" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
            </div>

            <!-- Submit -->
            <button
              type="submit"
              class="auth__submit"
              id="login-submit"
              :disabled="isLoading"
            >
              <span v-if="!isLoading">Sign In</span>
              <span v-else class="auth__spinner"></span>
            </button>
          </form>

          <!-- Divider -->
          <div class="auth__divider">
            <span>or continue with</span>
          </div>

          <!-- Social buttons -->
          <div class="auth__social">
            <button class="auth__social-btn" id="login-google">
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Google
            </button>
            <button class="auth__social-btn" id="login-github">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>
              GitHub
            </button>
          </div>

          <!-- Footer -->
          <p class="auth__footer">
            Don't have an account?
            <RouterLink to="/register" class="auth__link">Create one</RouterLink>
          </p>
        </div>

        <!-- Trust indicators -->
        <div class="auth__trust fade-in-up fade-in-up-delay-2">
          <span>🔒 256-bit encryption</span>
          <span>·</span>
          <span>SOC 2 compliant</span>
          <span>·</span>
          <span>GDPR ready</span>
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

.auth {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6rem 1.5rem 3rem;
  overflow: hidden;
}

.auth__grid {
  position: absolute;
  inset: 0;
  opacity: 0.3;
}

.auth__glow {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 500px;
  background: radial-gradient(ellipse at center, var(--color-primary-glow) 0%, transparent 70%);
  pointer-events: none;
}

.auth__container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 420px;
}

.auth__card {
  padding: 2.5rem;
}

.auth__header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth__logo {
  display: flex;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.auth__title {
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 0.35rem;
}

.auth__subtitle {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

/* --- Form --- */
.auth__form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.auth__field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.auth__label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.auth__label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.auth__forgot {
  font-size: 0.75rem;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.auth__forgot:hover {
  text-decoration: underline;
}

.auth__input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.auth__input-icon {
  position: absolute;
  left: 0.85rem;
  color: var(--color-text-muted);
  pointer-events: none;
}

.auth__input {
  width: 100%;
  padding: 0.7rem 0.85rem 0.7rem 2.5rem;
  font-size: 0.9rem;
  font-family: var(--font-body);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.auth__input::placeholder {
  color: var(--color-text-muted);
}

.auth__input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-glow);
}

.auth__toggle-pw {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
}

.auth__toggle-pw:hover {
  color: var(--color-text-secondary);
}

.auth__submit {
  width: 100%;
  padding: 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  font-family: var(--font-body);
  color: #fff;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
  margin-top: 0.25rem;
}

.auth__submit:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 4px 16px rgba(79, 70, 229, 0.3);
  transform: translateY(-1px);
}

.auth__submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.auth__spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* --- Divider --- */
.auth__divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.auth__divider::before,
.auth__divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

/* --- Social --- */
.auth__social {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.auth__social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.65rem;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: var(--font-body);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.auth__social-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

/* --- Footer --- */
.auth__footer {
  text-align: center;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-top: 1.5rem;
}

.auth__link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

.auth__link:hover {
  text-decoration: underline;
}

/* --- Trust --- */
.auth__trust {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 2rem;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

@media (max-width: 480px) {
  .auth__card { padding: 2rem 1.5rem; }
  .auth__trust { flex-wrap: wrap; justify-content: center; }
}
</style>
