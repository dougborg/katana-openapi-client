#!/usr/bin/env python3
"""Validate scraped response examples against local response schemas.

The live OpenAPI spec at ``https://api.katanamrp.com/v1/openapi.json``
defines request DTOs but no response shapes — every ``200`` response in
the live spec is just ``{description: "Return value of FooController..."}``
with no schema or example. The README.io-scraped markdown files in
``docs/katana-api-comprehensive/``, on the other hand, *do* contain rich
JSON response examples copied from Katana's developer docs.

This script bridges the two:

1. Parse each ``.md`` file in the comprehensive archive. Extract:
   - The endpoint (HTTP method + path) from the markdown header
     (``**METHOD** ``URL``\\``).
   - Each labelled JSON response block (``#### 200 Response``,
     ``#### 422 Response``, etc.).
2. For each ``(path, method, status_code)`` triple, look up the matching
   response schema in ``docs/katana-openapi.yaml``.
3. Validate the scraped JSON example against that schema using
   ``Draft202012Validator`` + ``referencing`` (same machinery as
   ``validate_spec_examples.py``).
4. Report failures: missing fields, type mismatches, unknown values
   (caught by enum constraints), examples that don't fit the schema at
   all.

This is the third and final example-validation tool, complementing:

- ``poe audit-spec`` — request-DTO drift between local and live spec
- ``poe validate-examples`` — local examples vs local schemas (internal
  consistency)
- this script — Katana docs response examples vs local response schemas
  (catches schema drift on the response side, which the live OpenAPI
  doesn't surface)

Wired as ``poe validate-response-examples``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = REPO_ROOT / "docs" / "katana-openapi.yaml"
DEFAULT_DOCS_DIR = REPO_ROOT / "docs" / "katana-api-comprehensive"

SPEC_URI = "urn:openapi-spec"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

# ``**METHOD** `https://api.katanamrp.com/v1/<path>``` — captures method + path.
_HEADER_RE = re.compile(
    r"^\*\*(GET|POST|PUT|PATCH|DELETE)\*\* `https://api\.katanamrp\.com/v\d+(/[^`]+)`",
    re.MULTILINE,
)
# ``#### 200 Response`` (followed by an optional descriptive paragraph and a
# JSON code block).
_SECTION_RE = re.compile(r"^####\s+(\d{3})\s+Response\s*$", re.MULTILINE)
_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


@dataclass
class ScrapedExample:
    """One JSON example extracted from a markdown file."""

    md_path: Path
    method: str  # uppercase: GET / POST / etc.
    path: str  # spec-style with ``{id}`` placeholders
    status_code: int
    payload: Any  # parsed JSON


@dataclass
class ValidationFailure:
    md_path: str
    method: str
    path: str
    status_code: int
    schema_name: str  # what schema was used to validate
    error_path: str  # JSON Pointer into the example
    failing_value: Any
    error_message: str


@dataclass
class ValidationReport:
    md_files_scanned: int = 0
    examples_extracted: int = 0
    examples_validated: int = 0
    examples_skipped_no_schema: int = 0
    examples_skipped_non_2xx: int = 0
    examples_skipped_invalid_json: int = 0
    failures: list[ValidationFailure] = field(default_factory=list)
    # informational
    paths_no_match: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


# ----------------------------------------------------------------------------
# Markdown parsing
# ----------------------------------------------------------------------------


def _normalize_path(raw_path: str) -> str:
    """Convert scraped path placeholders to OpenAPI-style ``{id}`` syntax.

    Scraped paths sometimes have ``:id`` placeholders or trailing slashes;
    normalize so they line up with the keys in ``spec['paths']``.
    """
    p = raw_path.rstrip("/")
    p = re.sub(r":(\w+)", r"{\1}", p)
    return p


def _unwrap_labeled_example(payload: Any) -> Any:
    """Strip README.io's labeled-example wrapper.

    README.io's API explorer renders multiple response examples for the same
    status code as a single JSON object whose keys are example labels (e.g.
    ``{"moOperationRowResponseExample": {...}, "errorExample": {...}}``).
    The scraped JSON keeps that wrapper. The actual response payload is
    inside, but applying the response schema to the wrapper produces only
    noise (every required field appears missing).

    Heuristic: if the payload is a dict with exactly one key whose value
    is itself a dict, and the key looks like a label (camelCase, contains
    "example"/"response"/"sample"), unwrap once. The list/object check
    keeps real single-property objects (e.g. ``{"data": [...]}``) intact.
    """
    if not isinstance(payload, dict) or len(payload) != 1:
        return payload
    (key,) = payload.keys()
    value = payload[key]
    if not isinstance(value, dict):
        return payload
    label_words = ("example", "response", "sample")
    if not any(w in key.lower() for w in label_words):
        return payload
    return value


def parse_md_file(path: Path) -> tuple[list[ScrapedExample], int]:
    """Extract every (method, path, status_code, json) tuple from one .md file.

    Returns ``(examples, invalid_json_count)``. ``invalid_json_count`` lets
    the caller surface how many code blocks were dropped due to malformed
    JSON (typically multi-line string examples with un-escaped embedded
    newlines that ``json.loads`` rejects). For files without a
    recognizable endpoint header (object-documentation pages, login.md),
    returns ``([], 0)``.
    """
    text = path.read_text(encoding="utf-8")
    header_match = _HEADER_RE.search(text)
    if not header_match:
        return [], 0
    method = header_match.group(1).upper()
    raw_path = header_match.group(2)
    spec_path = _normalize_path(raw_path)

    out: list[ScrapedExample] = []
    invalid_json = 0
    # Scan response sections in document order; the JSON block immediately
    # following each ``#### NNN Response`` heading belongs to that section.
    for sec_match in _SECTION_RE.finditer(text):
        status = int(sec_match.group(1))
        # Find the next code block after this section header. Stop at the
        # next response section header (so we don't accidentally grab a
        # block from the next status code's section).
        next_sec = _SECTION_RE.search(text, sec_match.end())
        block_search_end = next_sec.start() if next_sec else len(text)
        block_match = _JSON_BLOCK_RE.search(text, sec_match.end(), block_search_end)
        if not block_match:
            continue
        json_text = block_match.group(1)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            # Multi-line string examples (e.g. error message bodies with
            # embedded newlines) break ``json.loads``. Count them so the
            # report surfaces *why* the input/output ratio is what it is,
            # rather than silently dropping them.
            invalid_json += 1
            continue
        payload = _unwrap_labeled_example(payload)
        out.append(
            ScrapedExample(
                md_path=path,
                method=method,
                path=spec_path,
                status_code=status,
                payload=payload,
            )
        )
    return out, invalid_json


def scan_docs_dir(docs_dir: Path) -> tuple[list[ScrapedExample], int, int]:
    """Walk the docs dir; return ``(examples, files_scanned, invalid_json)``."""
    md_files = sorted(p for p in docs_dir.glob("*.md") if p.name != "README.md")
    examples: list[ScrapedExample] = []
    invalid_json = 0
    for p in md_files:
        ex, ij = parse_md_file(p)
        examples.extend(ex)
        invalid_json += ij
    return examples, len(md_files), invalid_json


# ----------------------------------------------------------------------------
# Spec + schema lookup
# ----------------------------------------------------------------------------


def _build_registry(spec: dict[str, Any]) -> Registry:
    """Same anchored-spec pattern used by ``validate_spec_examples.py``."""
    spec_resource = Resource.from_contents(spec, default_specification=DRAFT202012)
    return Registry().with_resource(uri=SPEC_URI, resource=spec_resource)


def find_response_schema(
    spec: dict[str, Any], path: str, method: str, status: int
) -> tuple[str | None, str | None]:
    """Return (ref_uri, schema_name) for the response schema if defined.

    Returns ``(None, None)`` when:
    - the path doesn't exist locally
    - the method isn't defined on that path
    - the response status isn't documented
    - the response uses an inline schema (skipped — same limitation as
      ``validate_spec_examples.py``)
    """
    paths = spec.get("paths") or {}
    op = (paths.get(path) or {}).get(method.lower()) or {}
    response = (op.get("responses") or {}).get(str(status)) or {}
    if not isinstance(response, dict):
        return (None, None)
    content = response.get("content") or {}
    for cval in content.values():
        if not isinstance(cval, dict):
            continue
        schema = cval.get("schema") or {}
        ref = schema.get("$ref", "")
        if ref.startswith("#/components/schemas/"):
            name = ref.rsplit("/", 1)[-1]
            return (f"{SPEC_URI}{ref}", name)
    return (None, None)


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------


def validate(
    spec: dict[str, Any],
    examples: list[ScrapedExample],
    md_files_scanned: int,
    *,
    only_2xx: bool = True,
    examples_skipped_invalid_json: int = 0,
) -> ValidationReport:
    """Validate every scraped example against the matching response schema."""
    registry = _build_registry(spec)
    report = ValidationReport(
        md_files_scanned=md_files_scanned,
        examples_extracted=len(examples),
        examples_skipped_invalid_json=examples_skipped_invalid_json,
    )

    for ex in examples:
        if only_2xx and not 200 <= ex.status_code < 300:
            report.examples_skipped_non_2xx += 1
            continue

        ref_uri, schema_name = find_response_schema(
            spec, ex.path, ex.method, ex.status_code
        )
        if ref_uri is None or schema_name is None:
            # Either the endpoint or the response schema is missing locally;
            # ``audit_spec_drift.py`` is the right surface for the former,
            # and inline schemas are intentionally not validated here.
            report.examples_skipped_no_schema += 1
            report.paths_no_match.append((ex.method, ex.path, str(ex.status_code)))
            continue

        validator = Draft202012Validator({"$ref": ref_uri}, registry=registry)
        report.examples_validated += 1
        for err in validator.iter_errors(ex.payload):
            ptr = (
                "/" + "/".join(str(p) for p in err.absolute_path)
                if err.absolute_path
                else "/"
            )
            # ``relative_to`` raises when ``--docs-dir`` lives outside the
            # repo (e.g. running against a scratch copy or a CI cache
            # mount). Fall back to the absolute path so the validation
            # pass doesn't abort just because the report can't be made
            # repo-relative.
            try:
                md_path = str(ex.md_path.relative_to(REPO_ROOT))
            except ValueError:
                md_path = str(ex.md_path)
            report.failures.append(
                ValidationFailure(
                    md_path=md_path,
                    method=ex.method,
                    path=ex.path,
                    status_code=ex.status_code,
                    schema_name=schema_name,
                    error_path=ptr,
                    failing_value=err.instance,
                    error_message=err.message,
                )
            )

    return report


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------


def format_report(report: ValidationReport, *, show_unmatched: bool = False) -> str:
    lines = [
        "# Response example validation report",
        "",
        f"- Markdown files scanned: {report.md_files_scanned}",
        f"- Response examples extracted: {report.examples_extracted}",
        f"- Examples validated: **{report.examples_validated}**",
        f"- Examples skipped (no local schema): {report.examples_skipped_no_schema}",
        f"- Examples skipped (non-2xx): {report.examples_skipped_non_2xx}",
        (f"- Examples skipped (invalid JSON): {report.examples_skipped_invalid_json}"),
        f"- Failures: **{len(report.failures)}**",
        "",
    ]
    if report.ok:
        if report.examples_validated == 0:
            # Zero failures *and* zero validated — usually means filters
            # excluded everything (e.g. ``--docs-dir`` pointed at a dir
            # with no recognized markdown, or all responses were non-2xx
            # with the default filter). Make this explicit so the report
            # doesn't read as "everything passed."
            lines.append(
                "No examples were validated against schemas — nothing to "
                "report. Check ``--docs-dir`` and ``--all-statuses``."
            )
        else:
            lines.append("All validated examples conform to their local schemas.")
        if show_unmatched and report.paths_no_match:
            lines.append("")
            lines.append("## Endpoints scraped but unmatched in local spec")
            lines.append("")
            for m, p, s in report.paths_no_match:
                lines.append(f"- `{m:6s} {p} → {s}`")
        return "\n".join(lines)

    lines.append("## Failures")
    lines.append("")
    # Group failures by (method, path) so multiple errors on one example
    # display together.
    by_endpoint: dict[tuple[str, str, int], list[ValidationFailure]] = {}
    for f in report.failures:
        key = (f.method, f.path, f.status_code)
        by_endpoint.setdefault(key, []).append(f)

    for (method, path, status), fails in sorted(by_endpoint.items()):
        lines.append(f"### `{method} {path} → {status}`")
        lines.append(f"_schema:_ `{fails[0].schema_name}` _from:_ `{fails[0].md_path}`")
        lines.append("")
        for f in fails:
            failing = repr(f.failing_value)
            if len(failing) > 200:
                failing = failing[:200] + "..."
            lines.append(f"- error path: `{f.error_path}`")
            lines.append(f"  - failing value: `{failing}`")
            lines.append(f"  - message: {f.error_message}")
        lines.append("")

    if show_unmatched and report.paths_no_match:
        lines.append("## Endpoints scraped but unmatched in local spec")
        lines.append("")
        for m, p, s in report.paths_no_match:
            lines.append(f"- `{m:6s} {p} → {s}`")

    return "\n".join(lines)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_SPEC,
        help=f"Path to local OpenAPI spec (default: {DEFAULT_SPEC.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DEFAULT_DOCS_DIR,
        help=(
            f"Directory of scraped markdown files "
            f"(default: {DEFAULT_DOCS_DIR.relative_to(REPO_ROOT)})"
        ),
    )
    parser.add_argument(
        "--all-statuses",
        action="store_true",
        help="Validate non-2xx examples too (default: 2xx only)",
    )
    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        help="Include endpoints with scraped examples but no local schema",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write report to FILE instead of stdout",
    )
    args = parser.parse_args(argv)

    if not args.spec.exists():
        print(f"error: spec not found: {args.spec}", file=sys.stderr)
        return 2
    if not args.docs_dir.is_dir():
        print(f"error: docs dir not found: {args.docs_dir}", file=sys.stderr)
        return 2

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    examples, files, invalid_json = scan_docs_dir(args.docs_dir)
    report = validate(
        spec,
        examples,
        files,
        only_2xx=not args.all_statuses,
        examples_skipped_invalid_json=invalid_json,
    )
    text = format_report(report, show_unmatched=args.show_unmatched)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote report to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
