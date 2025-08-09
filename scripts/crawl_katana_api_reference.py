#!/usr/bin/env python3
"""
Katana API Reference Crawler

Specialized crawler for extracting sidebar navigation links from
Katana's README.io-based API documentation site.
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


class KatanaApiReferenceCrawler:
    def __init__(
        self,
        base_url: str = "https://developer.katanamrp.com",
        output_dir: str = "docs/katana-api-reference",
    ):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: set[str] = set()
        self.failed_urls: list[str] = []
        self.api_endpoints: list[dict[str, str]] = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Headers to mimic a real browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch_page(
        self, session: aiohttp.ClientSession, url: str
    ) -> tuple[str, str, str]:
        """Fetch a single page and return URL, content, and title."""
        try:
            logger.info(f"Fetching: {url}")
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")
                    title = soup.title.string if soup.title else "Untitled"
                    title_str = title.strip() if title else "Untitled"
                    return url, content, title_str
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
            # Add metadata at the top of the file
            metadata = f"""<!--
URL: {url}
Title: {title}
Downloaded: {asyncio.get_event_loop().time()}
-->
"""
            full_content = metadata + content

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(full_content)
            logger.info(f"Saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")

    def extract_api_links_from_content(self, content: str, base_url: str) -> list[str]:
        """Extract API reference links from page content."""
        if not content:
            return []

        soup = BeautifulSoup(content, "html.parser")
        api_links = []

        # Look for sidebar navigation or similar structures
        # README.io typically uses specific class patterns
        nav_selectors = [
            'nav a[href*="/reference/"]',
            '.sidebar a[href*="/reference/"]',
            '.navigation a[href*="/reference/"]',
            'a[href*="/reference/"]',
            ".rm-SidebarMenu a",
            '[data-testid="sidebar"] a',
            ".docs-sidebar a",
        ]

        for selector in nav_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get("href")
                if href and isinstance(href, str):
                    full_url = urljoin(base_url, href)
                    if "/reference/" in full_url and full_url not in api_links:
                        api_links.append(full_url)

                        # Extract endpoint info
                        text = link.get_text(strip=True)
                        if text:
                            self.api_endpoints.append(
                                {"title": text, "url": full_url, "path": href}
                            )

        # Also look for links in the main content that reference API endpoints
        content_links = soup.find_all("a", href=True)
        for link in content_links:
            if hasattr(link, "get"):
                href = link.get("href")
                if href and isinstance(href, str) and "/reference/" in href:
                    full_url = urljoin(base_url, href)
                    if full_url not in api_links:
                        api_links.append(full_url)

                        text = link.get_text(strip=True)
                        if text:
                            self.api_endpoints.append(
                                {"title": text, "url": full_url, "path": href}
                            )

        return api_links

    async def discover_api_structure(self, session: aiohttp.ClientSession) -> list[str]:
        """Discover the API documentation structure from the main reference page."""
        # Start with the known working reference URL
        main_reference_url = f"{self.base_url}/reference/api-introduction"

        logger.info(f"🔍 Discovering API structure from: {main_reference_url}")

        url, content, title = await self.fetch_page(session, main_reference_url)
        if content:
            await self.save_page(url, content, title)

            # Extract all API reference links
            api_links = self.extract_api_links_from_content(content, url)
            logger.info(f"📋 Discovered {len(api_links)} API reference links")

            # Also try to find a sitemap or API index
            sitemap_patterns = [
                f"{self.base_url}/sitemap.xml",
                f"{self.base_url}/docs/sitemap.xml",
                f"{self.base_url}/reference/sitemap.xml",
            ]

            for sitemap_url in sitemap_patterns:
                try:
                    (
                        sitemap_url_obj,
                        sitemap_content,
                        sitemap_title,
                    ) = await self.fetch_page(session, sitemap_url)
                    if sitemap_content and "xml" in sitemap_content.lower():
                        logger.info(f"📄 Found sitemap: {sitemap_url}")
                        await self.save_page(
                            sitemap_url, sitemap_content, sitemap_title
                        )
                except Exception as e:
                    logger.debug(f"No sitemap at {sitemap_url}: {e}")

            return api_links

        return []

    async def crawl_api_endpoints(
        self, session: aiohttp.ClientSession, api_links: list[str]
    ) -> None:
        """Crawl all discovered API endpoint documentation."""
        logger.info(f"📚 Crawling {len(api_links)} API endpoints...")

        # Limit concurrent requests to be respectful
        semaphore = asyncio.Semaphore(5)

        async def crawl_single_endpoint(url: str):
            async with semaphore:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    endpoint_url, content, title = await self.fetch_page(session, url)
                    if content:
                        await self.save_page(endpoint_url, content, title)

                        # Look for additional links in this page
                        more_links = self.extract_api_links_from_content(content, url)
                        return more_links
                return []

        # Crawl all discovered links
        tasks = [crawl_single_endpoint(url) for url in api_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect any additional links found
        additional_links = []
        for result in results:
            if isinstance(result, list):
                additional_links.extend(result)

        # Crawl second-level links if we found any new ones
        new_links = [link for link in additional_links if link not in self.visited_urls]
        if new_links:
            logger.info(f"🔗 Found {len(new_links)} additional links, crawling...")
            await self.crawl_api_endpoints(session, new_links)

    async def create_comprehensive_index(self) -> None:
        """Create a comprehensive index of all downloaded documentation."""
        # Deduplicate endpoints
        unique_endpoints = {}
        for endpoint in self.api_endpoints:
            url = endpoint["url"]
            if url not in unique_endpoints:
                unique_endpoints[url] = endpoint

        # Sort by title for better organization
        sorted_endpoints = sorted(unique_endpoints.values(), key=lambda x: x["title"])

        index_data = {
            "metadata": {
                "base_url": self.base_url,
                "total_pages_downloaded": len(list(self.output_dir.glob("*.html"))),
                "total_api_endpoints": len(sorted_endpoints),
                "failed_urls": self.failed_urls,
                "crawl_timestamp": asyncio.get_event_loop().time(),
            },
            "api_endpoints": sorted_endpoints,
            "endpoint_categories": self._categorize_endpoints(sorted_endpoints),
        }

        # Save main index
        index_path = self.output_dir / "api_reference_index.json"
        async with aiofiles.open(index_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(index_data, indent=2))

        # Create a simple markdown index too
        await self._create_markdown_index(sorted_endpoints)

        logger.info(f"📋 Created comprehensive index: {index_path}")

    def _categorize_endpoints(
        self, endpoints: list[dict[str, str]]
    ) -> dict[str, list[str]]:
        """Categorize endpoints by resource type."""
        categories: dict[str, list[str]] = {}

        for endpoint in endpoints:
            title = endpoint["title"].lower()
            path = endpoint["path"].lower()

            # Determine category based on title/path patterns
            if any(word in title or word in path for word in ["product", "variant"]):
                category = "Products & Variants"
            elif any(
                word in title or word in path for word in ["material", "bom", "recipe"]
            ):
                category = "Materials & BOMs"
            elif any(
                word in title or word in path for word in ["customer", "supplier"]
            ):
                category = "Customers & Suppliers"
            elif any(
                word in title or word in path for word in ["sales", "purchase", "order"]
            ):
                category = "Orders"
            elif any(
                word in title or word in path
                for word in ["inventory", "stock", "location"]
            ):
                category = "Inventory & Stock"
            elif any(
                word in title or word in path
                for word in ["manufacturing", "production"]
            ):
                category = "Manufacturing"
            elif any(
                word in title or word in path
                for word in ["auth", "api", "intro", "error"]
            ):
                category = "API Core"
            else:
                category = "Other"

            if category not in categories:
                categories[category] = []
            categories[category].append(endpoint["title"])

        return categories

    async def _create_markdown_index(self, endpoints: list[dict[str, str]]) -> None:
        """Create a markdown index for easier reading."""
        md_content = f"""# Katana API Reference Documentation Index

**Generated**: {asyncio.get_event_loop().time()}
**Base URL**: {self.base_url}
**Total Endpoints**: {len(endpoints)}

## API Endpoints

"""

        # Group by category
        categories = self._categorize_endpoints(endpoints)

        for category, endpoint_titles in categories.items():
            md_content += f"\n### {category}\n\n"

            # Find endpoints in this category
            category_endpoints = [
                ep for ep in endpoints if ep["title"] in endpoint_titles
            ]

            for endpoint in category_endpoints:
                md_content += f"- [{endpoint['title']}]({endpoint['url']})\n"

        md_content += """

## Files Downloaded

"""

        # List all downloaded files
        html_files = sorted(self.output_dir.glob("*.html"))
        for file_path in html_files:
            md_content += f"- `{file_path.name}`\n"

        md_path = self.output_dir / "README.md"
        async with aiofiles.open(md_path, "w", encoding="utf-8") as f:
            await f.write(md_content)

    async def crawl_all(self) -> None:
        """Main crawling function."""
        logger.info("🚀 Starting Katana API Reference crawl...")
        logger.info(f"🌐 Base URL: {self.base_url}")
        logger.info(f"📁 Output directory: {self.output_dir}")

        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=60, connect=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=self.headers
        ) as session:
            # Step 1: Discover API structure
            api_links = await self.discover_api_structure(session)

            if not api_links:
                logger.error("❌ Could not discover any API reference links!")
                return

            # Step 2: Crawl all API endpoints
            await self.crawl_api_endpoints(session, api_links)

        # Step 3: Create comprehensive index
        await self.create_comprehensive_index()

        # Summary
        total_files = len(list(self.output_dir.glob("*.html")))
        total_endpoints = len({ep["url"] for ep in self.api_endpoints})

        logger.info("\n✅ Crawl complete!")
        logger.info(f"📁 Downloaded {total_files} documentation pages")
        logger.info(f"🔗 Discovered {total_endpoints} unique API endpoints")
        logger.info(f"❌ Failed URLs: {len(self.failed_urls)}")
        logger.info(f"📍 Output directory: {self.output_dir}")
        logger.info("📋 Index files: api_reference_index.json, README.md")


async def main():
    parser = argparse.ArgumentParser(
        description="Crawl Katana API Reference documentation"
    )
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

    crawler = KatanaApiReferenceCrawler(args.base_url, args.output_dir)
    await crawler.crawl_all()


if __name__ == "__main__":
    asyncio.run(main())
