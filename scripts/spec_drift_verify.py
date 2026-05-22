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

from scripts._safety import (
    SafeClient,
    SilentDropError,
    UnsafeMutationError,
    discover_sdt_fixture,
    verify_production_serial_numbers_match,
)

__all__ = [
    "BASE_URL",
    "LEDGER_PATH",
    "SDT_PREFIX",
    "LedgerRow",
    "SafeClient",
    "SilentDropError",
    "UnsafeMutationError",
    "cleanup",
    "discover_sdt_fixture",
    "format_422",
    "label",
    "make_client",
    "pp_response",
    "read_ledger",
    "record_artifact",
    "tagged",
    "verify_production_serial_numbers_match",
]

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
    "/bom_rows": "/bom_rows/{id}",
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


def _initial_ledger_keys() -> set[tuple[str, str]]:
    """Build the in-memory ``(endpoint, entity_id)`` set from the on-disk ledger.

    **Tenant-scoped, fail-closed.** A row is admitted only when both
    ``base_url`` and ``factory_id`` are present AND match the current
    credential's tenant. The pre-fingerprint era admitted unscoped rows
    on the theory that the per-mutation pre-fetch + identity check was
    a sufficient final layer — but that doesn't hold for ledger-only
    guard paths: ``NO_GET_BY_ID`` endpoints (e.g. ``/stock_transfers``)
    skip the pre-fetch entirely, and child POSTs that vet only the
    parent's ledger membership (e.g. ``POST
    /manufacturing_order_productions`` against a parent MO) have no
    per-record identity check on the target. Admitting an unscoped row
    on those paths would let a stale cross-tenant entry act as an
    allow-list bypass.

    The cost is that older ledger files (written before fingerprinting
    landed) won't restore on the next run; the probe re-mints SDT
    artifacts and the new rows carry the fingerprint. Cleanup pairs
    this with its own tenant filter so cross-tenant rows aren't deleted
    either.

    Read once at ``SafeClient`` construction; subsequent
    ``record_artifact`` calls keep both the file and the client's
    in-memory copy in sync via ``SafeClient.register_artifact``.
    """
    keys: set[tuple[str, str]] = set()
    current_factory_id = _resolve_factory_id()
    for row in read_ledger():
        endpoint = row.get("endpoint")
        entity_id = row.get("entity_id")
        if endpoint is None or entity_id is None:
            continue
        row_base = row.get("base_url")
        row_factory = row.get("factory_id")
        # Fail closed on pre-fingerprint rows: with no tenant signal we
        # can't prove they belong to the current credential.
        if row_base is None or row_factory is None:
            continue
        # Tenant fingerprint must match exactly. Any divergence means a
        # different tenant; refuse to seed the ledger from foreign rows.
        if row_base != BASE_URL:
            continue
        if current_factory_id is None or row_factory != current_factory_id:
            continue
        keys.add((str(endpoint), str(entity_id)))
    return keys


# Process-local registry of every SafeClient ``make_client`` has handed
# out. ``record_artifact`` walks this list to keep each open client's
# in-memory ledger fresh as the run creates new artifacts. Weak-ref-free
# because probes hold their client open for the whole run; the small
# leak (one entry per ``with make_client()`` block) is bounded.
_LIVE_CLIENTS: list[SafeClient] = []


def make_client(*, allow_unsafe: bool = False) -> SafeClient:
    """Build a bearer-auth ``SafeClient`` pointed at the live Katana API.

    Shared by every probe script so they all hit the same base URL with
    the same auth header and timeout. The returned client refuses any
    ``POST`` / ``PATCH`` / ``DELETE`` whose target doesn't carry the
    SDT- prefix or doesn't appear in the local ledger (see
    ``scripts/_safety.py``). Bails with exit-2 when ``KATANA_API_KEY``
    is missing.

    ``allow_unsafe=True`` bypasses every check — reserved for cleanup
    paths where the ledger has already pre-vetted the target and for
    read-only internal helpers like ``_resolve_factory_id``. When set,
    ledger initialization is skipped entirely: the guard isn't engaged,
    so the (potentially expensive, factory-id-resolving) read is wasted
    work, and skipping breaks the bootstrap chicken-and-egg where
    ``_initial_ledger_keys`` itself calls ``_resolve_factory_id`` which
    needs a SafeClient to GET ``/factory``.
    """
    client = SafeClient(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {_api_key()}"},
        timeout=30.0,
        allow_unsafe=allow_unsafe,
        ledger_keys=set() if allow_unsafe else _initial_ledger_keys(),
    )
    _LIVE_CLIENTS.append(client)
    return client


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
    credential's factory, AND refuses rows where ``factory_id is None``
    (or ``base_url is None``) since without a complete fingerprint we
    can't prove tenant identity — fail-closed mirrors the seed side
    (``_initial_ledger_keys``). Populated by :func:`record_artifact`
    from a process-local cache so we hit ``GET /factory`` once per
    session."""
    extra: dict[str, Any] = field(default_factory=dict)
    deleted_at: str | None = None
    delete_error: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@cache
def _factory_id_for_key(api_key: str) -> int | None:
    """Inner GET /factory lookup, cached on ``api_key`` so a key rotation
    busts the cache naturally. Callers must reach this through
    ``_resolve_factory_id()``, which reads the current env key on every
    call and routes here; never call this directly with a stale key.

    Note: ``api_key`` is consumed by ``lru_cache`` as the cache key.
    The function body doesn't reference it (``make_client`` re-reads
    ``KATANA_API_KEY`` from env, which is correct because the env is
    always the fresh value at cache-miss time)."""
    del api_key  # used as the lru_cache key only; see docstring
    try:
        # ``allow_unsafe=True``: read-only GET, no need to engage the
        # mutation guard (which also has a startup cost from reading the
        # ledger). This call is the *guard's own dependency* in some
        # paths — keep it cheap and side-effect-free.
        with make_client(allow_unsafe=True) as client:
            data = client.get("/factory").json()
    except Exception:
        return None
    if isinstance(data, dict):
        fid = data.get("factory_id")
        if isinstance(fid, int):
            return fid
    return None


def _resolve_factory_id() -> int | None:
    """Look up the active credential's ``Factory.factory_id`` once per key.

    Reads ``KATANA_API_KEY`` fresh on every call and dispatches to
    ``_factory_id_for_key``, which memoizes on the key value. So the
    ``record_artifact`` fast path doesn't hit ``GET /factory`` for every
    artifact, AND an API-key rotation mid-process busts the cache
    naturally (closing the cross-tenant trap where a stale factory_id
    would be matched against fresh-tenant ledger rows).

    Returns ``None`` on lookup failure. On the record side, the ledger
    row is written without a ``factory_id`` fingerprint — and the
    cleanup side then treats that row as ``skipped_unverifiable`` (no
    URL-only fallback; both fingerprint fields are required to even
    consider a row for deletion, matching the seed-side
    ``_initial_ledger_keys`` fail-closed in #781).
    """
    return _factory_id_for_key(_api_key())


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
    # Keep every open SafeClient's in-memory ledger fresh so subsequent
    # PATCH/DELETE against this freshly-created record bypass the
    # pre-fetch round-trip via the ledger-membership fast path.
    for client in _LIVE_CLIENTS:
        if not client.is_closed:
            client.register_artifact(endpoint, entity_id)
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
    # Two distinct skip buckets so the summary can accurately tell
    # operators which rows still need attention vs. which are foreign:
    # * ``skipped_unverifiable``: tenant cannot be PROVEN (missing
    #   fingerprint field, or current ``/factory`` lookup failed). Could
    #   belong to the current tenant — operator should inspect.
    # * ``skipped_mismatch``: fingerprint definitively belongs to a
    #   DIFFERENT tenant. Foreign — should be cleaned up by re-running
    #   ``cleanup`` against that tenant's credentials.
    skipped_unverifiable: list[dict[str, Any]] = []
    skipped_mismatch: list[dict[str, Any]] = []
    # Rows whose endpoint has no DELETE template — the cleanup script
    # can't delete them automatically, but they're still ours (tenant
    # fingerprint passed). Tracked separately so the summary breakdown
    # accounts for them and ``total_skipped == sum(buckets)``.
    skipped_no_template: list[dict[str, Any]] = []
    current_factory_id = _resolve_factory_id()
    # ``allow_unsafe=True``: cleanup deliberately mutates ledger-recorded
    # rows that the harness itself created. Each row already passed the
    # factory/base_url tenant-fingerprint guard above, and the SafeClient
    # mutation guard would just re-check the same thing.
    with make_client(allow_unsafe=True) as client:
        for r in reversed(pending):
            # Clear any ``delete_error`` from a prior run before deciding
            # this row's fate. The ledger is rewritten at the end of the
            # loop; without this, a row that was ``failed`` in run #1
            # and ``skipped`` in run #2 would carry run #1's stale error
            # message in the serialised output, misleading operators
            # reading the ledger for forensic context.
            r.pop("delete_error", None)
            row_base = r.get("base_url")
            row_factory = r.get("factory_id")
            # Fail closed on pre-fingerprint rows. ``cleanup`` uses
            # ``allow_unsafe=True`` and so the SafeClient mutation guard
            # is NOT re-checking these rows for us — the tenant filter
            # below IS the only guard. Without a fingerprint we have no
            # signal that this row belongs to the current credential, so
            # deleting it could land on a real record on the active
            # tenant. (Mirror of the seed-side fail-closed in
            # ``_initial_ledger_keys`` — see issue #781 follow-up.)
            if row_base is None or row_factory is None:
                missing = []
                if row_base is None:
                    missing.append("base_url")
                if row_factory is None:
                    missing.append("factory_id")
                print(
                    f"  ⚠  skipping {r['endpoint']}/{r['entity_id']} — "
                    f"missing {' and '.join(missing)} in ledger row, "
                    "cannot verify tenant — delete by hand if known-safe"
                )
                skipped_unverifiable.append(r)
                continue
            # Refuse to delete when either the base URL OR the factory
            # fingerprint disagrees with the active credential — catches
            # both ``KATANA_BASE_URL`` swaps and ``KATANA_API_KEY`` swaps
            # against the same base.
            if row_base != BASE_URL:
                print(
                    f"  ⚠  skipping {r['endpoint']}/{r['entity_id']} — "
                    f"created against {row_base}, "
                    f"current client targets {BASE_URL}"
                )
                skipped_mismatch.append(r)
                continue
            # When the current credential's factory_id is unresolvable
            # (``/factory`` unreachable) we can't prove tenant identity
            # — unverifiable. When it's resolvable but differs, this is
            # a definitive mismatch.
            if current_factory_id is None:
                print(
                    f"  ⚠  skipping {r['endpoint']}/{r['entity_id']} — "
                    f"created on factory_id={row_factory}, current "
                    "credential's factory_id unresolved (cannot verify)"
                )
                skipped_unverifiable.append(r)
                continue
            if row_factory != current_factory_id:
                print(
                    f"  ⚠  skipping {r['endpoint']}/{r['entity_id']} — "
                    f"created on factory_id={row_factory}, current "
                    f"credential targets factory_id={current_factory_id}"
                )
                skipped_mismatch.append(r)
                continue
            template = DELETE_TEMPLATES.get(r["endpoint"])
            if template is None:
                print(
                    f"  ⚠  no DELETE template for {r['endpoint']} — "
                    "skipping (clean up by hand)"
                )
                skipped_no_template.append(r)
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

    # Compute total from the buckets themselves so the headline number
    # always equals the sum of the breakdown — no silent "other" gap.
    total_skipped = (
        len(skipped_mismatch) + len(skipped_unverifiable) + len(skipped_no_template)
    )
    skip_breakdown_parts = []
    if skipped_mismatch:
        skip_breakdown_parts.append(
            f"{len(skipped_mismatch)} from a different tenant/base URL"
        )
    if skipped_unverifiable:
        skip_breakdown_parts.append(
            f"{len(skipped_unverifiable)} could not be verified "
            "(missing fingerprint or /factory unreachable)"
        )
    if skipped_no_template:
        skip_breakdown_parts.append(
            f"{len(skipped_no_template)} have no DELETE template (clean up by hand)"
        )
    skip_breakdown = (
        f" ({'; '.join(skip_breakdown_parts)})" if skip_breakdown_parts else ""
    )
    print(
        f"\nResult: {len(deleted)} deleted, {len(failed)} failed, "
        f"{total_skipped} skipped{skip_breakdown}."
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
