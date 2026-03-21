"""
SQLAlchemy ORM Models — the database schema defined as Python classes.

In Rails, you define schema in migrations and the model is thin.
In SQLAlchemy, the model IS the schema definition.

Key concepts:
  - Mapped[type]: Type annotation that tells SQLAlchemy this is a DB column.
    Mapped[str] = non-nullable string column
    Mapped[Optional[str]] = nullable string column

  - mapped_column(): Configures the column (like `t.string :name` in Rails migration).

  - relationship(): Defines associations (like `has_many` / `belongs_to` in Rails).

  - JSON type: Used for flexible data (like Rails' jsonb columns).
    Stores Python dicts directly in PostgreSQL's JSONB column.

  - __tablename__: Explicit table name (Rails infers it, SQLAlchemy requires it).

  Quick Cheatsheet: Model Column Types
Rails Migration          →  SQLAlchemy
t.string :name           →  mapped_column(String(255))
t.text :body             →  mapped_column(Text)
t.integer :count         →  mapped_column(Integer)
t.float :score           →  mapped_column(Float)
t.boolean :active        →  mapped_column(Boolean)
t.datetime :published_at →  mapped_column(DateTime(timezone=True))
t.jsonb :data            →  mapped_column(JSONB)
t.uuid :ref_id           →  mapped_column(UUID(as_uuid=True))
t.references :batch      →  mapped_column(ForeignKey("batches.id"))
null: true               →  nullable=True
default: 0               →  default=0
index: true              →  index=True
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,          # VARCHAR column
    Text,            # TEXT column (unlimited length)
    Float,           # FLOAT column
    Integer,         # INTEGER column
    Boolean,         # BOOLEAN column
    DateTime,        # TIMESTAMP column
    ForeignKey,      # Foreign key constraint
    func,            # SQL functions like NOW()
    Index,           # Database indexes for performance
)
from sqlalchemy.orm import (
    Mapped,          # Type annotation for columns
    mapped_column,   # Column configuration
    relationship,    # Model associations (has_many, belongs_to)
)
from sqlalchemy.dialects.postgresql import (
    UUID,    # PostgreSQL native UUID type
    JSONB,   # PostgreSQL JSONB (binary JSON with indexing)
    ARRAY,   # PostgreSQL native array type
)

from app.database import Base


# ====================================================================
# USER MODEL
# ====================================================================

class User(Base):
    """
    Application user — supports email/password and Google OAuth.

    hashed_password is nullable because Google-only users don't set one.
    google_id links a Google account to a local user.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Nullable — Google-only users won't have a password
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # "local" | "google" — how the account was created
    auth_provider: Mapped[str] = mapped_column(String(50), default="local")

    # Google OAuth subject identifier (unique per Google account)
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True,
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    # has_many :batches (a user owns their uploaded batches)
    batches: Mapped[List["Batch"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.id} | {self.email} | {self.auth_provider}>"


# ====================================================================
# STATUS CONSTANTS
# Avoid raw strings scattered across code — import these instead.
#
# Usage:
#   from app.models import CompanyStatus, BatchStatus
#   company.status = CompanyStatus.SCRAPED
#   if company.status == CompanyStatus.ERROR: ...
# ====================================================================

class CompanyStatus:
    """Company processing lifecycle statuses."""
    PENDING = "pending"        # Waiting to be scraped
    SCRAPING = "scraping"      # Currently being scraped
    SCRAPED = "scraped"        # Scraped, waiting for AI analysis
    ANALYZING = "analyzing"    # AI analysis in progress
    DECIDING = "deciding"      # Accept/reject decision in progress
    COMPLETE = "complete"      # Fully processed with decision
    ERROR = "error"            # Failed at some stage
    EXCLUDED = "excluded"      # User excluded from processing


class BatchStatus:
    """Batch lifecycle statuses."""
    UPLOADED = "uploaded"                        # Excel parsed, awaiting confirmation
    PROCESSING = "processing"                    # Workers are running
    COMPLETED = "completed"                      # All companies done
    COMPLETED_WITH_ERRORS = "completed_with_errors"  # Done but some failed
    FAILED = "failed"                            # Batch-level failure


class Batch(Base):
    """
    A batch represents a single Excel upload.
    Groups companies that were uploaded together.

    Rails equivalent:
      class Batch < ApplicationRecord
        has_many :companies
      end
    """
    __tablename__ = "batches"

    # ---------------------------------------------------------------
    # Columns
    # ---------------------------------------------------------------

    # Primary key: UUID instead of auto-increment integer.
    # UUIDs are better for distributed systems and don't expose record count.
    # server_default=func.gen_random_uuid() → PostgreSQL generates the UUID.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # belongs_to :user — who uploaded this batch
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,  # Nullable so existing batches without a user still work
        index=True,
    )

    # Original filename of the uploaded Excel
    filename: Mapped[str] = mapped_column(String(255))

    # Total number of companies in this upload
    total_companies: Mapped[int] = mapped_column(Integer, default=0)

    # How many have finished processing
    completed_count: Mapped[int] = mapped_column(Integer, default=0)

    # How many had errors
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Batch-level status: uploaded | processing | completed | failed
    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        index=True,  # Index for fast filtering
    )

    # Accept/Reject strategy configured by the user in step 3.
    criteria: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps — server_default uses PostgreSQL's NOW() function.
    # onupdate=func.now() auto-updates updated_at on every save (like Rails' touch).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------

    # has_many :companies
    # back_populates="batch" links this to Company.batch (bidirectional).
    # cascade="all, delete-orphan" → deleting a batch deletes its companies
    #   (like dependent: :destroy in Rails)
    companies: Mapped[List["Company"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    # belongs_to :user
    user: Mapped[Optional["User"]] = relationship(back_populates="batches")

    def __repr__(self):
        return f"<Batch {self.id} | {self.filename} | {self.status}>"


class Company(Base):
    """
    A company to be scraped and analyzed.
    Tracks the full lifecycle: pending → scraping → scraped → analyzing → complete.

    Rails equivalent:
      class Company < ApplicationRecord
        belongs_to :batch
      end
    """
    __tablename__ = "companies"

    # ---------------------------------------------------------------
    # Columns
    # ---------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,  # Standard auto-increment PK
    )

    # Foreign key to batches table.
    # ForeignKey("batches.id") → references batches.id column.
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id"),
        index=True,
    )

    # --- Input Data (from Excel upload) ---

    company_name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(500))
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bvd_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # JSONB column for any extra columns from the Excel file.
    # Stores a Python dict, e.g. {"revenue": "10M", "employees": 500}
    # PostgreSQL indexes JSONB, so you can query inside it.
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in DB (metadata_ avoids Python reserved word clash)
        JSONB,
        nullable=True,
    )

    # --- Processing State ---

    # Status tracks where this company is in the pipeline.
    # pending → scraping → scraped → analyzing → complete
    #                                            → error (at any stage)
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        index=True,
    )

    # --- Scrape Results ---

    # The cleaned markdown content from the website.
    # Text type = unlimited length (unlike String which has a max).
    scraped_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Which pages were crawled (homepage, about, products, etc.)
    # ARRAY(String) → PostgreSQL native text[] array.
    pages_crawled: Mapped[Optional[list]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- AI Analysis Results ---

    # JSONB column storing the full extracted company profile.
    # Contains: business_description, products_services, functional_profile, etc.
    profile: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # The accept/reject/manual_review decision
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # AI confidence score (0.0 to 1.0)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Human-readable reasoning for the decision
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Human final decision set in Final Review step
    final_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    final_decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Which AI provider + model was used
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Total tokens consumed for this company (for cost tracking)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- Error Tracking ---

    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Timestamps ---

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------

    # belongs_to :batch
    batch: Mapped["Batch"] = relationship(back_populates="companies")

    # ---------------------------------------------------------------
    # Indexes
    # ---------------------------------------------------------------
    # Composite index for common query: "get all pending companies for a batch"
    __table_args__ = (
        Index("ix_companies_batch_status", "batch_id", "status"),
    )

    def __repr__(self):
        return f"<Company {self.id} | {self.company_name} | {self.status}>"
