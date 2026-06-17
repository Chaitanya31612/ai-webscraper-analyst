# AI Scraper Extractor - Frontend (`frontend`)

This directory contains the user interface for the AI Scraper Extractor application. It is a modern, single-page application (SPA) built using **Vue 3**, **Vite**, **TailwindCSS**, and **TypeScript**, designed to orchestrate data scraping batches, map Excel columns, and visualize AI extraction results in real time.

## Tech Stack

- **Framework**: [Vue 3](https://vuejs.org/) (Composition API via `<script setup>`)
- **Build Tool**: [Vite](https://vitejs.dev/) - fast, modern web build tool
- **Styling**: [TailwindCSS v4](https://tailwindcss.com/) - Utility-first CSS framework
- **State Management**: [Pinia](https://pinia.vuejs.org/) - Intuitive, type-safe store for Vue
- **Routing**: [Vue Router 4](https://router.vuejs.org/)
- **API Client**: [Axios](https://axios-http.com/)
- **Icons**: [Lucide Vue Next](https://lucide.dev/)

## Directory Structure

```text
frontend/
├── public/                 # Static assets (favicon, etc.)
├── src/                    # Source code
│   ├── assets/             # Global CSS and structural styles (Tailwind imports)
│   ├── components/         # Reusable Vue components
│   │   ├── common/         # Generic UI elements (Buttons, Layouts, etc.)
│   │   ├── steps/          # Flow specific components (Upload, Column Mapper, Processing)
│   │   └── ...             
│   ├── composables/        # Shared Vue composables (Vue-specific hooks)
│   ├── router/             # Vue Router configuration (`index.ts`)
│   ├── services/           # Axios API integrations (e.g., `batchService.ts`)
│   ├── stores/             # Pinia state stores (e.g., global state management)
│   ├── types/              # TypeScript interface & type definitions
│   ├── views/              # Main page components (e.g., HomeView, BatchResults)
│   ├── App.vue             # Root Vue component
│   └── main.ts             # Application entry point, initializing Vue, Pinia, Router
├── index.html              # Vite entry HTML
├── package.json            # Node dependencies and scripts
├── tailwind.config.ts      # Tailwind configuration (if explicitly defined alongside v4)
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite configuration (plugins, dev server ports, aliases)
```

## Getting Started

### Prerequisites

Ensure you have [Node.js](https://nodejs.org/) installed (version 20+ recommended).

### Installation

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Running for Development

To start the local development server with Hot-Module-Replacement (HMR):

```bash
npm run dev
```

The application will be accessible at `http://localhost:5173` (unless configured otherwise). 
*Note: Make sure your FastAPI backend is running concurrently on port 8000 for full functionality.*

### Build for Production

To compile, type-check, and minify the application for deployment:

```bash
npm run build
```

The optimized build artifacts will be placed in the `dist/` directory, ready to be served by a static file server like Nginx, Apache, or deployed to platforms like Vercel or Netlify.

### Formatting and Linting

- **Run Linter** (ESLint & Oxlint):
  ```bash
  npm run lint
  ```
- **Format Code** (Prettier):
  ```bash
  npm run format
  ```

## IDE Integration Setup

For the best development experience, we recommend using [VS Code](https://code.visualstudio.com/) alongside the **[Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)** extension (formerly Volar). Ensure any older extensions like Vetur are disabled.
