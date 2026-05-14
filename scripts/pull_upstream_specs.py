#!/usr/bin/env python3
"""Refresh the upstream Katana OpenAPI specs.

Pulls two complementary upstream sources and writes them to
``docs/upstream-specs/``, normalized through the same YAML formatter
(``yaml.safe_dump``, ``sort_keys=True``) so they diff cleanly against
each other and against our local spec at ``docs/katana-openapi.yaml``.

| Output file | Source | What it has | What it lacks |
| --- | --- | --- | --- |
| ``live-gateway.yaml`` | ``https://api.katanamrp.com/v1/openapi.json`` | Canonical request DTOs, paths, filter-param enums — what the gateway actually validates against | No response shapes — every ``200`` is just ``{description: "..."}`` |
| ``readme-portal.yaml`` | ``<script id="ssr-props">`` on a reference page at ``https://developer.katanamrp.com/reference/<slug>``, at ``document.api.schema`` | Inline **response examples** (real JSON payloads, copy-pasted from real responses by the docs team) | Slightly behind the live gateway on path coverage; no component schemas |

Together they're the inputs for our three audit tools:

- ``poe audit-spec`` compares local request DTOs against ``live-gateway.yaml``.
- ``poe validate-examples`` checks local inline examples for internal
  consistency.
- ``poe validate-response-examples`` validates the response examples
  inside ``readme-portal.yaml`` against our local response schemas.

Run as ``poe refresh-upstream-spec``. Idempotent — overwrites both
output files in place.

How the README.io slug is derived (no hard-coding):

1. Fetch any reference page (cheap one — ``api-introduction``) to read
   the public Algolia search config from its embedded ``<script>``
   blocks.
2. Query Algolia for a single ``type: "endpoint"`` hit (only
   endpoint-type pages embed the OAS in their ``ssr-props``; index/blog
   pages don't).
3. Fetch that endpoint page, pull the OAS from ``ssr-props``.

This keeps the script slug-agnostic — Katana can rename or reorganize
any individual page without breaking the refresh, as long as Algolia
search and the README.io ``ssr-props`` mechanism keep working.

History: this file used to drive a BeautifulSoup-based per-endpoint
scrape that produced ``.md`` files in
``docs/katana-api-comprehensive/``. That approach broke when README.io
migrated to a JS-rendered SPA. Replacing per-page HTML extraction with
a single ``ssr-props`` JSON pull (which carries the structured spec
directly, including response examples) is more reliable and gives us
better data — we now compare against a real OpenAPI spec instead of
grepping JSON code blocks out of markdown.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp
import yaml
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "upstream-specs"

LIVE_OPENAPI_SPEC_URL = "https://api.katanamrp.com/v1/openapi.json"
README_PORTAL_URL = "https://developer.katanamrp.com"
# Stable, content-light page used to extract Algolia search config. The
# slug is unlikely to change (every README.io project has it). The page
# *itself* doesn't have the OAS embedded — we use it for config only.
README_CONFIG_PAGE = f"{README_PORTAL_URL}/reference/api-introduction"

# Fallback slugs to try directly if Algolia lookup fails. They're known to
# embed the OAS as of 2026-04-28; widely-implemented endpoints across
# typical API projects, so unlikely to disappear simultaneously.
README_FALLBACK_SLUGS = ("list-all-customers", "list-all-products", "getallrecipes")

# README.io's standard LLM index — a complete listing of every doc page
# in the project with `.md` URLs that return raw markdown source. Used
# to discover the full reference-page tree without scraping the SPA.
README_LLMS_INDEX_URL = f"{README_PORTAL_URL}/llms.txt"
README_REFERENCE_DIR_NAME = "readme-reference"
README_MD_FETCH_CONCURRENCY = 4
README_MD_FETCH_RETRIES = 3
README_MD_FETCH_BACKOFF_SECONDS = 1.5

# Browser-shaped headers — the README.io CDN serves an empty/tiny
# payload for plain ``python-requests`` user agents, so we mimic Chrome.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
        "Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ----------------------------------------------------------------------------
# Live API gateway spec
# ----------------------------------------------------------------------------


async def fetch_live_openapi_spec(
    session: aiohttp.ClientSession,
) -> dict[str, Any] | None:
    """Pull the live OpenAPI spec from ``api.katanamrp.com/v1/openapi.json``.

    Public endpoint, no auth required. Returns the parsed spec or
    ``None`` if the fetch fails.
    """
    logger.info(f"📥 Fetching live OpenAPI spec: {LIVE_OPENAPI_SPEC_URL}")
    try:
        async with session.get(LIVE_OPENAPI_SPEC_URL, headers=HEADERS) as response:
            if response.status != 200:
                logger.warning(f"  HTTP {response.status}")
                return None
            text = await response.text()
            spec = json.loads(text)
    except (aiohttp.ClientError, json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"  fetch failed: {e}")
        return None

    if not isinstance(spec, dict) or "paths" not in spec:
        logger.warning("  not a valid spec (missing 'paths')")
        return None

    paths = spec.get("paths", {})
    schemas = spec.get("components", {}).get("schemas", {})
    logger.info(
        f"  ✓ {len(paths)} paths, {len(schemas)} schemas, "
        f"OpenAPI {spec.get('openapi', '?')}"
    )
    return spec


# ----------------------------------------------------------------------------
# README.io portal spec (via ssr-props on a reference page)
# ----------------------------------------------------------------------------


async def _fetch_text(session: aiohttp.ClientSession, url: str) -> str | None:
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                logger.debug(f"  {url} → HTTP {response.status}")
                return None
            return await response.text()
    except (aiohttp.ClientError, TimeoutError) as e:
        logger.debug(f"  {url} → {e}")
        return None


def _parse_ssr_props(page_html: str) -> dict[str, Any] | None:
    """Extract and parse ``<script id="ssr-props">`` JSON."""
    soup = BeautifulSoup(page_html, "html.parser")
    ssr_tag = soup.find("script", id="ssr-props")
    if not isinstance(ssr_tag, Tag):
        return None
    raw = ssr_tag.string or ""
    if not raw:
        data_attr = ssr_tag.get("data-json")
        if isinstance(data_attr, str):
            raw = html.unescape(data_attr)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _extract_oas_from_ssr_props(ssr: dict[str, Any]) -> dict[str, Any] | None:
    """Pull the OpenAPI spec from ssr-props, if it has one.

    Index pages (``api-introduction`` etc.) carry ssr-props but
    ``document.api.schema`` is ``None`` — only endpoint reference pages
    have the spec. Returns the spec dict or ``None``.
    """
    spec = ssr.get("document", {}).get("api", {}).get("schema")
    if isinstance(spec, dict) and "paths" in spec:
        return spec
    return None


async def _resolve_endpoint_slug_via_algolia(
    session: aiohttp.ClientSession, ssr: dict[str, Any]
) -> str | None:
    """Find any endpoint-page slug via README.io's public Algolia search.

    The ssr-props of *any* reference page carries the project's Algolia
    search config — App ID, public read-token, project tag filters,
    and the search index name. We use those to query Algolia for one
    endpoint hit; the returned ``slug`` is then the page we'll fetch
    for the OAS.

    Returns a slug like ``"list-all-customers"`` or ``None`` if the
    search config can't be assembled or Algolia rejects the query.
    """
    # ``hub-me`` carries the per-project search config (app, token,
    # filters); the top-level ``config`` script has the index name.
    search = ssr.get("search") or {}
    app_id = search.get("app")
    token = search.get("token")
    filters = search.get("filters")
    config = ssr.get("config") or {}
    index = config.get("algoliaIndex")
    if not (app_id and token and filters and index):
        return None

    # Restrict to endpoint-type hits — only those embed the OAS in
    # ssr-props. We accept any single endpoint; one is enough.
    body = {"query": "", "filters": "type:endpoint", "hitsPerPage": 1}
    headers = {
        "X-Algolia-Application-Id": app_id,
        "X-Algolia-API-Key": token,
        "Content-Type": "application/json",
    }
    url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index}/query"
    try:
        async with session.post(url, headers=headers, json=body) as response:
            if response.status != 200:
                logger.debug(f"  Algolia HTTP {response.status}")
                return None
            payload = await response.json()
    except (aiohttp.ClientError, json.JSONDecodeError, TimeoutError) as e:
        logger.debug(f"  Algolia query failed: {e}")
        return None

    hits = payload.get("hits") or []
    for hit in hits:
        slug = hit.get("slug")
        if isinstance(slug, str) and slug:
            return slug
    return None


async def fetch_readme_oas(
    session: aiohttp.ClientSession,
) -> dict[str, Any] | None:
    """Pull README.io's embedded OpenAPI spec from a reference page.

    Strategy:

    1. Fetch ``api-introduction`` (cheap, stable). Use its ssr-props
       to look up an endpoint slug via Algolia search — slug-agnostic
       so Katana can reorganize without breaking refresh.
    2. Fetch the endpoint page, extract OAS from ssr-props.
    3. If Algolia lookup fails, try a small list of fallback slugs.

    Returns the parsed spec or ``None`` on full failure.
    """
    logger.info(f"📥 Fetching README.io config page: {README_CONFIG_PAGE}")
    config_html = await _fetch_text(session, README_CONFIG_PAGE)
    if config_html is None:
        logger.warning("  could not fetch config page")
        return None

    config_ssr = _parse_ssr_props(config_html)
    if config_ssr is None:
        logger.warning("  no ssr-props on config page")
        return None

    # Try Algolia-derived slug first; fall back to known-good slugs.
    slug = await _resolve_endpoint_slug_via_algolia(session, config_ssr)
    candidates: tuple[str, ...] = ((slug,) if slug else ()) + README_FALLBACK_SLUGS

    for candidate in candidates:
        page_url = f"{README_PORTAL_URL}/reference/{candidate}"
        logger.info(f"📥 Fetching reference page for OAS: {page_url}")
        page_html = await _fetch_text(session, page_url)
        if page_html is None:
            continue
        page_ssr = _parse_ssr_props(page_html)
        if page_ssr is None:
            continue
        spec = _extract_oas_from_ssr_props(page_ssr)
        if spec is None:
            logger.debug(f"  {candidate} has no OAS in ssr-props; trying next")
            continue
        # Found it.
        paths = spec.get("paths", {})
        examples_count = sum(
            1
            for op in (paths.values() if isinstance(paths, dict) else [])
            if isinstance(op, dict)
            for method in op.values()
            if isinstance(method, dict)
            for resp in (method.get("responses") or {}).values()
            if isinstance(resp, dict)
            for cval in (resp.get("content") or {}).values()
            if isinstance(cval, dict) and cval.get("example") is not None
        )
        logger.info(
            f"  ✓ {len(paths)} paths, {examples_count} response media-types "
            f"with inline examples, OpenAPI {spec.get('openapi', '?')}"
        )
        return spec

    logger.warning("  no candidate slug yielded a usable OAS")
    return None


# ----------------------------------------------------------------------------
# README.io reference-page markdown crawl
# ----------------------------------------------------------------------------
#
# The OAS embedded in README.io's ssr-props (above) lags the human-curated
# per-object reference pages (e.g. ``the-variant-object`` documents
# ``abc_classification`` even though it's absent from the OAS Variant
# schema). We crawl the markdown source so our drift audit can compare
# the local OpenAPI schema against what Katana's docs team actually
# documents — catching field-level drift the OAS audit can't see.
#
# README.io serves a raw markdown export at ``<url>.md`` for every doc
# page, and publishes the full project tree at ``/llms.txt`` in a
# stable LLM-index format. We use ``llms.txt`` as the discovery source
# (slug-agnostic, no scraping) and the ``.md`` URL trick for the bodies.


# Matches a single llms.txt list entry, e.g.:
#   - [The variant object](https://developer.katanamrp.com/reference/the-variant-object.md): description
# The description suffix is optional — index-style pages have no description.
_LLMS_LINE_RE = re.compile(
    r"^- \[(?P<title>.*?)\]\((?P<url>https?://[^)]+\.md)\)"
    r"(?:\s*:\s*(?P<desc>.+))?$"
)


@dataclass(frozen=True)
class ReadmePage:
    """A single README.io page discovered from ``llms.txt``."""

    section: str  # H2 from llms.txt: "Guides" / "API Reference" / "Pages" / "Changelog"
    url: str
    title: str
    description: str | None
    relative_path: str  # URL path with leading slash stripped, e.g. "reference/foo.md"


def _parse_llms_index(text: str) -> list[ReadmePage]:
    """Parse README.io's ``llms.txt`` into a flat list of pages."""
    pages: list[ReadmePage] = []
    current_section = ""
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        match = _LLMS_LINE_RE.match(line)
        if match is None:
            continue
        url = match.group("url")
        path = urlparse(url).path.lstrip("/")
        pages.append(
            ReadmePage(
                section=current_section,
                url=url,
                title=match.group("title"),
                description=match.group("desc"),
                relative_path=path,
            )
        )
    return pages


def _write_if_changed(path: Path, content: str) -> None:
    """Write ``content`` only if the file is missing or differs.

    Keeps mtimes stable across no-op refreshes so downstream watchers
    (git, regen pipelines) don't trigger on every run.
    """
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


async def _fetch_with_retry(session: aiohttp.ClientSession, url: str) -> str | None:
    """Fetch with linear backoff. README.io rate-limits at the CDN edge."""
    for attempt in range(README_MD_FETCH_RETRIES):
        body = await _fetch_text(session, url)
        if body is not None:
            return body
        if attempt + 1 < README_MD_FETCH_RETRIES:
            await asyncio.sleep(README_MD_FETCH_BACKOFF_SECONDS * (attempt + 1))
    return None


async def _fetch_markdown_page(
    session: aiohttp.ClientSession,
    page: ReadmePage,
    output_dir: Path,
    sem: asyncio.Semaphore,
) -> bool:
    """Fetch one ``.md`` page and write it to ``output_dir/<relative_path>``.

    Returns True on success, False on any fetch/write failure.

    Handles a known README.io ``llms.txt`` inconsistency: entries under
    the ``Pages`` section list their URL at the root (e.g.
    ``/setting-up-oauth.md``) but the actual page is served at
    ``/page/<slug>.md``. When a root-level URL has no path segment, we
    retry with a ``page/`` prefix and remap the on-disk target so the
    layout stays predictable.
    """
    async with sem:
        body = await _fetch_with_retry(session, page.url)
        relative_path = page.relative_path
        # Retry root-level URLs under /page/ if the original 404s.
        if body is None and "/" not in page.relative_path:
            fallback_url = f"{README_PORTAL_URL}/page/{page.relative_path}"
            body = await _fetch_with_retry(session, fallback_url)
            if body is not None:
                relative_path = f"page/{page.relative_path}"
    if body is None:
        logger.warning(f"  ✗ {page.relative_path} — fetch failed")
        return False
    target = output_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    _write_if_changed(target, body)
    return True


async def fetch_readme_reference_markdown(
    session: aiohttp.ClientSession, output_dir: Path
) -> bool:
    """Pull every README.io reference / docs / changelog page as raw markdown.

    Strategy:

    1. Fetch ``/llms.txt`` to discover the full set of doc pages.
    2. For each page, fetch its ``.md`` export with bounded concurrency.
    3. Write each body to ``<output_dir>/<url_path>`` so the on-disk
       layout mirrors the URL structure (``reference/<slug>.md`` etc.).
    4. Drop a copy of ``llms.txt`` at the root for category lookup —
       it's the only place section headers (``API Reference`` vs
       ``Guides``) are preserved.

    Returns True if at least one page was written. Existing files in
    ``output_dir`` are cleared at the start of the run so upstream
    removals are reflected on disk.
    """
    logger.info(f"📥 Fetching README.io index: {README_LLMS_INDEX_URL}")
    text = await _fetch_text(session, README_LLMS_INDEX_URL)
    if text is None:
        logger.error("  could not fetch llms.txt index")
        return False
    pages = _parse_llms_index(text)
    sections = {p.section for p in pages}
    logger.info(f"  ✓ {len(pages)} pages across {len(sections)} sections")

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_if_changed(output_dir / "llms.txt", text)

    sem = asyncio.Semaphore(README_MD_FETCH_CONCURRENCY)
    results = await asyncio.gather(
        *(_fetch_markdown_page(session, p, output_dir, sem) for p in pages)
    )
    written = sum(results)
    logger.info(
        f"  ✓ {written}/{len(pages)} pages written to "
        f"{output_dir.relative_to(REPO_ROOT)}"
    )

    # Reap ``.md`` files no longer in the upstream index so removed pages
    # don't linger. Run after the fetch so a transient network failure
    # never leaves the tree empty.
    expected = {output_dir / "llms.txt"}
    for page in pages:
        expected.add(output_dir / page.relative_path)
        if "/" not in page.relative_path:
            expected.add(output_dir / "page" / page.relative_path)
    for stale in output_dir.rglob("*.md"):
        if stale not in expected:
            stale.unlink()

    return written > 0


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------


def save_spec(spec: dict[str, Any], path: Path) -> None:
    """Write a spec to disk as normalized YAML.

    Both the live-gateway and README.io specs go through this single
    formatter so they're byte-for-byte format-consistent with each
    other — identical key ordering, indentation, and quoting rules.
    That makes them diffable against each other (e.g. live vs README.io
    path coverage) and stable across refresh runs.

    Choices:

    - **YAML over JSON** — quote-free, comma-free, easier to read in
      PR review; YAML 1.1 is a JSON superset so the round-trip is
      lossless.
    - **``sort_keys=True``** — alphabetical key order eliminates
      spurious reordering churn when upstream tweaks property
      declaration order.
    - **``default_flow_style=False``** — block style throughout (no
      inline ``[a, b, c]`` lists).
    - **``width=1000``** — avoids mid-string folded line breaks on
      long descriptions. The pulled specs are listed in
      ``.yamllint.yml::line-length.ignore`` for the same reason —
      these are upstream-derived artefacts, not human-edited spec
      files.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            spec,
            sort_keys=True,
            default_flow_style=False,
            allow_unicode=True,
            width=1000,
        ),
        encoding="utf-8",
    )
    logger.info(f"  saved → {path.relative_to(REPO_ROOT)}")


async def refresh(output_dir: Path) -> int:
    """Fetch all upstream artefacts, save them. Returns 0 on full success."""
    output_dir.mkdir(parents=True, exist_ok=True)
    readme_reference_dir = output_dir / README_REFERENCE_DIR_NAME
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=60)
    ) as session:
        live, readme, reference_ok = await asyncio.gather(
            fetch_live_openapi_spec(session),
            fetch_readme_oas(session),
            fetch_readme_reference_markdown(session, readme_reference_dir),
        )

    rc = 0
    if live is not None:
        save_spec(live, output_dir / "live-gateway.yaml")
    else:
        logger.error("Live OpenAPI fetch failed — leaving live-gateway.yaml untouched")
        rc = 1
    if readme is not None:
        save_spec(readme, output_dir / "readme-portal.yaml")
    else:
        logger.error("README.io fetch failed — leaving readme-portal.yaml untouched")
        rc = 1
    if not reference_ok:
        logger.error(
            "README.io reference-page crawl produced no output — "
            f"leaving {readme_reference_dir.relative_to(REPO_ROOT)}/ stale"
        )
        rc = 1
    return rc


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            f"Directory to write the spec files into "
            f"(default: {DEFAULT_OUTPUT_DIR.relative_to(REPO_ROOT)})"
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    return asyncio.run(refresh(args.output_dir))


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "LIVE_OPENAPI_SPEC_URL",
    "README_LLMS_INDEX_URL",
    "README_REFERENCE_DIR_NAME",
    "fetch_live_openapi_spec",
    "fetch_readme_oas",
    "fetch_readme_reference_markdown",
]
