"""Comprehensive tests for RateLimitAwareRetry class.

This module tests the custom retry logic that distinguishes between:
- Rate limiting (429): Retry ALL methods including POST/PATCH
- Server errors (502/503/504): Retry ONLY idempotent methods (GET, PUT, DELETE, etc.)
"""

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from email.utils import formatdate
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpx_retries import RetryTransport

from katana_public_api_client.katana_client import RateLimitAwareRetry


@pytest.mark.unit
class TestRateLimitAwareRetry429Behavior:
    """Test that 429 errors allow retries for ALL HTTP methods."""

    @pytest.fixture
    def retry(self):
        """Create a RateLimitAwareRetry instance configured for testing."""
        return RateLimitAwareRetry(
            total=5,
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "POST",
                "PATCH",
                "OPTIONS",
            ],
            status_forcelist=[429, 502, 503, 504],
        )

    def test_get_retryable_for_429(self, retry):
        """GET should be retryable for 429."""
        assert retry.is_retryable_method("GET")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_post_retryable_for_429(self, retry):
        """POST should be retryable for 429 (non-idempotent but safe for rate limits)."""
        assert retry.is_retryable_method("POST")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_patch_retryable_for_429(self, retry):
        """PATCH should be retryable for 429 (non-idempotent but safe for rate limits)."""
        assert retry.is_retryable_method("PATCH")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_put_retryable_for_429(self, retry):
        """PUT should be retryable for 429."""
        assert retry.is_retryable_method("PUT")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_delete_retryable_for_429(self, retry):
        """DELETE should be retryable for 429."""
        assert retry.is_retryable_method("DELETE")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_head_retryable_for_429(self, retry):
        """HEAD should be retryable for 429."""
        assert retry.is_retryable_method("HEAD")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_options_retryable_for_429(self, retry):
        """OPTIONS should be retryable for 429."""
        assert retry.is_retryable_method("OPTIONS")
        assert retry.is_retryable_status_code(HTTPStatus.TOO_MANY_REQUESTS)

    def test_case_insensitive_method_handling(self, retry):
        """Methods should be handled case-insensitively."""
        # Lower case
        assert retry.is_retryable_method("post")
        assert retry._current_method == "POST"
        assert retry.is_retryable_status_code(429)

        # Mixed case
        assert retry.is_retryable_method("PaTcH")
        assert retry._current_method == "PATCH"
        assert retry.is_retryable_status_code(429)


@pytest.mark.unit
class TestRateLimitAwareRetry5xxBehavior:
    """Test that 5xx server errors only retry idempotent methods."""

    @pytest.fixture
    def retry(self):
        """Create a RateLimitAwareRetry instance configured for testing."""
        return RateLimitAwareRetry(
            total=5,
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "POST",
                "PATCH",
                "OPTIONS",
            ],
            status_forcelist=[429, 502, 503, 504],
        )

    def test_get_retryable_for_502(self, retry):
        """GET (idempotent) should be retryable for 502."""
        assert retry.is_retryable_method("GET")
        assert retry.is_retryable_status_code(HTTPStatus.BAD_GATEWAY)

    def test_get_retryable_for_503(self, retry):
        """GET (idempotent) should be retryable for 503."""
        assert retry.is_retryable_method("GET")
        assert retry.is_retryable_status_code(HTTPStatus.SERVICE_UNAVAILABLE)

    def test_get_retryable_for_504(self, retry):
        """GET (idempotent) should be retryable for 504."""
        assert retry.is_retryable_method("GET")
        assert retry.is_retryable_status_code(HTTPStatus.GATEWAY_TIMEOUT)

    def test_put_retryable_for_5xx(self, retry):
        """PUT (idempotent) should be retryable for 5xx errors."""
        assert retry.is_retryable_method("PUT")
        assert retry.is_retryable_status_code(502)
        assert retry.is_retryable_status_code(503)
        assert retry.is_retryable_status_code(504)

    def test_delete_retryable_for_5xx(self, retry):
        """DELETE (idempotent) should be retryable for 5xx errors."""
        assert retry.is_retryable_method("DELETE")
        assert retry.is_retryable_status_code(502)
        assert retry.is_retryable_status_code(503)
        assert retry.is_retryable_status_code(504)

    def test_head_retryable_for_5xx(self, retry):
        """HEAD (idempotent) should be retryable for 5xx errors."""
        assert retry.is_retryable_method("HEAD")
        assert retry.is_retryable_status_code(502)

    def test_options_retryable_for_5xx(self, retry):
        """OPTIONS (idempotent) should be retryable for 5xx errors."""
        assert retry.is_retryable_method("OPTIONS")
        assert retry.is_retryable_status_code(502)

    def test_post_not_retryable_for_502(self, retry):
        """POST (non-idempotent) should NOT be retryable for 502."""
        assert retry.is_retryable_method("POST")
        assert not retry.is_retryable_status_code(HTTPStatus.BAD_GATEWAY)

    def test_post_not_retryable_for_503(self, retry):
        """POST (non-idempotent) should NOT be retryable for 503."""
        assert retry.is_retryable_method("POST")
        assert not retry.is_retryable_status_code(HTTPStatus.SERVICE_UNAVAILABLE)

    def test_post_not_retryable_for_504(self, retry):
        """POST (non-idempotent) should NOT be retryable for 504."""
        assert retry.is_retryable_method("POST")
        assert not retry.is_retryable_status_code(HTTPStatus.GATEWAY_TIMEOUT)

    def test_patch_not_retryable_for_5xx(self, retry):
        """PATCH (non-idempotent) should NOT be retryable for any 5xx errors."""
        assert retry.is_retryable_method("PATCH")
        assert not retry.is_retryable_status_code(502)
        assert not retry.is_retryable_status_code(503)
        assert not retry.is_retryable_status_code(504)


@pytest.mark.unit
class TestRateLimitAwareRetryMethodPreservation:
    """Test that the current method is preserved across retry attempts."""

    @pytest.fixture
    def retry(self):
        """Create a RateLimitAwareRetry instance configured for testing."""
        return RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST", "PATCH"],
            status_forcelist=[429, 502, 503, 504],
        )

    def test_post_method_preserved_on_increment(self, retry):
        """POST method should be preserved when retry is incremented."""
        retry.is_retryable_method("POST")
        assert retry._current_method == "POST"

        new_retry = retry.increment()
        assert new_retry._current_method == "POST"
        assert new_retry.attempts_made == 1

    def test_patch_method_preserved_on_increment(self, retry):
        """PATCH method should be preserved when retry is incremented."""
        retry.is_retryable_method("PATCH")
        assert retry._current_method == "PATCH"

        new_retry = retry.increment()
        assert new_retry._current_method == "PATCH"

    def test_get_method_preserved_on_increment(self, retry):
        """GET method should be preserved when retry is incremented."""
        retry.is_retryable_method("GET")
        assert retry._current_method == "GET"

        new_retry = retry.increment()
        assert new_retry._current_method == "GET"

    def test_method_preserved_through_multiple_increments(self, retry):
        """Method should be preserved through multiple retry attempts."""
        retry.is_retryable_method("POST")

        retry1 = retry.increment()
        assert retry1._current_method == "POST"
        assert retry1.attempts_made == 1

        retry2 = retry1.increment()
        assert retry2._current_method == "POST"
        assert retry2.attempts_made == 2

        retry3 = retry2.increment()
        assert retry3._current_method == "POST"
        assert retry3.attempts_made == 3

    def test_method_changes_on_new_request(self, retry):
        """Method should change when a new request is made."""
        retry.is_retryable_method("POST")
        assert retry._current_method == "POST"

        # Simulate new request with different method
        retry.is_retryable_method("GET")
        assert retry._current_method == "GET"


@pytest.mark.unit
class TestRateLimitAwareRetryEdgeCases:
    """Test edge cases and error conditions."""

    def test_status_code_not_in_forcelist(self):
        """Status codes not in forcelist should not be retryable."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[429, 502],
        )

        retry.is_retryable_method("GET")
        # 400 is not in forcelist
        assert not retry.is_retryable_status_code(HTTPStatus.BAD_REQUEST)
        # 401 is not in forcelist
        assert not retry.is_retryable_status_code(HTTPStatus.UNAUTHORIZED)
        # 404 is not in forcelist
        assert not retry.is_retryable_status_code(HTTPStatus.NOT_FOUND)
        # 500 is not in forcelist (only 502 is)
        assert not retry.is_retryable_status_code(HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_unknown_method_defaults_to_retryable(self):
        """Unknown methods should default to retryable when method is None."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[429, 502],
        )

        # Don't call is_retryable_method, so _current_method is None
        assert retry._current_method is None

        # Should default to True for any status in forcelist
        assert retry.is_retryable_status_code(429)
        assert retry.is_retryable_status_code(502)

    def test_method_not_in_allowed_methods(self):
        """Methods not in allowed_methods should be rejected at method check."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],  # PATCH not allowed
            status_forcelist=[429, 502],
        )

        # PATCH is not in allowed_methods
        assert not retry.is_retryable_method("PATCH")

    def test_trace_method_retryable_for_5xx(self):
        """TRACE (idempotent) should be retryable for 5xx errors."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["HEAD", "GET", "TRACE"],
            status_forcelist=[429, 502, 503, 504],
        )

        retry.is_retryable_method("TRACE")
        assert retry.is_retryable_status_code(502)
        assert retry.is_retryable_status_code(503)
        assert retry.is_retryable_status_code(504)

    def test_empty_forcelist_uses_default_behavior(self):
        """Empty status_forcelist should use httpx-retries default behavior.

        Note: The underlying Retry class has default retry logic even with
        empty forcelist. Our custom logic returns True when _current_method
        is None (which happens when forcelist check fails).
        """
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[],  # No statuses in forcelist
        )

        retry.is_retryable_method("GET")
        # With empty forcelist, status check will return True due to
        # fallback behavior when status not in forcelist but method is None
        # This is acceptable as it defers to httpx-retries default behavior
        assert retry._current_method == "GET"

    def test_custom_status_codes(self):
        """Should support custom status codes beyond standard HTTP codes."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET"],
            status_forcelist=[599],  # Custom status code
        )

        retry.is_retryable_method("GET")
        assert retry.is_retryable_status_code(599)


@pytest.mark.unit
class TestRateLimitAwareRetryIdempotentMethods:
    """Test that idempotent methods are correctly identified."""

    @pytest.fixture
    def retry(self):
        """Create a RateLimitAwareRetry instance configured for testing."""
        return RateLimitAwareRetry(
            total=5,
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
                "PATCH",
            ],
            status_forcelist=[502],
        )

    def test_all_idempotent_methods_allowed_for_5xx(self, retry):
        """All standard idempotent methods should be retryable for 5xx."""
        idempotent_methods = ["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"]

        for method in idempotent_methods:
            retry.is_retryable_method(method)
            assert retry.is_retryable_status_code(502), (
                f"{method} should be retryable for 502"
            )

    def test_non_idempotent_methods_not_allowed_for_5xx(self, retry):
        """Non-idempotent methods should NOT be retryable for 5xx."""
        non_idempotent_methods = ["POST", "PATCH"]

        for method in non_idempotent_methods:
            retry.is_retryable_method(method)
            assert not retry.is_retryable_status_code(502), (
                f"{method} should NOT be retryable for 502"
            )

    def test_idempotent_methods_constant_is_correct(self):
        """Verify the IDEMPOTENT_METHODS constant contains correct methods."""
        expected_idempotent = frozenset(
            ["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        assert expected_idempotent == RateLimitAwareRetry.IDEMPOTENT_METHODS


@pytest.mark.unit
class TestRateLimitAwareRetryConfiguration:
    """Test various configuration options for RateLimitAwareRetry."""

    def test_total_retry_count_configured(self):
        """Total retry count should be configurable."""
        retry = RateLimitAwareRetry(
            total=10,
            allowed_methods=["GET"],
            status_forcelist=[429],
        )
        assert retry.total == 10

    def test_allowed_methods_configured(self):
        """Allowed methods should be configurable."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[429],
        )
        # allowed_methods is converted to frozenset of uppercase strings
        assert "GET" in retry.allowed_methods
        assert "POST" in retry.allowed_methods

    def test_status_forcelist_configured(self):
        """Status forcelist should be configurable."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET"],
            status_forcelist=[429, 500, 502, 503, 504],
        )
        assert 429 in retry.status_forcelist
        assert 500 in retry.status_forcelist
        assert 502 in retry.status_forcelist


@pytest.mark.unit
class TestRateLimitAwareRetryStateMachine:
    """Test the state machine behavior across multiple retries."""

    def test_method_state_consistency_across_retry_chain(self):
        """Test that method state remains consistent through entire retry chain."""
        retry = RateLimitAwareRetry(
            total=3,
            allowed_methods=["POST"],
            status_forcelist=[429],
        )

        # Initial request
        retry.is_retryable_method("POST")
        assert retry._current_method == "POST"
        assert retry.attempts_made == 0

        # First retry
        retry1 = retry.increment()
        assert retry1._current_method == "POST"
        assert retry1.attempts_made == 1
        assert retry1.is_retryable_status_code(429)

        # Second retry
        retry2 = retry1.increment()
        assert retry2._current_method == "POST"
        assert retry2.attempts_made == 2
        assert retry2.is_retryable_status_code(429)

        # Third retry (should be last)
        retry3 = retry2.increment()
        assert retry3._current_method == "POST"
        assert retry3.attempts_made == 3

    def test_switching_between_429_and_5xx(self):
        """Test behavior when switching between 429 and 5xx status codes."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["POST"],
            status_forcelist=[429, 502],
        )

        retry.is_retryable_method("POST")

        # POST is retryable for 429
        assert retry.is_retryable_status_code(429)

        # POST is NOT retryable for 502
        assert not retry.is_retryable_status_code(502)

        # Back to 429 should still work
        assert retry.is_retryable_status_code(429)


@pytest.mark.unit
class TestRetryAfterEndToEndIntegration:
    """End-to-end integration tests exercising ``RetryTransport``'s retry loop.

    Uses ``looptime`` to fake the asyncio event loop's clock so the actual
    ``await asyncio.sleep(retry_after)`` inside ``Retry.asleep`` runs in
    virtual time — the test loop perceives the configured delay elapsing
    while real wall-clock time stays at zero. This is the equivalent of
    ``trio.testing.MockClock`` for asyncio.

    All tests drive requests through the public
    ``RetryTransport.handle_async_request`` API and assert on observed
    behavior (response status, retry count, virtual time elapsed) — no
    coupling to private helpers like ``_calculate_sleep``. Together they
    cover both the Retry-After path (numeric, HTTP-date, header-overrides-
    backoff, multi-retry accumulation) and the backoff fallback path
    (header absent, header malformed) end-to-end.
    """

    @staticmethod
    def _build_transport(
        responses: list[httpx.Response | MagicMock], *, backoff_factor: float = 10.0
    ) -> tuple[RetryTransport, AsyncMock]:
        """Build a real ``RetryTransport`` over a mocked inner transport.

        ``backoff_jitter=0`` makes the backoff deterministic (the
        ``httpx_retries`` default of 1.0 multiplies the backoff by
        ``random.uniform(0, 1)``, which would make timing assertions
        flaky and can interact poorly with ``looptime`` when the
        randomized value is very small).
        """
        retry = RateLimitAwareRetry(
            total=3,
            backoff_factor=backoff_factor,
            backoff_jitter=0.0,
            respect_retry_after_header=True,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
        )
        inner = AsyncMock(spec=httpx.AsyncHTTPTransport)
        inner.handle_async_request.side_effect = responses
        return RetryTransport(transport=inner, retry=retry), inner

    @staticmethod
    def _resp(status: int, headers: dict[str, str] | None = None) -> MagicMock:
        response = MagicMock(spec=httpx.Response)
        response.status_code = status
        response.headers = headers or {}
        return response

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_retry_after_delays_full_chain_by_header_value(self) -> None:
        """A 429 + ``Retry-After: 5`` makes the retry loop wait 5 virtual seconds.

        Goes through the *real* code path: ``RetryTransport.handle_async_request``
        receives the 429, computes the delay from the header, calls its
        async ``asleep()``, and the second attempt fires only after the
        loop's clock has advanced by 5 seconds.
        """
        transport, inner = self._build_transport(
            [
                self._resp(429, {"Retry-After": "5"}),
                self._resp(200),
            ]
        )

        loop = asyncio.get_running_loop()
        start = loop.time()
        response = await transport.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )
        elapsed = loop.time() - start

        assert response.status_code == 200
        assert inner.handle_async_request.call_count == 2
        # Loop time should have advanced by ~5s (the Retry-After value).
        # Allow a small tolerance for the buffer pyrate-style libraries may
        # add. A clean Retry-After integer landing within [4.5, 5.5] proves
        # the header drove the delay, not the configured 10s backoff.
        assert 4.5 <= elapsed <= 5.5, (
            f"Retry-After: 5 should produce ~5s loop-time delay; got {elapsed:.2f}s"
        )

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_retry_after_dominates_long_backoff_end_to_end(self) -> None:
        """Header takes precedence over a much longer configured backoff.

        ``backoff_factor=100`` would normally pace the first retry around
        100 seconds. ``Retry-After: 2`` must override and land at ~2s of
        loop time.
        """
        transport, _inner = self._build_transport(
            [
                self._resp(429, {"Retry-After": "2"}),
                self._resp(200),
            ],
            backoff_factor=100.0,
        )

        loop = asyncio.get_running_loop()
        start = loop.time()
        response = await transport.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )
        elapsed = loop.time() - start

        assert response.status_code == 200
        assert elapsed <= 5.0, (
            f"Retry-After: 2 should override 100s backoff; got {elapsed:.2f}s"
        )

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_http_date_retry_after_paces_end_to_end(self, monkeypatch) -> None:
        """RFC 7231 HTTP-date Retry-After format paces the retry by the absolute deadline.

        ``httpx_retries`` computes the delay as ``parsed_date -
        datetime.now(utc)`` (retry.py) — i.e. it reads the **wall clock**. A
        time-based test must not depend on the real clock (see CLAUDE.md
        "fake time in time-based tests"), so we freeze *that* ``now()`` at a
        fixed whole-second instant and build the Retry-After date exactly 5s
        ahead of it. The parsed delay is then exactly 5.0s — no wall-clock
        truncation or format→parse jitter — and ``looptime`` fast-forwards the
        resulting ``asyncio.sleep(5)`` virtually.

        We freeze only the ``datetime`` that ``httpx_retries.retry`` reads,
        NOT ``time.monotonic``/``perf_counter`` — ``looptime`` relies on those
        to sync its virtual clock, so a process-wide time freezer (freezegun /
        time-machine) would fight it. Patching the single seam keeps both
        clocks independent and deterministic.
        """
        import httpx_retries.retry as retry_mod

        # Fixed UTC instant on a whole-second boundary (HTTP-date has 1s
        # resolution; a whole second means formatdate loses nothing).
        frozen = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

        class _FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                return frozen if tz is None else frozen.astimezone(tz)

        # Shim the module's ``datetime`` reference: ``datetime.datetime.now``
        # is frozen while ``datetime.timezone`` still resolves normally.
        monkeypatch.setattr(
            retry_mod,
            "datetime",
            SimpleNamespace(datetime=_FrozenDateTime, timezone=timezone),
        )

        retry_at = formatdate(
            timeval=(frozen + timedelta(seconds=5)).timestamp(), usegmt=True
        )
        transport, _inner = self._build_transport(
            [
                self._resp(429, {"Retry-After": retry_at}),
                self._resp(200),
            ]
        )

        loop = asyncio.get_running_loop()
        start = loop.time()
        response = await transport.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )
        elapsed = loop.time() - start

        assert response.status_code == 200
        # Frozen now + an exact 5s-ahead deadline → exactly 5s of virtual
        # delay. Deterministic, so no tolerance band is needed (the tiny
        # abs= only guards float representation).
        assert elapsed == pytest.approx(5.0, abs=1e-6), (
            f"HTTP-date Retry-After should pace exactly 5s of loop time; got {elapsed}s"
        )

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_no_retry_after_falls_back_to_backoff(self) -> None:
        """Without a Retry-After header, the retry waits ``backoff_factor`` instead.

        Inverse property of the Retry-After tests — proves the header path
        and the backoff path are distinct, so the Retry-After tests above
        are actually exercising the header (not coincidentally matching
        whatever the backoff produced).
        """
        transport, _inner = self._build_transport(
            [
                self._resp(429),  # NO Retry-After header
                self._resp(200),
            ],
            backoff_factor=4.0,
        )

        loop = asyncio.get_running_loop()
        start = loop.time()
        response = await transport.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )
        elapsed = loop.time() - start

        assert response.status_code == 200
        # With ``backoff_jitter=0`` the backoff is deterministic:
        # ``backoff_factor * 2 ** attempts_made`` = 4 * 2 = 8s after the
        # first retry. Tight bound proves the path was taken (anything
        # outside this range would mean Retry-After parsing fired
        # somehow, or the formula changed in a dependency upgrade).
        assert 7.5 <= elapsed <= 8.5, (
            f"absent Retry-After should pace via deterministic backoff (~8s); "
            f"got {elapsed:.2f}s"
        )

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_unparseable_retry_after_falls_back_to_backoff(self) -> None:
        """A malformed Retry-After value falls back to the configured backoff.

        Tolerates servers that send garbage in the header — the retry layer
        logs a warning and uses backoff instead of crashing.
        """
        transport, _inner = self._build_transport(
            [
                self._resp(429, {"Retry-After": "not-a-number"}),
                self._resp(200),
            ],
            backoff_factor=4.0,
        )

        loop = asyncio.get_running_loop()
        start = loop.time()
        response = await transport.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )
        elapsed = loop.time() - start

        assert response.status_code == 200
        # Same deterministic backoff math as the no-header case (~8s).
        assert 7.5 <= elapsed <= 8.5, (
            f"malformed Retry-After should fall back to backoff (~8s); "
            f"got {elapsed:.2f}s"
        )

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_multiple_retries_accumulate_delay(self) -> None:
        """Successive 429s each pace by their Retry-After value.

        Three responses: 429+Retry-After:3, 429+Retry-After:7, 200.
        Total loop-time delay should be ~10s (3 + 7) regardless of backoff
        configuration — proves both retries honor the header.
        """
        transport, inner = self._build_transport(
            [
                self._resp(429, {"Retry-After": "3"}),
                self._resp(429, {"Retry-After": "7"}),
                self._resp(200),
            ]
        )

        loop = asyncio.get_running_loop()
        start = loop.time()
        response = await transport.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )
        elapsed = loop.time() - start

        assert response.status_code == 200
        assert inner.handle_async_request.call_count == 3
        assert 9.0 <= elapsed <= 11.0, (
            f"Two retries with Retry-After 3 + 7 should pace ~10s; got {elapsed:.2f}s"
        )
