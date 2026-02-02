import asyncio
from datetime import datetime

from models import CompanyInput, ProcessedCompany
from scraper import Scraper, AIAnalyzer, scrape_company
from pipeline import (
    AcceptRejectCriteria,
    analyze_company,
    load_companies_from_excel,
    save_result_json,
    export_summary_excel,
    print_summary
)


async def process_company(
        company: CompanyInput,
        scraper: Scraper,
        ai: AIAnalyzer,
        criteria: AcceptRejectCriteria
) -> ProcessedCompany:
    """Process a single company: scrape → analyze → decide."""

    try:
        # Scrape
        scrape_result = await scrape_company(company.website, scraper)

        if not scrape_result["success"]:
            return ProcessedCompany(
                input=company,
                profile=None,
                decision=None,
                raw_markdown="",
                pages_crawled=[],
                processed_at=datetime.now(),
                error=scrape_result.get("error", "Scrape failed")
            )

        # Analyze
        profile, decision = await analyze_company(
            scrape_result["content"],
            criteria,
            ai
        )

        return ProcessedCompany(
            input=company,
            profile=profile,
            decision=decision,
            raw_markdown=scrape_result["content"],
            pages_crawled=scrape_result["pages_crawled"],
            processed_at=datetime.now()
        )

    except Exception as e:
        return ProcessedCompany(
            input=company,
            profile=None,
            decision=None,
            raw_markdown="",
            pages_crawled=[],
            processed_at=datetime.now(),
            error=str(e)
        )


async def main(
        excel_path: str = "companies.xlsx",
        output_dir: str = "output"
):
    # 1. Load companies
    companies = load_companies_from_excel(excel_path)
    print(f"Loaded {len(companies)} companies from {excel_path}")

    # 2. Initialize
    scraper = Scraper(headless=True)
    ai = AIAnalyzer(model="smart")
    criteria = AcceptRejectCriteria(
        accept_industries=["Technology", "Healthcare", "Software", "Financial Services"],
        accept_product_keywords=["SaaS", "platform", "cloud", "API", "analytics"],
        reject_product_keywords=["gambling", "casino", "adult"],
        require_b2b=False
    )

    # 3. Process each company
    results = []
    for i, company in enumerate(companies, 1):
        print(f"\n[{i}/{len(companies)}] {company.company_name}")
        print(f"  URL: {company.website}")

        result = await process_company(company, scraper, ai, criteria)

        if result.decision:
            decision = result.decision.get("decision", "error")
            confidence = result.decision.get("confidence", 0)
            print(f"  → {decision.upper()} (confidence: {confidence:.0%})")
        else:
            print(f"  → ERROR: {result.error}")

        results.append(result)
        save_result_json(result, output_dir)

    # 4. Export summary
    export_summary_excel(results, output_dir)
    print_summary(results)
    print(f"\nResults saved to {output_dir}/")


if __name__ == "__main__":
    asyncio.run(main())
