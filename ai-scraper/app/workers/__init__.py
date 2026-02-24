"""
Workers package — shared utilities for background tasks.

Workers are independent background loops that poll the database:
  - scrape_worker  → picks companies with status='pending', scrapes them
  - analyze_worker → picks companies with status='scraped', analyzes with AI

They don't call each other. Both watch the DB independently:

    ┌──────────────┐              ┌──────────────┐
    │ scrape_worker│              │analyze_worker│
    │              │              │              │
    │ polls:       │              │ polls:       │
    │ status=      │   DB         │ status=      │
    │ 'pending'    │◄────────────►│ 'scraped'    │
    │              │              │              │
    │ sets:        │              │ sets:        │
    │ 'scraped'    │              │ 'complete'   │
    └──────────────┘              └──────────────┘

This file contains shared utilities used by both workers:
  - RateLimiter: Token bucket rate limiter for AI API calls
  - update_company_status: Helper to update company status in DB
  - update_batch_progress: Helper to update batch counters
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Batch

logger = logging.getLogger(__name__)


# ====================================================================
# RATE LIMITER
# ====================================================================

class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Ensures we don't exceed API rate limits (e.g., Gemini free = 10 RPM).
    Uses a sliding window approach — tracks timestamps of recent requests
    and waits if we'd exceed the limit.

    Usage:
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        # Before each API call:
        await limiter.acquire()  # Blocks if rate limit reached
        response = await call_ai_api(...)

    How it works:
        - Keeps a list of timestamps when requests were made
        - On acquire(), removes timestamps older than the window
        - If remaining slots > 0, allows immediately
        - If no slots, calculates sleep time until oldest expires

    Example with max_requests=3, window=60s:
        t=0s   → acquire() → allowed (1/3 used)
        t=1s   → acquire() → allowed (2/3 used)
        t=2s   → acquire() → allowed (3/3 used)
        t=3s   → acquire() → WAIT until t=60s (oldest expires)
    """

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        # List of timestamps (float) when requests were made
        self.timestamps: list[float] = []

    async def acquire(self):
        """
        Wait until a request slot is available.
        Returns immediately if under the limit, blocks otherwise.
        """
        while True:
            now = time.monotonic()

            # Remove timestamps older than the window
            # e.g., if window=60s, remove anything older than 60s ago
            self.timestamps = [t for t in self.timestamps if now - t < self.window]

            if len(self.timestamps) < self.max_requests:
                # Slot available — record this request and proceed
                self.timestamps.append(now)
                return

            # No slots — calculate how long until the oldest slot expires
            oldest = self.timestamps[0]
            sleep_time = self.window - (now - oldest) + 0.1  # +0.1s buffer
            logger.info(f"Rate limit reached ({self.max_requests}/{self.window}s). "
                        f"Waiting {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)


# ====================================================================
# DB HELPERS — shared by both workers
# ====================================================================

async def update_company_status(
    db: AsyncSession,
    company_id: int,
    status: str,
    error: Optional[str] = None,
    **extra_fields,
):
    """
    Update a company's status and optional fields in DB.

    Usage:
        await update_company_status(db, company.id, "scraped",
            scraped_markdown=content,
            pages_crawled=["https://acme.com", "https://acme.com/about"],
            scraped_at=datetime.utcnow(),
        )

    Args:
        db: Database session
        company_id: Company PK
        status: New status string
        error: Error message (if status='error')
        **extra_fields: Any other Company columns to update
    """
    values = {"status": status, "updated_at": datetime.utcnow()}

    if error:
        values["error"] = error
    values.update(extra_fields)

    stmt = (
        update(Company)
        .where(Company.id == company_id)
        .values(**values)
    )
    await db.execute(stmt)
    await db.commit()


async def update_batch_progress(db: AsyncSession, batch_id):
    """
    Recalculate batch completed/error counts from company statuses.
    Called after each company finishes processing.

    Counts companies with status='complete' and status='error',
    then updates the batch record.
    """
    # Count completed
    stmt = select(func.count(Company.id)).where(
        Company.batch_id == batch_id,
        Company.status == "complete"
    )
    result = await db.execute(stmt)
    completed = result.scalar()

    # Count errors
    stmt = select(func.count(Company.id)).where(
        Company.batch_id == batch_id,
        Company.status == "error"
    )
    result = await db.execute(stmt)
    errors = result.scalar()

    # Count total that should be processed (not excluded)
    stmt = select(func.count(Company.id)).where(
        Company.batch_id == batch_id,
        Company.status != "excluded"
    )
    result = await db.execute(stmt)
    total_active = result.scalar()

    # Update batch
    batch_status = "processing"
    if (completed + errors) >= total_active:
        batch_status = "completed" if errors == 0 else "completed_with_errors"

    stmt = (
        update(Batch)
        .where(Batch.id == batch_id)
        .values(
            completed_count=completed,
            error_count=errors,
            status=batch_status,
        )
    )
    await db.execute(stmt)
    await db.commit()
