"""Tests for ``scripts/_safety.py`` — the ``SafeClient`` mutation guard.

Covers the pre-mutation identity guard, ledger-membership fallback,
``NO_GET_BY_ID`` ledger-only enforcement, ``allow_unsafe`` bypass,
post-mutation verify hooks (silent-drop detection), and the
``discover_sdt_fixture`` discovery helper.

All tests use ``httpx.MockTransport`` to avoid live API calls — the
guard logic is wire-shape-only and doesn't require a real tenant.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest
from scripts._safety import (
    SafeClient,
    SilentDropError,
    UnsafeMutationError,
    _is_sdt_tagged,
    _split_path,
    discover_sdt_fixture,
    verify_production_serial_numbers_match,
)

Handler = Callable[[httpx.Request], httpx.Response]


def _build_safe_client(
    handler: Handler,
    *,
    allow_unsafe: bool = False,
    ledger_keys: set[tuple[str, str]] | None = None,
) -> SafeClient:
    """Construct a ``SafeClient`` backed by ``httpx.MockTransport``."""
    return SafeClient(
        base_url="https://api.katana.test",
        transport=httpx.MockTransport(handler),
        allow_unsafe=allow_unsafe,
        ledger_keys=ledger_keys,
    )


# ----------------------------------------------------------------------
# POST guard — top-level identity check
# ----------------------------------------------------------------------


class TestPostIdentityGuard:
    """POST mutations are gated on the body's identity field carrying SDT-."""

    def test_post_with_sdt_identity_allowed(self) -> None:
        called: dict[str, bool] = {"sent": False}

        def handler(request: httpx.Request) -> httpx.Response:
            called["sent"] = True
            return httpx.Response(200, json={"id": 1, "order_no": "SDT-2026-05-19-A"})

        client = _build_safe_client(handler)
        try:
            resp = client.post("/sales_orders", json={"order_no": "SDT-2026-05-19-A"})
            assert resp.status_code == 200
            assert called["sent"]
        finally:
            client.close()

    def test_post_with_label_form_identity_allowed(self) -> None:
        """``label()`` produces ``[SDT-…] free text`` — the bracketed form."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 7, "name": "ok"})

        client = _build_safe_client(handler)
        try:
            resp = client.post(
                "/materials", json={"name": "[SDT-2026-05-19] Test Material"}
            )
            assert resp.status_code == 200
        finally:
            client.close()

    def test_post_without_sdt_identity_refused(self) -> None:
        """The WEB20604 class: identity field is set but doesn't carry SDT-."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse the request before the wire call")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post("/sales_orders", json={"order_no": "#WEB20604"})
            assert exc_info.value.method == "POST"
            assert exc_info.value.endpoint == "/sales_orders"
            assert exc_info.value.identity_field == "order_no"
            assert exc_info.value.identity_value == "#WEB20604"
        finally:
            client.close()

    def test_post_with_server_generated_identity_allowed(self) -> None:
        """Identity field absent from body → server generates it. Permit."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, json={"id": 1, "order_no": "Katana-generated-no"}
            )

        client = _build_safe_client(handler)
        try:
            # No ``order_no`` — caller relies on Katana minting one.
            resp = client.post("/sales_orders", json={"customer_id": 42})
            assert resp.status_code == 200
        finally:
            client.close()

    def test_post_to_unknown_endpoint_refused(self) -> None:
        """Defense-in-depth: unknown endpoints can't be mutated until mapped."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse on unknown endpoint")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post("/unknown_endpoint", json={"name": "SDT-x"})
            assert "not in IDENTITY_FIELDS" in exc_info.value.reason
        finally:
            client.close()

    def test_post_without_body_refused(self) -> None:
        """A POST that omits ``json=`` has nothing to inspect — fail closed
        rather than wire the empty payload (which Katana would 422)."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse before the wire call")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post("/sales_orders")
            assert "no JSON body" in exc_info.value.reason
        finally:
            client.close()

    def test_post_with_explicit_null_identity_refused(self) -> None:
        """``{"order_no": None, ...}`` is NOT the same as omitting the
        field. Explicit null is caller intent and must not be treated as
        "server-generated" — a real customer's record could plausibly
        have a null identity column, so we fail closed."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse explicit-null identity")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post(
                    "/sales_orders",
                    json={"order_no": None, "customer_id": 1, "location_id": 2},
                )
            assert "order_no" in exc_info.value.reason
            assert "no SDT- prefix" in exc_info.value.reason
        finally:
            client.close()

    def test_post_with_omitted_identity_allowed(self) -> None:
        """Key-absent (genuine server-generated identity request) is
        permissive — the probe records the resulting ID into the ledger
        and every subsequent mutation is then ledger-protected. This
        pairs with ``test_post_with_explicit_null_identity_refused`` to
        document the absent-vs-null asymmetry."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 99, "order_no": "auto-gen"})

        client = _build_safe_client(handler)
        try:
            resp = client.post(
                "/sales_orders",
                json={"customer_id": 1, "location_id": 2},  # no order_no key
            )
            assert resp.status_code == 200
        finally:
            client.close()

    def test_post_webhook_identity_field_is_description(self) -> None:
        """``/webhooks`` identity must be ``description`` not ``url`` —
        webhook URLs must be ``https://…`` per Katana's spec pattern, so
        the ``url`` field could never carry an ``SDT-`` prefix. The
        guard therefore looks at ``description``."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 1})

        client = _build_safe_client(handler)
        try:
            resp = client.post(
                "/webhooks",
                json={
                    "url": "https://webhook.example.test/probe",
                    "subscribed_events": ["sales_order.created"],
                    "description": "[SDT-2026-05-19] probe-webhook",
                },
            )
            assert resp.status_code == 200
        finally:
            client.close()

    def test_post_webhook_non_sdt_description_refused(self) -> None:
        """A webhook POST with a ``description`` that lacks SDT- must fail
        closed — confirms the identity field is being read."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse non-SDT webhook description")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post(
                    "/webhooks",
                    json={
                        "url": "https://webhook.example.test/probe",
                        "subscribed_events": ["sales_order.created"],
                        "description": "production integration",
                    },
                )
            assert exc_info.value.identity_field == "description"
            assert exc_info.value.identity_value == "production integration"
        finally:
            client.close()

    def test_post_webhook_missing_description_refused(self) -> None:
        """``/webhooks`` is in ``IDENTITY_REQUIRED`` because webhooks
        have IMMEDIATE live side effects — Katana starts delivering real
        tenant events to the caller-supplied URL the moment POST returns
        201. Unlike a missing ``order_no`` (which the server will
        generate and the ledger then protects), a missing
        ``description`` here is a data-exfiltration risk during the
        record's lifetime. Fail closed when the field is absent rather
        than the standard "key-absent ⇒ permissive" path."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse webhook without description")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post(
                    "/webhooks",
                    json={
                        "url": "https://webhook.example.test/probe",
                        "subscribed_events": ["sales_order.created"],
                        # description deliberately omitted
                    },
                )
            assert exc_info.value.identity_field == "description"
            assert "immediate live side effects" in exc_info.value.reason
        finally:
            client.close()


# ----------------------------------------------------------------------
# POST guard — child endpoints (no top-level identity)
# ----------------------------------------------------------------------


class TestPostChildEndpoint:
    """POST to child endpoints (e.g. ``/sales_order_fulfillments``)
    requires the parent ID to be in the local ledger."""

    def test_post_child_with_parent_in_ledger_allowed(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 99})

        client = _build_safe_client(handler, ledger_keys={("/sales_orders", "42")})
        try:
            resp = client.post(
                "/sales_order_fulfillments",
                json={"sales_order_id": 42, "status": "PACKED"},
            )
            assert resp.status_code == 200
        finally:
            client.close()

    def test_post_child_with_parent_missing_from_ledger_refused(self) -> None:
        """Exactly the WEB20604 failure mode: ``sales_order_id`` came
        from ``discover_fixtures()`` without an SDT discipline."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse on missing parent")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post(
                    "/sales_order_fulfillments",
                    json={"sales_order_id": 9999, "status": "PACKED"},
                )
            assert exc_info.value.identity_field == "sales_order_id"
            assert "not in the local ledger" in exc_info.value.reason
        finally:
            client.close()

    def test_post_child_missing_parent_fk_refused(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse on missing parent FK")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.post("/sales_order_fulfillments", json={"status": "PACKED"})
            assert "missing parent FK" in exc_info.value.reason
        finally:
            client.close()


# ----------------------------------------------------------------------
# PATCH / DELETE guard — ledger membership + pre-fetch check
# ----------------------------------------------------------------------


class TestPatchDeleteGuard:
    def test_patch_id_in_ledger_skips_prefetch(self) -> None:
        """Ledger membership bypasses the pre-fetch round-trip."""
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            return httpx.Response(200, json={"id": 7})

        client = _build_safe_client(handler, ledger_keys={("/materials", "7")})
        try:
            resp = client.patch("/materials/7", json={"name": "anything"})
            assert resp.status_code == 200
            # Only the PATCH itself — no pre-fetch GET.
            assert calls == [("PATCH", "/materials/7")]
        finally:
            client.close()

    def test_patch_id_not_in_ledger_fetches_and_accepts_sdt_prefix(self) -> None:
        """Pre-fetch fires; identity field carries SDT- → allow."""
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            if request.method == "GET":
                return httpx.Response(200, json={"id": 9, "name": "[SDT-2026-05-19] X"})
            return httpx.Response(200, json={"id": 9})

        client = _build_safe_client(handler)
        try:
            resp = client.patch("/materials/9", json={"name": "[SDT-…] Y"})
            assert resp.status_code == 200
            assert calls == [("GET", "/materials/9"), ("PATCH", "/materials/9")]
        finally:
            client.close()

    def test_patch_id_not_in_ledger_refused_when_prefix_missing(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(
                    200, json={"id": 9, "name": "Real Customer Order"}
                )
            pytest.fail("PATCH should not be sent")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.patch("/materials/9", json={"name": "anything"})
            assert exc_info.value.target_id == "9"
            assert exc_info.value.identity_value == "Real Customer Order"
        finally:
            client.close()

    def test_delete_id_not_in_ledger_404_treated_idempotent(self) -> None:
        """Pre-fetch returns 404 → already gone, let DELETE proceed."""

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(404, json={"error": "not found"})
            return httpx.Response(204)

        client = _build_safe_client(handler)
        try:
            resp = client.delete("/materials/123")
            assert resp.status_code == 204
        finally:
            client.close()

    def test_patch_id_not_in_ledger_404_refused(self) -> None:
        """PATCH must fail closed on a 404 pre-fetch — unlike DELETE
        (idempotent), a 404 PATCH means the SDT identity check never
        ran, so we can't prove the target was ever an SDT record."""

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(404, json={"error": "not found"})
            pytest.fail("guard should refuse PATCH before issuing the mutation")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.patch("/materials/123", json={"name": "anything"})
            assert "404" in exc_info.value.reason
            assert "PATCH cannot proceed" in exc_info.value.reason
        finally:
            client.close()

    def test_patch_prefetch_5xx_refused(self) -> None:
        """A 5xx pre-fetch (or 401/403) means the identity check never
        completed — fail closed rather than let the PATCH through."""

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(500, json={"error": "internal"})
            pytest.fail("PATCH should not be sent on failed pre-fetch")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.patch("/materials/9", json={"name": "anything"})
            assert "500" in exc_info.value.reason
        finally:
            client.close()

    def test_patch_prefetch_network_error_refused(self) -> None:
        """A transport-layer exception on pre-fetch (timeout, connect
        error) MUST fail closed — the most important fallback path of
        the entire guard, since a "let it through on transport error"
        bug would silently disable the SDT check for any flaky network."""
        import httpx as _httpx

        def handler(_request: httpx.Request) -> httpx.Response:
            raise _httpx.ConnectError("simulated network failure")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.patch("/materials/9", json={"name": "anything"})
            assert "pre-fetch GET failed" in exc_info.value.reason
        finally:
            client.close()

    def test_patch_no_get_by_id_endpoint_ledger_only_refused(self) -> None:
        """``/stock_transfers`` has no GET-by-id; without ledger
        membership the guard has nothing left to check → refuse."""

        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse on NO_GET_BY_ID without ledger")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.patch("/stock_transfers/55", json={"status": "received"})
            assert "does not support GET-by-id" in exc_info.value.reason
        finally:
            client.close()

    def test_patch_no_get_by_id_endpoint_with_ledger_allowed(self) -> None:
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            return httpx.Response(200, json={"id": 55})

        client = _build_safe_client(handler, ledger_keys={("/stock_transfers", "55")})
        try:
            resp = client.patch("/stock_transfers/55", json={"status": "received"})
            assert resp.status_code == 200
            assert calls == [("PATCH", "/stock_transfers/55")]
        finally:
            client.close()

    def test_delete_no_path_id_refused(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse DELETE without an id")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError) as exc_info:
                client.delete("/materials")
            assert "requires a target ID" in exc_info.value.reason
        finally:
            client.close()


# ----------------------------------------------------------------------
# ``allow_unsafe`` bypass
# ----------------------------------------------------------------------


class TestAllowUnsafe:
    def test_allow_unsafe_bypasses_all_checks(self) -> None:
        """Used by cleanup paths where the ledger pre-vetted the target."""
        sent: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            sent.append(request.method)
            return httpx.Response(204)

        client = _build_safe_client(handler, allow_unsafe=True)
        try:
            # Would normally raise: no SDT in body, no ledger entry.
            client.post("/sales_orders", json={"order_no": "#WEB20604"})
            client.delete("/materials/12345")
            client.patch("/stock_transfers/55", json={"status": "received"})
            assert sent == ["POST", "DELETE", "PATCH"]
        finally:
            client.close()


# ----------------------------------------------------------------------
# Ledger registration — keeps the in-memory ledger fresh
# ----------------------------------------------------------------------


class TestLedgerRegistration:
    def test_register_artifact_extends_in_memory_ledger(self) -> None:
        """A freshly-created record should be PATCHable without a
        pre-fetch — the in-memory ledger is the fast path."""
        get_called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal get_called
            if request.method == "GET":
                get_called = True
            return httpx.Response(200, json={"id": 11})

        client = _build_safe_client(handler)
        try:
            client.register_artifact("/materials", 11)
            client.patch("/materials/11", json={"name": "[SDT-…]"})
            assert not get_called, "register_artifact should bypass pre-fetch"
        finally:
            client.close()

    def test_register_artifact_handles_int_and_str_ids(self) -> None:
        """``CustomFieldDefinition.id`` is a UUID string; others are ints."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        client = _build_safe_client(handler)
        try:
            client.register_artifact("/custom_field_definitions", "abc-123-uuid")
            assert client.in_ledger("/custom_field_definitions", "abc-123-uuid")
            client.register_artifact("/materials", 42)
            # Both string and int IDs resolve under the same canonical key.
            assert client.in_ledger("/materials", 42)
            assert client.in_ledger("/materials", "42")
        finally:
            client.close()


# ----------------------------------------------------------------------
# Read-only methods bypass the guard
# ----------------------------------------------------------------------


class TestReadOnlyBypass:
    def test_get_is_unrestricted(self) -> None:
        sent: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            sent.append(request.method)
            return httpx.Response(200, json={"data": []})

        client = _build_safe_client(handler)
        try:
            client.get("/sales_orders")
            client.get("/sales_orders/99")  # arbitrary ID — no guard
            assert sent == ["GET", "GET"]
        finally:
            client.close()


# ----------------------------------------------------------------------
# Verify hooks — post-mutation silent-drop detection
# ----------------------------------------------------------------------


class TestVerifyHook:
    def test_verify_hook_fires_on_2xx_and_can_raise(self) -> None:
        """Hook registered on ``(POST, /materials)`` runs after 2xx."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 1})

        def assertion_hook(_req: httpx.Request, _resp: httpx.Response) -> None:
            raise SilentDropError(
                method="POST",
                endpoint="/materials",
                reason="synthetic",
            )

        client = _build_safe_client(handler)
        client.register_verify("POST", "/materials", assertion_hook)
        try:
            with pytest.raises(SilentDropError):
                client.post("/materials", json={"name": "[SDT-…]"})
        finally:
            client.close()

    def test_verify_hook_does_not_fire_on_non_2xx(self) -> None:
        """422 / 5xx — no silent drop, hook should not run (the
        response itself signals the failure)."""
        hook_called = False

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"error": "validation"})

        def hook(_req: httpx.Request, _resp: httpx.Response) -> None:
            nonlocal hook_called
            hook_called = True

        client = _build_safe_client(handler)
        client.register_verify("POST", "/materials", hook)
        try:
            client.post("/materials", json={"name": "[SDT-…]"})
            assert not hook_called
        finally:
            client.close()

    def test_production_serial_drop_hook_detects_mismatch(self) -> None:
        """The companion-comment use case: ``POST /manufacturing_order_productions``
        with serial IDs that Katana silently drops on the wire."""

        def handler(_: httpx.Request) -> httpx.Response:
            # Caller asked for 3 serials, response carries 0 — the
            # silent-drop wire shape we're guarding against.
            return httpx.Response(200, json={"id": 1, "serial_numbers": []})

        client = _build_safe_client(
            handler,
            ledger_keys={("/manufacturing_orders", "77")},
        )
        client.register_verify(
            "POST",
            "/manufacturing_order_productions",
            verify_production_serial_numbers_match,
        )
        try:
            with pytest.raises(SilentDropError) as exc_info:
                client.post(
                    "/manufacturing_order_productions",
                    json={
                        "manufacturing_order_id": 77,
                        "serial_numbers": [101, 102, 103],
                    },
                )
            assert "requested 3" in exc_info.value.reason
            assert "carries 0" in exc_info.value.reason
        finally:
            client.close()

    def test_production_serial_hook_accepts_matching_counts(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"id": 1, "serial_numbers": [{"id": 101}, {"id": 102}]},
            )

        client = _build_safe_client(
            handler,
            ledger_keys={("/manufacturing_orders", "77")},
        )
        client.register_verify(
            "POST",
            "/manufacturing_order_productions",
            verify_production_serial_numbers_match,
        )
        try:
            resp = client.post(
                "/manufacturing_order_productions",
                json={"manufacturing_order_id": 77, "serial_numbers": [101, 102]},
            )
            assert resp.status_code == 200
        finally:
            client.close()

    def test_verify_hook_does_not_fire_on_get(self) -> None:
        """Hooks are post-mutation only; GET responses bypass them even
        if a hook is registered on ``("GET", endpoint)`` (defensive: the
        registration API doesn't reject non-mutation methods, but
        ``request()`` must not invoke them on reads)."""
        hook_called = False

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": []})

        def hook(_req: httpx.Request, _resp: httpx.Response) -> None:
            nonlocal hook_called
            hook_called = True

        client = _build_safe_client(handler)
        client.register_verify("GET", "/customers", hook)
        try:
            resp = client.get("/customers")
            assert resp.status_code == 200
            assert not hook_called
        finally:
            client.close()


# ----------------------------------------------------------------------
# ``_is_sdt_tagged`` / ``_SDT_RE`` — anchored prefix match
# ----------------------------------------------------------------------


class TestSdtRegexAnchoring:
    """``_SDT_RE`` only accepts ``SDT-`` at the very start of the string
    (bare or wrapped in ``[…]``). Substrings like ``MySDT-foo`` must
    NOT match — otherwise a real customer named e.g.
    ``"Acme [SDT-Subdivision] Co"`` would slip the guard."""

    @pytest.mark.parametrize(
        "value",
        [
            "SDT-2026-05-19-customer",
            "[SDT-2026-05-19] probe-customer",
            "[SDT-…] free text",
        ],
    )
    def test_accepts_prefix_forms(self, value: str) -> None:
        assert _is_sdt_tagged(value)

    @pytest.mark.parametrize(
        "value",
        [
            "MySDT-something",  # SDT- not at start (bare form)
            "Acme [SDT-Sub] Co",  # [SDT- embedded mid-string
            "prefix SDT-tail",  # SDT- preceded by whitespace
            "",  # empty
            "SDT",  # missing trailing hyphen
            "[SDT]",  # missing trailing hyphen
        ],
    )
    def test_rejects_non_prefix_forms(self, value: str) -> None:
        assert not _is_sdt_tagged(value)

    def test_rejects_non_strings(self) -> None:
        assert not _is_sdt_tagged(None)
        assert not _is_sdt_tagged(42)
        assert not _is_sdt_tagged(["SDT-foo"])


# ----------------------------------------------------------------------
# ``discover_sdt_fixture`` — replaces "grab first customer" with
# "grab first SDT- customer"
# ----------------------------------------------------------------------


class TestDiscoverSdtFixture:
    def test_returns_first_sdt_row_filtered_clientside(self) -> None:
        """Katana list filters are exact-match; client-side filter is the only path."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 1, "name": "Real Customer"},
                        {"id": 2, "name": "Another Real One"},
                        {"id": 3, "name": "[SDT-2026-05-19] probe-customer"},
                        {"id": 4, "name": "[SDT-…] another"},
                    ]
                },
            )

        client = _build_safe_client(handler)
        try:
            row = discover_sdt_fixture(client, "/customers", "name")
            assert row is not None
            assert row["id"] == 3
        finally:
            client.close()

    def test_returns_none_when_no_sdt_row_exists(self) -> None:
        """Empty result is a deliberate ``None`` so the caller decides
        whether to create one or skip."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 1, "name": "Real A"},
                        {"id": 2, "name": "Real B"},
                    ]
                },
            )

        client = _build_safe_client(handler)
        try:
            assert discover_sdt_fixture(client, "/customers", "name") is None
        finally:
            client.close()

    def test_paginates_through_results(self) -> None:
        """Walks pages until it finds an SDT row or runs out."""
        pages_hit: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            pages_hit.append(str(request.url.params))
            params = request.url.params
            page = int(params.get("page", "1"))
            limit = int(params.get("limit", "50"))
            if page == 1:
                # Full page of non-SDT rows — must paginate.
                return httpx.Response(
                    200,
                    json={
                        "data": [{"id": i, "name": f"Real {i}"} for i in range(limit)]
                    },
                )
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 100, "name": "[SDT-…] probe"},
                    ]
                },
            )

        client = _build_safe_client(handler)
        try:
            row = discover_sdt_fixture(client, "/customers", "name", limit=10)
            assert row is not None
            assert row["id"] == 100
            assert len(pages_hit) == 2
        finally:
            client.close()

    def test_returns_none_when_list_endpoint_errors(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "boom"})

        client = _build_safe_client(handler)
        try:
            assert discover_sdt_fixture(client, "/customers", "name") is None
        finally:
            client.close()


# ----------------------------------------------------------------------
# Custom-field definition: UUID string IDs (the only non-int identity)
# ----------------------------------------------------------------------


class TestCustomFieldUuidIds:
    def test_patch_custom_field_definition_uuid_in_ledger(self) -> None:
        """Custom field IDs are UUID strings; the ledger key must
        round-trip them as strings, not ints."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": "abc-123-uuid"})

        ledger = {("/custom_field_definitions", "abc-123-uuid")}
        client = _build_safe_client(handler, ledger_keys=ledger)
        try:
            resp = client.patch(
                "/custom_field_definitions/abc-123-uuid",
                json={"label": "[SDT-…]"},
            )
            assert resp.status_code == 200
        finally:
            client.close()


# ----------------------------------------------------------------------
# Verify hook decode helper — request body parsing
# ----------------------------------------------------------------------


class TestVerifyHookDecode:
    def test_production_hook_silently_returns_on_empty_request(self) -> None:
        """No ``serial_numbers`` in the request → nothing to verify."""

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 1, "serial_numbers": []})

        client = _build_safe_client(
            handler, ledger_keys={("/manufacturing_orders", "77")}
        )
        client.register_verify(
            "POST",
            "/manufacturing_order_productions",
            verify_production_serial_numbers_match,
        )
        try:
            # Caller didn't request serials → response shape doesn't matter.
            resp = client.post(
                "/manufacturing_order_productions",
                json={"manufacturing_order_id": 77, "quantity": 1},
            )
            assert resp.status_code == 200
        finally:
            client.close()


# ----------------------------------------------------------------------
# POST array-body inspection (some endpoints accept ``[{...}, ...]``)
# ----------------------------------------------------------------------


class TestArrayBodyInspection:
    def test_post_array_body_all_items_must_pass(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse on first failing item")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError):
                client.post(
                    "/sales_orders",
                    json=[
                        {"order_no": "SDT-2026-05-19-A"},
                        {"order_no": "#WEB20604"},  # second one fails
                    ],
                )
        finally:
            client.close()


# ----------------------------------------------------------------------
# Encoding sanity — body is sent JSON-encoded, hooks see it decoded.
# ----------------------------------------------------------------------


class TestSplitPathNormalization:
    """``_split_path`` must accept absolute and relative URL forms.

    httpx attaches ``base_url`` at send-time, so the guard sees whatever
    the caller passed in — including relative strings like
    ``sales_orders/42``. The pre-fix code assumed a leading ``/`` and
    would IndexError or mis-attribute the collection name on relative
    inputs, silently bypassing the identity check.
    """

    def test_absolute_path_collection_only(self) -> None:
        assert _split_path("/sales_orders") == ("/sales_orders", None)

    def test_absolute_path_with_id(self) -> None:
        assert _split_path("/sales_orders/42") == ("/sales_orders", "42")

    def test_relative_path_collection_only(self) -> None:
        assert _split_path("sales_orders") == ("/sales_orders", None)

    def test_relative_path_with_id(self) -> None:
        assert _split_path("sales_orders/42") == ("/sales_orders", "42")

    def test_trailing_slash_stripped(self) -> None:
        assert _split_path("/sales_orders/") == ("/sales_orders", None)
        assert _split_path("sales_orders/") == ("/sales_orders", None)

    def test_query_string_ignored(self) -> None:
        assert _split_path("/sales_orders/42?include=rows") == (
            "/sales_orders",
            "42",
        )

    def test_full_url_with_scheme(self) -> None:
        assert _split_path("https://api.katana.test/sales_orders/42") == (
            "/sales_orders",
            "42",
        )

    def test_sub_resource_falls_through_to_parent(self) -> None:
        # ``/sales_orders/42/rows`` — guard targets the parent SO id.
        assert _split_path("/sales_orders/42/rows") == ("/sales_orders", "42")

    def test_empty_path_returns_empty(self) -> None:
        assert _split_path("") == ("", None)
        assert _split_path("/") == ("", None)


class TestLedgerTenantScoping:
    """``_initial_ledger_keys`` must filter rows by tenant.

    If an API-key swap happens but the on-disk ledger still has rows
    from the previous tenant, those rows must NOT seed the in-memory
    ledger fast-path — otherwise the SafeClient would let through a
    PATCH/DELETE targeting an ID that belongs to a *real* record on
    the new tenant.

    Mirrors the cleanup-side filter in ``cleanup()``.
    """

    def test_filters_out_rows_with_different_base_url(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        from scripts import spec_drift_verify as sdv

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "endpoint": "/sales_orders",
                            "entity_id": 1,
                            "base_url": "https://api.katana.test",
                            "factory_id": 100,
                            "issue": "x",
                            "method": "POST",
                            "created_at": "2026-01-01T00:00:00",
                        }
                    ),
                    json.dumps(
                        {
                            "endpoint": "/sales_orders",
                            "entity_id": 2,
                            "base_url": "https://other-tenant.katana.example",
                            "factory_id": 200,
                            "issue": "x",
                            "method": "POST",
                            "created_at": "2026-01-01T00:00:00",
                        }
                    ),
                ]
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)

        keys = sdv._initial_ledger_keys()
        assert keys == {("/sales_orders", "1")}

    def test_filters_out_rows_with_different_factory_id(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """Same base_url, different API key → different factory_id → exclude."""
        from scripts import spec_drift_verify as sdv

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "endpoint": "/sales_orders",
                            "entity_id": 10,
                            "base_url": "https://api.katana.test",
                            "factory_id": 100,
                            "issue": "x",
                            "method": "POST",
                            "created_at": "2026-01-01T00:00:00",
                        }
                    ),
                    json.dumps(
                        {
                            "endpoint": "/sales_orders",
                            "entity_id": 11,
                            "base_url": "https://api.katana.test",
                            "factory_id": 999,  # other tenant
                            "issue": "x",
                            "method": "POST",
                            "created_at": "2026-01-01T00:00:00",
                        }
                    ),
                ]
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)

        keys = sdv._initial_ledger_keys()
        assert keys == {("/sales_orders", "10")}

    def test_fail_closed_when_current_factory_id_unresolvable(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """Row carries factory_id, current credential can't resolve one → exclude.

        Same fail-closed posture as ``cleanup()`` — when the active
        tenant is unverifiable, refuse to admit fingerprinted rows
        rather than admit them and hope.
        """
        from scripts import spec_drift_verify as sdv

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            json.dumps(
                {
                    "endpoint": "/sales_orders",
                    "entity_id": 5,
                    "base_url": "https://api.katana.test",
                    "factory_id": 100,
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: None)

        keys = sdv._initial_ledger_keys()
        assert keys == set()

    def test_pre_fingerprint_rows_rejected(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """Pre-fingerprint rows (no ``base_url`` / ``factory_id``) MUST
        be dropped — without a tenant signal we can't prove they belong
        to the current credential, and ledger-only guard paths
        (``NO_GET_BY_ID`` endpoints + child POSTs that only check parent
        ledger membership) would otherwise accept them as a cross-tenant
        allow-list bypass."""
        from scripts import spec_drift_verify as sdv

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            json.dumps(
                {
                    "endpoint": "/sales_orders",
                    "entity_id": 7,
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)

        keys = sdv._initial_ledger_keys()
        assert keys == set()


class TestCleanupTenantScoping:
    """``cleanup()`` runs with ``allow_unsafe=True`` so the SafeClient
    mutation guard is bypassed — the tenant fingerprint check in cleanup
    itself is the ONLY guard against cross-tenant deletion. Symmetric
    with the seed-side ``_initial_ledger_keys`` fail-closed: a row
    without a fingerprint MUST be skipped, not deleted."""

    def test_pre_fingerprint_row_skipped_not_deleted(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        from scripts import spec_drift_verify as sdv

        deletes: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "DELETE":
                deletes.append(request.url.path)
            return httpx.Response(204)

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            # Pre-fingerprint row: no base_url, no factory_id. Under the
            # pre-fix cleanup logic this would have been DELETED.
            json.dumps(
                {
                    "endpoint": "/sales_orders",
                    "entity_id": 42,
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)
        monkeypatch.setattr(
            sdv,
            "make_client",
            lambda allow_unsafe=False: SafeClient(
                base_url="https://api.katana.test",
                transport=httpx.MockTransport(handler),
                allow_unsafe=True,
            ),
        )

        rc = sdv.cleanup()
        # Should have refused to delete the unscoped row.
        assert deletes == []
        # Skipped rows do not flip the exit code to failure.
        assert rc == 0

    def test_skip_message_names_which_fingerprint_field_is_missing(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ) -> None:
        """A row with ``base_url`` present but ``factory_id`` missing (e.g.
        ``/factory`` lookup failed transiently at record time) must be
        skipped, and the operator-facing skip message must name the
        actually-missing field so manual triage isn't misled."""
        from scripts import spec_drift_verify as sdv

        deletes: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "DELETE":
                deletes.append(request.url.path)
            return httpx.Response(204)

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            json.dumps(
                {
                    "endpoint": "/sales_orders",
                    "entity_id": 42,
                    "base_url": "https://api.katana.test",
                    # factory_id deliberately omitted (transient miss)
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)
        monkeypatch.setattr(
            sdv,
            "make_client",
            lambda allow_unsafe=False: SafeClient(
                base_url="https://api.katana.test",
                transport=httpx.MockTransport(handler),
                allow_unsafe=True,
            ),
        )

        rc = sdv.cleanup()
        captured = capsys.readouterr()
        assert deletes == []
        assert rc == 0
        # Message names the actually-missing field, not the union label.
        assert "missing factory_id" in captured.out
        assert "missing base_url" not in captured.out

    def test_factory_id_unresolvable_skips_scoped_row(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """A scoped row whose tenant cannot be verified (factory_id
        currently unresolvable) MUST be skipped, not deleted — matches
        the cross-tenant fail-closed posture of the seed side."""
        from scripts import spec_drift_verify as sdv

        deletes: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "DELETE":
                deletes.append(request.url.path)
            return httpx.Response(204)

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            json.dumps(
                {
                    "endpoint": "/sales_orders",
                    "entity_id": 42,
                    "base_url": "https://api.katana.test",
                    "factory_id": 100,
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: None)
        monkeypatch.setattr(
            sdv,
            "make_client",
            lambda allow_unsafe=False: SafeClient(
                base_url="https://api.katana.test",
                transport=httpx.MockTransport(handler),
                allow_unsafe=True,
            ),
        )

        rc = sdv.cleanup()
        assert deletes == []
        assert rc == 0


class TestMakeClientAllowUnsafeSkipsLedger:
    """``make_client(allow_unsafe=True)`` must NOT read the ledger.

    ``allow_unsafe`` bypasses the guard, so the ledger-keys aren't
    consulted at runtime. Skipping the initial read removes the
    wasted I/O AND breaks a chicken-and-egg bootstrap:
    ``_initial_ledger_keys`` calls ``_resolve_factory_id``, which itself
    constructs a SafeClient via ``make_client(allow_unsafe=True)`` to
    GET ``/factory``. Without the skip, that path would recurse.
    """

    def test_allow_unsafe_does_not_call_initial_ledger_keys(
        self,
        monkeypatch,
    ) -> None:
        from scripts import spec_drift_verify as sdv

        called = {"n": 0}

        def fake_ledger_keys() -> set[tuple[str, str]]:
            called["n"] += 1
            return set()

        monkeypatch.setattr(sdv, "_initial_ledger_keys", fake_ledger_keys)
        monkeypatch.setattr(sdv, "_api_key", lambda: "fake-key")
        # Drain the live-client registry between tests so leak doesn't
        # cross test boundaries.
        monkeypatch.setattr(sdv, "_LIVE_CLIENTS", [])

        client = sdv.make_client(allow_unsafe=True)
        client.close()
        assert called["n"] == 0

    def test_default_does_call_initial_ledger_keys(
        self,
        monkeypatch,
    ) -> None:
        """Sanity: the skip only kicks in for ``allow_unsafe=True``."""
        from scripts import spec_drift_verify as sdv

        called = {"n": 0}

        def fake_ledger_keys() -> set[tuple[str, str]]:
            called["n"] += 1
            return set()

        monkeypatch.setattr(sdv, "_initial_ledger_keys", fake_ledger_keys)
        monkeypatch.setattr(sdv, "_api_key", lambda: "fake-key")
        monkeypatch.setattr(sdv, "_LIVE_CLIENTS", [])

        client = sdv.make_client()
        client.close()
        assert called["n"] == 1


class TestIdentityRequiredInvariant:
    """``IDENTITY_REQUIRED`` opts endpoints out of the key-absent permissive
    path. The module-level assertion must reject configurations where an
    opt-in endpoint either (a) is missing from ``IDENTITY_FIELDS``, or
    (b) is mapped to ``None`` — both would silently disable the
    required-identity enforcement at call time."""

    def test_required_must_be_in_identity_fields(self) -> None:
        """An ``IDENTITY_REQUIRED`` entry with no matching
        ``IDENTITY_FIELDS`` row would make the guard raise an
        ``UnsafeMutationError`` with ``identity_field=None`` — opaque.
        The assertion forbids this configuration."""
        from scripts._safety import IDENTITY_FIELDS, IDENTITY_REQUIRED

        # The shipped configuration must satisfy the invariant.
        missing = IDENTITY_REQUIRED - IDENTITY_FIELDS.keys()
        assert not missing, f"unexpected drift: {missing}"

    def test_required_must_map_to_non_none(self) -> None:
        """An ``IDENTITY_REQUIRED`` entry mapped to ``None`` would
        short-circuit ``_check_post_item`` at the ``identity_field is
        not None`` gate, so the required-identity branch would never
        fire on that endpoint. The assertion forbids this too."""
        from scripts._safety import IDENTITY_FIELDS, IDENTITY_REQUIRED

        none_mapped = {
            ep for ep in IDENTITY_REQUIRED if IDENTITY_FIELDS.get(ep) is None
        }
        assert not none_mapped, f"unexpected drift: {none_mapped}"


class TestCleanupSummaryBuckets:
    """``cleanup()`` summary must distinguish "different tenant" rows
    (foreign — re-run cleanup against that tenant) from "unverifiable"
    rows (could be ours, can't prove it). Mixing them was the original
    misleading wording."""

    def test_summary_labels_mismatch_distinct_from_unverifiable(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ) -> None:
        from scripts import spec_drift_verify as sdv

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            "\n".join(
                [
                    # Mismatch: definitively wrong base_url.
                    json.dumps(
                        {
                            "endpoint": "/sales_orders",
                            "entity_id": 1,
                            "base_url": "https://wrong.katana.test",
                            "factory_id": 200,
                            "issue": "x",
                            "method": "POST",
                            "created_at": "2026-01-01T00:00:00",
                        }
                    ),
                    # Unverifiable: missing fingerprint fields.
                    json.dumps(
                        {
                            "endpoint": "/sales_orders",
                            "entity_id": 2,
                            "issue": "x",
                            "method": "POST",
                            "created_at": "2026-01-01T00:00:00",
                        }
                    ),
                ]
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)
        monkeypatch.setattr(
            sdv,
            "make_client",
            lambda allow_unsafe=False: SafeClient(
                base_url="https://api.katana.test",
                transport=httpx.MockTransport(handler),
                allow_unsafe=True,
            ),
        )

        sdv.cleanup()
        out = capsys.readouterr().out
        # Both buckets surfaced separately.
        assert "1 from a different tenant/base URL" in out
        assert "1 could not be verified" in out

    def test_stale_delete_error_cleared_when_row_now_skipped(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """A row that was ``failed`` in a prior run carries
        ``delete_error`` in the ledger. If on a subsequent run the row
        now qualifies for a skip bucket (e.g. the operator swapped
        ``BASE_URL``), the rewritten ledger must NOT preserve the stale
        error — that would mislead forensic readers into thinking the
        row failed this run when in fact it was silently skipped."""
        from scripts import spec_drift_verify as sdv

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        ledger = tmp_path / "ledger.jsonl"
        # Row state from a prior failed run: has delete_error AND is on
        # a different base_url than the current credential targets.
        ledger.write_text(
            json.dumps(
                {
                    "endpoint": "/sales_orders",
                    "entity_id": 42,
                    "base_url": "https://other.katana.test",
                    "factory_id": 200,
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                    "delete_error": "HTTP 500: stale error from prior run",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)
        monkeypatch.setattr(
            sdv,
            "make_client",
            lambda allow_unsafe=False: SafeClient(
                base_url="https://api.katana.test",
                transport=httpx.MockTransport(handler),
                allow_unsafe=True,
            ),
        )

        sdv.cleanup()

        # Read back the rewritten ledger — the stale error must be gone.
        rewritten = [json.loads(line) for line in ledger.read_text().splitlines()]
        assert len(rewritten) == 1
        assert "delete_error" not in rewritten[0], (
            f"stale delete_error survived skip: {rewritten[0].get('delete_error')!r}"
        )

    def test_no_delete_template_skip_counted_in_breakdown(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ) -> None:
        """Rows for endpoints without a ``DELETE_TEMPLATES`` entry must
        appear in their own skip bucket so the summary's total equals
        the sum of bucket counts — no silent "other" gap."""
        from scripts import spec_drift_verify as sdv

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(
            json.dumps(
                {
                    "endpoint": "/some_undeletable_endpoint",  # no template
                    "entity_id": 1,
                    "base_url": "https://api.katana.test",
                    "factory_id": 100,
                    "issue": "x",
                    "method": "POST",
                    "created_at": "2026-01-01T00:00:00",
                }
            )
            + "\n"
        )
        monkeypatch.setattr(sdv, "LEDGER_PATH", ledger)
        monkeypatch.setattr(sdv, "BASE_URL", "https://api.katana.test")
        sdv._factory_id_for_key.cache_clear()
        monkeypatch.setattr(sdv, "_resolve_factory_id", lambda: 100)
        monkeypatch.setattr(
            sdv,
            "make_client",
            lambda allow_unsafe=False: SafeClient(
                base_url="https://api.katana.test",
                transport=httpx.MockTransport(handler),
                allow_unsafe=True,
            ),
        )

        sdv.cleanup()
        out = capsys.readouterr().out
        # The breakdown labels the no-template bucket distinctly.
        assert "1 have no DELETE template" in out
        # And the total skipped matches.
        assert "1 skipped" in out


class TestRelativePathGuardIntegration:
    """The mutation guard must engage on relative paths too.

    Regression for the ``_split_path`` IndexError-on-relative bug: if the
    guard fell over on a relative URL, the request would short-circuit
    or worse, silently slip through. Verify both refusal-on-bad-identity
    and ledger-allow paths work with relative inputs.
    """

    def test_post_relative_path_with_sdt_identity_allowed(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": {"id": 99}})

        client = _build_safe_client(handler)
        try:
            response = client.post(
                "sales_orders",
                json={"order_no": "SDT-2026-05-19-RELATIVE"},
            )
            assert response.status_code == 200
        finally:
            client.close()

    def test_post_relative_path_without_sdt_identity_refused(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            pytest.fail("guard should refuse before the wire call")

        client = _build_safe_client(handler)
        try:
            with pytest.raises(UnsafeMutationError):
                client.post("sales_orders", json={"order_no": "#WEB20604"})
        finally:
            client.close()


class TestRequestBodyDecoding:
    def test_verify_hook_sees_dict_request_body(self) -> None:
        captured: dict[str, object] = {}

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 1, "serial_numbers": [1, 2]})

        def hook(req: httpx.Request, _resp: httpx.Response) -> None:
            captured["body"] = json.loads(req.content)

        client = _build_safe_client(
            handler, ledger_keys={("/manufacturing_orders", "77")}
        )
        client.register_verify("POST", "/manufacturing_order_productions", hook)
        try:
            client.post(
                "/manufacturing_order_productions",
                json={"manufacturing_order_id": 77, "serial_numbers": [1, 2]},
            )
            assert captured["body"] == {
                "manufacturing_order_id": 77,
                "serial_numbers": [1, 2],
            }
        finally:
            client.close()
