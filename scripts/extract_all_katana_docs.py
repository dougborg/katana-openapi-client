#!/usr/bin/env python3
"""
Comprehensive Katana API Documentation Extractor

This script combines crawling and extraction functionality to:
1. Discover all Katana API documentation pages
2. Download the content
3. Extract embedded OpenAPI specifications
4. Generate comprehensive documentation with real JSON examples
5. Clean up temporary files

Usage: python extract_all_katana_docs.py [output_dir]
"""

import asyncio
import html
import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
import mdformat
from bs4 import BeautifulSoup, Tag

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KatanaDocumentationExtractor:
    def __init__(
        self,
        base_url: str = "https://developer.katanamrp.com",
        output_dir: str = "docs/katana-api-comprehensive",
    ):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: set[str] = set()
        self.failed_urls: list[str] = []
        self.api_endpoints: list[dict[str, str]] = []
        self.openapi_spec: dict[str, Any] | None = None

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

    def extract_api_links_from_content(self, content: str, base_url: str) -> list[str]:
        """Extract API reference links from page content."""
        if not content:
            return []

        soup = BeautifulSoup(content, "html.parser")
        api_links = []

        # Look for sidebar navigation or similar structures
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

        return api_links

    async def discover_api_structure(self, session: aiohttp.ClientSession) -> list[str]:
        """Discover the API documentation structure from the main reference page."""
        main_reference_url = f"{self.base_url}/reference/api-introduction"
        logger.info(f"🔍 Discovering API structure from: {main_reference_url}")

        url, content, title = await self.fetch_page(session, main_reference_url)
        if content:
            # Extract OpenAPI spec if present
            if not self.openapi_spec:
                self.openapi_spec = self.extract_openapi_from_html(content)
                if self.openapi_spec:
                    logger.info(
                        f"📋 Found OpenAPI spec with {len(self.openapi_spec.get('paths', {}))} endpoints"
                    )

            # Extract all API reference links
            api_links = self.extract_api_links_from_content(content, url)
            logger.info(f"📋 Discovered {len(api_links)} API reference links")
            return api_links

        return []

    async def crawl_all_endpoints(
        self, session: aiohttp.ClientSession, api_links: list[str]
    ) -> list[tuple[str, str, str]]:
        """Crawl all discovered API endpoint documentation and return content."""
        logger.info(f"📚 Crawling {len(api_links)} API endpoints...")

        # Limit concurrent requests to be respectful
        semaphore = asyncio.Semaphore(5)
        all_pages = []

        async def crawl_single_endpoint(url: str):
            async with semaphore:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    endpoint_url, content, title = await self.fetch_page(session, url)
                    if content:
                        # Extract OpenAPI spec if we haven't found one yet
                        if not self.openapi_spec:
                            self.openapi_spec = self.extract_openapi_from_html(content)

                        return (endpoint_url, content, title)

                        # Look for additional links in this page
                        more_links = self.extract_api_links_from_content(content, url)
                        return (endpoint_url, content, title), more_links
                return None

        # Crawl all discovered links
        tasks = [crawl_single_endpoint(url) for url in api_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect pages and additional links
        additional_links = []
        for result in results:
            if isinstance(result, tuple) and len(result) == 3:
                # Single page result
                all_pages.append(result)
            elif isinstance(result, tuple) and len(result) == 2:
                # Page with additional links
                page_data, more_links = result
                all_pages.append(page_data)
                additional_links.extend(more_links)

        # Crawl second-level links if we found any new ones
        new_links = [link for link in additional_links if link not in self.visited_urls]
        if new_links:
            logger.info(f"🔗 Found {len(new_links)} additional links, crawling...")
            more_pages = await self.crawl_all_endpoints(session, new_links)
            all_pages.extend(more_pages)

        return all_pages

    def extract_openapi_from_html(self, html_content: str) -> dict[str, Any] | None:
        """Extract the embedded OpenAPI specification from README.io HTML."""
        # Look for the data-initial-props attribute
        match = re.search(r'data-initial-props="({.*?})"', html_content)
        if not match:
            return None

        try:
            # Decode HTML entities and parse JSON
            json_str = html.unescape(match.group(1))
            data = json.loads(json_str)
            return data.get("oasDefinition")
        except (json.JSONDecodeError, KeyError):
            return None

    def extract_content_from_html(self, html_content: str) -> str:
        """Extract meaningful content from HTML using specific README.io DOM structure."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Strategy: Extract comprehensive content for object pages, fallback to description for others

        # Check if this is an "object" documentation page by looking for attribute tables
        has_attribute_table = bool(
            soup.find("table") or soup.select("[data-testid*='table']")
        )
        is_object_page = "object" in html_content.lower() and has_attribute_table

        if is_object_page:
            return self.extract_full_object_content(soup)
        else:
            return self.extract_description_content(soup)

    def extract_full_object_content(self, soup: BeautifulSoup) -> str:
        """Extract comprehensive content for object documentation pages including tables."""
        content_parts = []

        # 1. Look for README.io main content area
        readme_content = soup.select_one(".rm-Markdown")
        if readme_content and isinstance(readme_content, Tag):
            # Remove navigation and UI elements
            for elem in readme_content.find_all(
                ["nav", "script", "style", ".rm-SidebarMenu"]
            ):
                elem.decompose()

            # Extract structured content
            content_parts.extend(self.extract_structured_content(readme_content))

        # 2. Fallback to main content area
        if not content_parts:
            main_content = soup.select_one("#content")
            if main_content and isinstance(main_content, Tag):
                # Remove navigation and UI elements
                for elem in main_content.find_all(
                    ["nav", "script", "style", "form", ".sidebar"]
                ):
                    elem.decompose()

                content_parts.extend(self.extract_structured_content(main_content))

        # Join all content parts
        full_content = (
            "\n\n".join(content_parts)
            if content_parts
            else "No meaningful content found"
        )
        return self.clean_extracted_content(full_content)

    def extract_structured_content(self, container: Tag) -> list[str]:
        """Extract structured content including headings, paragraphs, and tables."""
        content_parts = []

        # Process content in document order
        for element in container.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "table", "div"]
        ):
            if not isinstance(element, Tag):
                continue

            # Skip if this element is inside a table (we'll process tables separately)
            if element.find_parent("table"):
                continue

            element_content = self.process_content_element(element)
            if element_content:
                content_parts.append(element_content)

        return content_parts

    def process_content_element(self, element: Tag) -> str:
        """Process individual content elements (headings, paragraphs, tables)."""
        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            # Process headings
            heading_text = element.get_text(strip=True)
            if heading_text and not self.is_navigation_text(heading_text):
                level = int(element.name[1])
                return f"{'#' * level} {heading_text}"

        elif element.name == "p":
            # Process paragraphs
            para_text = element.get_text(strip=True)
            if (
                para_text
                and len(para_text) > 10
                and not self.is_navigation_text(para_text)
            ):
                return para_text

        elif element.name == "table":
            # Process tables (attribute tables are key for object docs)
            return self.extract_table_content(element)

        elif element.name == "div":
            # Process divs that might contain structured content
            div_text = element.get_text(strip=True)
            if (
                div_text
                and len(div_text) > 20
                and not self.is_navigation_text(div_text)
                and not element.find("table")
            ):  # Don't double-process table containers
                return div_text

        return ""

    def extract_table_content(self, table: Tag) -> str:
        """Extract table content in markdown format."""
        rows = []

        # Extract header row
        header_row = table.find("tr")
        if header_row and isinstance(header_row, Tag):
            headers = []
            for th in header_row.find_all(["th", "td"]):
                if isinstance(th, Tag):
                    header_text = th.get_text(strip=True)
                    headers.append(header_text if header_text else "")

            if headers:
                rows.append("| " + " | ".join(headers) + " |")
                rows.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Extract data rows
        for tr in table.find_all("tr")[1:]:  # Skip header row
            if isinstance(tr, Tag):
                cells = []
                for td in tr.find_all(["td", "th"]):
                    if isinstance(td, Tag):
                        cell_text = (
                            td.get_text(strip=True)
                            .replace("\n", " ")
                            .replace("|", "\\|")
                        )
                        cells.append(cell_text if cell_text else "")

                if cells:
                    rows.append("| " + " | ".join(cells) + " |")

        return "\n".join(rows) if rows else ""

    def extract_description_content(self, soup: BeautifulSoup) -> str:
        """Extract description content for non-object pages (original logic)."""
        # 1. Look for the main description in the content header
        content_header = soup.select_one("#content > header:first-child")
        if content_header and isinstance(content_header, Tag):
            # Remove navigation elements from header
            for nav_elem in content_header.find_all(
                ["nav", '[class*="nav"]', '[class*="breadcrumb"]']
            ):
                nav_elem.decompose()

            # Look for the main description paragraph/text
            desc_elements = content_header.find_all(["p", "div"])
            for desc_element in desc_elements:
                if isinstance(desc_element, Tag):
                    desc_text = desc_element.get_text(strip=True)
                    if (
                        desc_text
                        and len(desc_text) > 20
                        and not self.is_navigation_text(desc_text)
                    ):
                        return desc_text

            # If no specific element found, get all text but filter it
            header_text = content_header.get_text(strip=True, separator=" ")
            if header_text and not self.is_navigation_text(header_text):
                return header_text

        # 2. Look for README.io specific content areas
        readme_content = soup.select_one(".rm-Markdown")
        if readme_content and isinstance(readme_content, Tag):
            # Find the first meaningful paragraph that's not navigation
            paragraphs = readme_content.find_all("p")
            for p in paragraphs:
                if isinstance(p, Tag):
                    p_text = p.get_text(strip=True)
                    if (
                        p_text
                        and len(p_text) > 20
                        and not self.is_navigation_text(p_text)
                    ):
                        return p_text

        # 3. Look for specific description elements
        desc_selectors = [
            '[data-testid="description"]',
            ".endpoint-description",
            ".api-description",
        ]

        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element and isinstance(element, Tag):
                text = element.get_text(strip=True)
                if text and len(text) > 20 and not self.is_navigation_text(text):
                    return text

        # 4. Fallback: Look for any meaningful content in the main content area
        main_content = soup.select_one("#content")
        if main_content and isinstance(main_content, Tag):
            # Remove known navigation and UI elements
            for elem in main_content.find_all(["nav", "script", "style", "form"]):
                elem.decompose()

            # Find first substantial text content
            text_content = main_content.get_text(strip=True, separator=" ")
            if text_content:
                # Split into sentences and take the first meaningful one
                sentences = text_content.split(". ")
                for sentence in sentences:
                    stripped_sentence = sentence.strip()
                    if (
                        stripped_sentence
                        and len(stripped_sentence) > 30
                        and not self.is_navigation_text(stripped_sentence)
                        and not stripped_sentence.lower().startswith(
                            ("get", "post", "put", "delete", "patch")
                        )
                    ):
                        return (
                            stripped_sentence + "."
                            if not stripped_sentence.endswith(".")
                            else stripped_sentence
                        )

        return "No meaningful content found"

    def clean_extracted_content(self, content: str) -> str:
        """Clean up extracted content by removing excessive whitespace and duplicates."""
        if not content:
            return "No meaningful content found"

        # Split into lines and clean each line
        lines = content.split("\n")
        cleaned_lines = []
        seen_lines = set()

        for line in lines:
            cleaned_line = line.strip()
            # Skip empty lines and duplicates
            if cleaned_line and cleaned_line not in seen_lines:
                cleaned_lines.append(cleaned_line)
                seen_lines.add(cleaned_line)

        # Join lines and limit excessive newlines
        result = "\n".join(cleaned_lines)
        # Replace multiple consecutive newlines with double newlines
        result = re.sub(r"\n{3,}", "\n\n", result)

        return result if result else "No meaningful content found"

    def is_navigation_text(self, text: str) -> bool:
        """Check if text appears to be navigation or UI text."""
        text_lower = text.lower()
        nav_patterns = [
            "jump to content",
            "api reference",
            "knowledge base",
            "navigation",
            "menu",
            "sidebar",
            "breadcrumb",
            "language",
            "shell",
            "node",
            "go",
            "ruby",
            "python",
            "credentials",
            "bearer",
            "copy",
            "show",
            "hide",
            "search",
            "login",
            "sign up",
            "documentation",
            "getting started",
            "guides",
            "tutorials",
        ]

        # Check if text is just navigation keywords
        for pattern in nav_patterns:
            if pattern in text_lower:
                return True

        return len(text) < 20 and any(
            word in text_lower for word in ["api", "docs", "home", "back"]
        )

    def filter_navigation_text(self, text: str) -> str:
        """Filter out navigation text from larger content blocks."""
        lines = text.split("\n")
        filtered_lines = []

        for current_line in lines:
            stripped_line = current_line.strip()
            if stripped_line and not self.is_navigation_text(stripped_line):
                filtered_lines.append(stripped_line)

        return "\n\n".join(filtered_lines)

    def format_markdown(self, content: str) -> str:
        """Format markdown content using mdformat with sentence-per-line formatting."""
        try:
            # Convert to sentence-per-line format
            content_with_sentences = self.convert_to_sentence_per_line(content)

            # Use mdformat to clean up the markdown
            formatted = mdformat.text(content_with_sentences)
            return formatted
        except Exception as e:
            logger.warning(f"Failed to format markdown: {e}")
            return content

    def convert_to_sentence_per_line(self, content: str) -> str:
        """Convert content to sentence-per-line format."""
        import re

        # Split content into lines
        lines = content.split("\n")
        result_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines, headers, code blocks, lists
            if (
                not stripped
                or stripped.startswith("#")
                or stripped.startswith("```")
                or stripped.startswith("- ")
                or stripped.startswith("* ")
                or stripped.startswith("1.")
                or "```" in stripped
            ):
                result_lines.append(line)
                continue

            # For description content, split on sentence boundaries
            # Match sentence endings: . ! ? followed by space or end of string
            # But avoid splitting on abbreviations, URLs, etc.
            sentence_list = re.split(r"(?<=[.!?])\s+(?=[A-Z])", stripped)

            for sentence in sentence_list:
                stripped_sentence = sentence.strip()
                if stripped_sentence:
                    # Preserve indentation for the first sentence, use same level for others
                    indent = len(line) - len(line.lstrip())
                    result_lines.append(" " * indent + stripped_sentence)

        return "\n".join(result_lines)

    def url_to_endpoint_key(self, url: str) -> str | None:
        """Convert a documentation URL to an endpoint key for mapping lookup."""
        # Extract the endpoint identifier from the URL
        # e.g., https://developer.katanamrp.com/reference/list-all-products -> list-all-products
        path = urlparse(url).path
        if "/reference/" in path:
            return path.split("/reference/")[-1]
        return None

    def generate_endpoint_mapping(self) -> dict[str, tuple[str, str]]:
        """Generate comprehensive endpoint mapping from OpenAPI spec."""
        if not self.openapi_spec or "paths" not in self.openapi_spec:
            return {}

        # Comprehensive mapping for all known endpoints
        endpoint_patterns = {
            # Additional Costs
            "getadditionalcosts": ("/additional_costs", "get"),
            # Batches
            "createbatch": ("/batches", "post"),
            "getbatchstock": ("/batch_stocks", "get"),
            "updatebatchstock": ("/batch_stocks/{batch_id}", "patch"),
            # BOM Rows
            "batchcreatebomrows": ("/bom_rows/batch/create", "post"),
            "getallbomrows": ("/bom_rows", "get"),
            "createbomrow": ("/bom_rows", "post"),
            "updatebomrow": ("/bom_rows/{id}", "patch"),
            "deletebomrow": ("/bom_rows/{id}", "delete"),
            # Customers
            "create-customer": ("/customers", "post"),
            "list-all-customers": ("/customers", "get"),
            "updatecustomer": ("/customers/{id}", "patch"),
            "deletecustomer": ("/customers/{id}", "delete"),
            # Customer Addresses
            "getcustomeraddresses": ("/customer_addresses", "get"),
            "createcustomeraddress": ("/customer_addresses", "post"),
            "updatecustomeraddress": ("/customer_addresses/{id}", "patch"),
            "deletecustomeraddress": ("/customer_addresses/{id}", "delete"),
            # Custom Fields
            "getcustomfieldscollections": ("/custom_fields_collections", "get"),
            # Storage Bins
            "getallstoragebins": ("/bin_locations", "get"),
            "updatedefaultstoragebin": ("/bin_locations/{id}", "patch"),
            "deletestoragebin": ("/bin_locations/{id}", "delete"),
            # Factory
            "getfactory": ("/factory", "get"),
            # Inventory
            "list-current-inventory": ("/inventory", "get"),
            "update-reorder-point": ("/inventory_reorder_points", "patch"),
            "createinventorysafetystocklevel": (
                "/inventory_safety_stock_levels",
                "post",
            ),
            "getallnegativestock": ("/inventory/negative_stock", "get"),
            "list-all-inventory-movements": ("/inventory_movements", "get"),
            # Locations
            "list-all-locations": ("/locations", "get"),
            "getlocation": ("/locations/{id}", "get"),
            # Manufacturing Orders
            "createmanufacturingorder": ("/manufacturing_orders", "post"),
            "getallmanufacturingorders": ("/manufacturing_orders", "get"),
            "getmanufacturingorder": ("/manufacturing_orders/{id}", "get"),
            "updatemanufacturingorder": ("/manufacturing_orders/{id}", "patch"),
            "deletemanufacturingorder": ("/manufacturing_orders/{id}", "delete"),
            "maketoordermanufacturingorder": (
                "/manufacturing_orders/{id}/make_to_order",
                "patch",
            ),
            "unlinkmanufacturingorder": ("/manufacturing_orders/{id}/unlink", "patch"),
            # Manufacturing Order Productions
            "getallmanufacturingorderproductions": (
                "/manufacturing_order_productions",
                "get",
            ),
            "createmanufacturingorderproduction": (
                "/manufacturing_order_productions",
                "post",
            ),
            "getmanufacturingorderproduction": (
                "/manufacturing_order_productions/{id}",
                "get",
            ),
            "updatemanufacturingorderproduction": (
                "/manufacturing_order_productions/{id}",
                "patch",
            ),
            "deletemanufacturingorderproduction": (
                "/manufacturing_order_productions/{id}",
                "delete",
            ),
            "updatemanufacturingorderproductioningredient": (
                "/manufacturing_order_production_ingredients/{id}",
                "patch",
            ),
            # Manufacturing Order Operations
            "createmanufacturingorderoperationrow": (
                "/manufacturing_order_operation_rows",
                "post",
            ),
            "getallmanufacturingorderoperationrows": (
                "/manufacturing_order_operation_rows",
                "get",
            ),
            "getmanufacturingorderoperationrow": (
                "/manufacturing_order_operation_rows/{id}",
                "get",
            ),
            "updatemanufacturingorderoperationrow": (
                "/manufacturing_order_operation_rows/{id}",
                "patch",
            ),
            "deletemanufacturingorderoperationrow": (
                "/manufacturing_order_operation_rows/{id}",
                "delete",
            ),
            # Manufacturing Order Recipes
            "createmanufacturingorderreciperows": (
                "/manufacturing_order_recipe_rows",
                "post",
            ),
            "getallmanufacturingorderreciperows": (
                "/manufacturing_order_recipe_rows",
                "get",
            ),
            "getmanufacturingorderreciperow": (
                "/manufacturing_order_recipe_rows/{id}",
                "get",
            ),
            "updatemanufacturingorderreciperows": (
                "/manufacturing_order_recipe_rows/{id}",
                "patch",
            ),
            "deletemanufacturingorderreciperow": (
                "/manufacturing_order_recipe_rows/{id}",
                "delete",
            ),
            # Materials
            "creatematerial": ("/materials", "post"),
            "getallmaterials": ("/materials", "get"),
            "getmaterial": ("/materials/{id}", "get"),
            "updatematerial": ("/materials/{id}", "patch"),
            "deletematerial": ("/materials/{id}", "delete"),
            # Operators
            "getoperators": ("/operators", "get"),
            # Purchase Order Recipe Rows
            "createpurchaseorderreciperow": ("/purchase_order_recipe_rows", "post"),
            "getallpurchaseorderreciperows": ("/purchase_order_recipe_rows", "get"),
            "getpurchaseorderreciperow": ("/purchase_order_recipe_rows/{id}", "get"),
            "updatepurchaseorderreciperow": (
                "/purchase_order_recipe_rows/{id}",
                "patch",
            ),
            "deletepurchaseorderreciperow": (
                "/purchase_order_recipe_rows/{id}",
                "delete",
            ),
            # Price Lists
            "createpricelist": ("/price_lists", "post"),
            "getallpricelists": ("/price_lists", "get"),
            "updatepricelist": ("/price_lists/{id}", "patch"),
            "deletepricelist": ("/price_lists/{id}", "delete"),
            "getpricelist": ("/price_lists/{id}", "get"),
            # Price List Rows
            "createpricelistrow": ("/price_list_rows", "post"),
            "getallpricelistrows": ("/price_list_rows", "get"),
            "updatepricelistrow": ("/price_list_rows/{id}", "patch"),
            "deletepricelistrow": ("/price_list_rows/{id}", "delete"),
            "getpricelistrow": ("/price_list_rows/{id}", "get"),
            # Price List Customers
            "createpricelistcustomer": ("/price_list_customers", "post"),
            "getallpricelistcustomers": ("/price_list_customers", "get"),
            "updatepricelistcustomer": ("/price_list_customers/{id}", "patch"),
            "deletepricelistcustomer": ("/price_list_customers/{id}", "delete"),
            "getpricelistcustomer": ("/price_list_customers/{id}", "get"),
            # Products
            "create-product": ("/products", "post"),
            "list-all-products": ("/products", "get"),
            "getproduct": ("/products/{id}", "get"),
            "updateproduct": ("/products/{id}", "patch"),
            "deleteproduct": ("/products/{id}", "delete"),
            # Product Operations
            "createproductoperationrows": ("/product_operation_rows", "post"),
            "getallproductoperationrows": ("/product_operation_rows", "get"),
            "updateproductoperationrow": ("/product_operation_rows/{id}", "patch"),
            "deleteproductoperationrow": ("/product_operation_rows/{id}", "delete"),
            "rerankproductoperation": ("/product_operation_rows/{id}/rerank", "patch"),
            # Purchase Orders
            "createpurchaseorder": ("/purchase_orders", "post"),
            "findpurchaseorders": ("/purchase_orders", "get"),
            "getpurchaseorder": ("/purchase_orders/{id}", "get"),
            "updatepurchaseorder": ("/purchase_orders/{id}", "patch"),
            "deletepurchaseorder": ("/purchase_orders/{id}", "delete"),
            "receivepurchaseorder": ("/purchase_orders/{id}/receive", "post"),
            # Purchase Order Additional Cost Rows
            "createpoadditionalcostrow": (
                "/purchase_order_additional_cost_rows",
                "post",
            ),
            "getpurchaseorderadditionalcostrows": (
                "/purchase_order_additional_cost_rows",
                "get",
            ),
            "getpoadditionalcostrow": (
                "/purchase_order_additional_cost_rows/{id}",
                "get",
            ),
            "updateadditionalcostrow": (
                "/purchase_order_additional_cost_rows/{id}",
                "patch",
            ),
            "deletepoadditionalcost": (
                "/purchase_order_additional_cost_rows/{id}",
                "delete",
            ),
            # Purchase Order Rows
            "createpurchaseorderrow": ("/purchase_order_rows", "post"),
            "getallpurchaseorderrows": ("/purchase_order_rows", "get"),
            "getpurchaseorderrow": ("/purchase_order_rows/{id}", "get"),
            "updatepurchaseorderrow": ("/purchase_order_rows/{id}", "patch"),
            "deletepurchaseorderrow": ("/purchase_order_rows/{id}", "delete"),
            # Purchase Order Accounting Metadata
            "getallpurchaseorderaccountingmetadata": (
                "/purchase_order_accounting_metadata",
                "get",
            ),
            # Recipes
            "createrecipes": ("/recipe_rows", "post"),
            "getallrecipes": ("/recipe_rows", "get"),
            "updatereciperow": ("/recipe_rows/{id}", "patch"),
            "deletereciperow": ("/recipe_rows/{id}", "delete"),
            # Sales Orders
            "create-sales-order": ("/sales_orders", "post"),
            "list-all-sales-orders": ("/sales_orders", "get"),
            "retrieve-sales-order": ("/sales_orders/{id}", "get"),
            "update-sales-order": ("/sales_orders/{id}", "patch"),
            "delete-sales-order": ("/sales_orders/{id}", "delete"),
            "getreturnableitems": ("/sales_orders/{id}/returnable_items", "get"),
            # Sales Order Addresses
            "getsalesorderaddresses": ("/sales_order_addresses", "get"),
            "create-sales-order-address": ("/sales_order_addresses", "post"),
            "update-sales-order-address": ("/sales_order_addresses/{id}", "patch"),
            "delete-sales-order-address": ("/sales_order_addresses/{id}", "delete"),
            # Sales Order Fulfillments
            "create-sales-order-fulfillment": ("/sales_order_fulfillments", "post"),
            "list-all-sales-order-fulfillments": ("/sales_order_fulfillments", "get"),
            "retrieve-sales-order-fulfillment": (
                "/sales_order_fulfillments/{id}",
                "get",
            ),
            "update-sales-order-fulfillment": (
                "/sales_order_fulfillments/{id}",
                "patch",
            ),
            "delete-sales-order-fulfillment": (
                "/sales_order_fulfillments/{id}",
                "delete",
            ),
            # Sales Order Rows
            "getallsalesorderrows": ("/sales_order_rows", "get"),
            "create-sales-order-row": ("/sales_order_rows", "post"),
            "retrieve-sales-order-row": ("/sales_order_rows/{id}", "get"),
            "update-sales-order-row": ("/sales_order_rows/{id}", "patch"),
            "delete-sales-order-row": ("/sales_order_rows/{id}", "delete"),
            # Sales Order Accounting Metadata
            "getallsalesorderaccountingmetadata": (
                "/sales_order_accounting_metadata",
                "get",
            ),
            # Shipping Fees
            "addshippingfee": ("/shipping_fees", "post"),
            "getallshippingfees": ("/shipping_fees", "get"),
            "getshippingfee": ("/shipping_fees/{id}", "get"),
            "updateshippingfee": ("/shipping_fees/{id}", "patch"),
            "deleteshippingfee": ("/shipping_fees/{id}", "delete"),
            # Sales Returns
            "createsalesreturn": ("/sales_returns", "post"),
            "getallsalesreturns": ("/sales_returns", "get"),
            "getsalesreturn": ("/sales_returns/{id}", "get"),
            "updatesalesreturn": ("/sales_returns/{id}", "patch"),
            "deletesalesreturn": ("/sales_returns/{id}", "delete"),
            "getreturnreasons": ("/sales_returns/return_reasons", "get"),
            # Sales Return Rows
            "createsalesreturnrow": ("/sales_return_rows", "post"),
            "getallsalesreturnrows": ("/sales_return_rows", "get"),
            "getsalesreturnrow": ("/sales_return_rows/{id}", "get"),
            "updatesalesreturnrow": ("/sales_return_rows/{id}", "patch"),
            "deletesalesreturnrow": ("/sales_return_rows/{id}", "delete"),
            "getsalesreturnrowunassignedbatchtransactions": (
                "/sales_return_rows/{id}/unassigned_batch_transactions",
                "get",
            ),
            # Serial Numbers
            "getserialnumbers": ("/serial_numbers", "get"),
            "createserialnumbers": ("/serial_numbers", "post"),
            "deleteserialnumbers": ("/serial_numbers/{id}", "delete"),
            # Serial Number Stock
            "getserialnumberstock": ("/serial_number_stock", "get"),
            # Stock Adjustments
            "createstockadjustment": ("/stock_adjustments", "post"),
            "findstockadjustments": ("/stock_adjustments", "get"),
            "updatestockadjustment": ("/stock_adjustments/{id}", "patch"),
            "deletestockadjustment": ("/stock_adjustments/{id}", "delete"),
            # Stock Transfers
            "createstocktransfer": ("/stock_transfers", "post"),
            "findstocktransfers": ("/stock_transfers", "get"),
            "updatestocktransfer": ("/stock_transfers/{id}", "patch"),
            "deletestocktransfer": ("/stock_transfers/{id}", "delete"),
            "updatestocktransferstatus": ("/stock_transfers/{id}/status", "patch"),
            # Stocktakes
            "createstocktake": ("/stocktakes", "post"),
            "findstocktakes": ("/stocktakes", "get"),
            "updatestocktakebyid": ("/stocktakes/{id}", "patch"),
            "deletestocktakebyid": ("/stocktakes/{id}", "delete"),
            # Stocktake Rows
            "createstocktakerows": ("/stocktake_rows", "post"),
            "findstocktakerows": ("/stocktake_rows", "get"),
            "updatestocktakerowbyid": ("/stocktake_rows/{id}", "patch"),
            "deletestocktakerowbyid": ("/stocktake_rows/{id}", "delete"),
            # Suppliers
            "create-supplier": ("/suppliers", "post"),
            "list-all-suppliers": ("/suppliers", "get"),
            "updatesupplier": ("/suppliers/{id}", "patch"),
            "deletesupplier": ("/suppliers/{id}", "delete"),
            # Supplier Addresses
            "getsupplieraddresses": ("/supplier_addresses", "get"),
            "createsupplieraddress": ("/supplier_addresses", "post"),
            "updatesupplieraddress": ("/supplier_addresses/{id}", "patch"),
            "deletesupplieraddress": ("/supplier_addresses/{id}", "delete"),
            # Tax Rates
            "create-tax-rate": ("/tax_rates", "post"),
            "list-all-tax-rates": ("/tax_rates", "get"),
            # Users
            "getallusers": ("/users", "get"),
            # Variants
            "create-variant": ("/variants", "post"),
            "list-all-variants": ("/variants", "get"),
            "getvariant": ("/variants/{id}", "get"),
            "updatevariant": ("/variants/{id}", "patch"),
            "deletevariant": ("/variants/{id}", "delete"),
            "linkvariantdefaultstoragebins": (
                "/variants/{id}/default_storage_bins",
                "post",
            ),
            "unlinkvariantdefaultstoragebins": (
                "/variants/{id}/default_storage_bins",
                "delete",
            ),
            # Webhooks
            "createwebhook": ("/webhooks", "post"),
            "getallwebhooks": ("/webhooks", "get"),
            "getwebhook": ("/webhooks/{id}", "get"),
            "updatewebhook": ("/webhooks/{id}", "patch"),
            "deletewebhook": ("/webhooks/{id}", "delete"),
            "export-webhook-logs": ("/webhooks/{id}/logs/export", "post"),
            # Services
            "getallservices": ("/services", "get"),
            "createservice": ("/services", "post"),
            "getservice": ("/services/{id}", "get"),
            "updateservice": ("/services/{id}", "patch"),
            "deleteservice": ("/services/{id}", "delete"),
        }

        return endpoint_patterns

    def find_endpoint_in_openapi(self, file_url: str) -> dict[str, Any] | None:
        """Find the corresponding endpoint in OpenAPI spec based on URL path."""
        if not self.openapi_spec or "paths" not in self.openapi_spec:
            return None

        # Extract endpoint info from URL path
        parsed = urlparse(file_url)
        path_parts = [p for p in parsed.path.split("/") if p]

        if not path_parts or "reference" not in path_parts:
            return None

        # Get the last part after reference
        try:
            ref_index = path_parts.index("reference")
            if ref_index + 1 < len(path_parts):
                endpoint_slug = path_parts[ref_index + 1]
            else:
                return None
        except ValueError:
            return None

        # Get comprehensive endpoint mapping
        endpoint_mapping = self.generate_endpoint_mapping()

        if endpoint_slug in endpoint_mapping:
            path, method = endpoint_mapping[endpoint_slug]
            return self.openapi_spec["paths"].get(path, {}).get(method)

        return None

    def create_enhanced_documentation(
        self, url: str, html_content: str, title: str
    ) -> str:
        """Create comprehensive documentation combining HTML content and OpenAPI examples."""

        # Extract basic content
        basic_content = self.extract_content_from_html(html_content)

        # Try to find corresponding OpenAPI endpoint
        endpoint_spec = (
            self.find_endpoint_in_openapi(url) if self.openapi_spec else None
        )

        # Build enhanced documentation
        doc_parts = [f"# {title}\n\n"]

        # Add HTTP method and endpoint prominently if we have OpenAPI spec
        http_method_added = False
        if endpoint_spec:
            # Get HTTP method and path from the endpoint mapping
            endpoint_key = self.url_to_endpoint_key(url)
            endpoint_mapping = self.generate_endpoint_mapping()
            if endpoint_key and endpoint_key in endpoint_mapping:
                path, method = endpoint_mapping[endpoint_key]
                doc_parts.append(
                    f"**{method.upper()}** `https://api.katanamrp.com/v1{path}`\n\n"
                )
                http_method_added = True

        # Add basic description only if it doesn't duplicate method/URL info
        if basic_content and basic_content != "No meaningful content found":
            # Filter out basic content that just repeats method and URL information
            content_lower = basic_content.lower()
            if not (
                any(
                    method in content_lower
                    for method in ["get", "post", "put", "delete", "patch"]
                )
                and "api.katanamrp.com" in content_lower
            ):
                doc_parts.append(basic_content)
                doc_parts.append("\n\n")
            elif not http_method_added:
                # If we couldn't add method from OpenAPI but basic content has it, use basic content
                doc_parts.append(basic_content)
                doc_parts.append("\n\n")

        if endpoint_spec:
            doc_parts.append("## API Specification Details\n\n")

            # Add endpoint summary and description
            if "summary" in endpoint_spec:
                doc_parts.append(f"**Summary:** {endpoint_spec['summary']}\n")

            if "description" in endpoint_spec:
                doc_parts.append(f"**Description:** {endpoint_spec['description']}\n\n")

            # Add parameters first (query params, path params, headers)
            parameters = endpoint_spec.get("parameters", [])
            if parameters:
                doc_parts.append("### Parameters\n\n")
                for param in parameters:
                    param_info = f"- **{param.get('name', 'unknown')}** ({param.get('in', 'unknown')})"
                    if param.get("required"):
                        param_info += " *required*"
                    if "description" in param:
                        param_info += f": {param['description']}"
                    doc_parts.append(param_info + "\n")
                doc_parts.append("\n")

            # Add request body/payload for POST/PUT/PATCH operations
            request_body = endpoint_spec.get("requestBody", {})
            if request_body:
                content_data = request_body.get("content", {}).get(
                    "application/json", {}
                )

                if "schema" in content_data:
                    doc_parts.append("### Request Schema\n\n")
                    doc_parts.append(
                        f"```json\n{json.dumps(content_data['schema'], indent=2)}\n```\n\n"
                    )

                if "example" in content_data:
                    doc_parts.append("### Request Example\n\n")
                    doc_parts.append(
                        f"```json\n{json.dumps(content_data['example'], indent=2)}\n```\n\n"
                    )

            # Add response examples (success first, then errors)
            responses = endpoint_spec.get("responses", {})
            if responses:
                doc_parts.append("### Response Examples\n\n")

                # Sort responses: success codes (2xx) first, then errors
                sorted_responses = sorted(
                    responses.items(),
                    key=lambda x: (
                        0 if x[0].startswith("2") else 1,  # Success codes first
                        int(x[0]) if x[0].isdigit() else 999,  # Then by status code
                    ),
                )

                for status_code, response_data in sorted_responses:
                    content_data = response_data.get("content", {}).get(
                        "application/json", {}
                    )
                    if "example" in content_data:
                        doc_parts.append(f"#### {status_code} Response\n\n")
                        if "description" in response_data:
                            doc_parts.append(f"{response_data['description']}\n\n")
                        doc_parts.append(
                            f"```json\n{json.dumps(content_data['example'], indent=2)}\n```\n\n"
                        )

        return "".join(doc_parts)

    async def process_all_pages(self, pages: list[tuple[str, str, str]]) -> None:
        """Process all crawled pages and generate documentation."""
        logger.info(f"📝 Processing {len(pages)} pages into documentation...")

        processed_count = 0
        total_size_before = 0
        total_size_after = 0

        for url, html_content, title in pages:
            try:
                total_size_before += len(html_content)

                # Create enhanced documentation
                enhanced_doc = self.create_enhanced_documentation(
                    url, html_content, title
                )

                # Format the markdown content
                formatted_doc = self.format_markdown(enhanced_doc)

                # Create filename from URL path
                parsed = urlparse(url)
                path_parts = [p for p in parsed.path.split("/") if p]

                if not path_parts:
                    filename = "index.md"
                else:
                    # Get the part after 'reference'
                    try:
                        ref_index = path_parts.index("reference")
                        if ref_index + 1 < len(path_parts):
                            filename = f"{path_parts[ref_index + 1]}.md"
                        else:
                            filename = f"{'_'.join(path_parts)}.md"
                    except ValueError:
                        filename = f"{'_'.join(path_parts)}.md"

                # Write to markdown file
                output_file = self.output_dir / filename
                async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
                    await f.write(formatted_doc)

                total_size_after += len(formatted_doc)
                processed_count += 1

                logger.info(f"Processed {filename} ({len(formatted_doc):,} chars)")

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")

        # Save the OpenAPI specification
        if self.openapi_spec:
            openapi_file = self.output_dir / "openapi-spec.json"
            async with aiofiles.open(openapi_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(self.openapi_spec, indent=2))
            logger.info(f"Saved OpenAPI spec: {openapi_file}")

        # Summary
        size_reduction = (
            ((total_size_before - total_size_after) / total_size_before) * 100
            if total_size_before > 0
            else 0
        )
        logger.info("\n=== Processing Complete ===")
        logger.info(f"Files processed: {processed_count}")
        logger.info(f"Total size: {total_size_before:,} -> {total_size_after:,} bytes")
        logger.info(f"Size reduction: {size_reduction:.1f}%")

        if self.openapi_spec:
            logger.info(
                f"OpenAPI spec: {len(self.openapi_spec.get('paths', {}))} endpoints"
            )

    async def extract_complete_documentation(
        self, focus_pages: list[str] | None = None
    ) -> None:
        """Main method to extract complete Katana API documentation.

        Args:
            focus_pages: Optional list of specific page names to extract (e.g., ['list-all-products'])
        """
        async with aiohttp.ClientSession() as session:
            # Discover API structure
            api_links = await self.discover_api_structure(session)

            if not api_links:
                logger.error("❌ No API links discovered")
                return

            # Filter links if focus_pages is specified
            if focus_pages:
                filtered_links = []
                for link in api_links:
                    # Extract page name from URL (last part of path)
                    page_name = link.split("/")[-1]
                    if any(focus_page in page_name for focus_page in focus_pages):
                        filtered_links.append(link)
                        logger.info(f"🎯 Including page: {page_name}")

                if not filtered_links:
                    logger.error(f"❌ No pages found matching: {focus_pages}")
                    return

                api_links = filtered_links
                logger.info(f"🎯 Filtered to {len(api_links)} pages")

            # Crawl all pages
            pages = await self.crawl_all_endpoints(session, api_links)

            if not pages:
                logger.error("❌ No pages crawled successfully")
                return

            # Process all pages into documentation
            await self.process_all_pages(pages)

            # Create summary
            await self.create_summary()

    async def create_summary(self) -> None:
        """Create a summary README for the generated documentation."""
        summary_content = f"""# Comprehensive Katana API Documentation

This directory contains complete documentation for the Katana Manufacturing ERP API, extracted from {self.base_url}.

## Content Summary

- **Total pages processed**: {len(list(self.output_dir.glob("*.md")))}
- **OpenAPI specification**: {"✅ Included" if self.openapi_spec else "❌ Not found"}
- **API endpoints**: {len(self.openapi_spec.get("paths", {})) if self.openapi_spec else "Unknown"}
- **Failed URLs**: {len(self.failed_urls)}

## Files

### Documentation Pages
"""

        # List all markdown files
        md_files = sorted(self.output_dir.glob("*.md"))
        for md_file in md_files:
            if md_file.name != "README.md":
                summary_content += (
                    f"- **{md_file.name}**: {md_file.stat().st_size:,} bytes\n"
                )

        if self.openapi_spec:
            summary_content += f"\n### OpenAPI Specification\n- **openapi-spec.json**: Complete API specification with {len(self.openapi_spec.get('paths', {}))} endpoints\n"

        if self.failed_urls:
            summary_content += f"\n### Failed URLs ({len(self.failed_urls)})\n"
            for url in self.failed_urls:
                summary_content += f"- {url}\n"

        summary_content += f"""
## Extraction Details

- **Base URL**: {self.base_url}
- **Extraction method**: Combined crawling and OpenAPI spec extraction
- **Content source**: README.io documentation platform with embedded JSON data

This documentation is optimized for AI/LLM analysis and includes:
- Static content descriptions
- Complete OpenAPI specifications with real JSON examples
- Schema definitions and validation rules
- Request/response examples for all endpoints
"""

        readme_path = self.output_dir / "README.md"

        # Format the summary content before writing
        formatted_summary = self.format_markdown(summary_content)

        async with aiofiles.open(readme_path, "w", encoding="utf-8") as f:
            await f.write(formatted_summary)

        logger.info(f"📋 Created summary: {readme_path}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract Katana API documentation")
    parser.add_argument(
        "--output-dir",
        default="docs/katana-api-comprehensive",
        help="Output directory for documentation",
    )
    parser.add_argument(
        "--pages",
        nargs="*",
        help="Specific pages to extract (e.g., 'list-all-products' 'create-customer')",
    )

    args = parser.parse_args()

    logger.info("🚀 Starting comprehensive Katana API documentation extraction")
    logger.info(f"📁 Output directory: {args.output_dir}")

    if args.pages:
        logger.info(f"🎯 Focusing on specific pages: {', '.join(args.pages)}")

    extractor = KatanaDocumentationExtractor(output_dir=args.output_dir)
    await extractor.extract_complete_documentation(focus_pages=args.pages)

    logger.info("✅ Documentation extraction complete!")


if __name__ == "__main__":
    asyncio.run(main())
