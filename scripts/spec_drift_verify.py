"""Verification harness for spec-drift POSTs against a live Katana tenant.

Two responsibilities:

1. Tag every test artifact with the ``SDT-<date>`` prefix so the Katana
   UI / API list filters surface them under one searchable group, and
   append a row to ``/tmp/spec-drift-ledger.jsonl`` for cleanup.
2. Provide a ``cleanup`` CLI that walks the ledger in reverse, calls
   the matching DELETE endpoint, and marks the row as deleted (or
   reports the failure so the operator can clean up by hand).

Usage in a probe script::

    from scripts.spec_drift_verify import (
        SDT_PREFIX,
        record_artifact,
        tagged,
    )

    response = httpx.post(
        f"{BASE_URL}/materials",
        headers=HEADERS,
        json={"name": f"[{SDT_PREFIX}] Test Material", "variants": [...]},
    )
    record_artifact(
        endpoint="/materials",
        entity_id=response.json()["id"],
        issue="#734",
    )

Cleanup::

    $ uv run python scripts/spec_drift_verify.py cleanup
    Deleted: 12 / 14 artifacts (2 failed — see ledger for details)

Re-run safe — already-deleted ledger rows are skipped on subsequent
cleanup invocations.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

import httpx

# Date-stamped prefix so concurrent runs on different days don't collide
# and so a glance at any tagged record reveals when it was created.
SDT_PREFIX = f"SDT-{datetime.now(UTC).strftime('%Y-%m-%d')}"

LEDGER_PATH = Path("/tmp/spec-drift-ledger.jsonl")

BASE_URL = os.environ.get("KATANA_BASE_URL", "https://api.katanamrp.com/v1")

# Endpoint → DELETE-path template. ``{id}`` is substituted with the
# ledger row's ``entity_id``. Endpoints not listed here are treated as
# non-deletable and the cleanup script will warn rather than try.
DELETE_TEMPLATES: dict[str, str] = {
    "/materials": "/materials/{id}",
    "/products": "/products/{id}",
    "/services": "/services/{id}",
    "/variants": "/variants/{id}",
    "/sales_orders": "/sales_orders/{id}",
    "/sales_order_rows": "/sales_order_rows/{id}",
    "/sales_order_fulfillments": "/sales_order_fulfillments/{id}",
    "/sales_returns": "/sales_returns/{id}",
    "/purchase_orders": "/purchase_orders/{id}",
    "/purchase_order_rows": "/purchase_order_rows/{id}",
    "/manufacturing_orders": "/manufacturing_orders/{id}",
    "/manufacturing_order_recipe_rows": "/manufacturing_order_recipe_rows/{id}",
    "/stock_adjustments": "/stock_adjustments/{id}",
    "/stock_transfers": "/stock_transfers/{id}",
    "/custom_field_definitions": "/custom_field_definitions/{id}",
    "/webhooks": "/webhooks/{id}",
    "/suppliers": "/suppliers/{id}",
    "/customers": "/customers/{id}",
    "/locations": "/locations/{id}",
    "/bin_locations": "/bin_locations/{id}",
}


def tagged(suffix: str | int) -> str:
    """Return ``SDT-<date>-<suffix>`` — use for SKUs and short identifiers."""
    return f"{SDT_PREFIX}-{suffix}"


def _api_key() -> str:
    key = os.environ.get("KATANA_API_KEY")
    if not key:
        print("KATANA_API_KEY not set — source .env first.", file=sys.stderr)
        sys.exit(2)
    return key


def make_client() -> httpx.Client:
    """Build a bearer-auth httpx client pointed at the live Katana API.

    Shared by every probe script so they all hit the same base URL with
    the same auth header and timeout. Bails with exit-2 when
    ``KATANA_API_KEY`` is missing.
    """
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {_api_key()}"},
        timeout=30.0,
    )


def format_422(response: Any) -> str:
    """Pretty-print a Katana 422 by delegating to the client's ``ValidationError``.

    Builds a ``DetailedErrorResponse`` from the raw envelope and runs
    it through the same ``_format_ajv_detail`` dispatch the rest of the
    codebase uses (Ajv-keyword-typed: enum, required, minLength, etc.)
    so probe output matches what the transport layer would log. Falls
    back to the raw body when the response shape doesn't match the
    documented envelope.
    """
    from katana_public_api_client.models import DetailedErrorResponse
    from katana_public_api_client.utils import ValidationError

    try:
        body = response.json()
    except Exception:
        return f"HTTP {response.status_code}\n{response.text[:600]}"
    err = body.get("error") if isinstance(body, dict) else None
    if not isinstance(err, dict):
        return f"HTTP {response.status_code}\n{response.text[:600]}"
    parsed = DetailedErrorResponse.from_dict(err)
    name = err.get("name", "")
    message = err.get("message", "")
    full = f"{name}: {message}" if name else message
    return str(ValidationError(full, response.status_code, parsed))


def pp_response(response: Any, n: int = 600) -> str:
    """Pretty-print any response — Ajv summary for 422, raw body otherwise."""
    if response.status_code == 422:
        return format_422(response)
    body = response.text
    if response.headers.get("content-type", "").startswith("application/json"):
        with contextlib.suppress(Exception):
            body = json.dumps(response.json(), indent=2)
    return f"HTTP {response.status_code}\n{body[:n]}"


def label(text: str) -> str:
    """Wrap a free-text field so it's grep-discoverable in Katana lists.

    Use for ``name``, ``description``, ``additional_info``, ``notes`` —
    fields the UI surfaces directly. Returns ``"[SDT-<date>] <text>"``.
    """
    return f"[{SDT_PREFIX}] {text}"


@dataclass
class LedgerRow:
    endpoint: str
    entity_id: int | str
    """The created artifact's identifier. Most Katana endpoints use
    integer IDs; ``/custom_field_definitions`` uses UUID strings."""
    issue: str
    method: str = "POST"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    base_url: str = field(default_factory=lambda: BASE_URL)
    factory_id: int | None = None
    """The Katana ``Factory.factory_id`` singleton at create time —
    serves as a non-secret tenant fingerprint. ``cleanup`` refuses to
    delete rows whose ``factory_id`` doesn't match the active
    credential's factory, which catches the case where someone swaps
    ``KATANA_API_KEY`` between probe and cleanup but ``BASE_URL`` stays
    the default. Populated by :func:`record_artifact` from a process-
    local cache so we hit ``GET /factory`` once per session."""
    extra: dict[str, Any] = field(default_factory=dict)
    deleted_at: str | None = None
    delete_error: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@cache
def _resolve_factory_id() -> int | None:
    """Look up the active credential's ``Factory.factory_id`` once.

    ``@cache`` memoizes the result so the ``record_artifact`` fast path
    doesn't hit ``GET /factory`` for every artifact. Returns ``None`` on
    lookup failure; on the record side, the ledger row simply has no
    fingerprint (cleanup proceeds with only the URL check for those
    rows). On the cleanup side, ``None`` is treated as "tenant
    unverifiable" — rows that *do* carry a stored ``factory_id`` are
    refused rather than delete-anyway-and-hope.
    """
    try:
        with make_client() as client:
            data = client.get("/factory").json()
    except Exception:
        return None
    if isinstance(data, dict):
        fid = data.get("factory_id")
        if isinstance(fid, int):
            return fid
    return None


def record_artifact(
    *,
    endpoint: str,
    entity_id: int | str,
    issue: str,
    method: str = "POST",
    **extra: Any,
) -> LedgerRow:
    """Append a single artifact row to the ledger.

    Call this **immediately after** a successful create — the cleanup
    script reads ledger rows in reverse to build the delete queue. Any
    extra context (e.g. ``sku``, ``name``) goes into the ``extra`` dict
    and is surfaced by the cleanup summary.
    """
    row = LedgerRow(
        endpoint=endpoint,
        entity_id=entity_id,
        issue=issue,
        method=method,
        factory_id=_resolve_factory_id(),
        extra=extra,
    )
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a") as f:
        f.write(row.to_json() + "\n")
    return row


def read_ledger() -> list[dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    return [
        json.loads(line)
        for line in LEDGER_PATH.read_text().splitlines()
        if line.strip()
    ]


def cleanup(*, dry_run: bool = False) -> int:
    """Walk the ledger in reverse and delete every undeleted artifact.

    Returns 0 if all rows were either already deleted, freshly deleted,
    or knowingly skipped (non-deletable endpoint). Returns 1 if any
    delete call returned a non-2xx status — the operator should inspect
    the ledger and clean those up by hand before re-running.
    """
    rows = read_ledger()
    if not rows:
        print("Ledger is empty — nothing to clean up.")
        return 0

    pending = [r for r in rows if not r.get("deleted_at")]
    if not pending:
        print(f"All {len(rows)} ledger rows already cleaned up.")
        return 0

    print(
        f"Found {len(pending)} undeleted artifacts "
        f"({len(rows) - len(pending)} already cleaned)."
    )
    if dry_run:
        for r in reversed(pending):
            print(f"  would DELETE {r['endpoint']}/{r['entity_id']} ({r['issue']})")
        return 0

    failed: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    skipped_tenant: list[dict[str, Any]] = []
    current_factory_id = _resolve_factory_id()
    with make_client() as client:
        for r in reversed(pending):
            row_base = r.get("base_url")
            row_factory = r.get("factory_id")
            # Refuse to delete when either the base URL OR the factory
            # fingerprint disagrees with the active credential — catches
            # both ``KATANA_BASE_URL`` swaps and ``KATANA_API_KEY`` swaps
            # against the same base. Missing fingerprint (None on either
            # side) is skipped rather than enforced — older ledger rows
            # may pre-date the fingerprint field.
            if row_base and row_base != BASE_URL:
                print(
                    f"  ⚠  skipping {r['endpoint']}/{r['entity_id']} — "
                    f"created against {row_base}, "
                    f"current client targets {BASE_URL}"
                )
                skipped_tenant.append(r)
                continue
            # Fail closed on the factory check: when a row carries a
            # stored ``factory_id`` we require the current credential's
            # ``factory_id`` to be resolvable AND match. Falling through
            # because ``current_factory_id is None`` (e.g. ``/factory``
            # unreachable) would bypass the tenant guard precisely when
            # we can't verify the active tenant.
            if row_factory is not None and (
                current_factory_id is None or row_factory != current_factory_id
            ):
                reason = (
                    "current credential's factory_id unresolved (cannot verify)"
                    if current_factory_id is None
                    else f"current credential targets factory_id={current_factory_id}"
                )
                print(
                    f"  ⚠  skipping {r['endpoint']}/{r['entity_id']} — "
                    f"created on factory_id={row_factory}, {reason}"
                )
                skipped_tenant.append(r)
                continue
            template = DELETE_TEMPLATES.get(r["endpoint"])
            if template is None:
                print(
                    f"  ⚠  no DELETE template for {r['endpoint']} — "
                    "skipping (clean up by hand)"
                )
                continue
            path = template.format(id=r["entity_id"])
            resp = client.delete(path)
            if resp.status_code == 404:
                r["deleted_at"] = datetime.now(UTC).isoformat()
                deleted.append(r)
                print(f"  ✓  DELETE {path} → 404 (already gone)")
            elif 200 <= resp.status_code < 300:
                r["deleted_at"] = datetime.now(UTC).isoformat()
                deleted.append(r)
                print(f"  ✓  DELETE {path} → {resp.status_code}")
            else:
                r["delete_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                failed.append(r)
                print(f"  ✗  DELETE {path} → {resp.status_code}: {resp.text[:120]}")

    # ``pending`` rows are references into ``rows`` and are already
    # mutated in place; just re-serialize the list.
    LEDGER_PATH.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    print(
        f"\nResult: {len(deleted)} deleted, {len(failed)} failed, "
        f"{len(pending) - len(deleted) - len(failed)} skipped "
        f"({len(skipped_tenant)} from a different tenant/base URL)."
    )
    if failed:
        print("\nFailed rows (inspect manually):")
        for r in failed:
            print(
                f"  {r['endpoint']}/{r['entity_id']} ({r['issue']}): "
                f"{r['delete_error']}"
            )
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cleanup", help="Delete every artifact recorded in the ledger.")
    p_dry = sub.add_parser("plan", help="Show what cleanup would delete (dry run).")
    p_dry.set_defaults(dry_run=True)
    sub.add_parser("list", help="Print the ledger as a readable summary.")
    args = parser.parse_args()

    if args.cmd == "cleanup":
        return cleanup(dry_run=False)
    if args.cmd == "plan":
        return cleanup(dry_run=True)
    if args.cmd == "list":
        rows = read_ledger()
        if not rows:
            print("Ledger empty.")
            return 0
        for r in rows:
            status = "deleted" if r.get("deleted_at") else "active"
            print(
                f"  [{status}] {r['endpoint']}/{r['entity_id']} "
                f"({r['issue']}) — {r['extra']}"
            )
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
