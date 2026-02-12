"""
Batches Router — Handles Excel uploads and batch lifecycle.

This router manages the batch workflow:
  1. Upload Excel file → create Batch + Company records
  2. Verify companies   → user can exclude some before processing
  3. Confirm processing → triggers background workers
  4. Check status       → poll for progress updates

Endpoints:
  POST   /api/batches/upload           Upload Excel, return parsed companies for verification
  POST   /api/batches/{id}/confirm     Confirm processing (start scraping)
  GET    /api/batches/{id}/status      Get processing progress
  GET    /api/batches                  List all batches

Why two-step upload (upload → confirm)?
  - User can verify the Excel was parsed correctly
  - User can exclude specific companies before wasting API calls
  - User can see file validation errors before committing

Reuses:
  - pipeline/file_handler.py → load_companies_from_excel() for parsing
  - app/models.py            → Batch, Company DB models
  - app/schemas.py           → Request/response shapes
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Optional

# FastAPI imports
# ---------------------------------------------------------------
# APIRouter      — Groups related endpoints (like a Rails controller)
# UploadFile     — Handles multipart/form-data file uploads
# File           — Declares a parameter is a file upload
# Depends        — Dependency injection (provides DB session, etc.)
# HTTPException  — Raises HTTP errors (like render status: 404 in Rails)
# BackgroundTasks— Queue functions to run after response (like perform_later)
# Query          — Declares a query parameter with validation
# Path           — Declares a path parameter with validation
# ---------------------------------------------------------------
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    BackgroundTasks,
    Query,
    Path,
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# App imports
from app.config import settings
from app.database import get_db
from app.models import Batch, Company, BatchStatus, CompanyStatus
from app.workers.scrape_worker import run_scrape_worker
from app.workers.analyze_worker import run_analyze_worker

# Schemas for request/response validation
from app.schemas import (
    BatchUploadResponse,
    CompanyPreview,
    BatchConfirmRequest,
    BatchStatusResponse,
    StatusCounts,
    MessageResponse,
)

# ---------------------------------------------------------------
# IMPORT WORKAROUND (The "Path Hack")
#
# Project structure:
#   ai-scraper/
#   ├── app/routers/batches.py   <-- You are here
#   └── pipeline/file_handler.py  <-- We want to import this
#
# By default, Python doesn't look "up" and "over" into other folders.
# 1. __file__ is the path to THIS file.
# 2. dirname() goes up one level: batches.py -> routers/ -> app/ -> project_root/
# 3. sys.path.insert(0, ...) adds the project root to Python's "Search List".
# ---------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from pipeline.file_handler import load_companies_from_excel


# ---------------------------------------------------------------
# Create the router instance.
#
# Note: We DON'T set prefix here — main.py does that when including.
# This keeps the router reusable (could mount at different paths).
# Tags group endpoints in the auto-generated /api/docs.
# ---------------------------------------------------------------
router = APIRouter(tags=["Batches"])


# ====================================================================
# ENDPOINT 1: Upload Excel File
# ====================================================================
@router.post("/upload", response_model=BatchUploadResponse)
async def upload_excel(
    file: UploadFile = File(..., description="Excel file (.xlsx or .xls)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an Excel file and parse it for verification.

    This does NOT start processing yet — it just:
    1. Validates the file format
    2. Parses companies from the Excel
    3. Saves them to the database with status='pending'
    4. Returns the parsed companies for user verification

    Next step: Call /api/batches/{batch_id}/confirm to start processing.

    **Request:**
    - Content-Type: multipart/form-data
    - Field: file (required, .xlsx or .xls)

    **Response Example:**
    ```json
    {
      "batch_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "companies.xlsx",
      "total_companies": 25,
      "status": "uploaded",
      "companies": [
        {"id": 1, "company_name": "Acme Corp", "website": "https://acme.com", ...},
        ...
      ]
    }
    ```

    **Possible Errors:**
    - 400: Invalid file type (not .xlsx or .xls)
    - 400: File too large (> MAX_UPLOAD_SIZE_MB)
    - 400: Missing required columns (company_name, website)
    - 400: No valid companies found in file
    """

    # --- Step 1: Validate file extension ---
    # Only accept Excel files
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = (".xlsx", ".xls")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # --- Step 2: Read and validate file size ---
    # Read entire file into memory (for small files this is fine)
    # For large files, you'd stream to disk instead
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size_mb:.1f}MB). Max: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # --- Step 3: Save to temp file ---
    # We save temporarily because pandas needs a file path, not bytes
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(settings.UPLOAD_DIR, temp_filename)

    try:
        with open(temp_path, "wb") as f:
            f.write(contents)

        # --- Step 4: Parse Excel using existing pipeline code ---
        # load_companies_from_excel returns list[CompanyInput] dataclasses
        # Raises ValueError if required columns are missing
        try:
            company_inputs = load_companies_from_excel(temp_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not company_inputs:
            raise HTTPException(
                status_code=400,
                detail="No valid companies found. Check that rows have company_name and website."
            )

        # --- Step 5: Create Batch record ---
        batch = Batch(
            filename=file.filename,
            total_companies=len(company_inputs),
            status=BatchStatus.UPLOADED,  # Will change to 'processing' on confirm
        )
        db.add(batch)

        # flush() sends INSERT to DB but doesn't commit
        # We need batch.id to create the Company records
        await db.flush()

        # --- Step 6: Create Company records ---
        companies_created = []
        for company_input in company_inputs:
            company = Company(
                batch_id=batch.id,
                company_name=company_input.company_name,
                website=company_input.website,
                country=company_input.country,
                industry=company_input.industry,
                bvd_id=company_input.bvd_id,
                metadata_=company_input.metadata if company_input.metadata else None,
                status=CompanyStatus.PENDING,
            )
            db.add(company)
            await db.flush()  # Get company.id

            # Build preview for response
            companies_created.append(CompanyPreview(
                id=company.id,
                company_name=company.company_name,
                website=company.website,
                country=company.country,
                industry=company.industry,
                bvd_id=company.bvd_id,
            ))

        # --- Step 7: Commit transaction ---
        await db.commit()

        # Return response with all parsed companies
        return BatchUploadResponse(
            batch_id=batch.id,
            filename=batch.filename,
            total_companies=batch.total_companies,
            status=batch.status,
            companies=companies_created,
        )

    finally:
        # --- Cleanup: Remove temp file ---
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ====================================================================
# ENDPOINT 2: Confirm Processing
# ====================================================================
@router.post("/{batch_id}/confirm", response_model=MessageResponse)
async def confirm_batch(
    # Path(...) is a FastAPI helper for URL variables (the part in {batch_id}).
    # The '...' (Ellipsis) means "This is REQUIRED".
    batch_id: uuid.UUID = Path(..., description="Batch UUID"),
    request: BatchConfirmRequest = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm batch and start processing.

    Call this after reviewing the uploaded companies.
    Optionally exclude specific companies from processing.

    **Request Body (optional):**
    ```json
    {
      "exclude_company_ids": [3, 7, 12]  // IDs to skip
    }
    ```

    **What happens:**
    1. Excluded companies get status='excluded'
    2. Batch status changes to 'processing'
    3. Background workers pick up pending companies

    **Response:**
    ```json
    {
      "message": "Processing started for 23 companies"
    }
    ```
    """

    # --- Find the batch ---
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != BatchStatus.UPLOADED:
        raise HTTPException(
            status_code=400,
            detail=f"Batch already {batch.status}. Can only confirm 'uploaded' batches."
        )

    # --- Mark excluded companies ---
    exclude_ids = request.exclude_company_ids if request else []

    if exclude_ids:
        # Get companies to exclude
        stmt = select(Company).where(
            Company.batch_id == batch_id,
            Company.id.in_(exclude_ids)
        )
        result = await db.execute(stmt)

        # scalars() -> Flattens the database rows into a simple list of objects.
        # all()      -> Executes the query and returns a real Python list [obj, obj].
        companies_to_exclude = result.scalars().all()

        for company in companies_to_exclude:
            company.status = CompanyStatus.EXCLUDED

    # --- Count companies that will be processed ---
    stmt = select(func.count(Company.id)).where(
        Company.batch_id == batch_id,
        Company.status == CompanyStatus.PENDING
    )
    result = await db.execute(stmt)
    pending_count = result.scalar()

    if pending_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No companies left to process. All were excluded."
        )

    # --- Update batch status ---
    batch.status = BatchStatus.PROCESSING
    batch.total_companies = pending_count  # Update to reflect actual count

    await db.commit()

    # --- Queue background tasks ---
    # We launch both workers. They run independently and watch the DB.
    # scrape_worker → processes PENDING → SCRAPED
    # analyze_worker → processes SCRAPED → COMPLETE
    if background_tasks:
        background_tasks.add_task(run_scrape_worker, batch_id)
        background_tasks.add_task(run_analyze_worker, batch_id)

    return MessageResponse(
        message=f"Processing started for {pending_count} companies"
    )


# ====================================================================
# ENDPOINT 3: Get Batch Status
# ====================================================================
@router.get("/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: uuid.UUID = Path(..., description="Batch UUID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get batch processing progress.

    Use this endpoint to poll for status updates from the frontend.
    Recommended polling interval: 2-5 seconds during active processing.

    **Response Example:**
    ```json
    {
      "batch_id": "550e8400-...",
      "filename": "companies.xlsx",
      "status": "processing",
      "total_companies": 25,
      "counts": {
        "pending": 10,
        "scraping": 2,
        "scraped": 5,
        "analyzing": 3,
        "complete": 5,
        "error": 0,
        "excluded": 0
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
    ```

    **Status Values:**
    - pending: Waiting to be scraped
    - scraping: Currently being scraped
    - scraped: Scraped, waiting for AI analysis
    - analyzing: AI analysis in progress
    - complete: Fully processed with decision
    - error: Failed at some stage
    - excluded: User excluded from processing
    """

    # --- Find the batch ---
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # --- Count companies by status ---
    # GROUP BY status, COUNT(*) for each
    # SQL: SELECT status, COUNT(*) FROM companies WHERE batch_id=? GROUP BY status
    stmt = (
        select(Company.status, func.count(Company.id).label("count"))
        .where(Company.batch_id == batch_id)
        .group_by(Company.status)
    )
    result = await db.execute(stmt)
    status_rows = result.all()

    # Convert to dict: {"pending": 10, "scraping": 2, ...}
    status_dict = {row.status: row.count for row in status_rows}

    # Build counts object with defaults for missing statuses
    counts = StatusCounts(
        pending=status_dict.get("pending", 0),
        scraping=status_dict.get("scraping", 0),
        scraped=status_dict.get("scraped", 0),
        analyzing=status_dict.get("analyzing", 0),
        complete=status_dict.get("complete", 0),
        error=status_dict.get("error", 0),
        excluded=status_dict.get("excluded", 0),
    )

    return BatchStatusResponse(
        batch_id=batch.id,
        filename=batch.filename,
        status=batch.status,
        total_companies=batch.total_companies,
        counts=counts,
        created_at=batch.created_at,
    )


# ====================================================================
# ENDPOINT 4: List All Batches
# ====================================================================
@router.get("", response_model=list[BatchStatusResponse])
async def list_batches(
    skip: int = Query(0, ge=0, description="Records to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all batches with pagination.

    Returns batches ordered by creation date (newest first).

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Max records to return (default: 20, max: 100)

    **Example:**
    - GET /api/batches?skip=0&limit=10  (first page)
    - GET /api/batches?skip=10&limit=10 (second page)

    **Response:** Array of BatchStatusResponse objects
    """

    # --- Get batches with pagination ---
    stmt = (
        select(Batch)
        .order_by(Batch.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    batches = result.scalars().all()

    # --- Build response with counts for each batch ---
    response = []
    for batch in batches:
        # Get status counts for this batch
        count_stmt = (
            select(Company.status, func.count(Company.id).label("count"))
            .where(Company.batch_id == batch.id)
            .group_by(Company.status)
        )
        count_result = await db.execute(count_stmt)
        status_dict = {row.status: row.count for row in count_result.all()}

        counts = StatusCounts(
            pending=status_dict.get("pending", 0),
            scraping=status_dict.get("scraping", 0),
            scraped=status_dict.get("scraped", 0),
            analyzing=status_dict.get("analyzing", 0),
            complete=status_dict.get("complete", 0),
            error=status_dict.get("error", 0),
            excluded=status_dict.get("excluded", 0),
        )

        response.append(BatchStatusResponse(
            batch_id=batch.id,
            filename=batch.filename,
            status=batch.status,
            total_companies=batch.total_companies,
            counts=counts,
            created_at=batch.created_at,
        ))

    return response
