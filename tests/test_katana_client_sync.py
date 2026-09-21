"""Regression coverage for generated synchronous endpoints on KatanaClient."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products


def test_generated_sync_endpoint_uses_sync_transport_and_closes_it():
    requests: list[httpx.Request] = []

    def handle(transport, request):
        requests.append(request)
        return httpx.Response(
            200, json={"data": [{"id": 42, "name": "Widget", "type": "product"}]}
        )

    with (
        patch.object(httpx.HTTPTransport, "handle_request", handle),
        KatanaClient(
            api_key="test-key", base_url="https://example.test/v1", timeout=7
        ) as client,
    ):
        sync_client = client.get_httpx_client()
        response = get_all_products.sync_detailed(client=client, limit=1)
        assert response.parsed is not None
        assert response.parsed.to_dict()["data"][0]["id"] == 42
        assert client.get_httpx_client() is sync_client

    assert sync_client.is_closed
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == "Bearer test-key"
    assert str(requests[0].url) == "https://example.test/v1/products?limit=1"
    assert requests[0].extensions["timeout"]["read"] == 7


@pytest.mark.asyncio
async def test_sync_calls_do_not_invoke_or_mutate_async_hooks_and_transport():
    hook = AsyncMock()
    client = KatanaClient(
        api_key="test-key",
        base_url="https://example.test/v1",
        requests_per_minute=None,
        event_hooks={"response": [hook]},
    )
    async_client = client.get_async_httpx_client()
    with (
        patch.object(
            httpx.HTTPTransport,
            "handle_request",
            return_value=httpx.Response(200, json={"data": []}),
        ),
        patch.object(
            httpx.AsyncHTTPTransport,
            "handle_async_request",
            return_value=httpx.Response(200, json={"data": []}),
        ),
    ):
        with client:
            get_all_products.sync_detailed(client=client)
        hook.assert_not_called()
        assert not async_client.is_closed
        async with client:
            await get_all_products.asyncio_detailed(client=client)
    hook.assert_awaited_once()
    assert async_client.is_closed


def test_explicit_sync_client_is_preserved():
    custom = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200))
    )
    client = KatanaClient(api_key="test-key", base_url="https://example.test/v1")
    client.set_httpx_client(client=custom)
    with client:
        assert client.get_httpx_client() is custom
    assert custom.is_closed


def test_sync_client_preserves_transport_and_request_settings():
    transport_options = {}
    requests = []

    def make_transport(**kwargs):
        transport_options.update(kwargs)
        return httpx.MockTransport(handle)

    def handle(request):
        requests.append(request)
        return httpx.Response(503)

    client = KatanaClient(
        api_key="test-key",
        base_url="https://example.test/v1",
        verify=False,
        trust_env=False,
        http2=True,
        local_address="127.0.0.1",
        headers={"X-Custom": "value"},
        cookies={"session": "test"},
    )
    with (
        patch(
            "katana_public_api_client.katana_client.httpx.HTTPTransport",
            side_effect=make_transport,
        ),
        client,
    ):
        response = client.get_httpx_client().get("/products")

    assert response.status_code == 503
    assert len(requests) == 1  # Sync calls don't inherit async retry policy.
    assert transport_options["verify"] is False
    assert transport_options["trust_env"] is False
    assert transport_options["http2"] is True
    assert transport_options["local_address"] == "127.0.0.1"
    assert requests[0].headers["Authorization"] == "Bearer test-key"
    assert requests[0].headers["X-Custom"] == "value"
    assert requests[0].headers["Cookie"] == "session=test"


def test_sync_call_preserves_explicit_custom_transport():
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handle)
    with (
        patch("katana_public_api_client.katana_client.httpx.HTTPTransport") as network,
        KatanaClient(
            api_key="test-key", base_url="https://example.test/v1", transport=transport
        ) as client,
    ):
        get_all_products.sync_detailed(client=client)
    assert len(requests) == 1
    network.assert_not_called()


@pytest.mark.asyncio
async def test_sync_call_rejects_async_only_override_without_network_fallback():
    transport = httpx.AsyncHTTPTransport()
    async with KatanaClient(
        api_key="test-key", base_url="https://example.test/v1", transport=transport
    ) as client:
        with (
            patch(
                "katana_public_api_client.katana_client.httpx.HTTPTransport"
            ) as network,
            pytest.raises(TypeError, match="custom transport is async-only"),
        ):
            client.get_httpx_client()
        network.assert_not_called()
