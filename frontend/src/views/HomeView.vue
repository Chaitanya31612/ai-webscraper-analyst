<script setup lang="ts">
/**
 * HomeView — Option 1: "Luminous Executive"
 *
 * A premium, light-first landing page with:
 * - Hero: Bold typography + dual CTAs + floating dashboard preview
 * - Features grid with metric cards
 * - Social proof strip
 * - Footer
 *
 * Design: Clean white space, indigo accent, dot-grid texture, editorial Swiss layout
 */
import { ref, onMounted } from 'vue'
import AppHeader from './AppHeader.vue'

const loaded = ref(false)
onMounted(() => {
  setTimeout(() => { loaded.value = true }, 100)
})
</script>

<template>
  <div class="page">
    <AppHeader />

    <!-- ============================== HERO ============================== -->
    <section id="hero" class="hero noise-overlay">
      <!-- Dot grid background -->
      <div class="hero__grid dot-grid" aria-hidden="true"></div>
      <!-- Radial glow -->
      <div class="hero__glow" aria-hidden="true"></div>

      <div class="hero__container" :class="{ 'hero__container--visible': loaded }">
        <!-- Badge -->
        <div class="hero__badge fade-in-up">
          <span class="hero__badge-dot"></span>
          <span>Now analyzing 10,000+ companies</span>
        </div>

        <!-- Heading -->
        <h1 class="hero__title fade-in-up fade-in-up-delay-1">
          Intelligence<br>
          <span class="hero__title-accent">at Scale</span>
        </h1>

        <!-- Subtext -->
        <p class="hero__subtitle fade-in-up fade-in-up-delay-2">
          Transform raw web data into surgical business intelligence.<br class="hero__br-desktop">
          Dual-stage AI analysis delivers accept/reject decisions in seconds, not weeks.
        </p>

        <!-- CTAs -->
        <div class="hero__ctas fade-in-up fade-in-up-delay-3">
          <RouterLink to="/register" class="hero__cta hero__cta--primary" id="hero-cta-primary">
            Get Started
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10m0 0L9 4m4 4L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </RouterLink>
          <a href="#features" class="hero__cta hero__cta--secondary" id="hero-cta-secondary">
            See How It Works
          </a>
        </div>

        <!-- Dashboard Preview Card -->
        <div class="hero__preview fade-in-up fade-in-up-delay-4">
          <div class="hero__preview-card glass-card">
            <!-- Preview header -->
            <div class="preview__header">
              <div class="preview__dots">
                <span></span><span></span><span></span>
              </div>
              <span class="preview__title-bar">company_analysis.json</span>
              <div class="preview__status preview__status--live">
                <span class="preview__status-dot"></span>
                Live
              </div>
            </div>

            <!-- Preview content -->
            <div class="preview__body">
              <!-- Company row 1 -->
              <div class="preview__row">
                <div class="preview__company">
                  <div class="preview__avatar preview__avatar--1">T</div>
                  <div>
                    <div class="preview__name">TechVentures Inc.</div>
                    <div class="preview__url">techventures.io</div>
                  </div>
                </div>
                <div class="preview__metrics">
                  <div class="preview__metric">
                    <span class="preview__metric-label">Confidence</span>
                    <span class="preview__metric-value">94%</span>
                  </div>
                  <span class="preview__badge preview__badge--accept">✓ Accept</span>
                </div>
              </div>

              <!-- Company row 2 -->
              <div class="preview__row">
                <div class="preview__company">
                  <div class="preview__avatar preview__avatar--2">G</div>
                  <div>
                    <div class="preview__name">GrowthMetrics</div>
                    <div class="preview__url">growthmetrics.com</div>
                  </div>
                </div>
                <div class="preview__metrics">
                  <div class="preview__metric">
                    <span class="preview__metric-label">Confidence</span>
                    <span class="preview__metric-value">71%</span>
                  </div>
                  <span class="preview__badge preview__badge--review">● Review</span>
                </div>
              </div>

              <!-- Company row 3 -->
              <div class="preview__row">
                <div class="preview__company">
                  <div class="preview__avatar preview__avatar--3">N</div>
                  <div>
                    <div class="preview__name">NovaAI Solutions</div>
                    <div class="preview__url">novaai.tech</div>
                  </div>
                </div>
                <div class="preview__metrics">
                  <div class="preview__metric">
                    <span class="preview__metric-label">Confidence</span>
                    <span class="preview__metric-value">97%</span>
                  </div>
                  <span class="preview__badge preview__badge--accept">✓ Accept</span>
                </div>
              </div>

              <!-- Shimmer row -->
              <div class="preview__row preview__row--loading">
                <div class="preview__shimmer shimmer"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ========================== FEATURES ========================== -->
    <section id="features" class="features">
      <div class="features__container">
        <div class="features__header fade-in-up">
          <span class="features__label">How It Works</span>
          <h2 class="features__title">Three stages.<br>Zero guesswork.</h2>
          <p class="features__subtitle">
            From raw Excel uploads to structured intelligence, every step is automated and auditable.
          </p>
        </div>

        <div class="features__grid">
          <!-- Card 1 -->
          <div class="feature-card glass-card noise-overlay fade-in-up fade-in-up-delay-1">
            <div class="feature-card__number">01</div>
            <div class="feature-card__icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <h3 class="feature-card__title">Upload & Discover</h3>
            <p class="feature-card__desc">
              Drop an Excel file with company names. Our crawler discovers every relevant page, subpage, and resource automatically.
            </p>
            <div class="feature-card__stat">
              <span class="feature-card__stat-value">200+</span>
              <span class="feature-card__stat-label">pages/min crawled</span>
            </div>
          </div>

          <!-- Card 2 -->
          <div class="feature-card glass-card noise-overlay fade-in-up fade-in-up-delay-2">
            <div class="feature-card__number">02</div>
            <div class="feature-card__icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h3 class="feature-card__title">Dual-Stage AI Analysis</h3>
            <p class="feature-card__desc">
              Stage 1 extracts structured profiles. Stage 2 cross-references your benchmarking criteria to deliver precise evaluations.
            </p>
            <div class="feature-card__stat">
              <span class="feature-card__stat-value">2</span>
              <span class="feature-card__stat-label">AI passes per company</span>
            </div>
          </div>

          <!-- Card 3 -->
          <div class="feature-card glass-card noise-overlay fade-in-up fade-in-up-delay-3">
            <div class="feature-card__number">03</div>
            <div class="feature-card__icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <h3 class="feature-card__title">Accept / Reject / Review</h3>
            <p class="feature-card__desc">
              Every company receives a confidence-scored decision. Export the results, drill into profiles, or override manually.
            </p>
            <div class="feature-card__stat">
              <span class="feature-card__stat-value">94%</span>
              <span class="feature-card__stat-label">avg. accuracy</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ========================= METRICS STRIP ========================= -->
    <section class="metrics-strip noise-overlay">
      <div class="metrics-strip__inner">
        <div class="metric-item fade-in-up">
          <div class="metric-item__value">10K+</div>
          <div class="metric-item__label">Companies Analyzed</div>
        </div>
        <div class="metric-item fade-in-up fade-in-up-delay-1">
          <div class="metric-item__value">3.2s</div>
          <div class="metric-item__label">Avg. Processing Time</div>
        </div>
        <div class="metric-item fade-in-up fade-in-up-delay-2">
          <div class="metric-item__value">94%</div>
          <div class="metric-item__label">Decision Accuracy</div>
        </div>
        <div class="metric-item fade-in-up fade-in-up-delay-3">
          <div class="metric-item__value">50x</div>
          <div class="metric-item__label">Faster Than Manual</div>
        </div>
      </div>
    </section>

    <!-- ============================== FOOTER ============================== -->
    <footer class="footer">
      <div class="footer__inner">
        <div class="footer__brand">
          <div class="footer__logo">
            <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
              <rect x="2" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.9"/>
              <rect x="16" y="2" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
              <rect x="2" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.5"/>
              <rect x="16" y="16" width="10" height="10" rx="2" fill="var(--color-primary)" opacity="0.25"/>
            </svg>
            <span>AI Scraper</span>
          </div>
          <p class="footer__tagline">
            Automated company intelligence,<br>powered by dual-stage AI.
          </p>
        </div>
        <div class="footer__links">
          <div class="footer__col">
            <h4>Product</h4>
            <RouterLink to="/1/features">Features</RouterLink>
            <RouterLink to="/1/pricing">Pricing</RouterLink>
            <RouterLink to="/1/about">About</RouterLink>
          </div>
          <div class="footer__col">
            <h4>Company</h4>
            <RouterLink to="/1/team">Team</RouterLink>
            <RouterLink to="/1/careers">Careers</RouterLink>
            <RouterLink to="/1/contact">Contact</RouterLink>
          </div>
        </div>
      </div>
      <div class="footer__bottom">
        <span>© 2026 AI Scraper. All rights reserved.</span>
        <span class="footer__bottom-mono">v2.1.0 · built with precision</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text);
}

/* ============================= HERO ============================= */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 6rem 2rem 4rem;
}

.hero__grid {
  position: absolute;
  inset: 0;
  opacity: 0.4;
}

.hero__glow {
  position: absolute;
  top: -10%;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  height: 600px;
  background: radial-gradient(
    ellipse 50% 60% at 50% 30%,
    var(--color-primary-glow) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.hero__container {
  position: relative;
  z-index: 2;
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
  opacity: 0;
  transition: opacity 0.5s ease;
}

.hero__container--visible {
  opacity: 1;
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 1rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border: 1px solid rgba(79, 70, 229, 0.15);
  border-radius: 999px;
  margin-bottom: 2rem;
}

.hero__badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: pulseGlow 2s ease-in-out infinite;
}

@keyframes pulseGlow {
  0%, 100% { opacity: 1; box-shadow: 0 0 4px var(--color-primary); }
  50% { opacity: 0.5; box-shadow: 0 0 12px var(--color-primary); }
}

.hero__title {
  font-size: clamp(2.75rem, 7vw, 5.5rem);
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: -0.04em;
  margin-bottom: 1.5rem;
}

.hero__title-accent {
  background: linear-gradient(135deg, var(--color-primary) 0%, #818cf8 50%, var(--color-primary) 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 4s ease-in-out infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% center; }
  50% { background-position: 100% center; }
}

.hero__subtitle {
  font-size: 1.15rem;
  line-height: 1.7;
  color: var(--color-text-secondary);
  max-width: 600px;
  margin: 0 auto 2.5rem;
}

.hero__br-desktop {
  display: none;
}

@media (min-width: 640px) {
  .hero__br-desktop { display: block; }
}

.hero__ctas {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.hero__cta {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.hero__cta--primary {
  color: #fff;
  background: var(--color-primary);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3),
              0 0 0 1px rgba(79, 70, 229, 0.15);
}

.hero__cta--primary:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35),
              0 0 0 1px rgba(79, 70, 229, 0.2);
  transform: translateY(-2px);
}

.hero__cta--secondary {
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.hero__cta--secondary:hover {
  color: var(--color-text);
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

/* --- Dashboard Preview --- */
.hero__preview {
  margin-top: 4rem;
  perspective: 1200px;
}

.hero__preview-card {
  max-width: 720px;
  margin: 0 auto;
  overflow: hidden;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xl);
  transition: transform 0.4s ease, box-shadow 0.4s ease;
}

.hero__preview-card:hover {
  transform: translateY(-4px) rotateX(1deg);
  box-shadow: var(--shadow-xl), 0 0 60px var(--color-primary-glow);
}

.preview__header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-raised);
}

.preview__dots {
  display: flex;
  gap: 6px;
}

.preview__dots span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-border);
}

.preview__dots span:first-child { background: #f87171; }
.preview__dots span:nth-child(2) { background: #fbbf24; }
.preview__dots span:last-child { background: #34d399; }

.preview__title-bar {
  flex: 1;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--color-text-muted);
  letter-spacing: 0.02em;
}

.preview__status {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.7rem;
  font-weight: 600;
}

.preview__status--live {
  color: var(--color-accent);
}

.preview__status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.preview__body {
  padding: 0.5rem;
}

.preview__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem;
  border-radius: var(--radius-sm);
  transition: background 0.15s ease;
}

.preview__row:hover {
  background: var(--color-primary-light);
}

.preview__row--loading {
  padding: 1rem;
}

.preview__shimmer {
  height: 20px;
  width: 100%;
  border-radius: var(--radius-sm);
}

.preview__company {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.preview__avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.85rem;
  color: #fff;
}

.preview__avatar--1 { background: linear-gradient(135deg, #4f46e5, #818cf8); }
.preview__avatar--2 { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
.preview__avatar--3 { background: linear-gradient(135deg, #059669, #34d399); }

.preview__name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-text);
}

.preview__url {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.preview__metrics {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.preview__metric {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.preview__metric-label {
  font-size: 0.65rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview__metric-value {
  font-family: var(--font-mono);
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--color-text);
}

.preview__badge {
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.preview__badge--accept {
  color: #059669;
  background: rgba(52, 211, 153, 0.12);
  border: 1px solid rgba(52, 211, 153, 0.2);
}

.preview__badge--review {
  color: #d97706;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.2);
}

/* ========================== FEATURES ========================== */
.features {
  padding: 6rem 2rem;
  background: var(--color-bg-alt);
  border-top: 1px solid var(--color-border-subtle);
}

.features__container {
  max-width: 1100px;
  margin: 0 auto;
}

.features__header {
  text-align: center;
  margin-bottom: 4rem;
}

.features__label {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.features__title {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin-bottom: 1rem;
}

.features__subtitle {
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--color-text-secondary);
  max-width: 520px;
  margin: 0 auto;
}

.features__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  padding: 2rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg), 0 0 30px var(--color-primary-glow);
}

.feature-card__number {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-primary);
  opacity: 0.6;
  margin-bottom: 1.25rem;
}

.feature-card__icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  border-radius: var(--radius-md);
  margin-bottom: 1.25rem;
}

.feature-card__title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.feature-card__desc {
  font-size: 0.9rem;
  line-height: 1.65;
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
}

.feature-card__stat {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.feature-card__stat-value {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--color-primary);
}

.feature-card__stat-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

/* ========================= METRICS STRIP ========================= */
.metrics-strip {
  padding: 4rem 2rem;
  background: var(--color-primary);
  color: #fff;
  position: relative;
  overflow: hidden;
}

.metrics-strip__inner {
  position: relative;
  z-index: 2;
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 2rem;
  text-align: center;
}

.metric-item__value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  margin-bottom: 0.25rem;
}

.metric-item__label {
  font-size: 0.85rem;
  opacity: 0.8;
  font-weight: 500;
}

/* ============================= FOOTER ============================= */
.footer {
  padding: 4rem 2rem 2rem;
  background: var(--color-bg-alt);
  border-top: 1px solid var(--color-border);
}

.footer__inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  gap: 3rem;
  flex-wrap: wrap;
  padding-bottom: 3rem;
  border-bottom: 1px solid var(--color-border);
}

.footer__logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-text);
  margin-bottom: 0.75rem;
}

.footer__tagline {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.footer__links {
  display: flex;
  gap: 4rem;
}

.footer__col {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.footer__col h4 {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.footer__col a {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color 0.15s ease;
}

.footer__col a:hover {
  color: var(--color-primary);
}

.footer__bottom {
  max-width: 1100px;
  margin: 1.5rem auto 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.footer__bottom-mono {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.02em;
}

/* ======================== RESPONSIVE ======================== */
@media (max-width: 768px) {
  .hero { padding: 5rem 1.25rem 3rem; }
  .hero__preview-card { max-width: 100%; }
  .preview__metrics { display: none; }
  .features { padding: 4rem 1.25rem; }
  .metrics-strip__inner { grid-template-columns: repeat(2, 1fr); }
  .footer__inner { flex-direction: column; gap: 2rem; }
  .footer__links { gap: 2.5rem; }
  .footer__bottom { flex-direction: column; gap: 0.5rem; text-align: center; }
}
</style>
