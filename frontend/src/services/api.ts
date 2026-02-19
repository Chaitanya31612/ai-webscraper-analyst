/**
 * API Client Layer
 *
 * Centralized Axios instance configured to talk to our FastAPI backend.
 * The Vite dev server proxies /api/* requests to http://localhost:8000,
 * so we only need relative URLs here.
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

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
// Request Interceptor — attach auth token when we add login later
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
// Response Interceptor — normalize errors
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

    // If 401 and we have auth, clear token (future auth integration)
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      // Could redirect to /login here later
    }

    return Promise.reject({ message, status: error.response?.status, raw: error })
  },
)

export default apiClient
