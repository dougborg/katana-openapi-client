#!/usr/bin/env python3
"""Audit ``docs/katana-openapi.yaml`` against the canonical Katana OpenAPI spec.

Compares the local spec with the live upstream spec at
``docs/upstream-specs/live-gateway.yaml`` (refreshed by
``poe refresh-upstream-spec`` from
``https://api.katanamrp.com/v1/openapi.json``).

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

Two further dimensions run by default (disable with ``--no-params`` /
``--no-responses``):

5. **Query-parameter drift** (``--params``) — compares query parameters of
   shared operations against the live gateway by *wire name* (resolving
   ``$ref``'d component params): ``param_only_local`` / ``param_only_live`` /
   ``param_type_diff`` / ``param_enum_diff``. The ``pagination`` / ``dateFilter``
   JSON-blob expansion is filtered structurally (see ``STRUCTURAL_PARAM_NAMES``).
6. **Response-shape drift** (``--responses``) — missing response bodies
   (``response_empty_local`` / ``response_empty_both``) and ``{data: ...}``
   wrapper mismatches (``response_wrapper``). The live gateway has empty 2xx
   bodies, so the reference is the readme **portal** spec (``--portal``), which
   carries response *examples* (no schemas, so no response-level schema compare).

**Override registry.** Known divergences are catalogued in
``docs/upstream-specs/audit-overrides.yaml`` and applied by default. A finding
that matches an override is **suppressed** from the strict gate and re-surfaced
under a category section (intentional divergence, upstream punch list, or
pending local fix). Matching is narrow — an override pins the exact
(endpoint, kind, field, values) — so a spec change that alters the divergence
resurfaces it as new drift instead of staying hidden. Pass ``--no-overrides``
to see raw drift; ``--overrides PATH`` to point at a different registry.

Default output is Markdown to stdout; ``--json`` emits a machine-readable
report; ``--output FILE`` writes to disk. Exit code is **0 on success**
regardless of drift, so the command works equally well for human
inspection and CI. Pass ``--strict`` to exit 1 on any *un-overridden* drift
**or any stale override** (an entry that no longer matches anything — the
divergence it allowlisted is gone, so it must be removed); ``2`` is reserved
for script errors (missing input file, invalid YAML, invalid registry, etc.).

Usage:

    uv run python scripts/audit_spec_drift.py
    uv run python scripts/audit_spec_drift.py --no-overrides    # raw drift
    uv run python scripts/audit_spec_drift.py --json --output drift.json
    uv run poe audit-spec
    uv run poe audit-spec-strict                                # CI gate
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scripts._yaml import safe_load_yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL = REPO_ROOT / "docs" / "katana-openapi.yaml"
DEFAULT_LIVE = REPO_ROOT / "docs" / "upstream-specs" / "live-gateway.yaml"
DEFAULT_PORTAL = REPO_ROOT / "docs" / "upstream-specs" / "readme-portal.yaml"
DEFAULT_OVERRIDES = REPO_ROOT / "docs" / "upstream-specs" / "audit-overrides.yaml"

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

# Response statuses that legitimately carry no body — never flagged as empty.
BODYLESS_STATUSES = {"204", "205", "304"}

# Query params the local spec systematically expands from upstream's two opaque
# JSON-blob params: `pagination` → explicit `page`/`limit`, and `dateFilter` →
# the explicit created/updated bound scalars. This is a *universal* local
# convention applied across ~40 list endpoints, not per-endpoint drift, so it is
# filtered structurally here rather than catalogued as ~350 override entries
# (the registry is for narrow, per-endpoint divergences). Analogous to the way
# ``normalize_type`` structurally treats integer↔number as equivalent.
STRUCTURAL_PARAM_NAMES = frozenset(
    {
        "pagination",
        "dateFilter",
        "page",
        "limit",
        "created_at_min",
        "created_at_max",
        "updated_at_min",
        "updated_at_max",
    }
)

# Override categories. See docs/upstream-specs/audit-overrides.yaml for the
# full semantics. PUNCH_LIST_CATEGORIES are upstream bugs we'd recommend Katana
# fix; PENDING_LOCAL_CATEGORY is local-is-wrong, allowlisted only until fixed.
CATEGORY_INTENTIONAL = "intentional_local_divergence"
CATEGORY_UPSTREAM_WRONG = "local_correct_upstream_wrong"
CATEGORY_BOTH_WRONG = "both_wrong_live_correct"
CATEGORY_LOCAL_WRONG = "upstream_correct_local_wrong"
ALL_CATEGORIES = frozenset(
    {
        CATEGORY_INTENTIONAL,
        CATEGORY_UPSTREAM_WRONG,
        CATEGORY_BOTH_WRONG,
        CATEGORY_LOCAL_WRONG,
    }
)
PUNCH_LIST_CATEGORIES = frozenset({CATEGORY_UPSTREAM_WRONG, CATEGORY_BOTH_WRONG})

# DTO/request-body drift kinds (the original audit dimension).
DTO_KINDS = frozenset({"type_diff", "only_live", "only_local", "required_diff"})
# Query-parameter drift kinds (--params). Mirror the DTO kinds in param space.
PARAM_KINDS = frozenset(
    {"param_only_local", "param_only_live", "param_type_diff", "param_enum_diff"}
)
# Response-shape drift kinds (--responses).
RESPONSE_KINDS = frozenset(
    {"response_empty_local", "response_empty_both", "response_wrapper"}
)
# Kinds whose override entry pins exact `field` + `live`/`local` strings.
TYPED_KINDS = frozenset(
    {"type_diff", "param_type_diff", "param_enum_diff", "response_wrapper"}
)
# Kinds whose override entry pins a `field` (param name or status code).
FIELDED_KINDS = (
    frozenset({"type_diff", "only_live", "only_local"}) | PARAM_KINDS | RESPONSE_KINDS
)
OVERRIDE_KINDS = DTO_KINDS | PARAM_KINDS | RESPONSE_KINDS


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
    # Set by apply_overrides when a registry entry suppresses the required diff.
    required_diff_suppressed: bool = False

    @property
    def required_diff(self) -> bool:
        return set(self.live_required) != set(self.local_required)

    @property
    def has_drift(self) -> bool:
        """True if any *active* (un-suppressed) finding remains.

        ``apply_overrides`` removes suppressed field/type findings from the
        list attributes in place, so they only ever hold active findings here;
        the required diff is gated separately via ``required_diff_suppressed``.
        """
        return bool(
            self.only_live_fields
            or self.only_local_fields
            or self.type_diffs
            or (self.required_diff and not self.required_diff_suppressed)
        )


@dataclass
class ParamFinding:
    """One query-parameter drift finding, scoped to ``(endpoint, name)``.

    ``kind`` is one of ``PARAM_KINDS`` and maps directly onto an override
    ``kind`` so the same registry suppresses it:

    - ``param_only_local`` — we expose it, upstream doesn't.
    - ``param_only_live`` — upstream documents it, we don't (missing filter).
    - ``param_type_diff`` — both declare it, wire types disagree.
    - ``param_enum_diff`` — both declare an enum, value sets disagree.
    """

    method: str
    path: str
    name: str
    kind: str
    live: str | None = None  # type signature (param_type_diff / param_enum_diff)
    local: str | None = None

    @property
    def endpoint(self) -> str:
        return f"{self.method.upper()} {self.path}"


@dataclass
class ResponseFinding:
    """One response-shape drift finding, scoped to ``(endpoint, status)``.

    ``kind`` is one of ``RESPONSE_KINDS``:

    - ``response_empty_local`` — local declares no body but upstream documents
      one (the #527 class).
    - ``response_empty_both`` — neither side declares a body on a
      non-DELETE / non-204 operation.
    - ``response_wrapper`` — local ``{data: ...}`` wrapper vs a bare upstream
      example, or vice versa.

    Note: there is no response-level *schema* comparison — the live gateway has
    empty bodies for every 2xx and the readme portal carries only ``example``
    blocks (no ``schema``), so body presence and wrapper shape are the only
    signals available.
    """

    method: str
    path: str
    status: str
    kind: str
    live: str | None = None  # wrapper shape ("wrapped"/"bare") for response_wrapper
    local: str | None = None

    @property
    def endpoint(self) -> str:
        return f"{self.method.upper()} {self.path}"


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
    # Active (un-suppressed) param/response findings, populated when the
    # corresponding audit dimension ran. apply_overrides drops suppressed ones.
    param_findings: list[ParamFinding] = field(default_factory=list)
    response_findings: list[ResponseFinding] = field(default_factory=list)

    # Populated by apply_overrides; empty when no registry is applied.
    suppressed: list[SuppressedFinding] = field(default_factory=list)
    stale_overrides: list[Override] = field(default_factory=list)

    @property
    def total_drift_count(self) -> int:
        """Count of everything ``--strict`` gates on.

        Suppressed findings are excluded (``apply_overrides`` drops fully
        suppressed endpoints from ``drifted_endpoints`` and removes suppressed
        param/response findings). **Stale overrides are included** — an override
        that matches nothing means the divergence it allowlisted is gone, so the
        entry must be removed. Failing on it keeps the registry honest even on
        spec-only PRs, where CI skips the Python test suite (the `code` path
        filter) and only the `audit-spec-strict` step runs.
        """
        return (
            len(self.paths_only_in_live)
            + len(self.paths_only_in_local)
            + len(self.drifted_endpoints)
            + len(self.param_findings)
            + len(self.response_findings)
            + len(self.stale_overrides)
        )


@dataclass(frozen=True)
class Override:
    """One registry entry suppressing a known divergence."""

    endpoint: str  # "POST /sales_orders/search"
    kind: str  # one of OVERRIDE_KINDS
    category: str  # one of ALL_CATEGORIES
    reason: str
    field_name: str | None = None  # type_diff / only_live / only_local
    live: str | None = None  # type_diff only
    local: str | None = None  # type_diff only
    live_required: tuple[str, ...] = ()  # required_diff only
    local_required: tuple[str, ...] = ()  # required_diff only
    fix_tracked_in: str | None = None


@dataclass
class SuppressedFinding:
    """A drift finding that matched an override, retained for reporting."""

    endpoint: str
    kind: str
    field_name: str | None
    detail: str  # human-readable rendering of the divergence
    override: Override


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def load_spec(path: Path) -> dict[str, Any]:
    """Load a spec from JSON or YAML based on extension."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return safe_load_yaml(text)
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


def audit(
    local: dict[str, Any],
    live: dict[str, Any],
    *,
    portal: dict[str, Any] | None = None,
    include_params: bool = True,
    include_responses: bool = True,
) -> AuditReport:
    """Run the full audit and return a structured report.

    The DTO/path comparison always runs. ``include_params`` adds query-parameter
    drift (vs the live gateway); ``include_responses`` adds response-shape drift
    (vs the readme ``portal`` spec, which carries the only upstream response
    examples). Both default on so the strict gate covers every dimension; pass
    ``portal=None`` to skip the response audit when the portal spec is absent.
    """
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

    if include_params:
        report.param_findings = audit_params(local, live)
    if include_responses and portal is not None:
        report.response_findings = audit_responses(local, portal)

    return report


# ----------------------------------------------------------------------------
# Query-parameter audit (--params)
# ----------------------------------------------------------------------------


def resolve_query_params(
    spec: dict[str, Any], op: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Map wire ``name`` → parameter schema for an operation's query params.

    Resolves ``$ref`` parameters (local refs ``components/parameters``; the live
    gateway inlines them) and keys by the wire ``name`` — not the component key —
    so ``components/parameters/sku_list`` (wire name ``sku``) lines up across
    specs.
    """
    comps = spec.get("components", {}).get("parameters", {})
    out: dict[str, dict[str, Any]] = {}
    for raw in op.get("parameters", []):
        param = comps.get(raw["$ref"].rsplit("/", 1)[-1], {}) if "$ref" in raw else raw
        if param.get("in") != "query":
            continue
        name = param.get("name")
        if name:
            out[name] = param
    return out


def param_type_sig(schema: dict[str, Any]) -> str:
    """Wire-type signature for a query param's ``schema``.

    Arrays render as ``array<itemtype>`` (so scalar-vs-array and item-type drift
    surface); everything else delegates to ``normalize_type``.
    """
    if schema.get("type") == "array":
        items = schema.get("items", {}) or {}
        return f"array<{normalize_type(items)}>"
    return normalize_type(schema)


def param_types_equivalent(
    live_p: dict[str, Any], local_p: dict[str, Any], local_schemas: dict[str, Any]
) -> bool:
    """True if two query-param schemas are the same wire type.

    Arrays compare by item type; everything else delegates to ``types_equivalent``
    (canonicalizes integer↔number and resolves a local ``$ref`` enum against a
    live inline enum, so ``live=enum:[…]`` ↔ ``local=$ref:SomeEnum`` isn't flagged
    when the value sets match).
    """
    live_s = live_p.get("schema", {})
    local_s = local_p.get("schema", {})
    if live_s.get("type") == "array" or local_s.get("type") == "array":
        canon = {"integer": "number"}

        def c(s: str) -> str:
            if s.startswith("array<") and s.endswith(">"):
                inner = s[len("array<") : -1]
                return f"array<{canon.get(inner, inner)}>"
            return canon.get(s, s)

        return c(param_type_sig(live_s)) == c(param_type_sig(local_s))
    return types_equivalent(live_s, local_s, local_schemas)


def resolve_param_enum(
    schema: dict[str, Any], schemas: dict[str, Any]
) -> set[str] | None:
    """Enum value set for a param schema, resolving a ``$ref`` to a shared enum."""
    enum = schema.get("enum")
    if enum:
        return {str(v) for v in enum}
    ref = schema.get("$ref")
    if ref:
        ref_enum = schemas.get(ref.rsplit("/", 1)[-1], {}).get("enum")
        if ref_enum:
            return {str(v) for v in ref_enum}
    return None


def audit_params(local: dict[str, Any], live: dict[str, Any]) -> list[ParamFinding]:
    """Compare query parameters of shared operations (local ↔ live gateway)."""
    live_schemas = live.get("components", {}).get("schemas", {})
    local_schemas = local.get("components", {}).get("schemas", {})
    findings: list[ParamFinding] = []
    for path, methods in sorted(local.get("paths", {}).items()):
        for method, op in methods.items():
            if method not in HTTP_METHODS:
                continue
            live_op = live.get("paths", {}).get(path, {}).get(method)
            if not live_op:
                continue
            local_params = resolve_query_params(local, op)
            live_params = resolve_query_params(live, live_op)
            for name in sorted(set(local_params) | set(live_params)):
                if name in STRUCTURAL_PARAM_NAMES:
                    continue
                in_local = name in local_params
                in_live = name in live_params
                if in_local and not in_live:
                    findings.append(
                        ParamFinding(
                            method=method,
                            path=path,
                            name=name,
                            kind="param_only_local",
                            local=param_type_sig(local_params[name].get("schema", {})),
                        )
                    )
                elif in_live and not in_local:
                    findings.append(
                        ParamFinding(
                            method=method,
                            path=path,
                            name=name,
                            kind="param_only_live",
                            live=param_type_sig(live_params[name].get("schema", {})),
                        )
                    )
                else:
                    live_s = live_params[name].get("schema", {})
                    local_s = local_params[name].get("schema", {})
                    if param_types_equivalent(
                        live_params[name], local_params[name], local_schemas
                    ):
                        continue
                    live_e = resolve_param_enum(live_s, live_schemas)
                    local_e = resolve_param_enum(local_s, local_schemas)
                    if live_e is not None and local_e is not None:
                        # Both enums; equal values are just the live-omits-`type`
                        # shape that types_equivalent can't see through.
                        if live_e == local_e:
                            continue
                        findings.append(
                            ParamFinding(
                                method=method,
                                path=path,
                                name=name,
                                kind="param_enum_diff",
                                live=f"enum:[{','.join(sorted(live_e))}]",
                                local=f"enum:[{','.join(sorted(local_e))}]",
                            )
                        )
                    else:
                        findings.append(
                            ParamFinding(
                                method=method,
                                path=path,
                                name=name,
                                kind="param_type_diff",
                                live=param_type_sig(live_s),
                                local=param_type_sig(local_s),
                            )
                        )
    return findings


# ----------------------------------------------------------------------------
# Response-shape audit (--responses)
# ----------------------------------------------------------------------------


def resolve_response(spec: dict[str, Any], resp: dict[str, Any]) -> dict[str, Any]:
    """Resolve a ``$ref`` response object to its ``components/responses`` entry."""
    if "$ref" in resp:
        name = resp["$ref"].rsplit("/", 1)[-1]
        return spec.get("components", {}).get("responses", {}).get(name, {})
    return resp


def example_is_wrapped(resp: dict[str, Any]) -> bool | None:
    """Wrapper shape of an upstream response *example*, or ``None`` if unknown.

    ``True`` for a ``{"data": [...]}`` envelope, ``False`` for a bare array,
    ``None`` when there's no usable example (a bare single object also → ``None``).
    """
    for cval in (resp.get("content") or {}).values():
        ex = cval.get("example")
        if isinstance(ex, dict) and isinstance(ex.get("data"), list):
            return True
        if isinstance(ex, list):
            return False
    return None


def local_response_is_wrapped(
    spec: dict[str, Any], schemas: dict[str, Any], resp: dict[str, Any]
) -> bool | None:
    """Wrapper shape of a *local* response, read off its resolved schema."""
    for cval in (resp.get("content") or {}).values():
        schema = cval.get("schema", {})
        if schema.get("type") == "array":
            return False
        ref = schema.get("$ref")
        if ref:
            props, _ = fields_of(spec, schemas, ref.rsplit("/", 1)[-1])
            data = props.get("data")
            if data is not None:
                return data.get("type") == "array" or "items" in data
        elif schema.get("type") == "object" and "data" in schema.get("properties", {}):
            return True
    return None


def audit_responses(
    local: dict[str, Any], portal: dict[str, Any]
) -> list[ResponseFinding]:
    """Compare response shapes (local ↔ readme-portal examples)."""
    local_schemas = local.get("components", {}).get("schemas", {})
    findings: list[ResponseFinding] = []
    for path, methods in sorted(local.get("paths", {}).items()):
        for method, op in methods.items():
            if method not in HTTP_METHODS:
                continue
            portal_op = portal.get("paths", {}).get(path, {}).get(method)
            for raw_status, resp in (op.get("responses") or {}).items():
                status = str(raw_status)
                if not status.startswith("2") or status in BODYLESS_STATUSES:
                    continue
                local_resp = resolve_response(local, resp)
                local_has_body = bool(local_resp.get("content"))

                portal_resp: dict[str, Any] | None = None
                if portal_op and status in (portal_op.get("responses") or {}):
                    portal_resp = resolve_response(
                        portal, portal_op["responses"][status]
                    )

                if not local_has_body:
                    if method == "delete":
                        continue
                    # No corresponding portal response → no upstream signal. Don't
                    # guess "both empty" (the portal simply may not document this
                    # operation/status); only flag when the portal corroborates.
                    if portal_resp is None:
                        continue
                    findings.append(
                        ResponseFinding(
                            method=method,
                            path=path,
                            status=status,
                            kind=(
                                "response_empty_local"
                                if portal_resp.get("content")
                                else "response_empty_both"
                            ),
                        )
                    )
                    continue

                if portal_resp is None:
                    continue
                portal_wrapped = example_is_wrapped(portal_resp)
                if portal_wrapped is None:
                    continue
                local_wrapped = local_response_is_wrapped(
                    local, local_schemas, local_resp
                )
                if local_wrapped is None or local_wrapped == portal_wrapped:
                    continue
                findings.append(
                    ResponseFinding(
                        method=method,
                        path=path,
                        status=status,
                        kind="response_wrapper",
                        live="wrapped" if portal_wrapped else "bare",
                        local="wrapped" if local_wrapped else "bare",
                    )
                )
    return findings


# ----------------------------------------------------------------------------
# Override registry
# ----------------------------------------------------------------------------


def load_overrides(path: Path) -> list[Override]:
    """Load + validate the override registry. Raises ValueError on bad schema."""
    raw = safe_load_yaml(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("overrides") or []
    if not isinstance(entries, list):
        raise ValueError(f"{path}: `overrides` must be a list")

    out: list[Override] = []
    for i, e in enumerate(entries):
        where = f"{path} entry [{i}]"
        if not isinstance(e, dict):
            raise ValueError(f"{where}: must be a mapping")
        endpoint = e.get("endpoint")
        kind = e.get("kind")
        category = e.get("category")
        reason = e.get("reason")
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError(f"{where}: missing `endpoint`")
        if kind not in OVERRIDE_KINDS:
            raise ValueError(f"{where}: `kind` must be one of {sorted(OVERRIDE_KINDS)}")
        if category not in ALL_CATEGORIES:
            raise ValueError(
                f"{where}: `category` must be one of {sorted(ALL_CATEGORIES)}"
            )
        if not reason or not isinstance(reason, str):
            raise ValueError(f"{where}: missing `reason`")
        fix_tracked_in = e.get("fix_tracked_in")
        if category == CATEGORY_LOCAL_WRONG and not fix_tracked_in:
            raise ValueError(
                f"{where}: category `{CATEGORY_LOCAL_WRONG}` requires `fix_tracked_in`"
            )

        field_name = e.get("field")
        if kind in FIELDED_KINDS and (
            not isinstance(field_name, str) or not field_name
        ):
            raise ValueError(
                f"{where}: kind `{kind}` requires `field` (a non-empty string; "
                "the property/param name, or status code for response kinds)"
            )
        if kind in TYPED_KINDS and ("live" not in e or "local" not in e):
            raise ValueError(f"{where}: kind `{kind}` requires `live` + `local`")
        if kind == "required_diff":
            if "live_required" not in e or "local_required" not in e:
                raise ValueError(
                    f"{where}: kind `required_diff` requires "
                    f"`live_required` + `local_required`"
                )
            for key in ("live_required", "local_required"):
                val = e[key]
                if not isinstance(val, list) or not all(
                    isinstance(x, str) for x in val
                ):
                    raise ValueError(
                        f"{where}: `{key}` must be a list of strings "
                        f"(got {type(val).__name__}) — did you write a bare scalar "
                        f"instead of a YAML list?"
                    )

        out.append(
            Override(
                endpoint=endpoint,
                kind=kind,
                category=category,
                reason=" ".join(reason.split()),
                field_name=field_name,
                live=str(e["live"]) if "live" in e else None,
                local=str(e["local"]) if "local" in e else None,
                live_required=tuple(e.get("live_required") or ()),
                local_required=tuple(e.get("local_required") or ()),
                fix_tracked_in=fix_tracked_in,
            )
        )
    return out


def apply_overrides(report: AuditReport, overrides: list[Override]) -> None:
    """Suppress findings that match a registry entry; mutate ``report`` in place.

    Matched sub-findings are removed from each endpoint's active lists and
    recorded in ``report.suppressed``. Endpoints with no remaining active drift
    drop out of ``report.drifted_endpoints``. Overrides that match nothing are
    recorded in ``report.stale_overrides``.
    """
    used: set[int] = set()
    suppressed: list[SuppressedFinding] = []

    def take(endpoint: str, kind: str, predicate: Any) -> Override | None:
        for i, ov in enumerate(overrides):
            if i in used:
                continue
            if ov.endpoint == endpoint and ov.kind == kind and predicate(ov):
                used.add(i)
                return ov
        return None

    remaining: list[EndpointDrift] = []
    for ed in report.drifted_endpoints:
        endpoint = f"{ed.method.upper()} {ed.path}"

        kept_type: list[tuple[str, str, str]] = []
        for f, lv, lo in ed.type_diffs:
            ov = take(
                endpoint,
                "type_diff",
                lambda o, f=f, lv=lv, lo=lo: (
                    o.field_name == f and o.live == lv and o.local == lo
                ),
            )
            if ov:
                suppressed.append(
                    SuppressedFinding(
                        endpoint, "type_diff", f, f"live=`{lv}` local=`{lo}`", ov
                    )
                )
            else:
                kept_type.append((f, lv, lo))
        ed.type_diffs = kept_type

        for attr, kind in (
            ("only_live_fields", "only_live"),
            ("only_local_fields", "only_local"),
        ):
            kept: list[str] = []
            for f in getattr(ed, attr):
                ov = take(endpoint, kind, lambda o, f=f: o.field_name == f)
                if ov:
                    suppressed.append(
                        SuppressedFinding(endpoint, kind, f, f"`{f}`", ov)
                    )
                else:
                    kept.append(f)
            setattr(ed, attr, kept)

        if ed.required_diff:
            ov = take(
                endpoint,
                "required_diff",
                lambda o, ed=ed: (
                    set(o.live_required) == set(ed.live_required)
                    and set(o.local_required) == set(ed.local_required)
                ),
            )
            if ov:
                ed.required_diff_suppressed = True
                suppressed.append(
                    SuppressedFinding(
                        endpoint,
                        "required_diff",
                        None,
                        f"live={ed.live_required} local={ed.local_required}",
                        ov,
                    )
                )

        if ed.has_drift:
            remaining.append(ed)

    report.drifted_endpoints = remaining

    # Query-parameter findings: match on (endpoint, kind, field=name) and, for
    # the typed kinds, the exact live/local signatures.
    kept_params: list[ParamFinding] = []
    for pf in report.param_findings:
        ov = take(
            pf.endpoint,
            pf.kind,
            lambda o, pf=pf: (
                o.field_name == pf.name
                and (
                    o.kind not in TYPED_KINDS
                    or (o.live == pf.live and o.local == pf.local)
                )
            ),
        )
        if ov:
            detail = (
                f"live=`{pf.live}` local=`{pf.local}`"
                if pf.kind in TYPED_KINDS
                else (f"local=`{pf.local}`" if pf.local else f"live=`{pf.live}`")
            )
            suppressed.append(
                SuppressedFinding(pf.endpoint, pf.kind, pf.name, detail, ov)
            )
        else:
            kept_params.append(pf)
    report.param_findings = kept_params

    # Response findings: match on (endpoint, kind, field=status) and, for
    # response_wrapper, the exact shapes.
    kept_responses: list[ResponseFinding] = []
    for rf in report.response_findings:
        ov = take(
            rf.endpoint,
            rf.kind,
            lambda o, rf=rf: (
                o.field_name == rf.status
                and (
                    o.kind != "response_wrapper"
                    or (o.live == rf.live and o.local == rf.local)
                )
            ),
        )
        if ov:
            detail = (
                f"local {rf.local} vs upstream {rf.live}"
                if rf.kind == "response_wrapper"
                else f"status {rf.status} has no body"
            )
            suppressed.append(
                SuppressedFinding(rf.endpoint, rf.kind, rf.status, detail, ov)
            )
        else:
            kept_responses.append(rf)
    report.response_findings = kept_responses

    report.suppressed = suppressed
    report.stale_overrides = [ov for i, ov in enumerate(overrides) if i not in used]


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
    if report.param_findings:
        lines.append(f"- Query-parameter drift: **{len(report.param_findings)}**")
    if report.response_findings:
        lines.append(f"- Response-shape drift: **{len(report.response_findings)}**")
    if report.suppressed or report.stale_overrides:
        lines.append(
            f"- Suppressed by override registry: **{len(report.suppressed)}** "
            f"({len(report.stale_overrides)} stale overrides)"
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
            if ed.required_diff and not ed.required_diff_suppressed:
                lines.append("- ❗ required diff:")
                lines.append(f"    - live  required: `{ed.live_required}`")
                lines.append(f"    - local required: `{ed.local_required}`")
            lines.append("")

    if report.param_findings:
        lines.append("## Query-parameter drift")
        lines.append("")
        for pf in report.param_findings:
            if pf.kind in TYPED_KINDS:
                detail = f"live=`{pf.live}` local=`{pf.local}`"
            elif pf.kind == "param_only_live":
                detail = f"missing locally (live=`{pf.live}`)"
            else:
                detail = f"not in upstream (local=`{pf.local}`)"
            lines.append(f"- `{pf.endpoint}` `{pf.name}` ({pf.kind}): {detail}")
        lines.append("")

    if report.response_findings:
        lines.append("## Response-shape drift")
        lines.append("")
        for rf in report.response_findings:
            if rf.kind == "response_wrapper":
                detail = f"local {rf.local} vs upstream {rf.live}"
            else:
                detail = "no response body declared"
            lines.append(f"- `{rf.endpoint}` ({rf.status}) {rf.kind}: {detail}")
        lines.append("")

    _append_override_sections(lines, report)
    return "\n".join(lines)


def _append_override_sections(lines: list[str], report: AuditReport) -> None:
    """Render the suppressed-divergence, punch-list, and stale sections."""

    def render(group: list[SuppressedFinding]) -> None:
        for sf in group:
            tracked = (
                f" (tracked in {sf.override.fix_tracked_in})"
                if sf.override.fix_tracked_in
                else ""
            )
            field_part = f" `{sf.field_name}`" if sf.field_name else ""
            lines.append(f"- `{sf.endpoint}`{field_part} — {sf.detail}{tracked}")
            lines.append(f"  - {sf.override.reason}")

    punch = [
        s for s in report.suppressed if s.override.category in PUNCH_LIST_CATEGORIES
    ]
    pending = [
        s for s in report.suppressed if s.override.category == CATEGORY_LOCAL_WRONG
    ]
    intentional = [
        s for s in report.suppressed if s.override.category == CATEGORY_INTENTIONAL
    ]

    if punch:
        lines.append("## 📋 Upstream punch list (recommend Katana fix)")
        lines.append("")
        lines.append(
            "Divergences where our spec matches the real wire contract but "
            "Katana's published spec is wrong or under-documented."
        )
        lines.append("")
        render(punch)
        lines.append("")

    if pending:
        lines.append("## ⚠ Pending local fixes (allowlisted)")
        lines.append("")
        lines.append(
            "Local spec is wrong; allowlisted only so the gate stays green. "
            "Remove each entry when its tracked fix lands."
        )
        lines.append("")
        render(pending)
        lines.append("")

    if intentional:
        lines.append("## Accepted divergences (intentional)")
        lines.append("")
        render(intentional)
        lines.append("")

    if report.stale_overrides:
        lines.append("## 🧹 Stale overrides (drift resolved — remove these)")
        lines.append("")
        lines.append(
            "These registry entries matched no current finding. The divergence "
            "they suppressed is gone; delete them from the registry."
        )
        lines.append("")
        for ov in report.stale_overrides:
            field_part = f" `{ov.field_name}`" if ov.field_name else ""
            lines.append(f"- `{ov.endpoint}`{field_part} ({ov.kind}) — {ov.category}")
        lines.append("")


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
                    "required_diff": ed.required_diff
                    and not ed.required_diff_suppressed,
                    "live_required": ed.live_required,
                    "local_required": ed.local_required,
                }
                for ed in report.drifted_endpoints
            ],
            "param_findings": [
                {
                    "method": pf.method,
                    "path": pf.path,
                    "name": pf.name,
                    "kind": pf.kind,
                    "live": pf.live,
                    "local": pf.local,
                }
                for pf in report.param_findings
            ],
            "response_findings": [
                {
                    "method": rf.method,
                    "path": rf.path,
                    "status": rf.status,
                    "kind": rf.kind,
                    "live": rf.live,
                    "local": rf.local,
                }
                for rf in report.response_findings
            ],
            "suppressed": [
                {
                    "endpoint": sf.endpoint,
                    "kind": sf.kind,
                    "field": sf.field_name,
                    "category": sf.override.category,
                    "reason": sf.override.reason,
                    "fix_tracked_in": sf.override.fix_tracked_in,
                }
                for sf in report.suppressed
            ],
            "punch_list": [
                {
                    "endpoint": sf.endpoint,
                    "field": sf.field_name,
                    "category": sf.override.category,
                    "reason": sf.override.reason,
                }
                for sf in report.suppressed
                if sf.override.category in PUNCH_LIST_CATEGORIES
            ],
            "stale_overrides": [
                {"endpoint": ov.endpoint, "kind": ov.kind, "field": ov.field_name}
                for ov in report.stale_overrides
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
            "Refresh with `poe refresh-upstream-spec`."
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
    parser.add_argument(
        "--overrides",
        type=Path,
        default=None,
        help=(
            f"Path to the override registry "
            f"(default: {DEFAULT_OVERRIDES.relative_to(REPO_ROOT)}). "
            "Matched findings are suppressed from --strict."
        ),
    )
    parser.add_argument(
        "--no-overrides",
        action="store_true",
        help="Ignore the override registry — report all raw drift.",
    )
    parser.add_argument(
        "--portal",
        type=Path,
        default=DEFAULT_PORTAL,
        help=(
            f"Path to the readme-portal spec — the response-shape reference "
            f"(default: {DEFAULT_PORTAL.relative_to(REPO_ROOT)}). The live gateway "
            "has empty response bodies, so the --responses audit reads body "
            "presence + wrapper shape from the portal's examples."
        ),
    )
    parser.add_argument(
        "--no-params",
        action="store_true",
        help="Skip the query-parameter audit dimension.",
    )
    parser.add_argument(
        "--no-responses",
        action="store_true",
        help="Skip the response-shape audit dimension.",
    )
    args = parser.parse_args(argv)

    if not args.local.exists():
        print(f"error: local spec not found: {args.local}", file=sys.stderr)
        return 2
    if not args.live.exists():
        print(
            f"error: live spec not found: {args.live}\n"
            f"hint: run `uv run poe refresh-upstream-spec` first",
            file=sys.stderr,
        )
        return 2

    local = load_spec(args.local)
    live = load_spec(args.live)

    portal: dict[str, Any] | None = None
    if not args.no_responses:
        if args.portal.exists():
            portal = load_spec(args.portal)
        else:
            print(
                f"warning: portal spec not found ({args.portal}); skipping the "
                "response-shape audit. Run `uv run poe refresh-upstream-spec`.",
                file=sys.stderr,
            )

    report = audit(
        local,
        live,
        portal=portal,
        include_params=not args.no_params,
        include_responses=not args.no_responses,
    )

    if not args.no_overrides:
        # An explicit --overrides PATH must exist (a typo shouldn't silently run
        # with no overrides). The default registry is skipped if absent so the
        # script still works in a checkout that predates it.
        explicit = args.overrides is not None
        overrides_path = args.overrides if explicit else DEFAULT_OVERRIDES
        if explicit and not overrides_path.exists():
            print(
                f"error: override registry not found: {overrides_path}\n"
                f"hint: pass --no-overrides to run without one",
                file=sys.stderr,
            )
            return 2
        if overrides_path.exists():
            try:
                overrides = load_overrides(overrides_path)
            except (ValueError, yaml.YAMLError, OSError) as exc:
                # ValueError: schema violation; YAMLError: malformed YAML;
                # OSError: read failure. All are config/script errors → exit 2.
                print(f"error: invalid override registry: {exc}", file=sys.stderr)
                return 2
            apply_overrides(report, overrides)

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
