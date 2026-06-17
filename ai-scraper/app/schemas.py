"""
Pydantic Schemas — define the shape of API request/response data.

In Rails, you might use strong_params + JBuilder/ActiveModelSerializers for this.
In FastAPI, Pydantic schemas handle BOTH:
  1. Request validation  (like strong_params — rejects bad input automatically)
  2. Response shaping    (like JBuilder — controls what JSON gets sent back)

Why separate from models.py?
  - models.py  = database shape (what's stored)
  - schemas.py = API shape (what's sent/received)

  They often look similar but serve different purposes:
  - You might store 20 columns but only expose 10 in the API
  - You might accept different fields on create vs update
  - You might combine data from multiple models in one response

Key concepts:
  - BaseModel:    Base class for all schemas (auto-validates data types)
  - model_config: Controls serialization behavior
  - Field():      Add validation rules (min, max, regex, etc.)
  - Optional[]:   Field can be None / omitted
"""

import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# ====================================================================
# AUTH SCHEMAS
# ====================================================================

class UserRegisterRequest(BaseModel):
    """Registration request — email + password + name."""
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """Login request — email + password."""
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth — exchange the authorization code."""
    code: str
    redirect_uri: str


class UserResponse(BaseModel):
    """Public user profile returned in API responses."""
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    auth_provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT token + user info returned on login/register."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ====================================================================
# BATCH SCHEMAS
# ====================================================================

class BatchUploadResponse(BaseModel):
    """
    Response after uploading an Excel file.
    Returns batch info + parsed companies for user verification.

    Used by: POST /api/batches/upload
    """
    batch_id: uuid.UUID
    filename: str
    total_companies: int
    status: str
    companies: list["CompanyPreview"]  # Forward reference (defined below)


class CompanyPreview(BaseModel):
    """
    Minimal company info shown in the verification table
    before the user confirms processing.

    This is intentionally slim — just enough to verify the upload.
    """
    id: int
    company_name: str
    website: str
    country: Optional[str] = None
    industry: Optional[str] = None
    bvd_id: Optional[str] = None


class BatchConfirmRequest(BaseModel):
    """
    Request to confirm processing.
    Optionally allows excluding specific company IDs.

    Used by: POST /api/batches/{batch_id}/confirm
    """
    # Company IDs to exclude from processing (user unchecked them)
    exclude_company_ids: list[int] = Field(
        default_factory=list,  # Default to empty list (process all)
        description="Company IDs to skip during processing"
    )


class BatchStatusResponse(BaseModel):
    """
    Batch processing progress — used for polling from frontend.

    Used by: GET /api/batches/{batch_id}/status
    """
    batch_id: uuid.UUID
    filename: str
    status: str
    total_companies: int
    counts: "StatusCounts"
    criteria: Optional[dict] = None
    created_at: datetime


class StatusCounts(BaseModel):
    """Breakdown of company statuses within a batch."""
    pending: int = 0
    scraping: int = 0
    scraped: int = 0
    analyzing: int = 0
    deciding: int = 0
    complete: int = 0
    error: int = 0
    excluded: int = 0


class CriteriaUpdate(BaseModel):
    """Accept/reject strategy fields saved per batch."""
    accept_products: Optional[str] = None
    reject_products: Optional[str] = None
    ideal_functional_profile: Optional[str] = None
    reject_functions: Optional[str] = None


class CriteriaResponse(BaseModel):
    """Stored criteria for a batch."""
    criteria: Optional[dict] = None


class FinalDecisionUpdate(BaseModel):
    """Human final decision set during Final Review."""
    final_decision: Optional[Literal["accept", "reject"]] = None


# ====================================================================
# COMPANY SCHEMAS
# ====================================================================

class CompanyListItem(BaseModel):
    """
    Company in a results list — summarized view.

    Used by: GET /api/batches/{batch_id}/companies
    """
    id: int
    company_name: str
    website: str
    country: Optional[str] = None
    industry: Optional[str] = None
    bvd_id: Optional[str] = None
    status: str
    profile: Optional[dict] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    final_decision: Optional[str] = None
    final_decided_at: Optional[datetime] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    pages_crawled: Optional[list[str]] = None
    error: Optional[str] = None

    # ConfigDict tells Pydantic how to serialize this schema.
    # from_attributes=True allows creating this schema directly from
    # a SQLAlchemy model instance: CompanyListItem.model_validate(company_obj)
    # In Rails terms: this is like calling .as_json on an AR object.
    model_config = ConfigDict(from_attributes=True)


class CompanyDetail(BaseModel):
    """
    Full company detail with all AI analysis data.

    Used by: GET /api/companies/{company_id}
    """
    id: int
    company_name: str
    website: str
    country: Optional[str] = None
    industry: Optional[str] = None
    bvd_id: Optional[str] = None
    metadata_: Optional[dict] = Field(None, alias="metadata")

    # Status
    status: str

    # Scrape results
    pages_crawled: Optional[list[str]] = None
    scraped_at: Optional[datetime] = None

    # AI results
    profile: Optional[dict] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    final_decision: Optional[str] = None
    final_decided_at: Optional[datetime] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    tokens_used: int = 0
    analyzed_at: Optional[datetime] = None

    # Error
    error: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ====================================================================
# RESULTS / EXPORT SCHEMAS
# ====================================================================

class BatchResultsSummary(BaseModel):
    """
    Summary of a completed batch — for the results overview page.

    Used by: GET /api/batches/{batch_id}/results
    """
    batch_id: uuid.UUID
    filename: str
    total_companies: int
    counts: StatusCounts
    decisions: "DecisionSummary"
    companies: list[CompanyListItem]


class DecisionSummary(BaseModel):
    """Breakdown of accept/reject/review decisions."""
    accept: int = 0
    reject: int = 0
    manual_review: int = 0
    error: int = 0


# ====================================================================
# GENERIC SCHEMAS
# ====================================================================

class ErrorResponse(BaseModel):
    """Standard error response shape."""
    detail: str
    error_code: Optional[str] = None


class MessageResponse(BaseModel):
    """Simple success message."""
    message: str


# ---------------------------------------------------------------
# Rebuild forward references.
# Python can't resolve "CompanyPreview" inside BatchUploadResponse
# at class definition time because CompanyPreview is defined after.
# model_rebuild() resolves these forward references.
# Similar to Rails' lazy loading of associations.
# ---------------------------------------------------------------
BatchUploadResponse.model_rebuild()
BatchStatusResponse.model_rebuild()
BatchResultsSummary.model_rebuild()
