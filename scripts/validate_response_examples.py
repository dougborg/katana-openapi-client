#!/usr/bin/env python3
"""Validate README.io response examples against local response schemas.

The live OpenAPI spec at ``https://api.katanamrp.com/v1/openapi.json``
defines no response shapes — every ``200`` is just ``{description: ...}``
with no schema or example. The README.io developer portal's spec, on
the other hand, has inline response examples copied from real responses
by Katana's docs team. ``poe refresh-upstream-spec`` pulls that spec
into ``docs/upstream-specs/readme-portal.yaml``.

This script bridges that ``readme-portal.yaml`` against the local spec
at ``docs/katana-openapi.yaml``: for every endpoint where README.io has
an inline example, look up our local response schema for the same
``(path, method, status_code)`` and validate the example against it.

Failures fall into three buckets:

1. **Real schema drift** — our local schema is wrong; the live API
   actually returns what the example shows. Fix the schema.
2. **Documentation artefact** — the example is stale or hand-written
   poorly; the schema is correct. Verify against the live API or
   integration tests, then close as no-op.
3. **Mixed** — both sides need review.

Wired as ``poe validate-response-examples``. Reads exclusively from the
two YAML specs — no markdown parsing, no per-page scraping.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL = REPO_ROOT / "docs" / "katana-openapi.yaml"
DEFAULT_README = REPO_ROOT / "docs" / "upstream-specs" / "readme-portal.yaml"

SPEC_URI = "urn:openapi-spec"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@dataclass
class ValidationFailure:
    method: str
    path: str
    status_code: str
    schema_name: str
    error_path: str  # JSON Pointer into the example
    failing_value: Any
    error_message: str


@dataclass
class ValidationReport:
    examples_extracted: int = 0
    examples_validated: int = 0
    examples_skipped_no_schema: int = 0
    failures: list[ValidationFailure] = field(default_factory=list)
    paths_no_match: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


# ----------------------------------------------------------------------------
# Spec loading + helpers
# ----------------------------------------------------------------------------


def load_yaml_spec(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _build_local_registry(local_spec: dict[str, Any]) -> Registry:
    """Anchor the local spec under ``urn:openapi-spec`` for $ref resolution."""
    spec_resource = Resource.from_contents(
        local_spec, default_specification=DRAFT202012
    )
    return Registry().with_resource(uri=SPEC_URI, resource=spec_resource)


def _unwrap_labeled_example(payload: Any) -> Any:
    """Strip Katana docs' labeled-example wrapper if present.

    The README.io OAS sometimes carries response examples wrapped in a
    single-key dict whose key is a label (e.g.
    ``{"moOperationRowResponseExample": {...real payload...}}``). The
    wrapper comes from how the docs team authors the example in
    README.io's editor — it's a documentation artefact, not the API's
    actual response shape. Without unwrapping, validation reports every
    required field on the wrapped schema as missing.

    Heuristic: single-key dict whose key looks like a label (contains
    ``example``/``response``/``sample``) and whose value is itself a
    dict. Single-property objects with a real semantic key (e.g.
    ``{"data": [...]}`` for a list response wrapper) keep the key.
    """
    if not isinstance(payload, dict) or len(payload) != 1:
        return payload
    (key,) = payload.keys()
    value = payload[key]
    if not isinstance(value, dict):
        return payload
    if not any(w in key.lower() for w in ("example", "response", "sample")):
        return payload
    return value


def _find_local_response_schema(
    local_spec: dict[str, Any], path: str, method: str, status: str
) -> tuple[str | None, str | None]:
    """Return ``(ref_uri, schema_name)`` for the local response schema.

    Returns ``(None, None)`` when the local spec doesn't expose a
    matching ``(path, method, status, content[*].schema)`` $ref —
    inline schemas are deliberately not validated here (same limitation
    as ``validate_spec_examples.py``).
    """
    paths = local_spec.get("paths") or {}
    op = (paths.get(path) or {}).get(method.lower()) or {}
    response = (op.get("responses") or {}).get(status) or {}
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
    local_spec: dict[str, Any], readme_spec: dict[str, Any]
) -> ValidationReport:
    """Walk every example in ``readme_spec``, validate against local schemas."""
    registry = _build_local_registry(local_spec)
    report = ValidationReport()

    paths = readme_spec.get("paths") or {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method not in HTTP_METHODS or not isinstance(op, dict):
                continue
            for status, response in (op.get("responses") or {}).items():
                if not isinstance(response, dict):
                    continue
                for cval in (response.get("content") or {}).values():
                    if not isinstance(cval, dict):
                        continue
                    example = cval.get("example")
                    if example is None:
                        continue
                    example = _unwrap_labeled_example(example)
                    report.examples_extracted += 1

                    ref_uri, schema_name = _find_local_response_schema(
                        local_spec, path, method, str(status)
                    )
                    if ref_uri is None or schema_name is None:
                        report.examples_skipped_no_schema += 1
                        report.paths_no_match.append(
                            (method.upper(), path, str(status))
                        )
                        continue

                    validator = Draft202012Validator(
                        {"$ref": ref_uri}, registry=registry
                    )
                    report.examples_validated += 1
                    for err in validator.iter_errors(example):
                        ptr = (
                            "/" + "/".join(str(p) for p in err.absolute_path)
                            if err.absolute_path
                            else "/"
                        )
                        report.failures.append(
                            ValidationFailure(
                                method=method.upper(),
                                path=path,
                                status_code=str(status),
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
        f"- Response examples in README.io spec: {report.examples_extracted}",
        f"- Examples validated: **{report.examples_validated}**",
        (
            f"- Examples skipped (no local response schema): "
            f"{report.examples_skipped_no_schema}"
        ),
        f"- Failures: **{len(report.failures)}**",
        "",
    ]
    if report.ok:
        if report.examples_validated == 0:
            lines.append(
                "No examples were validated against schemas — nothing to "
                "report. Refresh upstream specs (`poe refresh-upstream-spec`) "
                "or check that README.io spec has inline examples."
            )
        else:
            lines.append("All validated examples conform to their local schemas.")
        if show_unmatched and report.paths_no_match:
            lines.append("")
            lines.append("## Endpoints with examples but no local schema")
            lines.append("")
            for m, p, s in report.paths_no_match:
                lines.append(f"- `{m:6s} {p} → {s}`")
        return "\n".join(lines)

    lines.append("## Failures")
    lines.append("")
    by_endpoint: dict[tuple[str, str, str], list[ValidationFailure]] = {}
    for f in report.failures:
        key = (f.method, f.path, f.status_code)
        by_endpoint.setdefault(key, []).append(f)

    for (method, path, status), fails in sorted(by_endpoint.items()):
        lines.append(f"### `{method} {path} → {status}`")
        lines.append(f"_schema:_ `{fails[0].schema_name}`")
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
        lines.append("## Endpoints with examples but no local schema")
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
        "--local",
        type=Path,
        default=DEFAULT_LOCAL,
        help=f"Path to local OpenAPI spec (default: {DEFAULT_LOCAL.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=DEFAULT_README,
        help=(
            f"Path to README.io upstream spec "
            f"(default: {DEFAULT_README.relative_to(REPO_ROOT)}). "
            "Refresh with `poe refresh-upstream-spec`."
        ),
    )
    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        help="Include endpoints with examples but no local response schema",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write report to FILE instead of stdout",
    )
    args = parser.parse_args(argv)

    if not args.local.exists():
        print(f"error: local spec not found: {args.local}", file=sys.stderr)
        return 2
    if not args.readme.exists():
        print(
            f"error: README.io spec not found: {args.readme}\n"
            f"hint: run `uv run poe refresh-upstream-spec` first",
            file=sys.stderr,
        )
        return 2

    local_spec = load_yaml_spec(args.local)
    readme_spec = load_yaml_spec(args.readme)
    report = validate(local_spec, readme_spec)
    text = format_report(report, show_unmatched=args.show_unmatched)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote report to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
