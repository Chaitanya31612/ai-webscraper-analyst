<script setup lang="ts">
/**
 * AppHeader — Option 1: "Luminous Executive"
 *
 * Premium sticky header with:
 * - Logo + Product links (About, Pricing, Features)
 * - Company dropdown (Team, Careers, Contact)
 * - Theme toggle + Log In CTA
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()
const scrolled = ref(false)
const companyOpen = ref(false)
const mobileOpen = ref(false)

function handleScroll() {
  scrolled.value = window.scrollY > 20
}

function closeDropdowns() {
  companyOpen.value = false
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  document.addEventListener('click', closeDropdowns)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', closeDropdowns)
})
</script>

<template>
  <header
    id="app-header"
    class="header"
    :class="{ 'header--scrolled': scrolled }"
  >
    <div class="header__inner">
      <!-- Logo -->
      <RouterLink to="/" class="header__logo" id="header-logo">
        <div class="header__logo-mark">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.9"/>
            <rect x="16" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
            <rect x="2" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
            <rect x="16" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.25"/>
          </svg>
        </div>
        <span class="header__logo-text">AI Scraper</span>
      </RouterLink>

      <!-- Desktop nav -->
      <nav class="header__nav" id="header-nav">
        <RouterLink to="/about" class="header__link">About</RouterLink>
        <RouterLink to="/pricing" class="header__link">Pricing</RouterLink>
        <RouterLink to="/features" class="header__link">Features</RouterLink>

        <!-- Company dropdown -->
        <div class="header__dropdown" @click.stop>
          <button
            class="header__link header__link--dropdown"
            @click="companyOpen = !companyOpen"
            id="company-dropdown-trigger"
          >
            Company
            <svg class="header__chevron" :class="{ 'header__chevron--open': companyOpen }" width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <Transition name="dropdown">
            <div v-if="companyOpen" class="header__dropdown-menu" id="company-dropdown-menu">
              <RouterLink to="/team" class="header__dropdown-item">
                <span class="header__dropdown-icon">👥</span>
                <div>
                  <div class="header__dropdown-title">Team</div>
                  <div class="header__dropdown-desc">Meet the people behind AI Scraper</div>
                </div>
              </RouterLink>
              <RouterLink to="/careers" class="header__dropdown-item">
                <span class="header__dropdown-icon">🚀</span>
                <div>
                  <div class="header__dropdown-title">Careers</div>
                  <div class="header__dropdown-desc">Join our growing team</div>
                </div>
              </RouterLink>
              <RouterLink to="/contact" class="header__dropdown-item">
                <span class="header__dropdown-icon">✉️</span>
                <div>
                  <div class="header__dropdown-title">Contact</div>
                  <div class="header__dropdown-desc">Get in touch with sales</div>
                </div>
              </RouterLink>
            </div>
          </Transition>
        </div>
      </nav>

      <!-- Actions -->
      <div class="header__actions">
        <!-- Theme toggle -->
        <button
          class="header__theme-toggle"
          @click="toggleTheme"
          id="theme-toggle"
          :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <!-- Sun -->
          <svg v-if="theme === 'dark'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
          <!-- Moon -->
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>

        <RouterLink to="/login" class="header__login" id="header-login">
          Log In
        </RouterLink>

        <!-- Mobile menu toggle -->
        <button class="header__mobile-toggle" @click="mobileOpen = !mobileOpen" id="mobile-menu-toggle">
          <svg v-if="!mobileOpen" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>

    <!-- Mobile menu -->
    <Transition name="mobile-menu">
      <div v-if="mobileOpen" class="header__mobile-menu" id="mobile-menu">
        <RouterLink to="/about" class="header__mobile-link" @click="mobileOpen = false">About</RouterLink>
        <RouterLink to="/pricing" class="header__mobile-link" @click="mobileOpen = false">Pricing</RouterLink>
        <RouterLink to="/features" class="header__mobile-link" @click="mobileOpen = false">Features</RouterLink>
        <div class="header__mobile-divider"></div>
        <RouterLink to="/team" class="header__mobile-link" @click="mobileOpen = false">Team</RouterLink>
        <RouterLink to="/careers" class="header__mobile-link" @click="mobileOpen = false">Careers</RouterLink>
        <RouterLink to="/contact" class="header__mobile-link" @click="mobileOpen = false">Contact</RouterLink>
        <div class="header__mobile-divider"></div>
        <RouterLink to="/login" class="header__mobile-cta" @click="mobileOpen = false">Log In</RouterLink>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 0 2rem;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  background: transparent;
}

.header--scrolled {
  /* background: rgba(253, 253, 253, 0.85); */
  backdrop-filter: blur(16px) saturate(1.4);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

:global(.dark) .header--scrolled {
  background: rgba(15, 23, 42, 0.88);
  border-bottom-color: var(--color-border);
}

.header__inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
}

/* --- Logo --- */
.header__logo {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
  color: var(--color-text);
}

.header__logo-mark {
  display: flex;
  transition: transform 0.3s ease;
}

.header__logo:hover .header__logo-mark {
  transform: rotate(5deg) scale(1.05);
}

.header__logo-text {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.03em;
}

/* --- Nav --- */
.header__nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.header__link {
  padding: 0.5rem 0.85rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.header__link:hover {
  color: var(--color-text);
  background: var(--color-primary-light);
}

.header__link--dropdown {
  cursor: pointer;
  background: none;
  border: none;
  font-family: inherit;
}

.header__chevron {
  transition: transform 0.2s ease;
}

.header__chevron--open {
  transform: rotate(180deg);
}

/* --- Dropdown --- */
.header__dropdown {
  position: relative;
}

.header__dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: 0.5rem;
  z-index: 110;
}

.header__dropdown-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--color-text);
  transition: background 0.15s ease;
}

.header__dropdown-item:hover {
  background: var(--color-primary-light);
}

.header__dropdown-icon {
  font-size: 1.15rem;
  line-height: 1.4;
}

.header__dropdown-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.header__dropdown-desc {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}

/* --- Actions --- */
.header__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header__theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.header__theme-toggle:hover {
  color: var(--color-text);
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.header__login {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff;
  background: var(--color-primary);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.25);
}

.header__login:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
  transform: translateY(-1px);
}

/* --- Mobile --- */
.header__mobile-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  color: var(--color-text);
  cursor: pointer;
}

.header__mobile-menu {
  display: none;
  flex-direction: column;
  padding: 1rem 0 1.5rem;
  border-top: 1px solid var(--color-border);
}

.header__mobile-link {
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.header__mobile-link:hover {
  color: var(--color-text);
  background: var(--color-primary-light);
}

.header__mobile-divider {
  height: 1px;
  background: var(--color-border);
  margin: 0.5rem 1rem;
}

.header__mobile-cta {
  margin: 0.5rem 1rem 0;
  padding: 0.7rem 1.25rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.9rem;
  color: #fff;
  background: var(--color-primary);
  border-radius: var(--radius-sm);
  text-decoration: none;
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .header { padding: 0 1rem; }
  .header__nav { display: none; }
  .header__login { display: none; }
  .header__mobile-toggle { display: flex; }
  .header__mobile-menu { display: flex; }
}

/* --- Transitions --- */
.dropdown-enter-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-leave-active {
  transition: all 0.15s ease;
}
.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

.mobile-menu-enter-active {
  transition: all 0.25s ease;
}
.mobile-menu-leave-active {
  transition: all 0.2s ease;
}
.mobile-menu-enter-from, .mobile-menu-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
