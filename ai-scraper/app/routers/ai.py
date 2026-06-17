"""
AI Router — Utility AI endpoints for frontend assistance.

Endpoints:
  POST /api/ai/generate-criteria   Generate accept/reject criteria from a text description
  POST /api/ai/map-columns         Suggest Excel column mappings (AI-assisted)
"""

import os
import sys
import json
import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scraper.ai.factory import AIAnalyzerFactory, AIProvider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Utilities"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class GenerateCriteriaRequest(BaseModel):
    description: str


class GenerateCriteriaResponse(BaseModel):
    accept_products: str = ""
    reject_products: str = ""
    ideal_functional_profile: str = ""
    reject_functions: str = ""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_analyzer():
    """Get the configured AI analyzer (tries Groq first, then Gemini)."""
    try:
        return AIAnalyzerFactory.create(AIProvider.GROQ)
    except Exception:
        pass
    try:
        return AIAnalyzerFactory.create(AIProvider.GEMINI)
    except Exception:
        pass
    raise HTTPException(
        status_code=503,
        detail="No AI provider available. Configure GROQ_API_KEY or GEMINI_API_KEY."
    )


# ── Endpoint: Generate Accept/Reject Criteria ─────────────────────────────────

CRITERIA_SYSTEM_PROMPT = """You are a business analyst assistant. Based on the user's description of a benchmark or business strategy, generate structured accept/reject criteria for a company screening tool.

Return ONLY a valid JSON object with exactly these 4 fields (no extra text, no markdown, no explanation):
{
  "accept_products": "Comma-separated list of ideal products/services to accept. Be specific with concrete examples.",
  "reject_products": "Comma-separated list of products/services that should cause rejection.",
  "ideal_functional_profile": "Description of the ideal company functional role (e.g. distributor, wholesaler, manufacturer, retailer, B2B/B2C mix).",
  "reject_functions": "Comma-separated list of functions/activities that should cause rejection (e.g. retail-only, end-consumer focus, pure manufacturing without distribution)."
}

Rules:
- Be specific and actionable. Avoid vague terms.
- All 4 fields must be non-empty strings.
- Return ONLY the JSON object, nothing else."""


@router.post("/generate-criteria", response_model=GenerateCriteriaResponse)
async def generate_criteria(request: GenerateCriteriaRequest):
    """
    Use AI to generate structured accept/reject criteria from a natural language description.

    Example input: "Distribution and wholesale of construction and electrical materials"
    Returns: Structured criteria JSON suitable for the benchmarking analysis pipeline.
    """
    if not request.description or not request.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")

    analyzer = _get_analyzer()
    # The base interface is analyze(content, prompt) where:
    #   prompt = system instruction (role/rules)
    #   content = user message (the actual description)
    try:
        response = await asyncio.to_thread(
            analyzer.analyze,
            request.description.strip(),  # content: the actual description
            CRITERIA_SYSTEM_PROMPT,        # prompt: system instructions
        )
        if not response.success:
            raise HTTPException(status_code=500, detail=f"AI error: {response.error}")
        raw_response = response.content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI criteria generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI request failed: {str(e)}"
        )

    # Parse the JSON from the AI response
    try:
        # Strip markdown code fences if present
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        data = json.loads(text)
        return GenerateCriteriaResponse(
            accept_products=str(data.get("accept_products", "")),
            reject_products=str(data.get("reject_products", "")),
            ideal_functional_profile=str(data.get("ideal_functional_profile", "")),
            reject_functions=str(data.get("reject_functions", "")),
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse AI criteria response: {raw_response!r} — {e}")
        raise HTTPException(
            status_code=500,
            detail="AI returned an unexpected format. Please try again."
        )
