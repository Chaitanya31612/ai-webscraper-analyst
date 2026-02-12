"""
Analyze Worker — Background task that processes scraped content with AI.

Runs independently from scrape_worker. Both watch the DB:
  - scrape_worker  → picks status=PENDING  → sets status=SCRAPED
  - analyze_worker → picks status=SCRAPED  → sets status=COMPLETE

Features:
  - Rate Limiting: Respects API limits (e.g. Gemini 10 RPM)
  - AI Factory: Auto-selects best provider (Gemini > Groq > Ollama)
  - Pipeline Reuse: Uses pipeline.processor for logic

Flow:
  1. Poll DB for 'scraped' companies
  2. RateLimiter.acquire()
  3. Call pipeline.processor.analyze_company()
  4. Save result (profile, decision, reasoning) to DB
  5. Update company status to 'complete'
  6. Update batch progress
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models import Company, CompanyStatus
from app.workers import RateLimiter, update_company_status, update_batch_progress

# ---------------------------------------------------------------
# Import pipeline modules (pipeline/ sits at root)
# ---------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scraper.ai.factory import AIAnalyzerFactory, AIProvider
from pipeline.processor import analyze_company
from pipeline.criteria import AcceptRejectCriteria

logger = logging.getLogger(__name__)


# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

async def run_analyze_worker(batch_id):
    """
    Analyze all scraped companies in a batch using AI.

    Called from the confirm endpoint:
        background_tasks.add_task(run_analyze_worker, batch_id)

    The loop:
      1. Initialize AI Analyzer & Rate Limiter
      2. Query for 'scraped' companies
      3. Process strictly sequentially (to respect rate limits)
      4. Update DB
      5. Repeat untill all are analyzed
    """
    logger.info(f"Analyze worker started for batch {batch_id}")

    # ---------------------------------------------------------------
    # Setup AI & Rate Limiter
    # ---------------------------------------------------------------
    try:
        # Auto-selects best provider based on env vars
        # analyzer = AIAnalyzerFactory.create_default()
        analyzer = AIAnalyzerFactory.create(AIProvider.GROQ)
        logger.info(f"Using AI Provider: {analyzer.provider.value} ({analyzer.model_name})")
    except Exception as e:
        logger.error(f"Failed to initialize AI: {e}")
        return

    # Create rate limiter based on config settings
    # Default: 10 RPM (Gemini free tier)
    limiter = RateLimiter(
        max_requests=settings.AI_REQUESTS_PER_MINUTE,
        window_seconds=60
    )

    # Use default criteria for now (can be customized per batch later)
    criteria = AcceptRejectCriteria()

    while True:
        # ---------------------------------------------------------------
        # Step 1: Get next batch of 'scraped' companies
        # ---------------------------------------------------------------
        async with async_session_factory() as db:
            stmt = (
                select(Company)
                .where(
                    Company.batch_id == batch_id,
                    Company.status == CompanyStatus.SCRAPED,
                )
                .limit(5)  # Process in small chunks
            )
            result = await db.execute(stmt)
            companies = result.scalars().all()

        if not companies:
            # Check if scrape worker is still running?
            # For now, we just exit if no 'scraped' found.
            # In a real queue system, we'd wait for a "batch complete" signal.
            # Since we launch this task ONCE, we assume scraping might be faster
            # or already done. If scraping is slower, this might exit early.

            # IMPROVEMENT: Check if any are still 'pending' or 'scraping'.
            # If yes, sleep and retry. If no, exit.
            async with async_session_factory() as db:
                stmt = select(Company).where(
                    Company.batch_id == batch_id,
                    Company.status.in_([CompanyStatus.PENDING, CompanyStatus.SCRAPING])
                )
                result = await db.execute(stmt)
                still_scraping = result.scalars().first()

            if still_scraping:
                logger.debug("Companies still scraping. Analyze worker sleeping...")
                await asyncio.sleep(5)
                continue
            else:
                logger.info(f"Analyze worker finished for batch {batch_id}")
                break

        # ---------------------------------------------------------------
        # Step 2: Analyze each company
        # ---------------------------------------------------------------
        for company in companies:
            await analyze_single_company(
                company.id,
                company.scraped_markdown,
                company.batch_id,
                analyzer,
                limiter,
                criteria
            )

    logger.info(f"Analyze worker exiting for batch {batch_id}")


# ====================================================================
# SINGLE COMPANY ANALYSIS
# ====================================================================

async def analyze_single_company(
    company_id: int,
    markdown: str,
    batch_id,
    analyzer,
    limiter: RateLimiter,
    criteria: AcceptRejectCriteria
):
    """
    Run AI analysis on a single company.

    Steps:
      1. Wait for rate limiter
      2. Mark as 'analyzing'
      3. Call pipeline.processor.analyze_company()
      4. Save results to DB
    """
    logger.info(f"Analyzing company {company_id}...")

    # Wait for rate limit slot
    await limiter.acquire()

    async with async_session_factory() as db:
        await update_company_status(db, company_id, CompanyStatus.ANALYZING)

    try:
        # ---------------------------------------------------------------
        # Call Pipeline — Heavy lifting happens here
        # Returns: (profile_dict, decision_dict)
        # ---------------------------------------------------------------
        profile, decision_data = await analyze_company(
            content=markdown,
            criteria=criteria,
            ai=analyzer
        )

        status = CompanyStatus.COMPLETE
        error = None

        # Check explicit error from pipeline
        if decision_data.get("decision") == "error":
            status = CompanyStatus.ERROR
            error = decision_data.get("error", "AI Analysis Failed")

        # Prepare update data
        update_data = {
            "profile": profile,  # JSONB field
            "decision": decision_data.get("decision"),
            "confidence": decision_data.get("confidence"),
            "reasoning": decision_data.get("reasoning"),
            "tokens_used": decision_data.get("tokens_used", 0),
            "ai_provider": analyzer.provider.value,
            "ai_model": analyzer.model_name,
        }

        # Save to DB
        async with async_session_factory() as db:
            await update_company_status(
                db, company_id, status,
                error=error,
                **update_data
            )
            await update_batch_progress(db, batch_id)

        logger.info(f"Analyzed company {company_id}: {status} ({decision_data.get('decision')})")

    except Exception as e:
        logger.error(f"Analysis error for company {company_id}: {e}", exc_info=True)
        async with async_session_factory() as db:
            await update_company_status(
                db, company_id, CompanyStatus.ERROR,
                error=f"Worker exception: {str(e)}"
            )
            await update_batch_progress(db, batch_id)
