# AI Scraper Extractor Project

## Brief Introduction

Welcome to the AI Scraper Extractor! This project is a robust, full-stack application engineered to automate the tedious process of B2B company research, data extraction, and lead qualification. 

**What this project does:**
1. **Data Ingestion**: Users can upload Excel (`.xlsx`) files containing lists of companies and their URLs via a modern Vue 3 frontend interface.
2. **Intelligent Scraping**: The FastAPI backend utilizes advanced browser automation (Playwright and Crawl4AI) to navigate these company websites, automatically discovering key pages like "About Us" and "Contact" while bypassing basic bot protections.
3. **AI-Powered Analysis**: The scraped raw HTML/text is fed into cutting-edge Large Language Models (LLMs). The project supports multiple providers out of the box, including Google Gemini, Groq (LLaMA 3), and local models via Ollama.
4. **Structured Data Extraction**: The AI processes the unstructured text to generate a highly structured "Business Profile", identifying the company's core services, target audience, technical stack, and more.
5. **Automated Qualification**: Based on customizable rules (e.g., "Company must be B2B" or "Company must offer SaaS solutions"), the AI pipeline makes intelligent "Accept" or "Reject" decisions for each lead.
6. **Results & Export**: The parsed data is persisted in a PostgreSQL database and presented in real-time back to the user on the frontend, where it can be reviewed and exported for use in CRM systems or further analysis.

Whether you are a sales professional building targeted lead lists, a researcher analyzing market competitors, or a developer exploring AI-agentic workflows, this pipeline handles the heavy lifting of unstructured data processing end-to-end.

## Demo



https://github.com/user-attachments/assets/370ce3f4-dd10-4fab-b12e-9dbb2ab26fe1



## Project Structure

This repository is organized into two main parts: the **Frontend** and the **Backend** (`ai-scraper`).

```text
AIScraperExtractorProject/
├── ai-scraper/      # Backend (FastAPI, Crawl4AI, Playwright, SQLAlchemy, AI integration)
├── frontend/        # Frontend (Vue 3, Vite, TailwindCSS, Pinia)
├── GEMINI.md        # AI Context & Architectural Guidelines
├── development.md   # General development notes and architecture roadmap
└── README.md        # This file
```

## Documentation

For detailed information about each component of the stack, including comprehensive setup instructions and architecture details, please refer to their respective README files:

- 🎨 **[Frontend Documentation](./frontend/README.md)**: Details about the Vue 3 application, UI components, state management, and running the dev server.
- ⚙️ **[Backend Documentation](./ai-scraper/README.md)**: Details about the FastAPI application, database setup, scraping pipeline, and AI integrations.

## Quick Start Guide

To get the entire application running locally, you'll need to start both the backend server and the frontend development server.

### Prerequisites
- **Python 3.10+**
- **Node.js 20+**
- **PostgreSQL** (running locally or remotely)
- API Keys for Google Gemini or Groq (optional if using local Ollama)

### 1. Start the Backend (`ai-scraper`)

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd ai-scraper
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Playwright browsers (required for scraping):
   ```bash
   playwright install
   ```
5. Configure your environment variables. Copy the example `.env` file (if available) or create a new `.env` file in the `ai-scraper` directory with your database URL and API keys (refer to `ai-scraper/README.md` for details).
6. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend API will be available at `http://localhost:8000`.

### 2. Start the Frontend (`frontend`)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend application will be available at `http://localhost:5173` (or the port specified in the console).

---

By running both the backend and frontend simultaneously, you will be able to access the UI, upload spreadsheets, map columns, and watch the background AI scraping and analysis pipeline run in real-time.
