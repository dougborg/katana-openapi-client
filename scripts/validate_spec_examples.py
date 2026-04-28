#!/usr/bin/env python3
"""Validate inline examples in ``docs/katana-openapi.yaml`` against their schemas.

OpenAPI specs commonly include ``example:`` fields embedded next to a schema,
a request body, or a response. These examples are documentation, but
silently — the spec engine doesn't enforce that the example actually matches
the schema. So examples can drift: a refactor changes a schema enum but
leaves the example alone, and the example then advertises a value the API
will never accept (the bug ``audit-2026-04-28.md`` flagged with
``refund_status: PROCESSED`` when the schema only allowed
``[NOT_REFUNDED, REFUNDED, PARTIALLY_REFUNDED]``).

This script walks the local spec, locates every ``example:`` block, and
validates it against the schema it's attached to using ``jsonschema``.
Three example locations are checked:

1. ``components.schemas.X.example`` — must validate against schema ``X``.
2. ``paths.../requestBody.content.<ctype>.schema.example`` — must validate
   against the request body schema.
3. ``paths.../responses.<status>.content.<ctype>.schema.example`` — must
   validate against the response schema.

Validation uses ``Draft202012Validator`` (OpenAPI 3.1 is JSON Schema 2020-12
compatible). ``$ref``s are resolved using the modern ``referencing``
library, anchored at ``#/components/schemas/``.

Exit code 0 if every example passes; 1 if any fails. Failures print the
schema path, the failing example value, and the validator's error message.

Usage:

    uv run python scripts/validate_spec_examples.py
    uv run poe validate-examples
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
DEFAULT_SPEC = REPO_ROOT / "docs" / "katana-openapi.yaml"

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@dataclass
class ValidationFailure:
    location: str  # e.g. "components.schemas.SalesReturn.example"
    schema_name: str  # which schema the example was validated against
    error_message: str
    failing_value: Any
    error_path: str  # JSON Pointer to where in the example the error occurred


@dataclass
class ValidationReport:
    examples_checked: int = 0
    failures: list[ValidationFailure] = field(default_factory=list)
    schemas_with_no_example: int = 0  # informational
    inline_examples_skipped: int = 0  # operations w/ inline schema + example

    @property
    def ok(self) -> bool:
        return not self.failures


SPEC_URI = "urn:openapi-spec"
"""Synthetic base URI for the whole spec.

``referencing`` resolves ``$ref: '#/components/...'`` relative to the
schema's *base URI*. Plain JSON schemas don't have one, so we wrap the
entire spec under ``urn:openapi-spec`` and validate against
``{"$ref": "urn:openapi-spec#/components/schemas/<Name>"}`` — this lets the
validator resolve fragments inside the same document, including transitive
``allOf`` references between sibling schemas.
"""


def _build_registry(spec: dict[str, Any]) -> Registry:
    """Register the entire spec under a known base URI for $ref resolution."""
    spec_resource = Resource.from_contents(spec, default_specification=DRAFT202012)
    return Registry().with_resource(uri=SPEC_URI, resource=spec_resource)


def _validate_via_ref(
    location: str,
    schema_name: str,
    ref_uri: str,
    example: Any,
    registry: Registry,
    failures: list[ValidationFailure],
) -> None:
    """Validate ``example`` against the schema at ``ref_uri``.

    Validating through a ``$ref`` (instead of inlining the schema) anchors
    the validator at the spec's base URI, so transitive ``allOf`` /
    ``$ref`` lookups inside the schema resolve correctly.
    """
    validator = Draft202012Validator({"$ref": ref_uri}, registry=registry)
    for err in validator.iter_errors(example):
        ptr = (
            "/" + "/".join(str(p) for p in err.absolute_path)
            if err.absolute_path
            else "/"
        )
        failures.append(
            ValidationFailure(
                location=location,
                schema_name=schema_name,
                error_message=err.message,
                failing_value=err.instance,
                error_path=ptr,
            )
        )


def validate_component_schemas(
    spec: dict[str, Any], registry: Registry, report: ValidationReport
) -> None:
    """Validate ``components.schemas.<X>.example`` against schema ``X``."""
    for name, schema in spec.get("components", {}).get("schemas", {}).items():
        example = schema.get("example")
        if example is None:
            report.schemas_with_no_example += 1
            continue
        report.examples_checked += 1
        location = f"components.schemas.{name}.example"
        ref_uri = f"{SPEC_URI}#/components/schemas/{name}"
        _validate_via_ref(location, name, ref_uri, example, registry, report.failures)


def _validate_against_media_schema(
    location: str,
    schema: dict[str, Any],
    example: Any,
    registry: Registry,
    report: ValidationReport,
) -> None:
    """Validate when the media schema is a ``$ref``; skip + count otherwise.

    Inline schemas in operations are rare in our spec and validating them
    needs more ref-rebasing scaffolding than the current implementation
    provides. Skip and record so the count is visible in the report.
    """
    ref = schema.get("$ref", "")
    if ref.startswith("#/components/schemas/"):
        name = ref.rsplit("/", 1)[-1]
        ref_uri = f"{SPEC_URI}{ref}"
        _validate_via_ref(location, name, ref_uri, example, registry, report.failures)
    else:
        report.inline_examples_skipped += 1


def _validate_media_examples(
    base_location: str,
    cval: dict[str, Any],
    registry: Registry,
    report: ValidationReport,
) -> None:
    """Walk every example carried by a media-type entry (singular + plural).

    OpenAPI media-type objects can carry examples in three places:

    1. ``content.<ctype>.example`` — singular inline example
    2. ``content.<ctype>.examples`` — map of named examples, each with a
       ``value`` (and optional ``summary``/``description``/
       ``externalValue``). Plural form lets a spec carry multiple examples
       for the same endpoint (e.g., ``created``, ``updated``, ``deleted``
       webhook payload examples sharing one schema).
    3. ``content.<ctype>.schema.example`` — singular example baked into
       the schema definition.

    Validate every populated location against the media-type's schema.
    """
    schema = cval.get("schema") or {}

    # Singular ``example``: media-type-level wins over schema-level when
    # both are present (per OpenAPI semantics).
    singular = cval.get("example")
    if singular is None:
        singular = schema.get("example")
    if singular is not None:
        report.examples_checked += 1
        _validate_against_media_schema(
            f"{base_location}.example", schema, singular, registry, report
        )

    # Plural ``examples``: each entry is an object with a ``value``
    # (string keys are the example names — used for the report location).
    examples = cval.get("examples") or {}
    if isinstance(examples, dict):
        for name, entry in examples.items():
            if not isinstance(entry, dict):
                continue
            if "value" not in entry:
                # ``externalValue`` (URL) or ``$ref``-only entries — can't
                # validate without fetching; skip silently.
                continue
            report.examples_checked += 1
            _validate_against_media_schema(
                f"{base_location}.examples.{name}.value",
                schema,
                entry["value"],
                registry,
                report,
            )


def _walk_operations(
    section_name: str,
    operations_root: dict[str, Any],
    registry: Registry,
    report: ValidationReport,
) -> None:
    """Walk every operation under a ``paths``- or ``webhooks``-shaped root.

    OpenAPI 3.1 puts ``webhooks:`` at the top level alongside ``paths:``;
    both are maps of operation containers (path-or-webhook key → method →
    operation), so a single walker covers both. The ``section_name``
    becomes the prefix in failure-report locations
    (``paths.<...>`` vs ``webhooks.<...>``).
    """
    for key, methods in operations_root.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method not in HTTP_METHODS or not isinstance(op, dict):
                continue
            # Request body
            rb = op.get("requestBody") or {}
            for ctype, cval in (rb.get("content") or {}).items():
                if not isinstance(cval, dict):
                    continue
                _validate_media_examples(
                    f"{section_name}.{key}.{method}.requestBody.content.{ctype}",
                    cval,
                    registry,
                    report,
                )
            # Responses
            for status, response in (op.get("responses") or {}).items():
                if not isinstance(response, dict):
                    continue
                for ctype, cval in (response.get("content") or {}).items():
                    if not isinstance(cval, dict):
                        continue
                    _validate_media_examples(
                        (
                            f"{section_name}.{key}.{method}.responses."
                            f"{status}.content.{ctype}"
                        ),
                        cval,
                        registry,
                        report,
                    )


def validate_spec(spec: dict[str, Any]) -> ValidationReport:
    """Run every example-validation pass; return the combined report."""
    registry = _build_registry(spec)
    report = ValidationReport()
    validate_component_schemas(spec, registry, report)
    _walk_operations("paths", spec.get("paths") or {}, registry, report)
    _walk_operations("webhooks", spec.get("webhooks") or {}, registry, report)
    return report


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------


def format_report(report: ValidationReport) -> str:
    lines = [
        "# Example validation report",
        "",
        f"- Examples checked: **{report.examples_checked}**",
        f"- Schemas without an example: {report.schemas_with_no_example}",
        f"- Inline-schema examples skipped: {report.inline_examples_skipped}",
        f"- Failures: **{len(report.failures)}**",
        "",
    ]
    if report.ok:
        lines.append("All examples validate against their schemas.")
        return "\n".join(lines)

    lines.append("## Failures")
    lines.append("")
    for f in report.failures:
        lines.append(f"### `{f.location}`")
        lines.append(f"- schema: `{f.schema_name}`")
        lines.append(f"- error path in example: `{f.error_path}`")
        lines.append(f"- failing value: `{f.failing_value!r}`")
        lines.append(f"- message: {f.error_message}")
        lines.append("")
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
        help=f"Path to OpenAPI spec (default: {DEFAULT_SPEC.relative_to(REPO_ROOT)})",
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

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    report = validate_spec(spec)
    text = format_report(report)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote report to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
