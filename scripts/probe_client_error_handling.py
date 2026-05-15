"""Exercise the project ``ValidationError`` against live-API 422 envelopes.

Sends deliberately-invalid ``POST /custom_field_definitions`` payloads
through ``KatanaClient.get_async_httpx_client()``, then parses each
422 envelope the same way the transport layer's ``_raise_for_status``
would. Lets us verify end-to-end that:

- ``DetailedErrorResponse.from_dict`` round-trips the live wire shape
- ``ValidationError.validation_errors`` captures the Ajv ``details[]``
- ``ValidationError.__str__`` / ``_format_ajv_detail`` produce readable
  output for the same payloads the raw-httpx probes hit

Uses raw httpx (not the generated API) deliberately — the generated
endpoint surface would reject these payloads at the client-side
validation step, never reaching the wire.

Pairs with ``scripts/probe_issue_737.py``: same wire calls, two
angles on the result.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from katana_public_api_client import KatanaClient
from katana_public_api_client.models import DetailedErrorResponse
from katana_public_api_client.utils import (
    APIError,
    ValidationError,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spec_drift_verify import record_artifact, tagged


def _build_error_from_raw(resp) -> APIError | None:
    """Replicate the transport's ``_raise_for_status`` for a raw ``httpx.Response``.

    The project's ``_raise_for_status`` consumes parsed ``Response[T]``
    objects from the generated API; the probes use raw httpx so we parse
    the error envelope ourselves and return the same ``ValidationError``
    instance the transport layer would raise.
    """
    if 200 <= resp.status_code < 300:
        return None
    try:
        body = resp.json()
    except Exception:
        return APIError(f"HTTP {resp.status_code}", resp.status_code, None)
    err = body.get("error") if isinstance(body, dict) else None
    if not isinstance(err, dict):
        err = {}
    name = err.get("name", "")
    message = err.get("message", "")
    full = f"{name}: {message}" if name else message

    if resp.status_code == 422:
        return ValidationError(
            full, resp.status_code, DetailedErrorResponse.from_dict(err)
        )
    return APIError(full, resp.status_code, None)


async def _post_and_inspect(client_httpx, url: str, payload: dict, label: str) -> None:
    print(f"\n=== {label} ===")
    print(f"POST {url}")
    print(f"Body: {payload}")
    resp = await client_httpx.post(url, json=payload)
    print(f"\nRaw response: HTTP {resp.status_code}")

    error = _build_error_from_raw(resp)
    if error is None:
        # The probe relies on the request being invalid — if the API
        # actually accepts it (live enum widened, schema relaxed, etc.)
        # we created a real custom field definition that the cleanup
        # ledger doesn't know about. Record it so cleanup can later
        # delete it, then exit non-zero so the operator notices.
        body = resp.json() if resp.content else {}
        entity_id = body.get("id") if isinstance(body, dict) else None
        if entity_id is not None:
            record_artifact(
                endpoint=url,
                entity_id=entity_id,
                issue="probe-error-handling",
                sku_or_name=payload.get("label", ""),
                probe_case=label,
            )
        print(
            f"\n✗ UNEXPECTED 2xx — the probe payload was accepted. "
            f"This means the live API contract has changed (or the "
            f"server accepts looser input than the probe assumes). "
            f"Recorded entity_id={entity_id} to the cleanup ledger. "
            "Re-tighten the probe payload before next run.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nConstructed error type: {type(error).__name__}")
    print(f"isinstance(error, APIError) = {isinstance(error, APIError)}")
    print(f"isinstance(error, ValidationError) = {isinstance(error, ValidationError)}")

    if isinstance(error, ValidationError):
        print(f"\nvalidation_errors captured: {len(error.validation_errors)} detail(s)")

    print("\n--- str(error) — what callers would see ---")
    print(error)


async def main() -> int:
    if not os.environ.get("KATANA_API_KEY"):
        print("KATANA_API_KEY not set — source .env first.", file=sys.stderr)
        return 2

    async with KatanaClient() as client:
        httpx_client = client.get_async_httpx_client()

        # Labels are SDT-tagged so any accidentally-created definition
        # is grep-discoverable in the Katana UI (and recorded to the
        # ledger by ``_post_and_inspect``) if the live contract widens.
        # Case 1: invalid field_type → 422 with enum detail
        await _post_and_inspect(
            httpx_client,
            "/custom_field_definitions",
            {
                "label": tagged("cfd-bad-field-type"),
                "field_type": "garbage",
                "entity_type": "SalesOrder",
                "source": "spec-drift-verify",
            },
            "Case 1 — invalid field_type",
        )

        # Case 2: invalid entity_type → 422 with much longer enum
        await _post_and_inspect(
            httpx_client,
            "/custom_field_definitions",
            {
                "label": tagged("cfd-bad-entity-type"),
                "field_type": "shortText",
                "entity_type": "garbage",
                "source": "spec-drift-verify",
            },
            "Case 2 — invalid entity_type (19-value enum)",
        )

        # Case 3: missing required fields → multiple 422 details
        await _post_and_inspect(
            httpx_client,
            "/custom_field_definitions",
            {"label": tagged("cfd-missing-required")},
            "Case 3 — missing required fields",
        )

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
