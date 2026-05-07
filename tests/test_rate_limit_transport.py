"""Tests for ``RateLimitTransport`` — proactive rate-limiter with header awareness.

Covers the eight behaviors from #590's plan:

1. Token bucket throttles when budget is exceeded.
2. ``X-Ratelimit-Remaining`` lower than local estimate → drain to match.
3. ``X-Ratelimit-Remaining: 0`` → reset gate engages until ``X-Ratelimit-Reset``.
4. Missing rate-limit headers → silent no-op, request proceeds normally.
5. 5xx responses without rate-limit headers → no state change. (Header parsing
   is status-agnostic — Katana could legitimately send the headers on errors —
   but in the absence of headers, nothing happens regardless of status code.)
6. Streaming responses pass through the layer unchanged.
7. ``requests_per_minute=None`` on ``KatanaClient`` omits the layer entirely.
8. Limiter composes cleanly with the rest of the resilient transport stack.

Tests instantiate a fresh ``RateLimitTransport`` per test (and therefore a fresh
``pyrate_limiter.Limiter``) — pyrate has process-global state with some
backends, and bleed across tests would mask real failures.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.katana_client import (
    PaginationTransport,
    RateLimitTransport,
)


def _build_response(
    *,
    status: int = 200,
    remaining: int | None = None,
    reset_offset_seconds: float | None = None,
    extra_headers: dict[str, str] | None = None,
) -> MagicMock:
    """Construct a MagicMock httpx.Response with optional rate-limit headers."""
    headers: dict[str, str] = {}
    if remaining is not None:
        headers["X-Ratelimit-Remaining"] = str(remaining)
    if reset_offset_seconds is not None:
        # Spec defines X-Ratelimit-Reset as epoch ms.
        reset_ms = int((time.time() + reset_offset_seconds) * 1000)
        headers["X-Ratelimit-Reset"] = str(reset_ms)
    if extra_headers:
        headers.update(extra_headers)

    response = MagicMock(spec=httpx.Response)
    response.status_code = status
    response.headers = headers
    return response


@pytest.fixture
def mock_wrapped_transport() -> AsyncMock:
    """Fresh AsyncMock wrapped transport per test."""
    return AsyncMock(spec=httpx.AsyncHTTPTransport)


def _make_request() -> httpx.Request:
    return httpx.Request("GET", "https://api.example.test/manufacturing_orders")


@pytest.mark.unit
class TestRateLimitTransportInit:
    """Validation at construction time."""

    @pytest.mark.parametrize("rpm", [0, -1, -60])
    def test_rejects_non_positive_rpm(self, rpm: int) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            RateLimitTransport(requests_per_minute=rpm)

    def test_creates_default_wrapped_when_none(self) -> None:
        transport = RateLimitTransport(requests_per_minute=60)
        assert transport._wrapped_transport is not None


@pytest.mark.unit
class TestRateLimitTransportThrottling:
    """Pacing behavior when callers exceed the budget."""

    @pytest.mark.asyncio
    async def test_acquires_token_before_forwarding(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """Single request inside burst budget passes straight through."""
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response()

        await transport.handle_async_request(_make_request())

        assert mock_wrapped_transport.handle_async_request.call_count == 1

    @pytest.mark.asyncio
    async def test_each_request_acquires_a_token(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """The transport must await ``try_acquire_async`` once per request.

        Spies on the pyrate Limiter's acquire method rather than measuring
        wall-time pacing — pacing is pyrate's contract (covered by its own
        tests), our contract is "acquire before forwarding". A wall-time
        test would be slow, scheduling-jittery, and would re-test pyrate.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response()

        # Replace the real limiter's acquire path with a spy that returns
        # immediately. ``cast(Any, ...)`` lets us monkey-patch a method on
        # pyrate's ``Limiter`` (which doesn't expose a public swap hook)
        # without tripping the static type checker on a method-assign.
        spy = AsyncMock(return_value=True)
        cast(Any, transport._limiter).try_acquire_async = spy

        for _ in range(3):
            await transport.handle_async_request(_make_request())

        assert spy.await_count == 3, (
            f"expected 3 token acquisitions for 3 requests, got {spy.await_count}"
        )
        # Verify each acquire used the consistent bucket name.
        for call in spy.call_args_list:
            assert call.kwargs.get("name") == "katana"

    @pytest.mark.asyncio
    async def test_acquires_before_forwarding(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """Acquire must happen before the wrapped transport sees the request."""
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response()

        order: list[str] = []

        async def acquire_spy(*_args: object, **_kwargs: object) -> bool:
            order.append("acquire")
            return True

        async def forward_spy(*_args: object, **_kwargs: object) -> MagicMock:
            order.append("forward")
            return _build_response()

        cast(Any, transport._limiter).try_acquire_async = acquire_spy
        mock_wrapped_transport.handle_async_request.side_effect = forward_spy

        await transport.handle_async_request(_make_request())

        assert order == ["acquire", "forward"], (
            f"acquire must precede forward, got {order}"
        )


@pytest.mark.unit
class TestRateLimitTransportSyncDown:
    """``X-Ratelimit-Remaining`` smaller than local estimate drains the bucket."""

    @pytest.mark.asyncio
    async def test_syncs_down_when_remote_lower_than_estimate(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """When server reports remaining < local estimate, drain to match."""
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        # Server says we have 5 left — much lower than our default-of-60 estimate.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=5, reset_offset_seconds=30
        )

        await transport.handle_async_request(_make_request())

        assert transport._estimated_remaining == 5

    @pytest.mark.asyncio
    async def test_does_not_sync_up_on_out_of_order_response(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """A late-arriving response with higher remaining must not overwrite a fresher (lower) estimate.

        Simulates: response B (remaining=3) lands first, then response A
        (remaining=4) arrives. The estimate should not climb back up.

        Each request also decrements the estimate by 1 optimistically (so the
        local estimate stays in lock-step with what the server is about to
        see), so after the second request the estimate is one less than
        whatever the latest sync-down produced — but it must still be ≤ 3.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )

        # First response: remaining=3 → sync-down to 3, then optimistic
        # decrement on the *next* request would make it 2.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=3, reset_offset_seconds=30
        )
        await transport.handle_async_request(_make_request())
        assert transport._estimated_remaining == 3

        # Out-of-order: remaining=4 — must NOT sync up. Optimistic decrement
        # before this request brought estimate to 2; remaining=4 > 2 so no
        # sync, estimate stays at 2.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=4, reset_offset_seconds=30
        )
        await transport.handle_async_request(_make_request())
        assert transport._estimated_remaining <= 3, (
            "estimate should never sync upward on a higher-remaining response"
        )


@pytest.mark.unit
class TestRateLimitTransportResetGate:
    """``X-Ratelimit-Remaining: 0`` engages the gate; release after reset."""

    @pytest.mark.asyncio
    async def test_engages_gate_on_remaining_zero(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """A response with remaining=0 closes the reset gate."""
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        # Reset window 30s out, no remaining budget.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=0, reset_offset_seconds=30
        )

        await transport.handle_async_request(_make_request())

        assert not transport._reset_gate.is_set(), (
            "reset gate should be cleared after remaining=0 response"
        )

    @pytest.mark.asyncio
    @pytest.mark.looptime
    async def test_blocks_subsequent_request_until_gate_releases(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """Integration: a closed gate blocks subsequent requests until ``loop.call_later`` fires.

        Uses ``looptime`` to fake the asyncio clock so the real
        ``loop.call_later`` chain (engage gate → schedule release → fire
        callback → spawn ``_release_reset_gate`` task → reopen gate) runs
        end-to-end through the production code path, without real wall
        time elapsing. The loop perceives ``reset_offset_seconds`` of
        virtual time passing; the test completes in milliseconds.

        Verifies:
        - the gate is closed after a remaining=0 response
        - a subsequent request parks on the gate (not done)
        - the gate reopens automatically once the virtual deadline elapses
        - the parked request then completes
        """
        # Important — looptime fast-forwards ``loop.time()`` but
        # ``time.time()`` (used by ``_engage_reset_gate`` for epoch-ms math)
        # is real wall-clock. Use a small offset so the wait_ms math lands
        # on a small positive value relative to the virtual loop clock.
        # The actual ``loop.call_later(wait_s, ...)`` schedules against
        # the loop's clock, so ``looptime`` advances over wait_s of
        # virtual time when the test ``awaits`` the gate.
        gate_seconds = 5.0

        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=0, reset_offset_seconds=gate_seconds
        )

        loop = asyncio.get_running_loop()
        await transport.handle_async_request(_make_request())
        assert not transport._reset_gate.is_set()

        # Second request: should block on the gate until the real
        # ``loop.call_later`` fires after ``gate_seconds`` of virtual time.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=10, reset_offset_seconds=600
        )

        start = loop.time()
        await transport.handle_async_request(_make_request())
        elapsed = loop.time() - start

        # Loop time should have advanced by ~gate_seconds; real wall time
        # is ~zero (looptime). Without looptime this would take 5 real
        # seconds — slow and timing-jittery. With looptime the same code
        # path runs through the actual production scheduler.
        assert elapsed >= gate_seconds * 0.5, (
            f"gate should have blocked ≥{gate_seconds * 0.5}s of loop time; "
            f"got {elapsed:.2f}s"
        )
        assert transport._reset_gate.is_set(), (
            "gate should have reopened via the real call_later → release chain"
        )

    @pytest.mark.asyncio
    async def test_past_reset_does_not_engage_gate(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """A response whose ``X-Ratelimit-Reset`` is already in the past must not engage.

        Out-of-order/stale responses from a previous window can carry an
        already-expired reset timestamp. Three things must hold:

        1. The gate stays open (no stalling future requests for no reason).
        2. ``_reset_until_epoch_ms`` stays None (no phantom active deadline).
        3. ``_estimated_remaining`` is **not** pinned to 0 — under the
           never-sync-up rule, that would silently disable sync-down for
           the rest of the client lifetime, masking a real regression.
           Only the optimistic per-request decrement should apply.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=0,
            reset_offset_seconds=-5,  # 5 seconds in the past
        )

        await transport.handle_async_request(_make_request())

        assert transport._reset_gate.is_set(), (
            "past-due reset should not engage the gate"
        )
        assert transport._reset_until_epoch_ms is None
        # Estimate should reflect only the optimistic per-request decrement
        # (60 → 59), NOT be pinned to 0 by the no-op'd gate engagement.
        assert transport._estimated_remaining == 59, (
            "past-due reset must not pin _estimated_remaining to 0"
        )

    @pytest.mark.asyncio
    async def test_past_reset_with_nonzero_remaining_is_ignored(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """A stale response with ``remaining=N`` AND past-due reset must not drain.

        The original past-reset guard only protected the gate-engage path.
        A stale response from a previous window with, say, ``remaining=5``
        and a reset 5 seconds in the past would still trigger sync-down,
        clamping pyrate to 5 tokens — but those 5 tokens described a window
        that has *already rolled*. Under the never-sync-up rule, that
        artificial clamp persists.

        Fix: ``_observe_response`` now treats any past-due reset as a
        full no-op for header observation, regardless of ``remaining``.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        # Stale response: remaining=5 with past reset.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=5, reset_offset_seconds=-5
        )

        await transport.handle_async_request(_make_request())

        # Estimate must reflect ONLY the optimistic per-request decrement
        # (60 → 59), not be drained to the stale remaining=5.
        assert transport._estimated_remaining == 59, (
            f"past-due reset with remaining=5 should be ignored; "
            f"got {transport._estimated_remaining}"
        )

    @pytest.mark.asyncio
    async def test_sync_down_still_works_after_past_due_reset(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """Regression guard: a stale remaining=0 response must not disable future sync-down.

        Under the never-sync-up rule, if a past-due ``remaining=0`` had
        permanently pinned ``_estimated_remaining=0``, no later response
        could ever trigger the sync-down path (the condition
        ``remaining < estimate`` with estimate=0 is never true). This
        proves the invariant holds: a fresh (future-dated)
        ``remaining=N`` response after a stale one *does* drain.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )

        # Stale remaining=0 with past reset.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=0, reset_offset_seconds=-5
        )
        await transport.handle_async_request(_make_request())

        # Fresh response with real remaining=10 should still trigger sync-down.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=10, reset_offset_seconds=60
        )
        await transport.handle_async_request(_make_request())

        assert transport._estimated_remaining == 10, (
            "fresh remaining=10 should sync down even after a prior stale "
            "remaining=0 with past-due reset"
        )

    @pytest.mark.asyncio
    async def test_request_queued_at_acquire_waits_if_gate_closes(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """A request that's mid-acquire when the gate closes must re-wait, not slip through.

        Race scenario:
        1. Request A enters ``handle_async_request``, finds the gate open,
           and starts ``try_acquire_async`` (queued on pyrate's bucket).
        2. While A is queued, request X (already in flight) gets a 429
           response with ``X-Ratelimit-Remaining: 0`` — engages the gate.
        3. Without the post-acquire re-check, A would proceed past the
           closed gate into the exhausted window.

        This test simulates the race by manually closing the gate
        between acquire and forward, verifying the request blocks until
        we explicitly reopen it.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response()

        # Replace pyrate's acquire with a spy that lets us close the gate
        # while the request is "queued" (i.e., between the first
        # gate-wait and the forward).
        async def acquire_then_close_gate(*_args: object, **_kwargs: object) -> bool:
            transport._reset_gate.clear()
            transport._reset_until_epoch_ms = 999_999_999_999
            return True

        cast(Any, transport._limiter).try_acquire_async = acquire_then_close_gate

        # Spawn the request — it should park on the second gate-wait.
        request_task = asyncio.create_task(
            transport.handle_async_request(_make_request())
        )
        await asyncio.sleep(0)  # let it reach the wait
        await asyncio.sleep(0)
        assert not request_task.done(), (
            "request should be parked on the post-acquire gate re-check, "
            "not have forwarded into an engaged-window"
        )
        assert mock_wrapped_transport.handle_async_request.call_count == 0, (
            "wrapped transport must NOT have been called while the gate was closed"
        )

        # Reopen the gate — request should now complete.
        transport._reset_until_epoch_ms = None
        transport._reset_gate.set()
        await request_task
        assert request_task.done()
        assert mock_wrapped_transport.handle_async_request.call_count == 1

    @pytest.mark.asyncio
    async def test_stale_release_callback_does_not_clear_fresh_task(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """A completed older release task must not clear a newer in-flight one.

        Race scenario: timer A fires, spawns task A (stored as
        ``_release_task``). Before task A completes, a later
        ``_engage_reset_gate`` schedules timer B; timer B fires and
        spawns task B, overwriting the reference. When task A finishes
        (its deadline-mismatch no-op), its ``add_done_callback`` would
        — without the identity check — clear the reference to the
        still-running task B, defeating ``aclose()``'s cancel logic.

        The identity check in ``_clear_release_task`` is the fix; this
        test pins it.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )

        # Simulate task A finishing: build a fake task identity, store
        # it, then call the done-callback as if a *different* task A
        # finished. The identity check should leave the stored reference
        # intact.
        loop = asyncio.get_running_loop()

        async def noop() -> None:
            return None

        task_a = loop.create_task(noop())
        task_b = loop.create_task(noop())
        await task_a  # finishes; we want this one to no-op the clear
        await task_b  # finishes; pretend this is the fresher in-flight

        transport._release_task = task_b
        transport._clear_release_task(task_a)  # stale callback firing

        assert transport._release_task is task_b, (
            "stale done-callback must not clear a fresher in-flight task"
        )

        # Sanity: when the *current* task's callback fires, it should clear.
        transport._clear_release_task(task_b)
        assert transport._release_task is None

    @pytest.mark.asyncio
    async def test_aclose_cancels_pending_release_task(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """``aclose()`` must cancel both the timer AND any spawned release task.

        If the ``loop.call_later`` callback fires *just before* shutdown,
        it spawns ``_release_reset_gate`` as a task that may still be
        running (waiting on ``self._lock``) when ``aclose()`` is called.
        Without explicit cancel + await, asyncio emits "Task was destroyed
        but it is pending" warnings, and the task can race with the
        wrapped transport's own shutdown.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )

        # Manually drive the timer callback to spawn a release task,
        # mirroring the path the real ``loop.call_later`` would trigger.
        transport._reset_until_epoch_ms = 999_999_999_999
        transport._reset_gate.clear()
        transport._schedule_release(999_999_999_999)
        release_task = transport._release_task
        assert release_task is not None, "release task should have been spawned"

        # Close before the task naturally completes.
        await transport.aclose()

        assert transport._release_task is None, (
            "aclose should clear the release-task reference"
        )
        assert release_task.done() or release_task.cancelled(), (
            "in-flight release task should be cancelled or completed by aclose"
        )
        mock_wrapped_transport.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_earlier_reset_does_not_shorten_active_gate(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """An out-of-order response with an earlier reset must not shorten the gate.

        First response engages the gate to a far-future deadline (60s). A
        subsequent stale response with an earlier reset (10s) must be
        ignored — otherwise the gate would release early and let requests
        through before the server's actual reset.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )

        # First response: large reset window engages the gate to ~60s out.
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=0, reset_offset_seconds=60
        )
        await transport.handle_async_request(_make_request())

        far_deadline = transport._reset_until_epoch_ms
        assert far_deadline is not None

        # Force-open the limiter gate to allow a second request through;
        # in production a request inside an active gate would block, but
        # here we just want to verify the engagement-time logic doesn't
        # shrink the deadline.
        transport._reset_gate.set()
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            remaining=0,
            reset_offset_seconds=10,  # earlier than the active gate
        )
        await transport.handle_async_request(_make_request())

        assert transport._reset_until_epoch_ms == far_deadline, (
            "an earlier reset must not replace a later active deadline"
        )


@pytest.mark.unit
class TestRateLimitTransportHeaderAbsence:
    """Auth/redirect endpoints often omit (or malform) X-Ratelimit-* — must no-op.

    Either case skips header-driven sync; only the optimistic per-request
    decrement applies. The reset gate stays open.
    """

    @pytest.mark.parametrize(
        ("response_kwargs", "case"),
        [
            ({}, "absent"),
            (
                {
                    "extra_headers": {
                        "X-Ratelimit-Remaining": "not-a-number",
                        "X-Ratelimit-Reset": "garbage",
                    }
                },
                "malformed",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_no_header_driven_sync(
        self,
        mock_wrapped_transport: AsyncMock,
        response_kwargs: dict[str, Any],
        case: str,
    ) -> None:
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            **response_kwargs
        )

        # Should not raise even on malformed headers.
        await transport.handle_async_request(_make_request())

        assert transport._estimated_remaining == 59, f"case={case}"
        assert transport._reset_gate.is_set(), f"case={case}"


@pytest.mark.unit
class TestRateLimitTransport5xx:
    """Server errors must not be misread as rate-limit signals."""

    @pytest.mark.asyncio
    async def test_5xx_without_rate_headers_does_not_engage(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )
        mock_wrapped_transport.handle_async_request.return_value = _build_response(
            status=502
        )

        await transport.handle_async_request(_make_request())

        # No rate-limit headers ⇒ no header-driven sync regardless of status
        # code. The optimistic per-request decrement still fires (it tracks
        # what the server saw, independent of the response shape). Gate stays
        # open since no remaining=0 signal arrived.
        assert transport._estimated_remaining == 59
        assert transport._reset_gate.is_set()


@pytest.mark.unit
class TestRateLimitTransportStreaming:
    """A streaming response object should pass through the limiter unchanged."""

    @pytest.mark.asyncio
    async def test_streaming_response_pass_through(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """The transport shouldn't read or consume the response body."""
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=60,
        )

        streaming_response = _build_response(remaining=50, reset_offset_seconds=30)
        mock_wrapped_transport.handle_async_request.return_value = streaming_response

        result = await transport.handle_async_request(_make_request())

        # Same object returned — limiter only inspects headers, not body.
        assert result is streaming_response


def _chain_has_rate_limit(client: KatanaClient) -> bool:
    """Walk the transport stack on ``client``'s underlying httpx client.

    Returns True iff a ``RateLimitTransport`` is found anywhere in the chain.
    Each transport class stores its inner transport under a different attr —
    ``_wrapped_transport`` for our own layers, ``_async_transport`` for
    httpx-retries' ``RetryTransport``.
    """
    async_client = client.get_async_httpx_client()
    transport: object = async_client._transport
    while transport is not None:
        if isinstance(transport, RateLimitTransport):
            return True
        # Use getattr because pyright won't narrow on hasattr for private
        # attrs; sentinel pattern keeps type-checker happy without casts.
        sentinel = object()
        next_transport = getattr(transport, "_wrapped_transport", sentinel)
        if next_transport is sentinel:
            next_transport = getattr(transport, "_async_transport", sentinel)
        if next_transport is sentinel:
            return False
        transport = next_transport
    return False


@pytest.mark.unit
class TestRateLimitTransportOptOut:
    """``requests_per_minute=None`` on ``KatanaClient`` omits the layer entirely."""

    def test_none_omits_layer(self) -> None:
        """When opted out, the chain has no RateLimitTransport instance."""
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.test",
            requests_per_minute=None,
        )

        assert not _chain_has_rate_limit(client), (
            "RateLimitTransport should not be in the chain when requests_per_minute=None"
        )

    def test_default_includes_layer(self) -> None:
        """Default constructor (rpm=60) puts a RateLimitTransport in the chain."""
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.test",
        )
        assert _chain_has_rate_limit(client), (
            "RateLimitTransport should be in the default chain (rpm=60 default)"
        )


@pytest.mark.unit
class TestRateLimitTransportComposition:
    """RateLimit + Pagination compose cleanly (no retry — that's the integration test in test_rate_limit_retry.py)."""

    @pytest.mark.asyncio
    async def test_pagination_through_rate_limiter(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """Each paginated page acquires its own token from the limiter.

        Builds the actual stack pattern (rate-limit innermost, pagination
        outside), fires a paginated request, and verifies that pagination
        triggered N HTTP calls — each of which went through the limiter.
        """
        rate_limit = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=600,  # 10/sec — plenty for a 2-page test
        )
        pagination = PaginationTransport(
            wrapped_transport=rate_limit,
            max_pages=10,
        )

        page1 = MagicMock(spec=httpx.Response)
        page1.status_code = 200
        page1.headers = {
            "X-Ratelimit-Remaining": "59",
            "X-Ratelimit-Reset": str(int((time.time() + 60) * 1000)),
        }
        page1.json.return_value = {
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"page": 1, "total_pages": 2},
        }

        async def aread1() -> None:
            return None

        page1.aread = aread1

        page2 = MagicMock(spec=httpx.Response)
        page2.status_code = 200
        page2.headers = {
            "X-Ratelimit-Remaining": "58",
            "X-Ratelimit-Reset": str(int((time.time() + 60) * 1000)),
        }
        page2.json.return_value = {
            "data": [{"id": 3}],
            "pagination": {"page": 2, "total_pages": 2},
        }

        async def aread2() -> None:
            return None

        page2.aread = aread2

        mock_wrapped_transport.handle_async_request.side_effect = [page1, page2]

        await pagination.handle_async_request(
            httpx.Request("GET", "https://api.example.test/items")
        )

        # Two HTTP calls (one per page), each acquired a token. The limiter's
        # estimate should reflect the latest header (58 from page 2).
        assert mock_wrapped_transport.handle_async_request.call_count == 2
        assert rate_limit._estimated_remaining == 58


@pytest.mark.unit
class TestRateLimitTransportConcurrency:
    """Concurrent observe_response calls are serialized by the lock."""

    @pytest.mark.asyncio
    async def test_concurrent_responses_use_lock(
        self, mock_wrapped_transport: AsyncMock
    ) -> None:
        """Fire multiple requests concurrently; estimate stays bounded by lowest remaining.

        Each request optimistically decrements the estimate (-1) and each
        response can sync-down to a lower value, but neither path is allowed
        to sync upward. The exact final value depends on async interleaving
        (a request can decrement before *or* after another request's
        sync-down completes), so the assertion is a *bound*: the final
        estimate must be at most the lowest reported ``remaining`` value
        (5 in this fixture). Going above 5 would prove the lock failed
        and one update overwrote a fresher (lower) one.
        """
        transport = RateLimitTransport(
            wrapped_transport=mock_wrapped_transport,
            requests_per_minute=600,
        )

        responses = [
            _build_response(remaining=10, reset_offset_seconds=60),
            _build_response(remaining=5, reset_offset_seconds=60),
            _build_response(remaining=8, reset_offset_seconds=60),
        ]
        mock_wrapped_transport.handle_async_request.side_effect = responses

        await asyncio.gather(
            transport.handle_async_request(_make_request()),
            transport.handle_async_request(_make_request()),
            transport.handle_async_request(_make_request()),
        )

        assert transport._estimated_remaining <= 5, (
            "concurrent updates must respect the lowest reported remaining "
            f"(got {transport._estimated_remaining}, expected ≤5)"
        )
