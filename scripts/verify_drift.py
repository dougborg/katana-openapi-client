#!/usr/bin/env python3
"""Verify suspected spec-drift findings against the live Katana API.

Companion to ``audit_spec_drift.py`` and ``validate_response_examples.py``.
Where those tools surface *suspected* drift by comparing local YAML against
upstream YAML / README.io examples, this script makes **live API calls** and
reports what Katana actually puts on the wire — the ultimate source of truth.

Each finding is keyed by an ID matching ``docs/audit-2026-05-06.md``
(F1, F2, …). Run a single finding with ``verify F1`` or the full suite with
``verify --all``. Output is structured JSON / Markdown so it can land directly
in the audit doc or in issue comments.

Bypasses the typed client deliberately for findings that question the typed
client's signature (e.g. F1 — `variant_id: int` vs `array[int]`). Loads
credentials from the primary worktree's ``.env`` if ``KATANA_API_KEY`` is not
already set in the environment.

Usage:

    uv run python scripts/verify_drift.py F1
    uv run python scripts/verify_drift.py --all --output docs/audit-2026-05-06.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY_WORKTREE_ENV = Path("/Users/dougborg/Projects/katana-openapi-client/.env")
DEFAULT_BASE_URL = "https://api.katanamrp.com/v1"


# ---------------------------------------------------------------------------
# Result types


@dataclass
class CallResult:
    method: str
    url: str
    params: dict[str, Any]
    status_code: int
    response_keys: list[str] | None = None
    response_count: int | None = None
    sample_record: dict[str, Any] | None = None
    raw_excerpt: str = ""


@dataclass
class FindingResult:
    finding_id: str
    title: str
    hypothesis: str
    calls: list[CallResult] = field(default_factory=list)
    conclusion: str = ""
    triage_category: str = ""
    suggested_action: str = ""


# ---------------------------------------------------------------------------
# Helpers


def make_client() -> httpx.Client:
    """Create an httpx client with live-API credentials.

    Loads ``.env`` from the primary worktree if ``KATANA_API_KEY`` isn't
    already set. Raises if no key is found.
    """
    if "KATANA_API_KEY" not in os.environ and PRIMARY_WORKTREE_ENV.exists():
        load_dotenv(PRIMARY_WORKTREE_ENV)
    api_key = os.environ.get("KATANA_API_KEY")
    if not api_key:
        raise SystemExit(
            f"KATANA_API_KEY required (set env var or populate {PRIMARY_WORKTREE_ENV})"
        )
    base_url = os.environ.get("KATANA_BASE_URL", DEFAULT_BASE_URL)
    return httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    )


def _capture(
    client: httpx.Client,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> CallResult:
    """Make one HTTP call and capture a structured summary of the response.

    Records top-level keys, count of `data` array if present, the first
    record (if list response), and a short raw excerpt. Doesn't raise on
    non-2xx — captures the status and what the server said.
    """
    request_params = params or {}
    response = client.request(method, path, params=request_params)
    raw_excerpt = response.text[:500] if response.text else ""

    result = CallResult(
        method=method,
        url=str(response.request.url),
        params=request_params,
        status_code=response.status_code,
        raw_excerpt=raw_excerpt,
    )

    if response.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return result
        if isinstance(payload, dict):
            result.response_keys = list(payload.keys())
            data = payload.get("data")
            if isinstance(data, list):
                result.response_count = len(data)
                if data:
                    result.sample_record = (
                        data[0] if isinstance(data[0], dict) else None
                    )
        elif isinstance(payload, list):
            result.response_keys = ["<bare-array>"]
            result.response_count = len(payload)
            if payload and isinstance(payload[0], dict):
                result.sample_record = payload[0]

    return result


# ---------------------------------------------------------------------------
# Verifications — one function per finding


def verify_F1(client: httpx.Client) -> FindingResult:
    """`/inventory variant_id` — int vs array[int]."""
    finding = FindingResult(
        finding_id="F1",
        title="GET /inventory variant_id — int vs array[int]",
        hypothesis=(
            "Wire accepts multi-value ?variant_id=<a>&variant_id=<b>; "
            "response narrows to those variants."
        ),
    )

    # First, find a couple of variant IDs that have inventory rows we can use
    # for the multi-value test.
    seed = _capture(client, "GET", "/inventory", {"limit": 5})
    finding.calls.append(seed)

    if seed.status_code != 200 or not seed.sample_record:
        finding.conclusion = (
            "Couldn't seed test — /inventory returned no rows or non-200."
        )
        return finding

    # Pull two variant_ids from the seeded response
    if not isinstance(seed.sample_record, dict):
        finding.conclusion = "Seed sample_record not a dict; aborting."
        return finding

    payload = client.get("/inventory", params={"limit": 10}).json()
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    variant_ids: list[int] = []
    for row in rows:
        v = row.get("variant_id")
        if isinstance(v, int) and v not in variant_ids:
            variant_ids.append(v)
        if len(variant_ids) >= 2:
            break

    if len(variant_ids) < 2:
        finding.conclusion = (
            "Couldn't find 2 distinct variant_ids in /inventory to test "
            "multi-value filtering."
        )
        return finding

    # Now try multi-value ?variant_id=<a>&variant_id=<b>
    multi = _capture(client, "GET", "/inventory", {"variant_id": variant_ids})
    finding.calls.append(multi)

    # Compare to single-value control
    single = _capture(client, "GET", "/inventory", {"variant_id": variant_ids[0]})
    finding.calls.append(single)

    multi_count = multi.response_count or 0
    single_count = single.response_count or 0

    if multi.status_code != 200:
        finding.conclusion = (
            f"Multi-value call returned {multi.status_code}; wire "
            "doesn't accept array form."
        )
        finding.triage_category = "intentional_local_divergence?"
        finding.suggested_action = "Investigate further — upstream spec may be wrong."
    elif multi_count > single_count:
        finding.conclusion = (
            f"Multi-value call returned {multi_count} rows vs single "
            f"{single_count}: confirms array filtering. Local spec lies."
        )
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Inline param on /inventory as type: array, items: integer."
        )
    else:
        finding.conclusion = (
            f"Multi-value call returned {multi_count} rows, single returned "
            f"{single_count}. Indeterminate — counts didn't widen."
        )
        finding.triage_category = "needs_more_investigation"

    return finding


def verify_F2(client: httpx.Client) -> FindingResult:
    """`/products batch_tracked` — boolean vs string."""
    finding = FindingResult(
        finding_id="F2",
        title="GET /products batch_tracked — boolean vs string",
        hypothesis=(
            "HTTP wire accepts both `true`/`false` (lowercase) regardless "
            "of how the spec types it. Real question: does Katana also "
            "accept literal Python `True` (capital T) or only canonical "
            "lowercase strings?"
        ),
    )

    base = _capture(client, "GET", "/products", {"limit": 5})
    finding.calls.append(base)

    finding.calls.append(
        _capture(client, "GET", "/products", {"limit": 5, "batch_tracked": "true"})
    )
    finding.calls.append(
        _capture(client, "GET", "/products", {"limit": 5, "batch_tracked": "false"})
    )
    finding.calls.append(
        _capture(client, "GET", "/products", {"limit": 5, "batch_tracked": "True"})
    )

    statuses = [c.status_code for c in finding.calls[1:]]
    if all(s == 200 for s in statuses):
        finding.conclusion = (
            "All forms returned 200. Likely: Katana accepts any case-folded "
            "truthy/falsy string. boolean→string typing both work in "
            "practice; openapi-python-client serializes True/False to "
            "lowercase, so the current local typing is functionally fine."
        )
        finding.triage_category = "stylistic_mismatch_no_runtime_impact"
        finding.suggested_action = (
            "Low priority. Could change local to string for upstream "
            "consistency, but not a runtime bug."
        )
    elif statuses[2] == 200 and statuses[3] != 200:
        finding.conclusion = (
            "lowercase 'true' works; capital-T 'True' doesn't. Local "
            "boolean typing must serialize lowercase — confirm openapi-"
            "python-client does this; if so, no runtime bug."
        )
        finding.triage_category = "stylistic_mismatch_no_runtime_impact"
    else:
        finding.conclusion = f"Mixed results: {statuses}. Investigate further."
        finding.triage_category = "needs_more_investigation"

    return finding


def verify_F18(client: httpx.Client) -> FindingResult:
    """`/operators` — bare array vs wrapped."""
    finding = FindingResult(
        finding_id="F18",
        title="GET /operators — bare array vs {data: [...]}",
        hypothesis=(
            "README example shows bare array; local schema says wrapped. "
            "Live response is the tiebreaker."
        ),
    )
    finding.calls.append(_capture(client, "GET", "/operators"))
    keys = finding.calls[0].response_keys or []
    if keys == ["<bare-array>"]:
        finding.conclusion = "Live API returns bare array. Local schema is wrong."
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Fix local schema: drop OperatorListResponse wrapper, return "
            "type: array directly."
        )
    elif "data" in keys:
        finding.conclusion = (
            "Live API returns {data: [...]} wrapped. README example is stale."
        )
        finding.triage_category = "stale_readme_example"
        finding.suggested_action = "No spec change needed."
    else:
        finding.conclusion = f"Unexpected response keys: {keys}"
        finding.triage_category = "needs_more_investigation"
    return finding


def verify_F20(client: httpx.Client) -> FindingResult:
    """`/bin_locations` — `name` vs `bin_name`."""
    finding = FindingResult(
        finding_id="F20",
        title="GET /bin_locations — name vs bin_name",
        hypothesis="Live response field name resolves spec/example mismatch.",
    )
    finding.calls.append(_capture(client, "GET", "/bin_locations", {"limit": 1}))
    sample = finding.calls[0].sample_record or {}
    has_name = "name" in sample
    has_bin_name = "bin_name" in sample
    if has_name and not has_bin_name:
        finding.conclusion = (
            "Live response has `name`. Local schema requires `bin_name` — wrong."
        )
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Fix local StorageBin: rename bin_name → name (or add name as "
            "the canonical field with bin_name as deprecated alias if "
            "back-compat matters)."
        )
    elif has_bin_name and not has_name:
        finding.conclusion = "Live response has `bin_name`. README example is stale."
        finding.triage_category = "stale_readme_example"
    elif has_name and has_bin_name:
        finding.conclusion = "Both fields present. Investigate semantics."
        finding.triage_category = "needs_more_investigation"
    else:
        finding.conclusion = (
            f"Neither field present. Sample keys: {list(sample.keys())}"
        )
        finding.triage_category = "needs_more_investigation"
    return finding


def verify_F19(client: httpx.Client) -> FindingResult:
    """`/purchase_order_accounting_metadata` — camelCase vs snake_case."""
    finding = FindingResult(
        finding_id="F19",
        title=("GET /purchase_order_accounting_metadata — camelCase vs snake_case"),
        hypothesis="Live response key casing resolves spec/example mismatch.",
    )
    finding.calls.append(
        _capture(client, "GET", "/purchase_order_accounting_metadata", {"limit": 1})
    )
    sample = finding.calls[0].sample_record or {}
    keys = list(sample.keys())
    has_camel = any("_" not in k and any(c.isupper() for c in k) for k in keys)
    has_snake = any("_" in k for k in keys)
    if has_camel and not has_snake:
        finding.conclusion = f"Live keys are camelCase: {keys}"
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Fix local PurchaseOrderAccountingMetadata: switch to camelCase, "
            "or add `x-aliases` if pydantic generation supports them."
        )
    elif has_snake and not has_camel:
        finding.conclusion = f"Live keys are snake_case: {keys}"
        finding.triage_category = "stale_readme_example"
    elif has_camel and has_snake:
        finding.conclusion = f"Mixed casing: {keys}"
        finding.triage_category = "needs_more_investigation"
    else:
        finding.conclusion = f"No keys captured: {keys}"
        finding.triage_category = "needs_more_investigation"
    return finding


def verify_F17(client: httpx.Client) -> FindingResult:
    """`/sales_order_shipping_fee.amount` — string vs number."""
    finding = FindingResult(
        finding_id="F17",
        title="GET /sales_order_shipping_fee — amount type",
        hypothesis="Real `amount` value type resolves spec/example mismatch.",
    )
    finding.calls.append(
        _capture(client, "GET", "/sales_order_shipping_fee", {"limit": 1})
    )
    sample = finding.calls[0].sample_record or {}
    amount = sample.get("amount")
    finding.conclusion = (
        f"Live `amount` value: {amount!r} (type: {type(amount).__name__})"
    )
    if isinstance(amount, str):
        finding.triage_category = "local_schema_correct"
        finding.suggested_action = "No change. README example is wrong."
    elif isinstance(amount, (int, float)):
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Fix local SalesOrderShippingFee.amount: type to number."
        )
    else:
        finding.triage_category = "needs_more_investigation"
    return finding


def verify_F22(client: httpx.Client) -> FindingResult:
    """`StockTransferStatus` enum values."""
    finding = FindingResult(
        finding_id="F22",
        title="StockTransferStatus enum values on the wire",
        hypothesis=(
            "Local: [pending, in_transit, completed, cancelled]. "
            "Upstream: [received, created]. Live API is the tiebreaker."
        ),
    )
    finding.calls.append(_capture(client, "GET", "/stock_transfers", {"limit": 50}))
    payload_call = finding.calls[0]
    rows = []
    if payload_call.status_code == 200:
        # Re-fetch to get all rows (sample_record only has first row)
        full = client.get("/stock_transfers", params={"limit": 50}).json()
        rows = full.get("data", []) if isinstance(full, dict) else []
    distinct_statuses = sorted(
        {
            str(r["status"])
            for r in rows
            if isinstance(r, dict) and r.get("status") is not None
        }
    )
    finding.conclusion = (
        f"Distinct status values across {len(rows)} rows: {distinct_statuses}"
    )
    finding.triage_category = "see_distinct_values_above"
    return finding


def verify_F23(client: httpx.Client) -> FindingResult:
    """`InventoryMovementResourceType.ProductionIngredient`."""
    finding = FindingResult(
        finding_id="F23",
        title=("InventoryMovementResourceType — is ProductionIngredient on the wire?"),
        hypothesis="Local has it; upstream doesn't. Live API is the tiebreaker.",
    )
    finding.calls.append(
        _capture(client, "GET", "/inventory_movements", {"limit": 200})
    )
    if finding.calls[0].status_code == 200:
        full = client.get("/inventory_movements", params={"limit": 200}).json()
        rows = full.get("data", []) if isinstance(full, dict) else []
    else:
        rows = []
    distinct = sorted(
        {
            str(r["resource_type"])
            for r in rows
            if isinstance(r, dict) and r.get("resource_type") is not None
        }
    )
    finding.conclusion = (
        f"Distinct resource_type values across {len(rows)} rows: {distinct}"
    )
    if "ProductionIngredient" in distinct:
        finding.triage_category = "local_correct_upstream_wrong"
        finding.suggested_action = (
            "No change to local; upstream spec is missing the value."
        )
    else:
        finding.triage_category = "needs_wider_sample"
        finding.suggested_action = (
            "Sample didn't include ProductionIngredient. Either upstream "
            "is right (value is dead) or sample is too narrow. Pull more "
            "rows or check workflow that should generate it."
        )
    return finding


def verify_F21(client: httpx.Client) -> FindingResult:
    """`/serial_numbers` and `/serial_numbers_stock` — bare array vs wrapped."""
    finding = FindingResult(
        finding_id="F21",
        title="GET /serial_numbers + /serial_numbers_stock — wire shape",
        hypothesis=(
            "README example shows bare array; local schema says wrapped. "
            "Same shape question as F18; live response is the tiebreaker."
        ),
    )
    finding.calls.append(_capture(client, "GET", "/serial_numbers", {"limit": 1}))
    finding.calls.append(_capture(client, "GET", "/serial_numbers_stock", {"limit": 1}))

    sn_keys = finding.calls[0].response_keys or []
    sns_keys = finding.calls[1].response_keys or []
    sn_bare = sn_keys == ["<bare-array>"]
    sns_bare = sns_keys == ["<bare-array>"]

    if sn_bare and sns_bare:
        finding.conclusion = (
            "Both endpoints return BARE ARRAY on the wire. Local schema "
            "(wrapped {data: []}) is wrong."
        )
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Fix local: drop list-response wrappers, return type: array "
            "directly. Add /serial_numbers + /serial_numbers_stock to the "
            "documented exceptions next to /user_info, /operators (whose "
            "wrapper status was confirmed in F18)."
        )
    elif not sn_bare and not sns_bare:
        finding.conclusion = (
            "Both endpoints return wrapped {data: [...]}. README example is stale."
        )
        finding.triage_category = "stale_readme_example"
    else:
        finding.conclusion = (
            f"Mixed: serial_numbers={sn_keys}, "
            f"serial_numbers_stock={sns_keys}. Investigate."
        )
        finding.triage_category = "needs_more_investigation"
    return finding


def verify_F20b(client: httpx.Client) -> FindingResult:
    """Confirm /bin_locations bare-array shape with non-empty data."""
    finding = FindingResult(
        finding_id="F20b",
        title="GET /bin_locations — confirm bare-array shape",
        hypothesis=(
            "F20 saw empty bare array []. Try other locations / unrestricted "
            "to confirm the shape isn't an empty-result artifact."
        ),
    )
    # Try without filters — if any factory has bin_locations they should show
    finding.calls.append(_capture(client, "GET", "/bin_locations"))
    keys = finding.calls[0].response_keys or []
    count = finding.calls[0].response_count or 0
    if keys == ["<bare-array>"]:
        finding.conclusion = (
            f"Confirmed: bare-array shape (count={count}). Local "
            "StorageBinListResponse wrapper is wrong."
        )
        finding.triage_category = "upstream_correct_local_wrong"
        finding.suggested_action = (
            "Fix local /bin_locations response: bare array, drop "
            "StorageBinListResponse wrapper."
        )
    elif "data" in keys:
        finding.conclusion = (
            f"With unrestricted query, response is wrapped {{data: [...]}} "
            f"(count={count}). F20's bare-array signal was an artifact."
        )
        finding.triage_category = "no_drift_after_all"
    else:
        finding.conclusion = f"Unexpected keys: {keys}"
        finding.triage_category = "needs_more_investigation"
    return finding


VERIFIERS = {
    "F1": verify_F1,
    "F2": verify_F2,
    "F17": verify_F17,
    "F18": verify_F18,
    "F19": verify_F19,
    "F20": verify_F20,
    "F20b": verify_F20b,
    "F21": verify_F21,
    "F22": verify_F22,
    "F23": verify_F23,
}


# ---------------------------------------------------------------------------
# Output


def render_finding_markdown(result: FindingResult) -> str:
    lines = [f"### {result.finding_id} — {result.title}", ""]
    lines.append(f"**Hypothesis:** {result.hypothesis}")
    lines.append("")
    lines.append("**Calls:**")
    lines.append("")
    for c in result.calls:
        lines.append(
            f"- `{c.method} {c.url}` → **{c.status_code}**, "
            f"keys={c.response_keys}, count={c.response_count}"
        )
    lines.append("")
    lines.append(f"**Conclusion:** {result.conclusion}")
    lines.append("")
    if result.triage_category:
        lines.append(f"**Triage:** `{result.triage_category}`")
    if result.suggested_action:
        lines.append(f"**Suggested action:** {result.suggested_action}")
    if result.calls and result.calls[0].sample_record:
        lines.append("")
        lines.append("<details><summary>Sample record</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(result.calls[0].sample_record, indent=2)[:1500])
        lines.append("```")
        lines.append("")
        lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "finding",
        nargs="?",
        help="Finding ID (e.g. F1) or omitted with --all",
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all implemented verifiers"
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit JSON instead of Markdown"
    )
    args = parser.parse_args(argv)

    targets: list[str]
    if args.all:
        targets = list(VERIFIERS.keys())
    elif args.finding:
        targets = [args.finding]
    else:
        parser.error("Pass a finding ID (e.g. F1) or --all")

    unknown = [t for t in targets if t not in VERIFIERS]
    if unknown:
        print(
            f"Unknown findings: {unknown}. Implemented: {list(VERIFIERS.keys())}",
            file=sys.stderr,
        )
        return 2

    results: list[FindingResult] = []
    with make_client() as client:
        for tid in targets:
            print(f"Running {tid}…", file=sys.stderr)
            results.append(VERIFIERS[tid](client))

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "finding_id": r.finding_id,
                        "title": r.title,
                        "hypothesis": r.hypothesis,
                        "conclusion": r.conclusion,
                        "triage_category": r.triage_category,
                        "suggested_action": r.suggested_action,
                        "calls": [
                            {
                                "method": c.method,
                                "url": c.url,
                                "params": c.params,
                                "status_code": c.status_code,
                                "response_keys": c.response_keys,
                                "response_count": c.response_count,
                                "sample_record": c.sample_record,
                            }
                            for c in r.calls
                        ],
                    }
                    for r in results
                ],
                indent=2,
            )
        )
    else:
        for r in results:
            print(render_finding_markdown(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
