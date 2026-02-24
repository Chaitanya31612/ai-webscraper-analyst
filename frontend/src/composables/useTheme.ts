/**
 * Theme composable — manages light/dark mode toggle
 * Persists preference to localStorage, respects system preference on first visit
 */
import { ref, watch, onMounted } from 'vue'

type Theme = 'light' | 'dark'

const STORAGE_KEY = 'ai-scraper-theme'

const theme = ref<Theme>('light')

function applyTheme(t: Theme) {
  if (t === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

export function useTheme() {
  onMounted(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null
    if (stored) {
      theme.value = stored
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      theme.value = 'dark'
    }
    applyTheme(theme.value)
  })

  watch(theme, (val) => {
    localStorage.setItem(STORAGE_KEY, val)
    applyTheme(val)
  })

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return {
    theme,
    toggleTheme,
  }
}
