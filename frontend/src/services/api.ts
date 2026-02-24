/**
 * API Client Layer
 *
 * Centralized Axios instance configured to talk to our FastAPI backend.
 * The Vite dev server proxies /api/* requests to http://localhost:8000,
 * so we only need relative URLs here.
 */

import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'

// ---------------------------------------------------------------------------
// Axios Instance
// ---------------------------------------------------------------------------
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60_000, // 60s — some AI analysis endpoints are slow
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request Interceptor — attach auth token
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response Interceptor — normalize errors + handle 401
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    // Extract the best error message we can
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    // If 401 and we have auth, clear token and redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      // Only redirect if not already on a public/auth page
      const path = window.location.pathname
      if (!path.startsWith('/login') && !path.startsWith('/register') && path !== '/') {
        window.location.href = `/login?redirect=${encodeURIComponent(path)}`
      }
    }

    return Promise.reject({ message, status: error.response?.status, raw: error })
  },
)

export default apiClient
