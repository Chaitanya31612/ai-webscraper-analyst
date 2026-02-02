from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Decision(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    REVIEW = "manual_review"  # When AI is uncertain


@dataclass
class CompanyInput:
    """From Excel upload."""
    company_name: str
    website: str
    country: str
    industry: str
    bvd_id: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ProductService:
    """Extracted product/service."""
    name: str
    description: str
    category: str  # e.g., "SaaS", "Consulting", "Manufacturing"
    is_core: bool  # Primary offering vs ancillary


@dataclass
class CompanyProfile:
    """AI-extracted company profile."""
    business_description: str
    products_services: list[ProductService]
    functional_profile: str  # "B2B SaaS", "B2C E-commerce", etc.
    target_market: str
    company_size: str  # "Startup", "SMB", "Enterprise"
    geographic_presence: list[str]
    technology_stack: list[str]  # If detectable
    certifications: list[str]  # ISO, SOC2, etc.


@dataclass
class DecisionResult:
    """Accept/Reject decision with reasoning."""
    decision: Decision
    confidence: float  # 0.0 to 1.0
    reasoning: str
    matching_criteria: list[str]  # Which accept criteria matched
    rejection_reasons: list[str]  # Which reject criteria triggered


@dataclass
class ProcessedCompany:
    """Final result for each company."""
    input: CompanyInput
    profile: Optional[CompanyProfile]
    decision: Optional[DecisionResult]
    raw_markdown: str
    pages_crawled: list[str]
    processed_at: datetime
    error: Optional[str] = None