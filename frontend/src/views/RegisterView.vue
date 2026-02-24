<script setup lang="ts">
/**
 * RegisterView — "Luminous Executive"
 *
 * Registration form with:
 * - Full name, email, password, confirm password
 * - Password strength indicator
 * - Google OAuth button
 * - Link to login
 */
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppHeader from './AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const agreed = ref(false)

async function handleSubmit() {
  if (confirmPassword.value !== password.value) return
  try {
    await authStore.register(fullName.value, email.value, password.value)
    router.push('/dashboard')
  } catch {
    // error is set in the store
  }
}

async function handleGoogleLogin() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) {
    authStore.error = 'Google OAuth is not configured'
    return
  }

  const redirectUri = `${window.location.origin}/auth/google/callback`
  const scope = 'openid email profile'
  const googleAuthUrl =
    `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${clientId}&` +
    `redirect_uri=${encodeURIComponent(redirectUri)}&` +
    `response_type=code&` +
    `scope=${encodeURIComponent(scope)}&` +
    `access_type=offline&` +
    `prompt=consent`

  const width = 500
  const height = 600
  const left = window.screenX + (window.innerWidth - width) / 2
  const top = window.screenY + (window.innerHeight - height) / 2
  const popup = window.open(
    googleAuthUrl,
    'google-auth',
    `width=${width},height=${height},left=${left},top=${top}`,
  )

  const handleMessage = async (event: MessageEvent) => {
    if (event.origin !== window.location.origin) return
    if (event.data?.type === 'google-auth-code') {
      window.removeEventListener('message', handleMessage)
      popup?.close()
      try {
        await authStore.loginWithGoogle(event.data.code, redirectUri)
        router.push('/dashboard')
      } catch {
        // error is set in the store
      }
    }
  }
  window.addEventListener('message', handleMessage)

  const pollTimer = setInterval(() => {
    if (popup?.closed) {
      clearInterval(pollTimer)
      window.removeEventListener('message', handleMessage)
    }
  }, 500)
}
</script>

<template>
  <div class="page">
    <AppHeader />

    <main class="auth noise-overlay">
      <div class="auth__grid dot-grid" aria-hidden="true"></div>
      <div class="auth__glow" aria-hidden="true"></div>

      <div class="auth__container fade-in-up">
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
            <h1 class="auth__title">Create your account</h1>
            <p class="auth__subtitle">Start analyzing companies in under 2 minutes</p>
          </div>

          <!-- Error message -->
          <div v-if="authStore.error" class="auth__alert auth__alert--error">
            {{ authStore.error }}
          </div>

          <!-- Form -->
          <form @submit.prevent="handleSubmit" class="auth__form" id="register-form">
            <!-- Full Name -->
            <div class="auth__field">
              <label for="register-name" class="auth__label">Full Name</label>
              <div class="auth__input-wrapper">
                <svg class="auth__input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                <input id="register-name" v-model="fullName" type="text" placeholder="Jane Smith" required autocomplete="name" class="auth__input"/>
              </div>
            </div>

            <!-- Email -->
            <div class="auth__field">
              <label for="register-email" class="auth__label">Work Email</label>
              <div class="auth__input-wrapper">
                <svg class="auth__input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                </svg>
                <input id="register-email" v-model="email" type="email" placeholder="jane@company.com" required autocomplete="email" class="auth__input"/>
              </div>
            </div>

            <!-- Password -->
            <div class="auth__field">
              <label for="register-password" class="auth__label">Password</label>
              <div class="auth__input-wrapper">
                <svg class="auth__input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input id="register-password" v-model="password" :type="showPassword ? 'text' : 'password'" placeholder="Minimum 8 characters" required minlength="8" autocomplete="new-password" class="auth__input"/>
                <button type="button" class="auth__toggle-pw" @click="showPassword = !showPassword">
                  <svg v-if="!showPassword" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <!-- Password strength indicator -->
              <div class="auth__strength">
                <div class="auth__strength-bar">
                  <div class="auth__strength-fill" :style="{ width: password.length >= 12 ? '100%' : password.length >= 8 ? '66%' : password.length >= 4 ? '33%' : '0%' }" :class="{
                    'auth__strength-fill--weak': password.length >= 4 && password.length < 8,
                    'auth__strength-fill--ok': password.length >= 8 && password.length < 12,
                    'auth__strength-fill--strong': password.length >= 12,
                  }"></div>
                </div>
                <span class="auth__strength-label" v-if="password.length > 0">
                  {{ password.length >= 12 ? 'Strong' : password.length >= 8 ? 'Good' : 'Weak' }}
                </span>
              </div>
            </div>

            <!-- Confirm Password -->
            <div class="auth__field">
              <label for="register-confirm" class="auth__label">Confirm Password</label>
              <div class="auth__input-wrapper">
                <svg class="auth__input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                <input id="register-confirm" v-model="confirmPassword" :type="showPassword ? 'text' : 'password'" placeholder="Re-enter your password" required autocomplete="new-password" class="auth__input"/>
              </div>
              <span v-if="confirmPassword && confirmPassword !== password" class="auth__error">Passwords do not match</span>
            </div>

            <!-- Terms -->
            <label class="auth__checkbox-row" for="register-terms">
              <input id="register-terms" v-model="agreed" type="checkbox" required class="auth__checkbox"/>
              <span class="auth__checkbox-label">
                I agree to the <a href="#" class="auth__link">Terms of Service</a> and <a href="#" class="auth__link">Privacy Policy</a>
              </span>
            </label>

            <!-- Submit -->
            <button type="submit" class="auth__submit" id="register-submit" :disabled="authStore.isLoading || !agreed || (confirmPassword !== password)">
              <span v-if="!authStore.isLoading">Create Account</span>
              <span v-else class="auth__spinner"></span>
            </button>
          </form>

          <!-- Divider -->
          <div class="auth__divider"><span>or continue with</span></div>

          <!-- Google -->
          <div class="auth__social">
            <button class="auth__social-btn auth__social-btn--full" id="register-google" @click="handleGoogleLogin" :disabled="authStore.isLoading">
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Continue with Google
            </button>
          </div>

          <p class="auth__footer">
            Already have an account?
            <RouterLink to="/login" class="auth__link">Sign in</RouterLink>
          </p>
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
  max-width: 440px;
}

.auth__card {
  padding: 2.5rem;
}

.auth__header {
  text-align: center;
  margin-bottom: 1.75rem;
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

/* --- Alert --- */
.auth__alert {
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.auth__alert--error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.auth__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.auth__label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-secondary);
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

.auth__input::placeholder { color: var(--color-text-muted); }

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

.auth__toggle-pw:hover { color: var(--color-text-secondary); }

.auth__error {
  font-size: 0.75rem;
  color: var(--color-danger);
  margin-top: 0.15rem;
}

/* Password strength */
.auth__strength {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.3rem;
}

.auth__strength-bar {
  flex: 1;
  height: 3px;
  background: var(--color-border);
  border-radius: 999px;
  overflow: hidden;
}

.auth__strength-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease, background 0.3s ease;
}

.auth__strength-fill--weak { background: var(--color-danger); }
.auth__strength-fill--ok { background: var(--color-warning); }
.auth__strength-fill--strong { background: var(--color-accent); }

.auth__strength-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

/* Checkbox */
.auth__checkbox-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
}

.auth__checkbox {
  margin-top: 0.15rem;
  accent-color: var(--color-primary);
}

.auth__checkbox-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  line-height: 1.4;
}

/* Submit */
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
  opacity: 0.5;
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

@keyframes spin { to { transform: rotate(360deg); } }

/* Divider, social, footer — shared */
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

.auth__social {
  display: flex;
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

.auth__social-btn--full {
  width: 100%;
}

.auth__social-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.auth__social-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

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

.auth__link:hover { text-decoration: underline; }

@media (max-width: 480px) {
  .auth__card { padding: 2rem 1.5rem; }
}
</style>
