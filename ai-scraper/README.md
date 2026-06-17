# AI Scraper Extractor - Backend (`ai-scraper`)

This directory contains the backend portion of the AI Scraper Extractor application. It is built with **FastAPI** to provide a robust RESTful API, **PostgreSQL/SQLAlchemy** for data persistence, and leverages advanced tools like **Crawl4AI**, **Playwright**, and LLMs (via **Gemini**, **Groq**, or **Ollama**) for web scraping and data extraction.

## Features

- **FastAPI-driven Web API**: High-performance asynchronous endpoints for batch creation, file uploading, and status querying.
- **Advanced Web Scraping**: Utilizes `crawl4ai` and Playwright to navigate complex websites, bypass basic protections, and extract meaningful content.
- **AI-Powered Data Extraction**: Integration with major LLM providers (Google Gemini, Groq/LLaMA3) or local models (Ollama) to structure unstructured website data into business profiles and make automated accept/reject decisions.
- **Background Processing**: Heavy tasks like scraping and AI analysis are processed asynchronously.
- **Database Driven**: Uses PostgreSQL via SQLAlchemy 2.0 (asyncpg) to persist batches, parsed companies, and extracted metadata securely.
- **Excel/Data Pipeline**: Reads directly from Excel (`.xlsx`), parses columns, maps data dynamically, and can output structured JSON or summarize findings.

## Directory Structure

```text
ai-scraper/
├── app/                  # FastAPI Application Core
│   ├── routers/          # API endpoint definitions (batches, companies)
│   ├── workers/          # Background tasks for scraping and AI analysis
│   ├── config.py         # Pydantic-based environment settings
│   ├── database.py       # SQLAlchemy engine & async session setup
│   ├── main.py           # FastAPI entrypoint, lifespan, and middlewares
│   ├── models.py         # SQLAlchemy ORM models (DB Tables)
│   └── schemas.py        # Pydantic models for request/response validation
├── pipeline/             # Business Logic & Processing Pipeline
│   ├── criteria.py       # Configurable rules for automated Accept/Reject
│   ├── file_handler.py   # Excel parsing and DataFrame management
│   └── processor.py      # Multi-stage AI execution logic
├── scraper/              # Core Scraping & AI Abstraction
│   ├── ai/               # Factory pattern for AI Providers (Base, Gemini, Groq, Ollama)
│   ├── cleaner.py        # HTML content cleaning/normalization
│   ├── core.py           # Playwright/crawl4ai integration
│   └── discovery.py      # Finding about/contact pages automatically
├── output/               # Directory for generated JSON profiles & result Excel files
├── uploads/              # Temporary storage for uploaded Batch Excel files
├── main.py               # (Legacy/CLI) Standalone script to process without API
└── test_endpoints.py     # Pytest test suite for API verification
```

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL Server
- Valid API keys for Google Gemini or Groq (optional if exclusively using Ollama locally)

### Setup & Installation

1. **Navigate to the directory**:
   ```bash
   cd ai-scraper
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright Browsers** (Required for the `crawl4ai` scraper):
   ```bash
   playwright install
   ```

5. **Configure Environment Variables**:
   Create a `.env` file in the root of the `ai-scraper` directory:
   ```env
   # AI Providers
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   DEFAULT_AI_PROVIDER=gemini  # Options: gemini | groq | ollama

   # Database settings
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_scraper

   # App settings
   ENVIRONMENT=development
   DEBUG=True
   ```
   *Make sure your local PostgreSQL server is running and a database named `ai_scraper` exists (or match the DB name in your connection string).*

## Running the Application

### 1. Web API Mode (Recommended)
This starts the FastAPI server which communicates with the frontend Vue application.

```bash
uvicorn app.main:app --reload
```
- **API Base URL**: `http://localhost:8000/api`
- **Interactive Docs (Swagger UI)**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

### 2. CLI Orchestrator Mode (Standalone)
If you wish to test the pipeline without the database or API overhead, you can use the standalone script.
Ensure you have a `companies.xlsx` file inside the `ai-scraper` folder.

```bash
python main.py
```
Results will be output directly to the console and saved to the `output/` directory.

## Testing

To run the API tests using `pytest` and HTTPX:

```bash
pytest test_endpoints.py -v
```

## Core Design Principles

- **Asynchronous I/O**: Heavy reliance on Python's `async/await` pattern (using `asyncpg` for db, async playwright for scraping) to ensure the FastAPI app does not block while waiting for LLM or scraping responses.
- **Factory Pattern**: The `scraper/ai` module utilizes a factory pattern to seamlessly switch between AI providers (Gemini, Groq, Ollama) without changing core processing logic.
- **Pydantic Validation**: Strict type enforcement using Pydantic in both FastAPI schemas (`schemas.py`) and application settings (`config.py`).
