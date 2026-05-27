"""Tests for :mod:`katana_public_api_client.testing`.

The helper is the only sanctioned way for test code, probes, and CI smoke
tests to talk to a non-production Katana tenant. The contract these tests
pin down is the no-prod-fallback safety guarantee: when
``KATANA_TEST_API_KEY`` is unset, ``make_test_client()`` MUST raise rather
than silently picking up ``KATANA_API_KEY``.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing import make_test_client


@pytest.mark.unit
class TestMakeTestClient:
    """Unit tests for ``make_test_client()`` — no live API calls."""

    def test_returns_configured_katana_client_with_test_env_set(self):
        """Happy path: helper reads KATANA_TEST_API_KEY and returns a client."""
        with patch.dict(
            os.environ,
            {
                "KATANA_TEST_API_KEY": "test-tenant-key",
                "KATANA_TEST_BASE_URL": "https://api.example-test.com/v1",
            },
            clear=True,
        ):
            client = make_test_client()

        assert isinstance(client, KatanaClient)
        assert client._base_url == "https://api.example-test.com/v1"
        assert client.token == "test-tenant-key"

    def test_defaults_base_url_to_production_when_test_base_unset(self):
        """KATANA_TEST_BASE_URL is optional; defaults to the prod URL.

        Same Katana deployment, different tenant — the API key scopes
        the credential to a sandbox tenant within the prod cluster.
        """
        with (
            patch(
                "katana_public_api_client.testing.dotenv_values",
                lambda *_a, **_kw: {},
            ),
            patch.dict(
                os.environ,
                {"KATANA_TEST_API_KEY": "test-tenant-key"},
                clear=True,
            ),
        ):
            client = make_test_client()

        assert client._base_url == "https://api.katanamrp.com/v1"

    def test_raises_runtime_error_when_test_key_missing(self):
        """Safety guarantee: no silent fallback to KATANA_API_KEY."""
        # Even with a prod key present in the environment, the helper
        # must refuse — this is the entire point of the no-fallback rule.
        with (
            patch(
                "katana_public_api_client.testing.dotenv_values",
                lambda *_a, **_kw: {},
            ),
            patch.dict(os.environ, {"KATANA_API_KEY": "prod-key"}, clear=True),
            pytest.raises(RuntimeError) as exc_info,
        ):
            make_test_client()

        msg = str(exc_info.value)
        assert "KATANA_TEST_API_KEY" in msg
        assert "KATANA_API_KEY" in msg, (
            "Error message should explicitly mention why we don't fall back"
        )
        assert "production" in msg.lower() or "prod" in msg.lower()

    def test_raises_runtime_error_when_test_key_empty_string(self):
        """Empty-string env var counts as unset — same as missing entirely."""
        with (
            patch(
                "katana_public_api_client.testing.dotenv_values",
                lambda *_a, **_kw: {},
            ),
            patch.dict(os.environ, {"KATANA_TEST_API_KEY": ""}, clear=True),
            pytest.raises(RuntimeError, match="KATANA_TEST_API_KEY"),
        ):
            make_test_client()

    def test_kwargs_pass_through_to_katana_client(self):
        """Extra kwargs forward to KatanaClient so callers can tune timeouts etc."""
        with patch.dict(
            os.environ,
            {"KATANA_TEST_API_KEY": "test-key"},
            clear=True,
        ):
            client = make_test_client(timeout=5.0, max_retries=1, max_pages=3)

        assert client.max_pages == 3
