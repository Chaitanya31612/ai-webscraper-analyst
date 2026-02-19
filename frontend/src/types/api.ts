/**
 * API Types — TypeScript mirrors of the FastAPI Pydantic schemas.
 *
 * These are kept in sync with ai-scraper/app/schemas.py
 */

// ===================================================================
// BATCH TYPES
// ===================================================================

export interface BatchUploadResponse {
  batch_id: string
  filename: string
  total_companies: number
  status: string
  companies: CompanyPreview[]
}

export interface CompanyPreview {
  id: number
  company_name: string
  website: string
  country: string | null
  industry: string | null
  bvd_id: string | null
}

export interface BatchConfirmRequest {
  exclude_company_ids: number[]
}

export interface BatchStatusResponse {
  batch_id: string
  filename: string
  status: string
  total_companies: number
  counts: StatusCounts
  created_at: string
}

export interface StatusCounts {
  pending: number
  scraping: number
  scraped: number
  analyzing: number
  complete: number
  error: number
  excluded: number
}

/** Used in list_batches response */
export interface BatchListItem {
  batch_id: string
  filename: string
  status: string
  total_companies: number
  counts: StatusCounts
  created_at: string
}

// ===================================================================
// COMPANY TYPES
// ===================================================================

export interface CompanyListItem {
  id: number
  company_name: string
  website: string
  country: string | null
  industry: string | null
  bvd_id: string | null
  status: string
  decision: string | null
  confidence: number | null
  reasoning: string | null
  error: string | null
}

export interface CompanyDetail {
  id: number
  company_name: string
  website: string
  country: string | null
  industry: string | null
  bvd_id: string | null
  metadata: Record<string, unknown> | null

  status: string

  // Scrape results
  pages_crawled: string[] | null
  scraped_at: string | null

  // AI results
  profile: Record<string, unknown> | null
  decision: string | null
  confidence: number | null
  reasoning: string | null
  ai_provider: string | null
  ai_model: string | null
  tokens_used: number
  analyzed_at: string | null

  error: string | null
  created_at: string
  updated_at: string
}

// ===================================================================
// RESULTS / EXPORT TYPES
// ===================================================================

export interface BatchResultsSummary {
  batch_id: string
  filename: string
  total_companies: number
  counts: StatusCounts
  decisions: DecisionSummary
  companies: CompanyListItem[]
}

export interface DecisionSummary {
  accept: number
  reject: number
  manual_review: number
  error: number
}

// ===================================================================
// GENERIC TYPES
// ===================================================================

export interface ErrorResponse {
  detail: string
  error_code?: string
}

export interface MessageResponse {
  message: string
}
