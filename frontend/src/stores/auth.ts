/**
 * Auth Store — manages authentication state.
 *
 * Handles email/password login & register, Google OAuth,
 * and JWT token persistence via localStorage.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/services/api'

export interface User {
  id: string
  email: string
  full_name: string
  avatar_url?: string | null
  auth_provider: string
  created_at: string
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
      const { data } = await apiClient.post('/auth/login', { email, password })
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem('auth_token', data.access_token)
      return data
    } catch (e: any) {
      error.value = e.message || 'Login failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function register(fullName: string, email: string, password: string) {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await apiClient.post('/auth/register', {
        full_name: fullName,
        email,
        password,
      })
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem('auth_token', data.access_token)
      return data
    } catch (e: any) {
      error.value = e.message || 'Registration failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function loginWithGoogle(code: string, redirectUri: string) {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await apiClient.post('/auth/google', { code, redirect_uri: redirectUri })
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem('auth_token', data.access_token)
      return data
    } catch (e: any) {
      error.value = e.message || 'Google login failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const { data } = await apiClient.get('/auth/me')
      user.value = data
    } catch {
      // Token expired or invalid — clear it
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('auth_token')
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    fetchUser,
    logout,
  }
})
