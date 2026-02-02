import os
import json
from dataclasses import asdict
import pandas as pd
from models import CompanyInput, ProcessedCompany

def load_companies_from_excel(filepath: str) -> list[CompanyInput]:
    """Load company data from Excel file."""

    df = pd.read_excel(filepath)

    # Normalize column names
    df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]

    required_cols = ["company_name", "website"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    companies = []
    for idx, row in df.iterrows():
        # Skip rows without website
        if pd.isna(row.get("website")) or not str(row["website"]).strip():
            continue

        website = str(row["website"]).strip()
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"

        company = CompanyInput(
            company_name=str(row.get("company_name", "")).strip(),
            website=website,
            country=str(row.get("country", "")).strip() or None,
            industry=str(row.get("industry", "")).strip() or None,
            bvd_id=str(row.get("bvd_id", idx)).strip(),
            metadata={
                k: v for k, v in row.items()
                if k not in ["company_name", "website", "country", "industry", "bvd_id"]
                and pd.notna(v)
            }
        )
        companies.append(company)

    return companies


def save_result_json(result: ProcessedCompany, output_dir: str) -> str:
    """Save individual result as JSON."""

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{result.input.bvd_id}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, default=str)

    return filepath


def save_markdown(content: str, filename: str, output_dir: str) -> str:
    """Save raw markdown content."""

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def export_summary_excel(results: list[ProcessedCompany], output_dir: str) -> str:
    """Export all results to summary Excel file."""

    rows = []
    for r in results:
        decision = r.decision or {}
        profile = r.profile or {}

        row = {
            "company_name": r.input.company_name,
            "website": r.input.website,
            "country": r.input.country,
            "industry": r.input.industry,
            "bvd_id": r.input.bvd_id,
            "decision": decision.get("decision", "error"),
            "confidence": decision.get("confidence", 0),
            "reasoning": decision.get("reasoning", r.error or ""),
            "business_description": profile.get("business_description", ""),
            "products_count": len(profile.get("products_services", [])),
            "functional_profile": profile.get("functional_profile", ""),
            "target_market": profile.get("target_market", ""),
            "company_size": profile.get("company_size", ""),
            "pages_crawled": len(r.pages_crawled),
            "tokens_used": decision.get("tokens_used", 0),
            "processed_at": r.processed_at,
            "error": r.error or "",
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Sort: accepts first, then by confidence
    sort_map = {"accept": 0, "manual_review": 1, "reject": 2, "error": 3}
    df["sort_key"] = df["decision"].map(sort_map)
    df = df.sort_values(["sort_key", "confidence"], ascending=[True, False])
    df = df.drop(columns=["sort_key"])

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "results_summary.xlsx")
    df.to_excel(filepath, index=False)

    return filepath


def print_summary(results: list[ProcessedCompany]):
    """Print processing summary to console."""

    total = len(results)
    decisions = []
    for r in results:
        if r.decision:
            decisions.append(r.decision.get("decision", "error"))
        else:
            decisions.append("error")

    print("")
    print("=" * 50)
    print("PROCESSING SUMMARY")
    print("=" * 50)
    print(f"Total companies: {total}")
    print(f"  Accept:        {decisions.count('accept')}")
    print(f"  Reject:        {decisions.count('reject')}")
    print(f"  Manual review: {decisions.count('manual_review')}")
    print(f"  Errors:        {decisions.count('error')}")
    print("=" * 50)
