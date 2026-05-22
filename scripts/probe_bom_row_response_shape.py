"""Probe the actual HTTP response shape of ``POST /bom_rows``.

Three sources disagree on what Katana returns:

- Our local spec: 204 No Content
- Live-gateway upstream: 200 (no schema documented)
- Readme reference docs: only document ``/bom_rows/batch/create`` (204)

This script POSTs a single ``bom_row`` against the live API and prints
the actual status code + body so we can align the local spec to reality.
Creates SDT-tagged scaffolding (product variant + material variant) so
``cleanup`` can revert everything via the ledger.

Usage::

    uv run python scripts/probe_bom_row_response_shape.py
    # ...inspect output...
    uv run python scripts/spec_drift_verify.py cleanup

Tracking: #820 (the spec realignment work this probe surfaced).
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spec_drift_verify import (
    SDT_PREFIX,
    label,
    make_client,
    pp_response,
    record_artifact,
    tagged,
)

# Per-run nonce so the probe's ``notes`` marker is unique even across
# multiple runs on the same day. ``SDT_PREFIX`` is date-based
# (``SDT-YYYY-MM-DD``) — without a nonce, two runs on the same day
# would emit identical notes, and the 204 fallback's notes-match
# would pick whichever row Katana returned first.
RUN_ID = secrets.token_hex(4)


def main() -> int:
    print(f"\n=== POST /bom_rows response-shape probe ({SDT_PREFIX}) ===\n")

    # Context-managed client so connections are released even on early
    # exit (any of the steps below can short-circuit on 4xx/5xx).
    with make_client() as client:
        # 1. Create a SDT-tagged product (producible by default).
        product_body = {
            "name": label("BOM response-shape probe product"),
            "is_producible": True,
            "is_sellable": False,
            "variants": [
                {
                    "sku": tagged(f"probe-product-{RUN_ID}"),
                }
            ],
        }
        r = client.post("/products", json=product_body)
        print(f"[1] POST /products → HTTP {r.status_code}")
        if r.status_code >= 400:
            print(pp_response(r))
            return 1
        product = r.json()
        product_id = product["id"]
        product_variant_id = product["variants"][0]["id"]
        record_artifact(endpoint="/products", entity_id=product_id, issue="#820")
        print(f"    product_id={product_id}  variant_id={product_variant_id}")

        # 2. Create a SDT-tagged material (used as an ingredient).
        material_body = {
            "name": label("BOM response-shape probe material"),
            "variants": [
                {
                    "sku": tagged(f"probe-material-{RUN_ID}"),
                }
            ],
        }
        r = client.post("/materials", json=material_body)
        print(f"[2] POST /materials → HTTP {r.status_code}")
        if r.status_code >= 400:
            print(pp_response(r))
            return 1
        material = r.json()
        material_id = material["id"]
        ingredient_variant_id = material["variants"][0]["id"]
        record_artifact(endpoint="/materials", entity_id=material_id, issue="#820")
        print(f"    material_id={material_id}  variant_id={ingredient_variant_id}")

        # 3. The actual probe: POST /bom_rows and inspect the response.
        # ``RUN_ID`` makes the notes string distinct even across multiple
        # runs on the same day — used as the lookup key in the 204
        # fallback path of ``_extract_row_id``.
        probe_notes = label(f"BOM response-shape probe row {tagged(RUN_ID)}")
        bom_row_body = {
            "product_item_id": product_id,
            "product_variant_id": product_variant_id,
            "ingredient_variant_id": ingredient_variant_id,
            "quantity": 2.0,
            "notes": probe_notes,
        }
        r = client.post("/bom_rows", json=bom_row_body)
        print("\n[3] POST /bom_rows  ← the actual probe target")
        print(f"    HTTP status: {r.status_code}")
        print(f"    Body bytes:  {len(r.content)}")
        print(f"    Content-Type: {r.headers.get('content-type', '(none)')}")
        print(f"    Body preview:\n{pp_response(r, n=400)}\n")

        # Fail-fast on 4xx/5xx so automation/reporting can't mistake a
        # failed probe for a successful one. The earlier ``print`` already
        # surfaced the body; the scaffolding products/materials remain in
        # the ledger so ``cleanup`` can still revert them.
        if r.status_code >= 400:
            print(f"    Probe FAILED: HTTP {r.status_code} — see body above.")
            return 1

        # Record the new bom_row for cleanup. Prefer the response body
        # (HTTP 200 with BomRow — what we observed live); fall back to
        # ``GET /bom_rows`` filtered by the SDT-tagged notes if the
        # response shape is empty (the documented 204 path).
        row_id = _extract_row_id(r, client, product_variant_id, probe_notes)
        if row_id is not None:
            record_artifact(
                endpoint="/bom_rows",
                entity_id=row_id,
                issue="#820",
            )
            print(f"    Recorded bom_row id={row_id} for cleanup.")
        else:
            print(
                "    ⚠ Could not resolve new bom_row id for cleanup — "
                "the parent product DELETE will cascade it."
            )

    print(
        "\nFindings:\n"
        f"  - Katana returned HTTP {r.status_code} "
        f"({'with' if r.content else 'without'} a body)\n"
        f"  - Our local spec declares 204 No Content\n"
        f"  - The runtime shape "
        + ("matches" if r.status_code == 204 else "differs from")
        + " the local spec\n"
        "  - Run ``uv run python scripts/spec_drift_verify.py cleanup`` "
        "to remove the test artifacts.\n"
    )
    return 0


def _extract_row_id(
    response, client, product_variant_id: int, probe_notes: str
) -> int | str | None:
    """Resolve the new BOM row's id from either the POST body or a follow-up GET.

    Two paths, tried in order:

    1. **POST body carries the row** (HTTP 200 with full ``BomRow`` — what
       Katana actually does today): read ``id`` directly off the parsed
       JSON. Most reliable when the body is present.
    2. **Notes-match fallback**: any success status where the body
       extraction didn't yield an id — 204 No Content, 200/201 with empty
       body, 2xx with non-JSON body, JSON without ``id``. Re-list
       ``/bom_rows`` filtered by the parent variant and pick the row whose
       ``notes`` equals the probe's SDT-tagged marker. Matching by notes
       (not ``data[-1]``) is robust to orphaned rows from prior probe
       runs and to concurrent writes because ``probe_notes`` embeds a
       per-run nonce (``RUN_ID``) on top of the date-based ``SDT_PREFIX``.

    Caller short-circuits on 4xx/5xx before invoking this — ``response``
    is always a 2xx by the time we look at it.
    """
    if response.content:
        try:
            body = response.json()
            row_id = body.get("id")
            if row_id is not None:
                return row_id
        except Exception:
            pass

    # Fall back to the notes-match path for any "success but no id in body"
    # shape (#820-followup): the original gate was ``status == 204`` only,
    # which silently skipped recording when a 2xx success returned an empty
    # body or unexpected payload.
    list_r = client.get(
        "/bom_rows",
        params={"product_variant_id": product_variant_id},
    )
    if list_r.status_code != 200:
        return None
    data = list_r.json().get("data", []) or []
    for row in data:
        if row.get("notes") == probe_notes:
            return row.get("id")
    return None


if __name__ == "__main__":
    sys.exit(main())
