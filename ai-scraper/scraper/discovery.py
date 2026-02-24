"""
Discovery module — scrape company websites and discover key pages.

Two modes:
  1. scrape_company()           → single company (existing, used for testing/CLI)
  2. scrape_companies_batch()   → multiple companies via arun_many (used by workers)

Both reuse the same discovery logic and content processing.
"""

from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
from .core import Scraper, ScrapeResult
from .cleaner import clean_markdown, estimate_tokens

TARGET_PAGES = {
    "about": ["/about", "/about-us", "/company", "/who-we-are", "/our-story"],
    "products": ["/products", "/services", "/solutions", "/offerings", "/what-we-do"],
    "contact": ["/contact", "/contact-us", "/locations"],
}

# Token limit settings (~4 chars = 1 token)
MAX_CHARS_PER_PAGE = 8000   # ~2,000 tokens per page (increased since we clean first)
MAX_TOTAL_CHARS = 24000     # ~6,000 tokens total, leaves room for prompts


def process_content(text: str, max_chars: int = MAX_CHARS_PER_PAGE) -> str:
    """Clean and truncate content to stay within token limits."""
    cleaned = clean_markdown(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + "\n\n[...content truncated...]"


def _discover_key_pages_from_links(links: dict) -> dict[str, str]:
    """
    Extract key page URLs from a links dict.

    Shared logic used by both scrape_company() and scrape_companies_batch().
    Looks for internal links matching TARGET_PAGES patterns.

    Args:
        links: Dict with "internal" key containing list of {href, text} dicts

    Returns:
        Dict mapping page_type → URL, e.g. {"about": "https://acme.com/about"}
    """
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


# ====================================================================
# SINGLE COMPANY SCRAPE (existing — used for CLI/testing)
# ====================================================================

async def scrape_company(website: str, scraper: Optional[Scraper] = None) -> dict:
    """
    Full scrape of a single company website including key pages.

    Flow:
      1. Scrape homepage (with link extraction)
      2. Discover key pages from links
      3. Scrape key pages
      4. Clean + truncate all content

    Returns:
        {
          "content": "# Homepage\n\n...\n\n---\n\n# About Page\n\n...",
          "pages_crawled": ["https://acme.com", "https://acme.com/about"],
          "success": True/False,
          "error": None or error string
        }
    """
    if scraper is None:
        scraper = Scraper(headless=True)

    all_content = []
    pages_crawled = []
    total_chars = 0

    # 1. Homepage with links
    homepage = await scraper.scrape_url(website, extract_links=True)

    if homepage.success:
        truncated_homepage = process_content(homepage.markdown)
        all_content.append(f"# Homepage\n\n{truncated_homepage}")
        pages_crawled.append(website)
        total_chars += len(truncated_homepage)

        # 2. Discover and crawl key pages (reuses shared helper)
        key_pages = _discover_key_pages_from_links(homepage.links or {})

        for page_type, url in key_pages.items():
            # Stop if we're approaching the limit
            if total_chars >= MAX_TOTAL_CHARS:
                break

            result = await scraper.scrape_url(url)
            if result.success:
                # Calculate remaining space
                remaining = MAX_TOTAL_CHARS - total_chars
                page_limit = min(MAX_CHARS_PER_PAGE, remaining)
                truncated = process_content(result.markdown, page_limit)

                all_content.append(f"# {page_type.title()} Page\n\n{truncated}")
                pages_crawled.append(url)
                total_chars += len(truncated)

    return {
        "content": "\n\n---\n\n".join(all_content),
        "pages_crawled": pages_crawled,
        "success": len(pages_crawled) > 0,
        "error": homepage.error if not homepage.success else None
    }


# ====================================================================
# BATCH COMPANY SCRAPE — uses crawl4ai's arun_many() for parallelism
# ====================================================================

async def scrape_companies_batch(
    websites: list[str],
    max_concurrent: int = 10,
    headless: bool = True,
    timeout: int = 30000,
) -> dict[str, dict]:
    """
    Scrape multiple company websites in parallel using crawl4ai's arun_many().

    Two-phase approach:
      Phase 1: Scrape all homepages in parallel (with link extraction)
      Phase 2: Discover key pages, scrape all key pages in parallel

    Args:
        websites: List of company website URLs
        max_concurrent: Max concurrent browser sessions
        headless: Run browser without GUI
        timeout: Page load timeout in ms

    Returns:
        Dict mapping website URL → result dict (same shape as scrape_company)

    Example:
        results = await scrape_companies_batch(
            ["https://acme.com", "https://example.com"],
            max_concurrent=5,
        )
        for url, data in results.items():
            if data["success"]:
                print(f"{url}: {len(data['pages_crawled'])} pages")
    """
    import logging
    logger = logging.getLogger(__name__)

    browser_config = BrowserConfig(headless=headless, verbose=False)
    run_config = CrawlerRunConfig(
        wait_until="domcontentloaded",
        page_timeout=timeout,
    )

    # MemoryAdaptiveDispatcher: crawl4ai's built-in concurrency manager.
    # Pauses crawling if system RAM exceeds threshold — prevents OOM crashes.
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        max_session_permit=max_concurrent,
    )

    # Initialize results dict — one entry per company
    results = {
        url: {"content": "", "pages_crawled": [], "success": False, "error": None}
        for url in websites
    }

    # ---------------------------------------------------------------
    # PHASE 1: Scrape all homepages in parallel
    #
    # arun_many() opens multiple browser tabs concurrently.
    # Returns list of CrawlResult in same order as input URLs.
    # ---------------------------------------------------------------
    logger.info(f"Phase 1: Scraping {len(websites)} homepages in parallel with {max_concurrent} max concurrent sessions")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        homepage_results = await crawler.arun_many(
            urls=websites,
            config=run_config,
            dispatcher=dispatcher,
        )

    # Process homepage results + discover key pages for phase 2
    key_page_tasks = []  # [(original_website, page_type, key_page_url), ...]

    for url, crawl_result in zip(websites, homepage_results):
        if crawl_result.success:
            truncated = process_content(crawl_result.markdown)
            results[url]["content"] = f"# Homepage\n\n{truncated}"
            results[url]["pages_crawled"].append(url)
            results[url]["success"] = True

            # Discover key pages from homepage links
            if crawl_result.links:
                key_pages = _discover_key_pages_from_links(crawl_result.links)
                for page_type, page_url in key_pages.items():
                    key_page_tasks.append((url, page_type, page_url))
        else:
            results[url]["error"] = crawl_result.error_message or "Homepage scrape failed"
            logger.warning(f"Failed to scrape homepage: {url}")

    # ---------------------------------------------------------------
    # PHASE 2: Scrape all discovered key pages in parallel
    # ---------------------------------------------------------------
    if key_page_tasks:
        key_page_urls = [task[2] for task in key_page_tasks]
        logger.info(f"Phase 2: Scraping {len(key_page_urls)} key pages in parallel")

        async with AsyncWebCrawler(config=browser_config) as crawler:
            key_results = await crawler.arun_many(
                urls=key_page_urls,
                config=run_config,
                dispatcher=dispatcher,
            )

        # Merge key page content back into company results
        for (original_url, page_type, _page_url), crawl_result in zip(key_page_tasks, key_results):
            if crawl_result.success:
                # Respect per-company token limits
                current_len = len(results[original_url]["content"])
                remaining = MAX_TOTAL_CHARS - current_len
                if remaining <= 0:
                    continue

                page_limit = min(MAX_CHARS_PER_PAGE, remaining)
                truncated = process_content(crawl_result.markdown, page_limit)
                results[original_url]["content"] += f"\n\n---\n\n# {page_type.title()} Page\n\n{truncated}"
                results[original_url]["pages_crawled"].append(_page_url)

    succeeded = sum(1 for r in results.values() if r["success"])
    logger.info(f"Batch scrape complete: {succeeded}/{len(websites)} succeeded")
    return results
