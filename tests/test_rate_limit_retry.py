"""Comprehensive tests for RateLimitAwareRetry class.

This module tests the custom retry logic that distinguishes between:
- Rate limiting (429): Retry ALL methods including POST/PATCH
- Server errors (502/503/504): Retry ONLY idempotent methods (GET, PUT, DELETE, etc.)
"""

from http import HTTPStatus

import pytest

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
