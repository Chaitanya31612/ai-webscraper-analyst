/**
 * Auth Store — manages authentication state.
 *
 * Placeholder for Phase 2 login/register integration.
 * Currently provides reactive auth state and mock methods.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface User {
  id: string
  email: string
  name: string
}

export const useAuthStore = defineStore('auth', () => {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------
  const isAuthenticated = computed(() => !!token.value)

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function login(email: string, password: string) {
    isLoading.value = true
    error.value = null
    try {
      // TODO: Replace with actual API call when auth endpoint is ready
      // const { data } = await apiClient.post('/auth/login', { email, password })
      // token.value = data.access_token
      // user.value = data.user
      // localStorage.setItem('auth_token', data.access_token)
      console.warn('[AuthStore] login() is a stub — no auth endpoint yet')
    } catch (e: any) {
      error.value = e.message || 'Login failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function register(name: string, email: string, password: string) {
    isLoading.value = true
    error.value = null
    try {
      // TODO: Replace with actual API call
      console.warn('[AuthStore] register() is a stub — no auth endpoint yet')
    } catch (e: any) {
      error.value = e.message || 'Registration failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('auth_token')
  }

  function setUser(u: User) {
    user.value = u
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    setUser,
  }
})
