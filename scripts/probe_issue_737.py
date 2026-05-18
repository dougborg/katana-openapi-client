"""Live-API probes for issue #737 — CustomFieldDefinition shape.

Open questions (from issue body):

1. ``CustomFieldDefinition.id`` — UUID-string or integer?
2. ``field_type`` enum strictness — does the server reject unknown values?
3. ``entity_type`` enum strictness — what entity_types are actually supported?
4. ``options`` field shape — opaque ``additionalProperties`` (local spec) or
   structured ``{choices: [{label, ...}]}`` (upstream README)?

Strategy: create a small SDT-tagged definition, GET it back, inspect wire
shape; try a malformed ``field_type`` to see if 422 fires; try other
``entity_type`` values to map the accepted set. Every successful POST gets
recorded in the ledger.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spec_drift_verify import (
    label,
    make_client,
    pp_response,
    record_artifact,
)


def probe_shorttext(client: httpx.Client) -> dict:
    """Q1: id type (UUID vs integer). Q4: response shape for shortText."""
    print("\n=== Q1 + Q4: POST shortText CustomFieldDefinition ===")
    payload = {
        "label": label("verify-shorttext"),
        "field_type": "shortText",
        "entity_type": "SalesOrder",
        "source": "spec-drift-verify",
    }
    r = client.post("/custom_field_definitions", json=payload)
    print(pp_response(r))
    if not r.is_success:
        return {}
    data = r.json()
    record_artifact(
        endpoint="/custom_field_definitions",
        entity_id=data["id"],  # keep string-or-int as the live API returns it
        issue="#737",
        sku_or_name=payload["label"],
        field_type="shortText",
    )
    print(
        f"\n  → id={data.get('id')!r} ({type(data.get('id')).__name__})\n"
        f"  → response keys: {sorted(data.keys())}"
    )
    return data


def probe_singleselect(client: httpx.Client) -> dict:
    """Q4: options shape — structured choices on request + response."""
    print("\n=== Q4: POST singleSelect with structured options ===")
    payload = {
        "label": label("verify-singleselect"),
        "field_type": "singleSelect",
        "entity_type": "SalesOrder",
        "source": "spec-drift-verify",
        "options": {"choices": [{"label": "Option A"}, {"label": "Option B"}]},
    }
    r = client.post("/custom_field_definitions", json=payload)
    print(pp_response(r))
    if not r.is_success:
        return {}
    data = r.json()
    record_artifact(
        endpoint="/custom_field_definitions",
        entity_id=data["id"],
        issue="#737",
        sku_or_name=payload["label"],
        field_type="singleSelect",
    )
    print(f"\n  → options on response: {json.dumps(data.get('options'), indent=2)}")
    return data


def probe_invalid_field_type(client: httpx.Client) -> None:
    """Q2: does the server reject unknown field_type values?"""
    print("\n=== Q2: POST with invalid field_type='garbage' ===")
    r = client.post(
        "/custom_field_definitions",
        json={
            "label": label("verify-bogus-fieldtype"),
            "field_type": "garbage",
            "entity_type": "SalesOrder",
            "source": "spec-drift-verify",
        },
    )
    print(pp_response(r))
    if r.is_success:
        data = r.json()
        record_artifact(
            endpoint="/custom_field_definitions",
            entity_id=data["id"],
            issue="#737",
            sku_or_name=data.get("label"),
            note="unexpectedly-accepted invalid field_type",
        )
        print(
            "  ⚠  Unexpected: server accepted garbage field_type — local spec enum is wrong"
        )
    else:
        print(f"  ✓  Server rejected (status={r.status_code}) — enum constraint active")


def probe_other_entity_types(client: httpx.Client) -> None:
    """Q3: which entity_type values does the server accept?"""
    print("\n=== Q3: probe entity_type for accepted values ===")
    for entity_type in ("Material", "Product", "PurchaseOrder", "Customer"):
        payload = {
            "label": label(f"verify-entity-{entity_type}"),
            "field_type": "shortText",
            "entity_type": entity_type,
            "source": "spec-drift-verify",
        }
        r = client.post("/custom_field_definitions", json=payload)
        if r.is_success:
            data = r.json()
            record_artifact(
                endpoint="/custom_field_definitions",
                entity_id=data["id"],
                issue="#737",
                sku_or_name=payload["label"],
                entity_type=entity_type,
            )
            print(f"  ✓  {entity_type}: accepted (id={data['id']})")
        else:
            print(
                f"  ✗  {entity_type}: rejected (status={r.status_code}, body={r.text[:120]})"
            )


def main() -> int:
    with make_client() as client:
        probe_shorttext(client)
        probe_singleselect(client)
        probe_invalid_field_type(client)
        probe_other_entity_types(client)
    print("\nDone. Run `uv run python scripts/spec_drift_verify.py list` for ledger.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
