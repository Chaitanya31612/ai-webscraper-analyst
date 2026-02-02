from typing import Optional
from .core import Scraper, ScrapeResult

TARGET_PAGES = {
    "about": ["/about", "/about-us", "/company", "/who-we-are", "/our-story"],
    "products": ["/products", "/services", "/solutions", "/offerings", "/what-we-do"],
    "contact": ["/contact", "/contact-us", "/locations"],
}

# Token limit settings (~4 chars = 1 token)
MAX_CHARS_PER_PAGE = 6000   # ~1,500 tokens per page
MAX_TOTAL_CHARS = 20000     # ~5,000 tokens total, leaves room for prompts


def truncate_content(text: str, max_chars: int = MAX_CHARS_PER_PAGE) -> str:
    """Truncate content to stay within token limits."""
    if len(text) <= max_chars:
        return text
    # Keep beginning (usually most important) + add truncation notice
    return text[:max_chars] + "\n\n[...content truncated...]"


async def discover_key_pages(
        scraper: Scraper,
        base_url: str,
        homepage_result: Optional[ScrapeResult] = None
) -> dict[str, str]:
    """Find links to key pages from homepage."""

    if homepage_result is None or homepage_result.links is None:
        result = await scraper.scrape_url(base_url, extract_links=True)
        if not result.success:
            return {}
        links = result.links
    else:
        links = homepage_result.links

    found_pages = {}
    internal_links = links.get("internal", [])

    for link in internal_links:
        href = link.get("href", "").lower()

        for page_type, patterns in TARGET_PAGES.items():
            if page_type in found_pages:
                continue
            for pattern in patterns:
                if pattern in href:
                    found_pages[page_type] = link["href"]
                    break

    return found_pages


async def scrape_company(website: str, scraper: Optional[Scraper] = None) -> dict:
    """Full scrape of a company website including key pages."""

    if scraper is None:
        scraper = Scraper(headless=True)

    all_content = []
    pages_crawled = []
    total_chars = 0

    # 1. Homepage with links
    homepage = await scraper.scrape_url(website, extract_links=True)

    if homepage.success:
        # Truncate homepage content
        truncated_homepage = truncate_content(homepage.markdown)
        all_content.append(f"# Homepage\n\n{truncated_homepage}")
        pages_crawled.append(website)
        total_chars += len(truncated_homepage)

        # 2. Discover and crawl key pages
        key_pages = await discover_key_pages(scraper, website, homepage)

        for page_type, url in key_pages.items():
            # Stop if we're approaching the limit
            if total_chars >= MAX_TOTAL_CHARS:
                break

            result = await scraper.scrape_url(url)
            if result.success:
                # Calculate remaining space
                remaining = MAX_TOTAL_CHARS - total_chars
                page_limit = min(MAX_CHARS_PER_PAGE, remaining)
                truncated = truncate_content(result.markdown, page_limit)

                all_content.append(f"# {page_type.title()} Page\n\n{truncated}")
                pages_crawled.append(url)
                total_chars += len(truncated)

    return {
        "content": "\n\n---\n\n".join(all_content),
        "pages_crawled": pages_crawled,
        "success": len(pages_crawled) > 0,
        "error": homepage.error if not homepage.success else None
    }
