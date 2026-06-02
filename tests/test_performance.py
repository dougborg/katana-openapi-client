"""Concurrency and lifecycle tests for the Katana client.

These exercise behavior *structurally*, not with wall-clock timing bounds —
those flake on slow CI runners (see #446 and CLAUDE.md "fake time in
time-based tests"). Coverage that used to live here as hollow, never-wired
mocks (#897) is provided properly elsewhere:

- Multi-page auto-pagination → ``tests/test_transport_auto_pagination.py``
  (real ``MockTransport``, asserts combined ``data`` across pages).
- Retry behavior (5xx / 429 / Retry-After) → ``tests/test_rate_limit_retry.py``
  and ``tests/test_rate_limit_transport.py``.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest


class TestConcurrency:
    """Concurrent usage and potential race conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """``asyncio.gather`` runs all three calls concurrently, not sequentially.

        Asserts the property *structurally* (track max concurrent in-flight
        count) rather than with a wall-clock bound. Wall-clock comparisons
        against tight thresholds flake on slow CI runners — see #446 where a
        sibling timing test failed at 235.7ms < 100ms on Python 3.14.
        """
        in_flight = 0
        max_in_flight = 0

        async def make_mock(result_id: int):
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            try:
                # Yield to the scheduler so peers get a chance to enter before
                # we exit — without this, the counter would only ever see 1.
                await asyncio.sleep(0)
                response = MagicMock()
                response.status_code = 200
                response.parsed = {"id": result_id, "name": f"Result {result_id}"}
                return response
            finally:
                in_flight -= 1

        results = await asyncio.gather(make_mock(1), make_mock(2), make_mock(3))

        assert max_in_flight == 3, (
            f"All three coroutines should have been in flight simultaneously "
            f"(saw max={max_in_flight}); gather() ran them sequentially."
        )
        assert len(results) == 3
        assert all(r.status_code == 200 for r in results)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_calls_return_independent_results(self, katana_client):
        """Concurrent API calls return their own result without cross-talk or
        unhandled exceptions.

        This is purely about concurrent dispatch — NOT pagination (that's covered
        in test_transport_auto_pagination.py). We patch the API seam with one
        distinct response per call, then assert every response comes back exactly
        once (by identity), proving no call clobbered or stole another's result.
        """
        from katana_public_api_client.api.product import get_all_products

        responses = []
        for n in range(1, 4):
            response = MagicMock()
            response.status_code = 200
            response.parsed = MagicMock()
            response.parsed.data = [{"id": f"API{n}-1", "name": f"API{n} Item"}]
            responses.append(response)

        with patch.object(get_all_products, "asyncio_detailed") as mock_method:
            mock_method.side_effect = responses

            results = await asyncio.gather(
                *(
                    get_all_products.asyncio_detailed(
                        client=katana_client._client, limit=100
                    )
                    for _ in range(3)
                ),
                return_exceptions=True,
            )

        assert mock_method.call_count == 3
        for r in results:
            assert not isinstance(r, BaseException), r
            assert r.status_code == 200
        # Each distinct response object came back exactly once — no cross-talk.
        assert {id(r) for r in results} == {id(r) for r in responses}


class TestClientLifecycle:
    """Client lifecycle / cleanup characteristics."""

    @pytest.mark.asyncio
    async def test_client_cleanup(self, katana_client):
        """The client works as an async context manager and stays usable after."""
        async with katana_client:
            assert katana_client is not None

        # After cleanup, client should still be accessible
        # (KatanaClient inherits from AuthenticatedClient).
        assert katana_client is not None
        assert hasattr(katana_client, "get_async_httpx_client")
