# AI Scraper Extractor Project - GEMINI Context

This document provides architectural context, development guidelines, and operational procedures for the AI Scraper Extractor Project.

## Project Overview

The AI Scraper Extractor is a sophisticated company data analysis pipeline. It processes company information (typically from Excel), scrapes their websites using advanced tools, and employs AI (Gemini, Groq, or Ollama) to extract structured business profiles and make automated accept/reject decisions based on configurable criteria.

### Key Technologies
- **Backend:** FastAPI (Python 3.10+)
- **Scraping:** [crawl4ai](https://github.com/unclecode/crawl4ai), Playwright, BeautifulSoup4
- **AI Integration:** Google Gemini, Groq (LLaMA 3), Ollama (Local)
- **Database:** PostgreSQL with SQLAlchemy (asyncpg) and Alembic for migrations
- **Data Handling:** Pandas, OpenPyXL (Excel integration)
- **Environment Management:** `python-dotenv`, `pydantic-settings`

---

## Architecture

The project consists of two primary interaction modes:

1.  **CLI Orchestrator (`ai-scraper/main.py`):** A standalone script for batch processing Excel files directly.
2.  **Web API (`ai-scraper/app/main.py`):** A FastAPI-based REST API designed for integration with a frontend (Vue.js) and managing data through a database.

### Core Modules (in `ai-scraper/`)
- `scraper/`: Contains the core scraping logic (`core.py`), page discovery (`discovery.py`), and AI analyzer factory (`ai/`).
- `pipeline/`: Manages the business logic for data processing, including `criteria.py` for accept/reject rules and `processor.py` for the two-stage AI analysis.
- `app/`: The FastAPI application structure including routers, models, schemas, and background workers.

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (if using the Web API)
- API Keys for Gemini or Groq (optional if using local Ollama)

### Installation
```bash
# Navigate to the project directory
cd ai-scraper

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required by crawl4ai/playwright)
playwright install
```

### Configuration
Create a `.env` file in the `ai-scraper/` directory:
```env
# AI Providers
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
DEFAULT_AI_PROVIDER=gemini  # gemini | groq | ollama

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_scraper

# App Settings
ENVIRONMENT=development
DEBUG=True
```

---

## Commands

### Running the Web API
```bash
cd ai-scraper
uvicorn app.main:app --reload
```
- **API Docs:** http://localhost:8000/api/docs

### Running the CLI Orchestrator
```bash
cd ai-scraper
python main.py
```
*Note: Ensure `companies.xlsx` is present in the `ai-scraper/` directory.*

### Running Tests
```bash
cd ai-scraper
pytest test_endpoints.py
```

---

## Development Conventions

- **Type Hinting:** Strictly use Python type hints for all function signatures and class members.
- **Asynchronous Programming:** Prefer `async/await` for all I/O bound operations (scraping, DB queries, AI requests).
- **Configuration:** Always use `app/config.py` (Pydantic Settings) for managing environment variables.
- **Error Handling:** Use custom exception classes and ensure the pipeline can recover from individual company processing failures without crashing.
- **Data Models:** Use Pydantic schemas (`app/schemas.py`) for API request/response validation and SQLAlchemy models (`app/models.py`) for DB persistence.

---

## Project Structure Highlights
- `ai-scraper/output/`: Where JSON results and summary Excel files are saved.
- `ai-scraper/uploads/`: Temporary storage for uploaded Excel files.
- `ai-scraper/scraper/ai/`: Modular AI implementations (factory pattern).
- `ai-scraper/app/workers/`: Logic for handling long-running scraping and analysis tasks.
