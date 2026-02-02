import asyncio
from dataclasses import dataclass
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


@dataclass
class ScrapeResult:
    url: str
    markdown: str
    html: Optional[str] = None
    links: Optional[dict] = None
    success: bool = True
    error: Optional[str] = None


class Scraper:
    def __init__(self, headless: bool = True, timeout: int = 60000, max_retries: int = 2):
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=False
        )
        self.timeout = timeout
        self.max_retries = max_retries

    async def scrape_url(
        self,
        url: str,
        wait_for: Optional[str] = None,
        extract_links: bool = False
    ) -> ScrapeResult:
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # Use 'domcontentloaded' instead of 'networkidle' to avoid
                # timeouts on sites with continuous background activity
                run_config = CrawlerRunConfig(
                    wait_until="domcontentloaded",
                    wait_for=wait_for,
                    page_timeout=self.timeout,
                )

                async with AsyncWebCrawler(config=self.browser_config) as crawler:
                    result = await crawler.arun(url=url, config=run_config)

                    if result.success:
                        return ScrapeResult(
                            url=url,
                            markdown=result.markdown,
                            html=result.html,
                            links=result.links if extract_links else None
                        )
                    else:
                        last_error = result.error_message

            except Exception as e:
                last_error = str(e)

            # If we get here, the attempt failed - try again if we have retries left
            if attempt < self.max_retries:
                await asyncio.sleep(2)  # Brief delay before retry

        # All attempts failed
        return ScrapeResult(
            url=url,
            markdown="",
            success=False,
            error=last_error or "Unknown error after retries"
        )

    async def scrape_urls(self, urls: list[str]) -> list[ScrapeResult]:
        tasks = [self.scrape_url(url) for url in urls]
        return await asyncio.gather(*tasks)
