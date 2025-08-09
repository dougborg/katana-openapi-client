#!/usr/bin/env python3
"""
Katana API Documentation Crawler

Advanced crawler for downloading Katana Manufacturing API documentation
for offline reference by Copilot and developers.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KatanaDocsCrawler:
    def __init__(
        self,
        base_url: str = "https://developer.katanamrp.com",
        output_dir: str = "docs/katana-api-reference",
    ):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: set[str] = set()
        self.failed_urls: list[str] = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Documentation structure mapping
        self.doc_sections = {
            "core": [
                "/docs/api/introduction",
                "/docs/api/authentication",
                "/docs/api/errors",
                "/docs/api/pagination",
                "/docs/api/rate-limiting",
                "/docs/api/webhooks",
            ],
            "resources": [
                "/docs/api/products",
                "/docs/api/materials",
                "/docs/api/variants",
                "/docs/api/customers",
                "/docs/api/suppliers",
                "/docs/api/sales-orders",
                "/docs/api/purchase-orders",
                "/docs/api/manufacturing-orders",
                "/docs/api/inventory",
                "/docs/api/inventory-movements",
                "/docs/api/locations",
                "/docs/api/batches",
                "/docs/api/stock-adjustments",
                "/docs/api/stock-transfers",
                "/docs/api/stocktakes",
                "/docs/api/price-lists",
                "/docs/api/bom-rows",
                "/docs/api/recipes",
                "/docs/api/operators",
                "/docs/api/factories",
                "/docs/api/additional-costs",
                "/docs/api/custom-fields",
            ],
            "reference": ["/api-reference", "/docs", "/docs/sdks"],
        }

    async def fetch_page(
        self, session: aiohttp.ClientSession, url: str
    ) -> tuple[str, str, str]:
        """Fetch a single page and return URL, content, and title."""
        try:
            logger.info(f"Fetching: {url}")
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")
                    title = soup.title.string if soup.title else "Untitled"
                    return url, content, title
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    self.failed_urls.append(url)
                    return url, "", ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self.failed_urls.append(url)
            return url, "", ""

    async def save_page(self, url: str, content: str, title: str) -> None:
        """Save page content to file system."""
        if not content:
            return

        # Create filename from URL path
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        if not path_parts:
            filename = "index.html"
        else:
            filename = f"{'_'.join(path_parts)}.html"

        file_path = self.output_dir / filename

        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
            logger.info(f"Saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")

    async def extract_links(self, content: str, base_url: str) -> list[str]:
        """Extract relevant documentation links from page content."""
        if not content:
            return []

        soup = BeautifulSoup(content, "html.parser")
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)

            # Only include documentation links
            if (
                any(pattern in full_url for pattern in ["/docs/", "/api-reference"])
                and full_url not in self.visited_urls
            ):
                links.append(full_url)

        return links

    async def crawl_section(
        self, session: aiohttp.ClientSession, urls: list[str]
    ) -> list[str]:
        """Crawl a section of documentation and return discovered links."""
        tasks = []
        for url_path in urls:
            full_url = urljoin(self.base_url, url_path)
            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                tasks.append(self.fetch_page(session, full_url))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks)
        discovered_links = []

        for url, content, title in results:
            if content:
                await self.save_page(url, content, title)
                new_links = await self.extract_links(content, url)
                discovered_links.extend(new_links)

        return discovered_links

    async def create_index(self) -> None:
        """Create an index of all downloaded documentation."""
        index_data = {
            "base_url": self.base_url,
            "downloaded_pages": len(list(self.output_dir.glob("*.html"))),
            "failed_urls": self.failed_urls,
            "sections": self.doc_sections,
        }

        index_path = self.output_dir / "index.json"
        async with aiofiles.open(index_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(index_data, indent=2))

        logger.info(f"Created index: {index_path}")

    async def crawl_all(self) -> None:
        """Main crawling function."""
        logger.info("Starting Katana API documentation crawl...")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Output directory: {self.output_dir}")

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Katana-OpenAPI-Client-Documentation-Crawler/1.0"},
        ) as session:
            # Crawl each section
            all_discovered_links = []

            for section_name, urls in self.doc_sections.items():
                logger.info(f"\n📚 Crawling {section_name} section...")
                discovered = await self.crawl_section(session, urls)
                all_discovered_links.extend(discovered)

            # Crawl discovered links (one level deep)
            if all_discovered_links:
                logger.info(
                    f"\n🔍 Crawling {len(all_discovered_links)} discovered links..."
                )
                unique_links = list(set(all_discovered_links))
                await self.crawl_section(session, unique_links)

        # Create index
        await self.create_index()

        # Summary
        total_files = len(list(self.output_dir.glob("*.html")))
        logger.info("\n✅ Crawl complete!")
        logger.info(f"📁 Downloaded {total_files} pages")
        logger.info(f"❌ Failed URLs: {len(self.failed_urls)}")
        logger.info(f"📍 Output directory: {self.output_dir}")


async def main():
    parser = argparse.ArgumentParser(description="Crawl Katana API documentation")
    parser.add_argument(
        "--base-url",
        default="https://developer.katanamrp.com",
        help="Base URL for Katana documentation",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/katana-api-reference",
        help="Output directory for downloaded documentation",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    crawler = KatanaDocsCrawler(args.base_url, args.output_dir)
    await crawler.crawl_all()


if __name__ == "__main__":
    asyncio.run(main())
