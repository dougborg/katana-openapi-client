"""Tests for ``scripts/audit_frontend_enums.py`` — the soft-fail drift audit
that re-checks the hand-maintained ecommerce deep-link platform set against
Katana's live frontend enum.

All network I/O is faked with ``httpx.MockTransport`` so the tests are
deterministic; the live chain is exercised separately by running
``poe audit-frontend-enums``.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest

scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
# Scope the sys.path mutation to just this import: insert, import, then remove
# in a finally so the entry doesn't linger for the whole test session (where it
# could shadow other imports or shift resolution order). audit_frontend_enums
# is cached in sys.modules after the first import, so dropping the path is safe.
sys.path.insert(0, str(scripts_dir))
try:
    from audit_frontend_enums import (  # type: ignore[import-not-found]
        AuditResult,
        audit,
        extract_ecommerce_enum,
        main,
        resolve_katana_npm_chunk_url,
    )
finally:
    sys.path.remove(str(scripts_dir))

# A minimal remoteEntry.js: a webpack name map (id -> npm.katana-npm) plus a
# hash map (id -> content hash), the two things the resolver needs.
_REMOTE_ENTRY = (
    'var n=({8494:"npm.katana-npm"}[e]||e)+"."+'
    '{8494:"deadbeefdeadbeef1234"}[e]+".chunk.js";'
)
# A chunk containing the real-shaped EcommerceIntegrationType IIFE.
_CHUNK_OK = (
    'function(e){e.Shopify="shopify",e.WooCommerce="wooCommerce",'
    'e.BigCommerce="bigCommerce"}(a||(t.EcommerceIntegrationType=a={}))'
)
# Same, but the frontend has gained a 4th platform — the drift case.
_CHUNK_DRIFT = (
    'function(e){e.Shopify="shopify",e.WooCommerce="wooCommerce",'
    'e.BigCommerce="bigCommerce",e.Squarespace="squarespace"}'
    "(a||(t.EcommerceIntegrationType=a={}))"
)
# A chunk that resolves/fetches fine but has no enum (parse-failure path).
_CHUNK_NO_ENUM = 'function(e){e.Foo="bar"}(a||(t.SomethingElse=a={}))'


_Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def make_client() -> Iterator[Callable[[_Handler], httpx.Client]]:
    """Yield a factory that builds ``MockTransport``-backed clients and closes
    every one it handed out in teardown — so no test leaks an open
    ``httpx.Client`` (which would emit a ResourceWarning)."""
    clients: list[httpx.Client] = []

    def factory(handler: _Handler) -> httpx.Client:
        client = httpx.Client(transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.close()


def _route(*, sales_remote=_REMOTE_ENTRY, sales_chunk=_CHUNK_OK):
    """Build a handler serving the sales-mf remoteEntry + chunk."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/sales-mf/remoteEntry.js":
            return httpx.Response(200, text=sales_remote)
        if path.startswith("/sales-mf/npm.katana-npm."):
            return httpx.Response(200, text=sales_chunk)
        return httpx.Response(404)

    return handler


def test_resolver_builds_chunk_url() -> None:
    url = resolve_katana_npm_chunk_url(_REMOTE_ENTRY, "https://cdn/sales-mf")
    assert url == "https://cdn/sales-mf/npm.katana-npm.deadbeefdeadbeef1234.chunk.js"


def test_resolver_returns_none_when_no_katana_npm() -> None:
    assert resolve_katana_npm_chunk_url('{1:"npm.vendor.react"}', "https://cdn") is None


def test_extract_enum_finds_camelcase_values() -> None:
    enum = extract_ecommerce_enum(_CHUNK_OK)
    assert enum == {
        "Shopify": "shopify",
        "WooCommerce": "wooCommerce",
        "BigCommerce": "bigCommerce",
    }


def test_extract_enum_ignores_unrelated_iife() -> None:
    # A PascalCase look-alike enum NOT bound to EcommerceIntegrationType (the
    # header-mf decoy) must not be matched.
    decoy = 'function(e){e.Shopify="Shopify"}(({}))'
    assert extract_ecommerce_enum(decoy) is None


def test_audit_no_drift(make_client: Callable[[_Handler], httpx.Client]) -> None:
    result = audit(client=make_client(_route()))
    assert result.reachable is True
    assert result.frontend_values == {"shopify", "wooCommerce", "bigCommerce"}
    assert result.has_drift is False
    assert result.added == set()


def test_audit_detects_added_platform(
    make_client: Callable[[_Handler], httpx.Client],
) -> None:
    result = audit(client=make_client(_route(sales_chunk=_CHUNK_DRIFT)))
    assert result.reachable is True
    assert result.added == {"squarespace"}
    assert result.has_drift is True


def test_audit_falls_back_to_header_mf(
    make_client: Callable[[_Handler], httpx.Client],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.startswith("/sales-mf/"):
            return httpx.Response(503)  # sales-mf down
        if path == "/header-mf/remoteEntry.js":
            return httpx.Response(200, text=_REMOTE_ENTRY)
        if path.startswith("/header-mf/npm.katana-npm."):
            return httpx.Response(200, text=_CHUNK_OK)
        return httpx.Response(404)

    result = audit(client=make_client(handler))
    assert result.reachable is True
    assert "header-mf" in (result.source or "")
    assert result.has_drift is False


def test_audit_both_unreachable_is_soft(
    make_client: Callable[[_Handler], httpx.Client],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no network", request=request)

    result = audit(client=make_client(handler))
    assert result.reachable is False
    assert result.has_drift is False  # never drift when we couldn't read
    assert result.notes  # records why each MF failed


def test_audit_parse_failure_is_soft(
    make_client: Callable[[_Handler], httpx.Client],
) -> None:
    result = audit(client=make_client(_route(sales_chunk=_CHUNK_NO_ENUM)))
    assert result.reachable is False
    assert any("not found" in n for n in result.notes)


def test_main_exit_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    drift = AuditResult(reachable=True, frontend_values={"shopify", "etsy"})
    monkeypatch.setattr("audit_frontend_enums.audit", lambda: drift)
    # Soft by default: drift still exits 0.
    assert main([]) == 0
    # --strict gates on genuine drift.
    assert main(["--strict"]) == 1


def test_main_unreachable_never_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    unreachable = AuditResult(reachable=False)
    monkeypatch.setattr("audit_frontend_enums.audit", lambda: unreachable)
    # Even --strict must exit 0 when we simply couldn't reach the frontend.
    assert main(["--strict"]) == 0
