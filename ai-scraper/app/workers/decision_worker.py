"""
Decision Worker — Background task for Stage 2 accept/reject decisioning.

Flow:
  1. Load batch criteria
  2. Find companies with profile extracted but no decision yet
  3. Call pipeline.processor.make_decision()
  4. Save decision/confidence/reasoning
"""

import os
import sys
import logging
from datetime import datetime

from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models import Batch, Company, CompanyStatus
from app.workers import RateLimiter, update_company_status, update_batch_progress

# ---------------------------------------------------------------
# Import pipeline/scraper modules (sit at project root)
# ---------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scraper.ai.factory import AIAnalyzerFactory
from pipeline.processor import make_decision

logger = logging.getLogger(__name__)


async def run_decision_worker(batch_id):
    """
    Execute Stage 2 decisions for all eligible companies in a batch.

    Eligible company:
      - status='complete'
      - profile IS NOT NULL
      - decision IS NULL
    """
    logger.info(f"Decision worker started for batch {batch_id}")

    try:
        analyzer = AIAnalyzerFactory.create_default()
        logger.info(f"Using AI Provider: {analyzer.provider.value} ({analyzer.model_name})")
    except Exception as e:
        logger.error(f"Failed to initialize AI analyzer for decision worker: {e}")
        return

    limiter = RateLimiter(
        max_requests=settings.AI_REQUESTS_PER_MINUTE,
        window_seconds=60,
    )

    while True:
        async with async_session_factory() as db:
            batch = await db.get(Batch, batch_id)
            if not batch:
                logger.error(f"Batch {batch_id} not found. Decision worker exiting.")
                return

            if not batch.criteria:
                logger.error(f"Batch {batch_id} has no criteria. Decision worker exiting.")
                return

            stmt = (
                select(Company)
                .where(
                    Company.batch_id == batch_id,
                    Company.status == CompanyStatus.COMPLETE,
                    Company.profile.is_not(None),
                    Company.decision.is_(None),
                )
                .limit(10)
            )
            result = await db.execute(stmt)
            companies = result.scalars().all()
            criteria = batch.criteria

        if not companies:
            logger.info(f"Decision worker finished for batch {batch_id}")
            break

        for company in companies:
            await _decide_single_company(
                company_id=company.id,
                batch_id=company.batch_id,
                profile=company.profile,
                existing_tokens=company.tokens_used or 0,
                criteria=criteria,
                analyzer=analyzer,
                limiter=limiter,
            )

    logger.info(f"Decision worker exiting for batch {batch_id}")


async def _decide_single_company(
    company_id: int,
    batch_id,
    profile: dict,
    existing_tokens: int,
    criteria: dict,
    analyzer,
    limiter: RateLimiter,
):
    """Run decisioning for one company and persist the result."""
    await limiter.acquire()

    async with async_session_factory() as db:
        await update_company_status(db, company_id, CompanyStatus.DECIDING)

    try:
        decision_data, decision_tokens = await make_decision(
            profile=profile,
            criteria=criteria,
            ai=analyzer,
        )

        if decision_data.get("decision") == "error":
            error = decision_data.get("error", "Decision failed")
            async with async_session_factory() as db:
                await update_company_status(
                    db,
                    company_id,
                    CompanyStatus.ERROR,
                    error=str(error),
                    tokens_used=existing_tokens + decision_tokens,
                )
                await update_batch_progress(db, batch_id)
            return

        decision_value = str(decision_data.get("decision", "manual_review")).lower()
        if decision_value not in {"accept", "reject", "manual_review"}:
            decision_value = "manual_review"

        confidence = decision_data.get("confidence")
        if isinstance(confidence, (int, float)):
            confidence_value = float(confidence)
        else:
            confidence_value = None

        reasoning = decision_data.get("reasoning")
        reasoning_value = str(reasoning) if reasoning is not None else None

        async with async_session_factory() as db:
            await update_company_status(
                db,
                company_id,
                CompanyStatus.COMPLETE,
                decision=decision_value,
                confidence=confidence_value,
                reasoning=reasoning_value,
                ai_provider=analyzer.provider.value,
                ai_model=analyzer.model_name,
                analyzed_at=datetime.utcnow(),
                tokens_used=existing_tokens + decision_tokens,
            )
            await update_batch_progress(db, batch_id)

    except Exception as e:
        logger.error(f"Decision error for company {company_id}: {e}", exc_info=True)
        async with async_session_factory() as db:
            await update_company_status(
                db,
                company_id,
                CompanyStatus.ERROR,
                error=f"Decision worker exception: {str(e)}",
            )
            await update_batch_progress(db, batch_id)
