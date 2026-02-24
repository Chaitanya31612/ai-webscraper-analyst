"""
Scrape Worker — Background task that scrapes all pending companies in a batch.

Runs independently from analyze_worker. Both watch the DB:
  - scrape_worker  → picks status=PENDING  → sets status=SCRAPED
  - analyze_worker → picks status=SCRAPED  → sets status=COMPLETE

Uses scraper/discovery.scrape_companies_batch() which leverages
crawl4ai's arun_many() for parallel scraping — no sequential one-by-one.

Flow:
  1. Query DB for all pending companies in the batch
  2. Call scrape_companies_batch(all_websites) → parallel scrape
  3. Update each company in DB with results
  4. Update batch progress
"""

import os
import sys
import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models import Company, CompanyStatus
from app.workers import update_company_status, update_batch_progress

# ---------------------------------------------------------------
# Import scraper from sibling folder (scraper/ sits next to app/)
# ---------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scraper.discovery import scrape_companies_batch

logger = logging.getLogger(__name__)


# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

async def run_scrape_worker(batch_id):
    """
    Scrape all pending companies in a batch using parallel batch scraping.

    Called from the confirm endpoint:
        background_tasks.add_task(run_scrape_worker, batch_id)

    Steps:
      1. Fetch all pending companies from DB
      2. Mark them all as 'scraping'
      3. Call scrape_companies_batch() → parallel scrape via arun_many
      4. Update each company with results
      5. Update batch progress

    Args:
        batch_id: UUID of the batch to process
    """
    logger.info(f"Scrape worker started for batch {batch_id}")

    # ---------------------------------------------------------------
    # Step 1: Get all pending companies in one query
    # ---------------------------------------------------------------
    async with async_session_factory() as db:
        stmt = (
            select(Company)
            .where(
                Company.batch_id == batch_id,
                Company.status == CompanyStatus.PENDING,
            )
        )
        result = await db.execute(stmt)
        companies = result.scalars().all()

    if not companies:
        logger.info(f"No pending companies in batch {batch_id}")
        return

    # ---------------------------------------------------------------
    # Step 2: Mark all as 'scraping' so UI shows progress
    # ---------------------------------------------------------------
    company_ids = [c.id for c in companies]
    async with async_session_factory() as db:
        stmt = (
            update(Company)
            .where(Company.id.in_(company_ids))
            .values(status=CompanyStatus.SCRAPING)
        )
        await db.execute(stmt)
        await db.commit()

    # ---------------------------------------------------------------
    # Step 3: Batch scrape all websites in parallel
    #
    # scrape_companies_batch() uses crawl4ai's arun_many():
    #   Phase 1: All homepages scraped concurrently
    #   Phase 2: All discovered key pages scraped concurrently
    #
    # Returns dict: { "https://acme.com": { content, pages_crawled, success, error } }
    # ---------------------------------------------------------------
    websites = [c.website for c in companies]
    website_to_company = {c.website: c for c in companies}

    try:
        scrape_results = await scrape_companies_batch(
            websites=websites,
            max_concurrent=settings.MAX_CONCURRENT_SCRAPES,
            headless=settings.HEADLESS_BROWSER,
            timeout=settings.SCRAPE_TIMEOUT_MS,
        )
    except Exception as e:
        # Batch-level failure (browser crash, etc.)
        logger.error(f"Batch scrape failed: {e}", exc_info=True)
        async with async_session_factory() as db:
            for company in companies:
                await update_company_status(
                    db, company.id, CompanyStatus.ERROR,
                    error=f"Batch scrape failed: {str(e)}"
                )
            await update_batch_progress(db, batch_id)
        return

    # ---------------------------------------------------------------
    # Step 4: Save results to DB per company
    # ---------------------------------------------------------------
    async with async_session_factory() as db:
        for website, data in scrape_results.items():
            company = website_to_company.get(website)
            if not company:
                continue

            if data["success"]:
                await update_company_status(
                    db, company.id, CompanyStatus.SCRAPED,
                    scraped_markdown=data["content"],
                    pages_crawled=data["pages_crawled"],
                    scraped_at=datetime.utcnow(),
                )
                logger.info(
                    f"Scraped {company.company_name}: "
                    f"{len(data['pages_crawled'])} pages, "
                    f"{len(data['content'])} chars"
                )
            else:
                await update_company_status(
                    db, company.id, CompanyStatus.ERROR,
                    error=data.get("error", "Scrape failed — no pages loaded"),
                )
                logger.warning(f"Scrape failed for {company.company_name}: {data.get('error')}")

        # Step 5: Update batch progress
        await update_batch_progress(db, batch_id)

    logger.info(f"Scrape worker finished for batch {batch_id}")
