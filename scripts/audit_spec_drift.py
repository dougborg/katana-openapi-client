#!/usr/bin/env python3
"""Audit ``docs/katana-openapi.yaml`` against the canonical Katana OpenAPI spec.

Compares the local spec with the live upstream spec at
``docs/katana-api-comprehensive/openapi-spec.json`` (refreshed by
``scripts/extract_all_katana_docs.py``, which now pulls
``https://api.katanamrp.com/v1/openapi.json`` directly).

Reports four categories of drift, each scoped to a single ``(path, method)``
pair so findings are immediately actionable as fix PRs:

1. **Path coverage** — endpoints in live but not local (we don't expose) and
   endpoints in local but not live (we may have invented).
2. **Wrong ``required`` fields** — the live spec's ``required`` list differs
   from local's. Direction-of-drift matters: under-requiring causes the API
   to 422 at runtime; over-requiring blocks valid callers.
3. **Missing or invented fields** — fields present in one side but not the
   other.
4. **Type/enum mismatches** — same field name on both sides but different
   types or different enum values. Filters out OpenAPI 3.0/3.1 syntax noise
   (``nullable: true`` vs ``type: [..., "null"]``; ``integer`` vs ``number``)
   so only semantic differences are reported.

Default output is Markdown to stdout; ``--json`` emits a machine-readable
report; ``--output FILE`` writes to disk. Exit code is **0 on success**
regardless of drift, so the command works equally well for human
inspection and CI. Pass ``--strict`` to make any drift exit 1 (suitable
for CI gating); ``2`` is reserved for script errors (missing input
file, invalid YAML, etc.).

Usage:

    uv run python scripts/audit_spec_drift.py
    uv run python scripts/audit_spec_drift.py --json --output drift.json
    uv run poe audit-spec
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL = REPO_ROOT / "docs" / "katana-openapi.yaml"
DEFAULT_LIVE = REPO_ROOT / "docs" / "katana-api-comprehensive" / "openapi-spec.json"

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


# ----------------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------------


@dataclass
class EndpointDrift:
    """One endpoint's drift findings."""

    method: str
    path: str
    live_dto: str
    local_dto: str
    only_live_fields: list[str] = field(default_factory=list)
    only_local_fields: list[str] = field(default_factory=list)
    type_diffs: list[tuple[str, str, str]] = field(default_factory=list)
    live_required: list[str] = field(default_factory=list)
    local_required: list[str] = field(default_factory=list)

    @property
    def required_diff(self) -> bool:
        return set(self.live_required) != set(self.local_required)

    @property
    def has_drift(self) -> bool:
        return bool(
            self.only_live_fields
            or self.only_local_fields
            or self.type_diffs
            or self.required_diff
        )


@dataclass
class AuditReport:
    """Top-level audit findings."""

    live_path_count: int  # unique paths (e.g. /sales_orders, /sales_orders/{id})
    local_path_count: int
    live_endpoint_count: int = 0  # path-method pairs (e.g. GET /sales_orders)
    local_endpoint_count: int = 0
    paths_only_in_live: list[tuple[str, str]] = field(default_factory=list)
    paths_only_in_local: list[tuple[str, str]] = field(default_factory=list)
    shared_endpoints: int = 0
    drifted_endpoints: list[EndpointDrift] = field(default_factory=list)

    @property
    def total_drift_count(self) -> int:
        return (
            len(self.paths_only_in_live)
            + len(self.paths_only_in_local)
            + len(self.drifted_endpoints)
        )


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def load_spec(path: Path) -> dict[str, Any]:
    """Load a spec from JSON or YAML based on extension."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def collect_request_dtos(spec: dict[str, Any]) -> dict[tuple[str, str], str]:
    """Map ``(path, method)`` → request body schema name (only $ref'd ones).

    Endpoints with inline schemas (no $ref) are skipped — they can't be
    cross-compared by name. The path is still included in the path-coverage
    report.
    """
    out: dict[tuple[str, str], str] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if method not in HTTP_METHODS:
                continue
            rb = op.get("requestBody") or {}
            for cval in rb.get("content", {}).values():
                schema = cval.get("schema", {})
                ref = schema.get("$ref", "")
                if ref:
                    out[(path, method)] = ref.rsplit("/", 1)[-1]
                    break
    return out


def all_endpoints(spec: dict[str, Any]) -> set[tuple[str, str]]:
    """All ``(path, method)`` pairs in a spec (any HTTP method)."""
    return {
        (path, method)
        for path, methods in spec.get("paths", {}).items()
        for method in methods
        if method in HTTP_METHODS
    }


def expand_schema(
    spec: dict[str, Any], schemas: dict[str, Any], schema: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    """Walk ``allOf`` to flatten properties + accumulate required fields."""
    out_props: dict[str, dict[str, Any]] = {}
    out_required: set[str] = set(schema.get("required", []))
    if "allOf" in schema:
        for sub in schema["allOf"]:
            if "$ref" in sub:
                ref_name = sub["$ref"].rsplit("/", 1)[-1]
                ref_schema = schemas.get(ref_name)
                if ref_schema:
                    sub_props, sub_req = expand_schema(spec, schemas, ref_schema)
                    out_props.update(sub_props)
                    out_required |= sub_req
            else:
                for pn, pd in sub.get("properties", {}).items():
                    out_props[pn] = pd
                out_required |= set(sub.get("required", []))
    for pn, pd in schema.get("properties", {}).items():
        out_props[pn] = pd
    return out_props, out_required


def fields_of(
    spec: dict[str, Any], schemas: dict[str, Any], name: str
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    s = schemas.get(name) or {}
    return expand_schema(spec, schemas, s)


def normalize_type(pd: dict[str, Any]) -> str:
    """Render a property's type signature, ignoring nullability syntax noise.

    OpenAPI 3.0 uses ``nullable: true``; OpenAPI 3.1 uses ``type: [t, "null"]``.
    Both mean the same thing. This function strips ``null`` so the comparator
    only flags semantic differences. Likewise ``integer`` vs ``number`` is
    treated as equivalent for the JSON wire (both arrive as numbers).
    """
    t = pd.get("type")
    enum = pd.get("enum")
    ref = pd.get("$ref", "")
    one_of = pd.get("oneOf")

    if ref:
        return f"$ref:{ref.rsplit('/', 1)[-1]}"
    if one_of:
        names = []
        for o in one_of:
            if "$ref" in o:
                names.append("$ref:" + o["$ref"].rsplit("/", 1)[-1])
            elif o.get("type") == "null":
                continue  # drop null branch — handled by nullable
            elif "type" in o:
                names.append(str(o["type"]))
        return "oneOf:[" + ",".join(names) + "]"
    if isinstance(t, list):
        non_null = [x for x in t if x != "null"]
        return non_null[0] if len(non_null) == 1 else "|".join(str(x) for x in non_null)
    if t == "string" and enum:
        return f"enum:[{','.join(sorted(enum))}]"
    return str(t) if t else "?"


def types_equivalent(
    live_pd: dict[str, Any], local_pd: dict[str, Any], local_schemas: dict[str, Any]
) -> bool:
    """True if the two property defs are semantically the same."""
    live_t = normalize_type(live_pd)
    local_t = normalize_type(local_pd)

    # integer ↔ number — both fit JSON numbers
    canon = {"integer": "number"}

    def canonicalize(t: str) -> str:
        return canon.get(t, t)

    if canonicalize(live_t) == canonicalize(local_t):
        return True

    # Live inlines an enum; local references a shared schema. Compare the
    # actual enum value sets — semantically equivalent if they match.
    if live_t.startswith("enum:[") and local_t.startswith("$ref:"):
        ref_name = local_t[5:]
        ref_schema = local_schemas.get(ref_name) or {}
        local_values = set(ref_schema.get("enum", []))
        live_values = set(live_pd.get("enum", []))
        return local_values == live_values

    return False


# ----------------------------------------------------------------------------
# Audit logic
# ----------------------------------------------------------------------------


def audit(local: dict[str, Any], live: dict[str, Any]) -> AuditReport:
    """Run the full audit and return a structured report."""
    local_paths = all_endpoints(local)
    live_paths = all_endpoints(live)

    report = AuditReport(
        live_path_count=len({p for p, _ in live_paths}),
        local_path_count=len({p for p, _ in local_paths}),
        live_endpoint_count=len(live_paths),
        local_endpoint_count=len(local_paths),
    )
    report.paths_only_in_live = sorted(live_paths - local_paths)
    report.paths_only_in_local = sorted(local_paths - live_paths)

    live_schemas = live.get("components", {}).get("schemas", {})
    local_schemas = local.get("components", {}).get("schemas", {})

    live_dtos = collect_request_dtos(live)
    local_dtos = collect_request_dtos(local)
    shared = sorted(set(live_dtos) & set(local_dtos))
    report.shared_endpoints = len(shared)

    for path, method in shared:
        live_n = live_dtos[(path, method)]
        local_n = local_dtos[(path, method)]
        live_f, live_req = fields_of(live, live_schemas, live_n)
        local_f, local_req = fields_of(local, local_schemas, local_n)

        only_live = sorted(set(live_f) - set(local_f))
        only_local = sorted(set(local_f) - set(live_f))
        common = set(live_f) & set(local_f)

        type_diffs: list[tuple[str, str, str]] = []
        for f in sorted(common):
            if not types_equivalent(live_f[f], local_f[f], local_schemas):
                type_diffs.append(
                    (f, normalize_type(live_f[f]), normalize_type(local_f[f]))
                )

        ed = EndpointDrift(
            method=method,
            path=path,
            live_dto=live_n,
            local_dto=local_n,
            only_live_fields=only_live,
            only_local_fields=only_local,
            type_diffs=type_diffs,
            live_required=sorted(live_req),
            local_required=sorted(local_req),
        )
        if ed.has_drift:
            report.drifted_endpoints.append(ed)

    return report


# ----------------------------------------------------------------------------
# Output formatting
# ----------------------------------------------------------------------------


def format_markdown(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("# Spec drift report")
    lines.append("")
    lines.append(
        f"- Live spec: {report.live_path_count} unique paths, "
        f"{report.live_endpoint_count} path-method endpoints"
    )
    lines.append(
        f"- Local spec: {report.local_path_count} unique paths, "
        f"{report.local_endpoint_count} path-method endpoints"
    )
    lines.append(f"- Shared endpoints with named DTOs: {report.shared_endpoints}")
    lines.append(
        f"- Endpoints with drift: **{len(report.drifted_endpoints)}** "
        f"({len(report.paths_only_in_live)} live-only, "
        f"{len(report.paths_only_in_local)} local-only)"
    )
    lines.append("")

    if report.paths_only_in_live:
        lines.append("## Endpoints in live but not local")
        lines.append("")
        for path, method in report.paths_only_in_live:
            lines.append(f"- `{method.upper():6s} {path}`")
        lines.append("")

    if report.paths_only_in_local:
        lines.append("## Endpoints in local but not live")
        lines.append("")
        lines.append("(May exist in live with inline schemas — verify shapes match.)")
        lines.append("")
        for path, method in report.paths_only_in_local:
            lines.append(f"- `{method.upper():6s} {path}`")
        lines.append("")

    if report.drifted_endpoints:
        lines.append("## Field-level drift")
        lines.append("")
        for ed in report.drifted_endpoints:
            lines.append(f"### `{ed.method.upper()} {ed.path}`")
            lines.append(f"_live:_ `{ed.live_dto}` _↔ local:_ `{ed.local_dto}`")
            lines.append("")
            if ed.only_live_fields:
                lines.append(f"- ❗ live has, local missing: {ed.only_live_fields}")
            if ed.only_local_fields:
                lines.append(f"- ⚠ local has, live missing: {ed.only_local_fields}")
            if ed.type_diffs:
                lines.append("- ✱ type/enum mismatches:")
                for f, lv, lo in ed.type_diffs:
                    lines.append(f"    - `{f}`: live=`{lv}` local=`{lo}`")
            if ed.required_diff:
                lines.append("- ❗ required diff:")
                lines.append(f"    - live  required: `{ed.live_required}`")
                lines.append(f"    - local required: `{ed.local_required}`")
            lines.append("")

    return "\n".join(lines)


def format_json(report: AuditReport) -> str:
    return json.dumps(
        {
            "live_path_count": report.live_path_count,
            "local_path_count": report.local_path_count,
            "live_endpoint_count": report.live_endpoint_count,
            "local_endpoint_count": report.local_endpoint_count,
            "shared_endpoints": report.shared_endpoints,
            "paths_only_in_live": [
                {"method": m, "path": p} for p, m in report.paths_only_in_live
            ],
            "paths_only_in_local": [
                {"method": m, "path": p} for p, m in report.paths_only_in_local
            ],
            "drifted_endpoints": [
                {
                    "method": ed.method,
                    "path": ed.path,
                    "live_dto": ed.live_dto,
                    "local_dto": ed.local_dto,
                    "only_live_fields": ed.only_live_fields,
                    "only_local_fields": ed.only_local_fields,
                    "type_diffs": [
                        {"field": f, "live": lv, "local": lo}
                        for f, lv, lo in ed.type_diffs
                    ],
                    "required_diff": ed.required_diff,
                    "live_required": ed.live_required,
                    "local_required": ed.local_required,
                }
                for ed in report.drifted_endpoints
            ],
        },
        indent=2,
    )


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
        "--live",
        type=Path,
        default=DEFAULT_LIVE,
        help=(
            f"Path to live/upstream OpenAPI spec "
            f"(default: {DEFAULT_LIVE.relative_to(REPO_ROOT)}). "
            "Refresh with scripts/extract_all_katana_docs.py."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write report to FILE instead of stdout",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any drift is detected (for CI gating)",
    )
    args = parser.parse_args(argv)

    if not args.local.exists():
        print(f"error: local spec not found: {args.local}", file=sys.stderr)
        return 2
    if not args.live.exists():
        print(
            f"error: live spec not found: {args.live}\n"
            f"hint: run `uv run python scripts/extract_all_katana_docs.py` first",
            file=sys.stderr,
        )
        return 2

    local = load_spec(args.local)
    live = load_spec(args.live)
    report = audit(local, live)

    out = format_json(report) if args.json else format_markdown(report)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"wrote report to {args.output}", file=sys.stderr)
    else:
        print(out)

    if args.strict and report.total_drift_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
