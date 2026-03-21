<script setup lang="ts">
/**
 * AppSidebar — collapsible left navigation for authenticated pages.
 * Uses Tailwind v4 utility classes and lucide-vue-next icons.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Activity,
  Sun,
  Moon,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'
import { useBenchmarkStore } from '@/stores/benchmark'
import { useSidebar } from '@/composables/useSidebar'

const { theme, toggleTheme } = useTheme()
const authStore = useAuthStore()
const benchmarkStore = useBenchmarkStore()
const router = useRouter()
const route = useRoute()
const { collapsed, toggle } = useSidebar()

/** Navigate to a fresh /benchmark session — clears any existing batch ID from the URL. */
function goToNewBenchmark() {
  benchmarkStore.reset()
  router.push('/benchmark')
}

const accountOpen = ref(false)
// Template ref for the user-wrap element — used for click-outside detection
const userWrapRef = ref<HTMLElement | null>(null)

function handleLogout() {
  authStore.logout()
  accountOpen.value = false
  router.push('/')
}

function isActive(path: string) {
  if (path === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(path)
}

// Close popover when clicking anywhere outside the user-wrap element
function handleDocumentClick(event: MouseEvent) {
  if (accountOpen.value && userWrapRef.value && !userWrapRef.value.contains(event.target as Node)) {
    accountOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleDocumentClick))
onUnmounted(() => document.removeEventListener('click', handleDocumentClick))

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Benchmarks', to: '/benchmark', icon: Activity },
]
</script>

<template>
  <!-- Sidebar -->
  <aside
    id="app-sidebar"
    :class="[
      'fixed top-0 left-0 bottom-0 z-90 flex flex-col',
      'bg-[var(--color-surface)] border-r border-[var(--color-border)]',
      'transition-all duration-300 ease-in-out',
      collapsed ? 'w-[60px]' : 'w-[220px]',
    ]"
  >
    <!-- Top: logo + collapse toggle -->
    <!-- When expanded: logo left, chevron right. When collapsed: only chevron centered. -->
    <div
      :class="[
        'flex items-center px-3 py-3 min-h-[56px]',
        collapsed ? 'justify-center' : 'gap-2',
      ]"
    >
      <!-- Logo — hidden when collapsed -->
      <RouterLink
        v-if="!collapsed"
        to="/dashboard"
        id="sidebar-logo"
        class="flex items-center gap-2 flex-1 min-w-0 no-underline text-[var(--color-text)] rounded-md px-1 py-1 hover:bg-[var(--color-primary-light)] transition-colors"
      >
        <svg class="shrink-0" width="22" height="22" viewBox="0 0 28 28" fill="none">
          <rect x="2" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.9"/>
          <rect x="16" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
          <rect x="2" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
          <rect x="16" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.25"/>
        </svg>
        <span class="font-display font-bold text-[1.05rem] tracking-tight whitespace-nowrap overflow-hidden">
          AI Scraper
        </span>
      </RouterLink>

      <!-- Collapse toggle button -->
      <button
        id="sidebar-collapse-btn"
        @click="toggle"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        class="shrink-0 flex items-center justify-center w-7 h-7 rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)] hover:border-[var(--color-primary)] transition-all duration-200"
      >
        <ChevronLeft v-if="!collapsed" :size="14" />
        <ChevronRight v-else :size="14" />
      </button>
    </div>

    <!-- Divider -->
    <div class="h-px bg-[var(--color-border)] mx-3 mb-2" />

    <!-- Nav items -->
    <nav id="sidebar-nav" class="flex flex-col gap-1 flex-1 px-2">
      <template v-for="item in navItems" :key="item.to">
        <!-- Benchmarks: always resets store + navigates to /benchmark (clears batch ID from URL) -->
        <button
          v-if="item.label === 'Benchmarks'"
          :id="`sidebar-nav-${item.label.toLowerCase()}`"
          :title="collapsed ? item.label : undefined"
          @click="goToNewBenchmark"
          :class="[
            'flex items-center gap-2.5 px-2.5 py-2.5 rounded-md border-none bg-transparent w-full text-left',
            'font-medium text-sm transition-all duration-150 relative cursor-pointer',
            'hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)]',
            isActive(item.to)
              ? 'text-[var(--color-primary)] bg-[var(--color-primary-light)] font-semibold'
              : 'text-[var(--color-text-secondary)]',
            collapsed ? 'justify-center' : '',
          ]"
        >
          <span
            v-if="isActive(item.to)"
            class="absolute left-0 top-[20%] bottom-[20%] w-[3px] rounded-r-sm bg-[var(--color-primary)]"
          />
          <component :is="item.icon" :size="18" class="shrink-0" />
          <span
            :class="[
              'whitespace-nowrap overflow-hidden transition-all duration-300',
              collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100',
            ]"
          >{{ item.label }}</span>
        </button>

        <!-- All other nav items: standard RouterLink -->
        <RouterLink
          v-else
          :to="item.to"
          :id="`sidebar-nav-${item.label.toLowerCase()}`"
          :title="collapsed ? item.label : undefined"
          :class="[
            'flex items-center gap-2.5 px-2.5 py-2.5 rounded-md no-underline',
            'font-medium text-sm transition-all duration-150 relative',
            'hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)]',
            isActive(item.to)
              ? 'text-[var(--color-primary)] bg-[var(--color-primary-light)] font-semibold'
              : 'text-[var(--color-text-secondary)]',
            collapsed ? 'justify-center' : '',
          ]"
        >
          <span
            v-if="isActive(item.to)"
            class="absolute left-0 top-[20%] bottom-[20%] w-[3px] rounded-r-sm bg-[var(--color-primary)]"
          />
          <component :is="item.icon" :size="18" class="shrink-0" />
          <span
            :class="[
              'whitespace-nowrap overflow-hidden transition-all duration-300',
              collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100',
            ]"
          >{{ item.label }}</span>
        </RouterLink>
      </template>
    </nav>

    <!-- Bottom: theme + user -->
    <div
      :class="[
        'flex items-center border-t border-[var(--color-border)] mt-2 pt-3 pb-3 px-2',
        collapsed ? 'flex-col gap-2' : 'justify-between gap-2',
      ]"
    >
      <!-- Theme toggle -->
      <button
        id="sidebar-theme-toggle"
        @click="toggleTheme"
        :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
        :title="theme === 'dark' ? 'Light mode' : 'Dark mode'"
        class="flex items-center justify-center w-9 h-9 rounded-md border border-[var(--color-border)] bg-transparent cursor-pointer text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-all duration-200 shrink-0"
      >
        <Sun v-if="theme === 'dark'" :size="17" />
        <Moon v-else :size="17" />
      </button>

      <!-- User avatar -->
      <div ref="userWrapRef" class="relative shrink-0">
        <button
          id="sidebar-user-trigger"
          @click="accountOpen = !accountOpen"
          :title="authStore.user?.full_name || 'Account'"
          class="flex items-center justify-center w-9 h-9 rounded-full border-2 border-[var(--color-border)] bg-[var(--color-primary)] text-white cursor-pointer overflow-hidden p-0 hover:border-[var(--color-primary)] hover:shadow-[0_0_0_3px_var(--color-primary-glow)] transition-all duration-200"
        >
          <img
            v-if="authStore.user?.avatar_url"
            :src="authStore.user.avatar_url"
            :alt="authStore.user?.full_name"
            class="w-full h-full object-cover"
          />
          <span v-else class="text-sm font-bold leading-none select-none">
            {{ authStore.user?.full_name?.charAt(0)?.toUpperCase() || 'U' }}
          </span>
        </button>

        <!-- Account popover -->
        <Transition name="popover">
          <div
            v-if="accountOpen"
            id="sidebar-account-popover"
            :class="[
              'absolute z-200 w-[260px]',
              'bg-[var(--color-surface)] border border-[var(--color-border)]',
              'rounded-[var(--radius-md)] shadow-[var(--shadow-lg)] p-3',
              'left-full bottom-4 ml-2',
            ]"
          >
            <!-- User info row -->
            <div class="flex items-center gap-3 mb-1">
              <div class="w-10 h-10 rounded-full bg-[var(--color-primary)] border-2 border-[var(--color-primary-light)] text-white flex items-center justify-center overflow-hidden shrink-0">
                <img
                  v-if="authStore.user?.avatar_url"
                  :src="authStore.user.avatar_url"
                  :alt="authStore.user?.full_name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-base font-bold select-none">
                  {{ authStore.user?.full_name?.charAt(0)?.toUpperCase() || 'U' }}
                </span>
              </div>
              <div class="min-w-0">
                <div class="text-sm font-semibold text-[var(--color-text)] truncate">{{ authStore.user?.full_name }}</div>
                <div class="text-xs text-[var(--color-text-muted)] truncate mt-0.5">{{ authStore.user?.email }}</div>
              </div>
            </div>

            <div class="h-px bg-[var(--color-border)] my-2.5" />

            <!-- Account details -->
            <div class="flex flex-col gap-2 mb-1">
              <div class="flex justify-between items-center">
                <span class="text-xs text-[var(--color-text-muted)] font-medium">Auth Provider</span>
                <span class="text-[0.7rem] font-semibold px-2 py-0.5 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)] capitalize">
                  {{ authStore.user?.auth_provider }}
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-[var(--color-text-muted)] font-medium">Joined</span>
                <span class="text-xs text-[var(--color-text)]">
                  {{ new Date(authStore.user?.created_at || '').toLocaleDateString('en-GB') }}
                </span>
              </div>
            </div>

            <div class="h-px bg-[var(--color-border)] my-2.5" />

            <!-- Logout -->
            <button
              id="sidebar-logout"
              @click="handleLogout"
              class="flex items-center gap-2 w-full px-2 py-2 rounded-md border-none bg-transparent text-[var(--color-danger)] text-sm font-medium cursor-pointer font-sans hover:bg-[rgba(244,63,94,0.08)] transition-colors duration-150"
            >
              <LogOut :size="14" />
              Log Out
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </aside>
</template>

<style scoped>
/* Only non-Tailwind-able transitions */
.popover-enter-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.popover-leave-active {
  transition: all 0.15s ease;
}
.popover-enter-from,
.popover-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.97);
}
</style>
