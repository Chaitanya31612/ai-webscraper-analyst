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
    """Download batch results as a structured Excel file with section headers."""
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = await db.execute(
        select(Company)
        .where(Company.batch_id == batch_id)
        .order_by(Company.confidence.desc())
    )
    companies = result.scalars().all()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Companies with AI web analysis"

    # ── Column layout ──────────────────────────────────────────────────────────
    #
    # Section 1: General Info          cols A-E (1-5)
    # Section 2: Business Description  cols F-J (6-10)
    # Section 3: AI Results            cols K-N (11-14)
    #
    # Col: A              B           C        D         E           | F       G                    H                    I                   J                      | K            L               M            N
    #      Company Name   BVD ID      Country  Website   Industry    | Source  Business Description  Products & Services  Functional Profile   Corporate Structure    | AI Decision  Final Decision  Confidence   AI Reasoning

    # ── Styles ─────────────────────────────────────────────────────────────────
    HEADER_FONT  = Font(bold=True, color="FFFFFF", size=10)
    COL_FONT     = Font(bold=True, color="333333", size=9)
    DATA_FONT    = Font(size=9)
    CENTER       = Alignment(horizontal="center", vertical="center", wrap_text=True)
    LEFT_WRAP    = Alignment(horizontal="left",   vertical="top",    wrap_text=True)
    LEFT_CENTER  = Alignment(horizontal="left",   vertical="center", wrap_text=False)
    THIN         = Side(style="thin", color="D0D5DD")
    BORDER       = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

    FILL_GENERAL    = PatternFill("solid", fgColor="3B6CB0")   # blue
    FILL_BUSINESS   = PatternFill("solid", fgColor="2E7D5C")   # green
    FILL_AI         = PatternFill("solid", fgColor="7C3AED")   # purple
    FILL_COL_HEADER = PatternFill("solid", fgColor="F2F4F7")

    # ── Row 1: Section headers (merged) ────────────────────────────────────────
    sheet.merge_cells("A1:E1")
    sheet.merge_cells("F1:J1")
    sheet.merge_cells("K1:N1")

    for cell_ref, label, fill in [
        ("A1", "General Info",           FILL_GENERAL),
        ("F1", "Business Description",  FILL_BUSINESS),
        ("K1", "AI Results",            FILL_AI),
    ]:
        cell = sheet[cell_ref]
        cell.value = label
        cell.font = HEADER_FONT
        cell.fill = fill
        cell.alignment = CENTER
        cell.border = BORDER

    sheet.row_dimensions[1].height = 22

    # ── Row 2: Column headers ──────────────────────────────────────────────────
    col_headers = [
        # General Info
        "Company Name", "BVD ID", "Country", "Website", "Industry",
        # Business Description
        "Source", "Business Description", "Products & Services", "Functional Profile", "Corporate Structure",
        # AI Results
        "AI Decision", "Final Decision", "Confidence %", "AI Reasoning",
    ]

    for col_idx, header in enumerate(col_headers, start=1):
        cell = sheet.cell(row=2, column=col_idx, value=header)
        cell.font = COL_FONT
        cell.fill = FILL_COL_HEADER
        cell.alignment = CENTER
        cell.border = BORDER

    sheet.row_dimensions[2].height = 30

    # ── Column widths ──────────────────────────────────────────────────────────
    col_widths = [
        28, 16, 14, 32, 16,         # General Info
        32, 50, 50, 38, 28,         # Business Description
        14, 16, 14, 60,             # AI Results
    ]
    for idx, width in enumerate(col_widths, start=1):
        sheet.column_dimensions[get_column_letter(idx)].width = width

    # ── Data rows ──────────────────────────────────────────────────────────────
    for row_idx, company in enumerate(companies, start=3):
        profile          = company.profile or {}
        products_list    = profile.get("products_services", [])
        products_str     = "; ".join(
            p.get("name", "") for p in products_list if isinstance(p, dict) and p.get("name")
        )
        corporate_struct = profile.get("company_size", "")
        confidence_pct   = (
            f"{round(company.confidence * 100)}%" if isinstance(company.confidence, float) else ""
        )

        row_data = [
            # General Info
            company.company_name,
            company.bvd_id or "",
            company.country or "",
            company.website or "",
            company.industry or "",
            # Business Description
            company.website or "",                           # Source = website URL
            profile.get("business_description", ""),
            products_str,
            profile.get("functional_profile", ""),
            corporate_struct,
            # AI Results
            (company.decision or "").replace("_", " ").title(),
            (company.final_decision or "").replace("_", " ").title(),
            confidence_pct,
            company.reasoning or "",
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = sheet.cell(row=row_idx, column=col_idx, value=value)
            cell.font = DATA_FONT
            cell.border = BORDER
            # Reasoning and description cols get wrap; rest don't
            if col_idx in (7, 8, 9, 14):
                cell.alignment = LEFT_WRAP
            else:
                cell.alignment = LEFT_CENTER

        # Row height — data rows
        sheet.row_dimensions[row_idx].height = 60

    # ── Freeze panes at B3 so headers stay visible on scroll ──────────────────
    sheet.freeze_panes = "A3"

    # ── Write to buffer ────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    base_name = batch.filename.rsplit(".", 1)[0] if "." in batch.filename else batch.filename
    export_filename = f"{base_name}_results.xlsx"

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
