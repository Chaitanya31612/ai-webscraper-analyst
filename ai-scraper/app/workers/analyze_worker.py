"""
Analyze Worker — Background task that processes scraped content with AI.

Runs independently from scrape_worker. Both watch the DB:
  - scrape_worker  → picks status=PENDING  → sets status=SCRAPED
  - analyze_worker → picks status=SCRAPED  → sets status=COMPLETE (with profile, no decision yet)

Features:
  - Rate Limiting: Respects API limits (e.g. Gemini 10 RPM)
  - AI Factory: Auto-selects best provider (Gemini > Groq > Ollama)
  - Pipeline Reuse: Uses pipeline.processor for logic

Flow (Stage 1 — Profile Extraction only):
  1. Poll DB for 'scraped' companies
  2. RateLimiter.acquire()
  3. Call pipeline.processor.extract_profile()
  4. Save result (profile) to DB
  5. Update company status to 'complete'
  6. Update batch progress

Note: Stage 2 (accept/reject decision) runs separately in the Accept/Reject step.
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
from pipeline.processor import extract_profile

logger = logging.getLogger(__name__)


# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

async def run_analyze_worker(batch_id):
    """
    Extract profiles for all scraped companies in a batch using AI.

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
            # Check if scrape worker is still running
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
        # Step 2: Extract profile for each company (Stage 1 only)
        # ---------------------------------------------------------------
        for company in companies:
            await analyze_single_company(
                company.id,
                company.scraped_markdown,
                company.batch_id,
                analyzer,
                limiter,
            )

    logger.info(f"Analyze worker exiting for batch {batch_id}")


# ====================================================================
# SINGLE COMPANY ANALYSIS (Stage 1 — Profile Extraction)
# ====================================================================

async def analyze_single_company(
    company_id: int,
    markdown: str,
    batch_id,
    analyzer,
    limiter: RateLimiter,
):
    """
    Run Stage 1 AI analysis (profile extraction) on a single company.

    Steps:
      1. Wait for rate limiter
      2. Mark as 'analyzing'
      3. Call pipeline.processor.extract_profile()
      4. Save profile to DB, set status to 'complete'

    Note: decision/confidence/reasoning remain null.
    Stage 2 (accept/reject) runs separately later.
    """
    logger.info(f"Extracting profile for company {company_id}...")

    # Wait for rate limit slot
    await limiter.acquire()

    async with async_session_factory() as db:
        await update_company_status(db, company_id, CompanyStatus.ANALYZING)

    try:
        # ---------------------------------------------------------------
        # Call Pipeline Stage 1 — Profile extraction only
        # Returns: (profile_dict, error_string, tokens_used)
        # ---------------------------------------------------------------
        profile, error, tokens_used = await extract_profile(
            content=markdown,
            ai=analyzer
        )

        if error:
            status = CompanyStatus.ERROR
            async with async_session_factory() as db:
                await update_company_status(
                    db, company_id, status,
                    error=error,
                    ai_provider=analyzer.provider.value,
                    ai_model=analyzer.model_name,
                )
                await update_batch_progress(db, batch_id)
            logger.error(f"Profile extraction failed for company {company_id}: {error}")
            return

        # Save profile to DB — no decision yet (Stage 2 runs later)
        update_data = {
            "profile": profile,  # JSONB field with full extracted profile
            "tokens_used": tokens_used,
            "ai_provider": analyzer.provider.value,
            "ai_model": analyzer.model_name,
            "analyzed_at": datetime.utcnow(),
        }

        async with async_session_factory() as db:
            await update_company_status(
                db, company_id, CompanyStatus.COMPLETE,
                **update_data
            )
            await update_batch_progress(db, batch_id)

        logger.info(f"Profile extracted for company {company_id}: complete")

    except Exception as e:
        logger.error(f"Analysis error for company {company_id}: {e}", exc_info=True)
        async with async_session_factory() as db:
            await update_company_status(
                db, company_id, CompanyStatus.ERROR,
                error=f"Worker exception: {str(e)}"
            )
            await update_batch_progress(db, batch_id)

