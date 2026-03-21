"""
Companies Router — View, filter, and export company results.

Endpoints:
  GET  /api/companies/{id}            Full company detail
  GET  /api/batches/{batch_id}/companies  List companies in a batch (filterable)
  GET  /api/batches/{batch_id}/export     Export batch results as Excel

Why companies are accessed through batches?
  - Companies always belong to a batch
  - Filtering by batch prevents accidentally mixing results
  - Export is per-batch (one Excel per upload)

Reuses:
  - app/models.py   → Company, Batch
  - app/schemas.py  → CompanyDetail, CompanyListItem, BatchResultsSummary
"""

import io
import os
import sys
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# openpyxl: Library for writing Excel files.
# StreamingResponse: Sends the file as a download without saving to disk.
import openpyxl

from app.database import get_db
from app.models import Company, Batch, CompanyStatus
from app.schemas import (
    CompanyDetail,
    CompanyListItem,
    BatchResultsSummary,
    StatusCounts,
    DecisionSummary,
    FinalDecisionUpdate,
    MessageResponse,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.workers.scrape_worker import run_scrape_worker
from app.workers.analyze_worker import run_analyze_worker

# ---------------------------------------------------------------
# Router instance.
# tags=["Companies"] groups these endpoints in /api/docs.
# We don't set a prefix here — main.py handles that.
# ---------------------------------------------------------------
router = APIRouter(tags=["Companies"])


# ---------------------------------------------------------------
# GET /api/companies/{company_id}
#
# Returns full detail for a single company including:
#   - Input data (from Excel)
#   - Scraped pages list
#   - AI profile extraction
#   - Accept/reject decision + reasoning
#
# Rails equivalent:
#   def show
#     @company = Company.find(params[:id])
#     render json: @company
#   end
# ---------------------------------------------------------------
@router.get(
    "/{company_id}",
    response_model=CompanyDetail,
    summary="Get full company detail",
)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete company data including AI analysis."""

    company = await db.get(Company, company_id)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company  # Pydantic auto-serializes via from_attributes=True


@router.patch(
    "/{company_id}/final-decision",
    response_model=CompanyListItem,
    summary="Set final human decision for a company",
)
async def set_final_decision(
    company_id: int,
    payload: FinalDecisionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Save final accept/reject decision made in Final Review step."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.final_decision = payload.final_decision
    company.final_decided_at = datetime.utcnow() if payload.final_decision else None

    await db.commit()
    await db.refresh(company)
    return company


# ---------------------------------------------------------------
# GET /api/batches/{batch_id}/companies
#
# Lists all companies in a batch with optional filters.
# Query params allow filtering by status and decision.
#
# Examples:
#   /api/batches/{id}/companies                     → all
#   /api/batches/{id}/companies?status=complete      → only finished
#   /api/batches/{id}/companies?decision=accept      → only accepted
#   /api/batches/{id}/companies?status=error         → only errors
#
# Rails equivalent:
#   def index
#     @companies = Batch.find(params[:batch_id]).companies
#     @companies = @companies.where(status: params[:status]) if params[:status]
#     @companies = @companies.where(decision: params[:decision]) if params[:decision]
#     render json: @companies
#   end
#
# Note: This endpoint is registered under /api/batches prefix in main.py
# via batches router, OR we can keep it here and register with a separate prefix.
# We put it in companies.py because the logic is about companies.
# main.py can mount it at both prefixes.
# ---------------------------------------------------------------
@router.get(
    "/batch/{batch_id}",
    response_model=list[CompanyListItem],
    summary="List companies in a batch",
)
async def list_batch_companies(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    # Query() params — like Rails' params[:status]
    # Optional[str] = None means the param is not required.
    status: Optional[str] = Query(
        None,
        description="Filter by status: pending, scraping, scraped, analyzing, complete, error, excluded"
    ),
    decision: Optional[str] = Query(
        None,
        description="Filter by decision: accept, reject, manual_review"
    ),
):
    """List all companies in a batch, with optional status/decision filters."""

    # Verify batch exists
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Build query — SQLAlchemy's select() is like ActiveRecord's .where() chain.
    # Each .where() call adds an AND condition.
    query = select(Company).where(Company.batch_id == batch_id)

    if status:
        query = query.where(Company.status == status)

    if decision:
        query = query.where(Company.decision == decision)

    # Order by: errors first, then by decision, then by confidence descending.
    # This surfaces problems and best matches at the top.
    query = query.order_by(Company.status.desc(), Company.confidence.desc())

    result = await db.execute(query)

    # scalars() extracts the ORM objects from the result rows.
    # .all() collects them into a list.
    companies = result.scalars().all()

    return companies


# ---------------------------------------------------------------
# GET /api/batches/{batch_id}/results
#
# Aggregated results summary for a completed batch.
# Includes status counts, decision counts, and full company list.
# Used by the frontend results overview page.
# ---------------------------------------------------------------
@router.get(
    "/batch/{batch_id}/results",
    response_model=BatchResultsSummary,
    summary="Get batch results summary",
)
async def get_batch_results(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated results for a batch."""

    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Fetch all companies in one query
    result = await db.execute(
        select(Company)
        .where(Company.batch_id == batch_id)
        .order_by(Company.confidence.desc())
    )
    companies = result.scalars().all()

    # Count statuses — Python's list comprehension version of
    # Company.where(batch_id: id).group(:status).count in Rails
    status_list = [c.status for c in companies]
    decision_list = [c.decision for c in companies if c.decision]

    return BatchResultsSummary(
        batch_id=batch.id,
        filename=batch.filename,
        total_companies=batch.total_companies,
        counts=StatusCounts(
            pending=status_list.count("pending"),
            scraping=status_list.count("scraping"),
            scraped=status_list.count("scraped"),
            analyzing=status_list.count("analyzing"),
            complete=status_list.count("complete"),
            error=status_list.count("error"),
            excluded=status_list.count("excluded"),
        ),
        decisions=DecisionSummary(
            accept=decision_list.count("accept"),
            reject=decision_list.count("reject"),
            manual_review=decision_list.count("manual_review"),
            # Count errors from status, not decision (errors don't have a decision)
            error=status_list.count("error"),
        ),
        companies=[CompanyListItem.model_validate(c) for c in companies],
    )


# ---------------------------------------------------------------
# GET /api/batches/{batch_id}/export
#
# Exports results as a downloadable Excel file.
# Uses openpyxl to create the workbook in memory (no temp files).
# StreamingResponse sends it as a file download.
#
# Rails equivalent:
#   def export
#     companies = Batch.find(params[:id]).companies.complete
#     send_data generate_xlsx(companies),
#       filename: "results.xlsx",
#       type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#   end
# ---------------------------------------------------------------
@router.get(
    "/batch/{batch_id}/export",
    summary="Export batch results as Excel",
)
async def export_batch_results(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download batch results as an Excel file."""

    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = await db.execute(
        select(Company)
        .where(Company.batch_id == batch_id)
        .order_by(Company.confidence.desc())
    )
    companies = result.scalars().all()

    # --- Build Excel workbook in memory ---

    # openpyxl.Workbook() creates a new Excel file.
    # wb.active gets the default sheet.
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Results"

    # Header row
    headers = [
        "Company Name", "Website", "Country", "Industry", "BVD ID",
        "Decision", "Confidence", "Reasoning",
        "Business Description", "Products Count", "Functional Profile",
        "Target Market", "Company Size",
        "AI Provider", "AI Model", "Tokens Used",
        "Pages Crawled", "Status", "Error",
    ]
    sheet.append(headers)

    # Data rows
    for company in companies:
        profile = company.profile or {}
        products = profile.get("products_services", [])

        sheet.append([
            company.company_name,
            company.website,
            company.country,
            company.industry,
            company.bvd_id,
            company.decision,
            company.confidence,
            company.reasoning,
            profile.get("business_description", ""),
            len(products),
            profile.get("functional_profile", ""),
            profile.get("target_market", ""),
            profile.get("company_size", ""),
            company.ai_provider,
            company.ai_model,
            company.tokens_used,
            len(company.pages_crawled or []),
            company.status,
            company.error,
        ])

    # --- Write to bytes buffer (no temp file) ---
    # io.BytesIO is an in-memory binary stream.
    # We write the Excel file into it, then send it as response.
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)  # Rewind to start so StreamingResponse reads from beginning

    # --- Generate download filename ---
    # Take original filename, remove extension, add "_results.xlsx"
    # e.g., "companies.xlsx" -> "companies_results.xlsx"
    base_name = batch.filename.rsplit(".", 1)[0] if "." in batch.filename else batch.filename
    export_filename = f"{base_name}_results.xlsx"

    # StreamingResponse sends the bytes as a file download.
    # The Content-Disposition header tells the browser to download (not display).
    return StreamingResponse(
        content=buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        },
    )


# ---------------------------------------------------------------
# POST /api/companies/{company_id}/rescrape
#
# Re-runs scrape + analysis for a single company.
# Useful when results look wrong (e.g. data swap between companies).
#
# Steps:
#   1. Reset company to PENDING (clears old scraped/profile data)
#   2. Queue scrape_worker + analyze_worker for that company's batch
# ---------------------------------------------------------------
@router.post(
    "/{company_id}/rescrape",
    response_model=MessageResponse,
    summary="Re-scrape and re-analyse a single company",
)
async def rescrape_company(
    company_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Reset a company to PENDING and re-run scrape + AI analysis."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Clear previous results and reset status to trigger workers
    company.status = CompanyStatus.PENDING
    company.scraped_markdown = None
    company.pages_crawled = []
    company.profile = None
    company.decision = None
    company.confidence = None
    company.reasoning = None
    company.error = None
    company.scraped_at = None
    company.analyzed_at = None
    company.tokens_used = None
    company.ai_provider = None
    company.ai_model = None

    await db.commit()

    # Re-run both workers for the batch — they will only pick up PENDING companies
    batch_id = company.batch_id
    background_tasks.add_task(run_scrape_worker, batch_id)
    background_tasks.add_task(run_analyze_worker, batch_id)

    return MessageResponse(message=f"Re-scraping started for: {company.company_name}")
