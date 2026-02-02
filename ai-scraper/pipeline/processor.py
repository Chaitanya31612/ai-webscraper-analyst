import json
from typing import Optional
from scraper.ai import AIAnalyzer
from .criteria import AcceptRejectCriteria


EXTRACTION_PROMPT = """You are a business analyst extracting company information.

Extract from the website content:
1. Business Description: 2-3 sentence summary
2. Products/Services: List each with name, description, category
3. Functional Profile: B2B/B2C/Both + business model (SaaS, Consulting, etc.)
4. Target Market: Who are their customers?
5. Company Size: Startup/SMB/Enterprise (based on indicators)
6. Geographic Presence: Countries/regions

Return ONLY valid JSON:
{"business_description": "string",
    "products_services": [
        {"name": "string", "description": "string", "category": "string", "is_core": true}
    ],
    "functional_profile": "string",
    "target_market": "string",
    "company_size": "string",
    "geographic_presence": ["string"],
    "technology_indicators": ["string"],
    "certifications": ["string"]
}

Use null for unavailable fields. Be factual."""


def build_decision_prompt(criteria: AcceptRejectCriteria) -> str:
    return f"""Evaluate this company for partnership eligibility.

ACCEPT if matches:
- Industries: {criteria.accept_industries}
- Product keywords: {criteria.accept_product_keywords}
- Company sizes: {criteria.accept_company_sizes}

REJECT if matches (overrides accept):
- Industries: {criteria.reject_industries}
- Product keywords: {criteria.reject_product_keywords}

Requirements:
- Minimum products: {criteria.min_products_count}
- B2B required: {criteria.require_b2b}

Return ONLY valid JSON:
{{"decision": "accept" | "reject" | "manual_review", "confidence": 0.0-1.0, "reasoning": "2-3 sentence explanation", "matching_accept_criteria": ["list matched accept criteria"], "triggered_reject_criteria": ["list triggered reject criteria"]}}"""


def parse_json_response(content: str) -> Optional[dict]:
    """Parse JSON from AI response, handling markdown wrappers."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        clean = content.strip()
        if clean.startswith("```json"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:])
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()
        return json.loads(clean)


async def analyze_company(
        content: str,
        criteria: AcceptRejectCriteria,
        ai: Optional[AIAnalyzer] = None
) -> tuple[Optional[dict], dict]:
    """
    Two-stage AI analysis:
    Extract company profile
    Make accept/reject decision
    Returns: (profile_dict, decision_dict)
    """
    if ai is None:
        ai = AIAnalyzer(model="smart")

    # Stage 1: Extract profile
    profile_result = ai.analyze(content, EXTRACTION_PROMPT)
    if not profile_result.success:
        return None, {"decision": "error", "error": profile_result.error}

    try:
        profile = parse_json_response(profile_result.content)
    except (json.JSONDecodeError, Exception) as e:
        return None, {"decision": "error", "error": f"Profile parse failed: {e}"}

    # Stage 2: Decision
    decision_prompt = build_decision_prompt(criteria)
    decision_input = f"COMPANY PROFILE:\n{json.dumps(profile, indent=2)}"
    decision_result = ai.analyze(decision_input, decision_prompt)
    if not decision_result.success:
        return profile, {"decision": "error", "error": decision_result.error}

    try:
        decision = parse_json_response(decision_result.content)
    except (json.JSONDecodeError, Exception) as e:
        return profile, {"decision": "error", "error": f"Decision parse failed: {e}"}

    decision["tokens_used"] = profile_result.tokens_used + decision_result.tokens_used
    return profile, decision
