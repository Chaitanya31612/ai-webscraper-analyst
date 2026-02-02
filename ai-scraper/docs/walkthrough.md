# AI Scraper Project Walkthrough

A comprehensive guide to understanding the AI-powered company analysis pipeline.

---

## Project Overview

This application processes company data from Excel files, scrapes company websites, uses AI to extract structured business information, and makes **accept/reject recommendations** based on configurable criteria.

---

## Architecture Flow Diagram

```mermaid
flowchart TB
    subgraph INPUT["📥 Input Layer"]
        EXCEL["Excel File<br/>(companies.xlsx)"]
        CRITERIA["Accept/Reject Criteria<br/>(AcceptRejectCriteria)"]
    end

    subgraph LOADER["📂 File Handler"]
        LOAD["load_companies_from_excel()"]
        EXCEL --> LOAD
        LOAD --> COMPANIES["List of CompanyInput"]
    end

    subgraph MAIN["🔄 Main Processing Loop"]
        LOOP["For each company..."]
        COMPANIES --> LOOP
    end

    subgraph SCRAPER["🔍 Scraper Module"]
        direction TB
        S1["1. Scrape Homepage<br/>(core.py → Scraper)"]
        S2["2. Discover Key Pages<br/>(discovery.py)"]
        S3["3. Scrape About/Products/Contact<br/>pages"]
        S4["4. Combine Markdown Content"]
        S1 --> S2 --> S3 --> S4
    end

    subgraph AI["🤖 AI Analysis (Two-Stage)"]
        direction TB
        AI1["Stage 1: Extract Profile<br/>(business description,<br/>products/services,<br/>functional profile)"]
        AI2["Stage 2: Make Decision<br/>(accept/reject/review<br/>with reasoning)"]
        AI1 --> AI2
    end

    subgraph OUTPUT["📤 Output Layer"]
        JSON["Individual JSON files<br/>(per company)"]
        SUMMARY["Summary Excel<br/>(results_summary.xlsx)"]
        CONSOLE["Console Summary"]
    end

    LOOP --> SCRAPER
    SCRAPER --> AI
    CRITERIA --> AI
    AI --> OUTPUT

    style INPUT fill:#e1f5fe
    style SCRAPER fill:#fff3e0
    style AI fill:#f3e5f5
    style OUTPUT fill:#e8f5e9
```

---

## Module Breakdown

### 1. Entry Point: [main.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/main.py)

The orchestrator that ties everything together:

| Step | Action | Code Location |
|------|--------|---------------|
| 1 | Load companies from Excel | `load_companies_from_excel()` |
| 2 | Initialize Scraper & AI | `Scraper()`, `AIAnalyzer()` |
| 3 | Define Accept/Reject criteria | `AcceptRejectCriteria()` |
| 4 | Process each company | `process_company()` loop |
| 5 | Save results | `save_result_json()`, `export_summary_excel()` |

---

### 2. Data Models: [models.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/models.py)

```mermaid
classDiagram
    class CompanyInput {
        +company_name: str
        +website: str
        +country: str
        +industry: str
        +bvd_id: str
        +metadata: dict
    }

    class CompanyProfile {
        +business_description: str
        +products_services: List
        +functional_profile: str
        +target_market: str
        +company_size: str
        +geographic_presence: List
        +technology_stack: List
        +certifications: List
    }

    class DecisionResult {
        +decision: Decision
        +confidence: float
        +reasoning: str
        +matching_criteria: List
        +rejection_reasons: List
    }

    class ProcessedCompany {
        +input: CompanyInput
        +profile: CompanyProfile
        +decision: DecisionResult
        +raw_markdown: str
        +pages_crawled: List
        +processed_at: datetime
        +error: str
    }

    ProcessedCompany --> CompanyInput
    ProcessedCompany --> CompanyProfile
    ProcessedCompany --> DecisionResult
```

---

### 3. Scraper Module: [scraper/](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/scraper)

| File | Purpose |
|------|---------|
| [core.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/scraper/core.py) | `Scraper` class - uses **crawl4ai** to fetch webpage content as markdown |
| [discovery.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/scraper/discovery.py) | Finds key pages (about, products, contact) from homepage links |
| [ai.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/scraper/ai.py) | `AIAnalyzer` class - uses **Groq API** (LLaMA 3) for AI analysis |

#### How Scraping Works:
```
Homepage → Extract Links → Find /about, /products, /contact → Scrape Each → Combine as Markdown
```

---

### 4. Pipeline Module: [pipeline/](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/pipeline)

| File | Purpose |
|------|---------|
| [criteria.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/pipeline/criteria.py) | `AcceptRejectCriteria` - defines what makes a company acceptable/rejectable |
| [processor.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/pipeline/processor.py) | Two-stage AI analysis (extract profile → make decision) |
| [file_handler.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/pipeline/file_handler.py) | Excel loading, JSON saving, summary export |

---

## Accept/Reject Strategy

The criteria is configurable in [criteria.py](file:///home/chaitanya/Desktop/Development/learning/python-learnings/AIScraperExtractorProject/ai-scraper/pipeline/criteria.py):

| Type | Examples |
|------|----------|
| ✅ **Accept Industries** | Technology, Healthcare, Financial Services, Software |
| ✅ **Accept Keywords** | SaaS, platform, cloud, API, analytics |
| ❌ **Reject Keywords** | gambling, casino, tobacco, weapons |
| ❌ **Reject Industries** | Gambling, Tobacco, Adult Entertainment |

> [!NOTE]
> **Reject criteria override accept criteria** - if a company matches both, it will be rejected.

---

## What's Currently MISSING

Based on your use case, here are gaps in the current implementation:

| Feature | Status | What's Needed |
|---------|--------|---------------|
| **Database Storage** | ❌ Missing | No DB integration - results only saved as JSON/Excel files |
| **Web UI for Excel Upload** | ❌ Missing | Currently runs via command line only |
| **Criteria Configuration UI** | ❌ Missing | Accept/reject rules are hardcoded |
| **Comparison Study Dashboard** | ❌ Missing | No UI to compare companies side-by-side |
| **Real-time Progress Tracking** | ❌ Missing | Only console output during processing |
| **Error Recovery / Resume** | ⚠️ Partial | No way to resume if interrupted mid-batch |

---

## Recommended Next Steps

To complete your use case, consider adding:

1. **Database Layer** - SQLite or PostgreSQL to store:
   - Uploaded Excel data (`CompanyInput`)
   - Extracted profiles (`CompanyProfile`)
   - Decisions with reasoning (`DecisionResult`)

2. **Web Application** (Flask/FastAPI) with:
   - Excel file upload endpoint
   - Criteria configuration page
   - Progress tracking during batch processing
   - Results dashboard with filtering

3. **Comparison View** - Side-by-side company profiles for comparable study

4. **Batch Processing Queue** - Handle large files asynchronously with progress updates

---

## How to Run Currently

```bash
# 1. Install dependencies
cd ai-scraper
pip install -r requirements.txt

# 2. Set up GROQ API key
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Place your Excel file as companies.xlsx

# 4. Run
python main.py
```

Results will be saved to the `output/` folder.
