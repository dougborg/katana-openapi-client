"""Fluent configuration preserves KatanaClient's single transport owner."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products


@pytest.mark.asyncio
@pytest.mark.parametrize("initialized", [False, True])
async def test_fluent_configuration_reaches_sync_and_async_requests(initialized):
    requests: list[httpx.Request] = []
    hook = AsyncMock()

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handle)
    client = KatanaClient(
        api_key="test-key",
        base_url="https://example.test/v1",
        transport=transport,
        headers={"X-Original": "kept", "X-Change": "old"},
        cookies={"original": "kept", "change": "old"},
        event_hooks={"response": [hook]},
        max_pages=7,
    )
    products, api = client.products, client.api
    sync_http = client.get_httpx_client() if initialized else None
    async_http = client.get_async_httpx_client() if initialized else None
    configured = (
        client.with_headers(headers={"x-change": "new"})
        .with_cookies(cookies={"change": "new"})
        .with_timeout(timeout=httpx.Timeout(9, connect=2))
    )
    assert configured is client
    assert configured.products is products
    assert configured.api is api
    assert configured.max_pages == 7
    if initialized:
        assert configured.get_httpx_client() is sync_http
        assert configured.get_async_httpx_client() is async_http
    with configured:
        get_all_products.sync_detailed(client=configured)
    async with configured:
        await get_all_products.asyncio_detailed(client=configured)
    hook.assert_awaited_once()
    assert len(requests) == 2
    for request in requests:
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["X-Original"] == "kept"
        assert request.headers.get_list("X-Change") == ["new"]
        assert "original=kept" in request.headers["Cookie"]
        assert "change=new" in request.headers["Cookie"]
        assert request.extensions["timeout"] == {
            "connect": 2,
            "read": 9,
            "write": 9,
            "pool": 9,
        }


@pytest.mark.asyncio
async def test_fluent_configuration_preserves_explicit_clients_and_closes_once():
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    sync_http = httpx.Client(transport=transport)
    async_http = httpx.AsyncClient(transport=transport)
    client = KatanaClient(api_key="test-key", transport=transport)
    client.set_httpx_client(client=sync_http)
    client.set_async_httpx_client(async_client=async_http)
    with (
        patch.object(transport, "close", wraps=transport.close) as close,
        patch.object(transport, "aclose", wraps=transport.aclose) as aclose,
        patch(
            "katana_public_api_client.katana_client.ResilientAsyncTransport"
        ) as factory,
    ):
        async with client:
            with client:
                configured = client.with_headers(headers={"X-Test": "ok"})
                configured.with_cookies(cookies={"test": "ok"})
                configured.with_timeout(timeout=httpx.Timeout(4))
                assert configured.get_httpx_client() is sync_http
                assert configured.get_async_httpx_client() is async_http
                close.assert_not_called()
                aclose.assert_not_called()
            close.assert_called_once()
            aclose.assert_not_called()
        aclose.assert_awaited_once()
        factory.assert_not_called()
    assert sync_http.is_closed
    assert async_http.is_closed


@pytest.mark.asyncio
async def test_uninitialized_helpers_preserve_resilience_without_allocating_clients():
    client = KatanaClient(
        api_key="test-key", max_retries=2, max_pages=7, requests_per_minute=None
    )
    transport = client._httpx_args["transport"]
    client.with_headers(headers={"X-Test": "ok"})
    client.with_cookies(cookies={"test": "ok"})
    client.with_timeout(timeout=httpx.Timeout(4))
    assert client._client is None
    assert client._async_client is None
    assert client._httpx_args["transport"] is transport
    assert transport.retry.total == 2
    await transport.aclose()
