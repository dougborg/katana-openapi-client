"""Helpers for building a :class:`KatanaClient` against a non-production tenant.

Phase 1 of the live test environment epic (issue #837). The helper exposed
here is the only sanctioned way for test code, probe scripts, and CI smoke
tests to talk to a Katana tenant that *isn't* prod. It deliberately does
**not** fall back to ``KATANA_API_KEY`` — silently picking up the prod key
when the test key is unset is the exact failure mode this helper exists to
prevent.

See ``CLAUDE.md`` ("Test environment") for the rule + reasoning.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from dotenv import dotenv_values

from .katana_client import KatanaClient

__all__ = ["make_test_client"]

_DEFAULT_TEST_BASE_URL = "https://api.katanamrp.com/v1"


def _read_test_env(name: str, env_values: Mapping[str, str | None]) -> str | None:
    """Look up ``name`` from the real environment, then ``env_values``.

    ``env_values`` is the pre-read mapping from :func:`dotenv_values` —
    passed in by the caller so the ``.env`` file is parsed once per
    :func:`make_test_client` call rather than once per lookup. Using
    :func:`dotenv_values` (read-only) rather than :func:`load_dotenv`
    keeps this helper from mutating ``os.environ``;
    ``KatanaClient.__init__`` calls ``load_dotenv()`` itself when it
    constructs the client.
    """
    value = os.environ.get(name)
    if value:
        return value
    return env_values.get(name)


def make_test_client(**kwargs: Any) -> KatanaClient:
    """Build a :class:`KatanaClient` bound to the test tenant.

    Reads ``KATANA_TEST_API_KEY`` (required) and ``KATANA_TEST_BASE_URL``
    (optional, defaults to the production base URL — same Katana
    deployment, different tenant). Extra keyword arguments pass through
    to :class:`KatanaClient` unchanged so callers can tune timeouts, the
    rate limiter, etc.

    Raises:
        RuntimeError: when ``KATANA_TEST_API_KEY`` is unset. There is
            **no** fallback to ``KATANA_API_KEY`` — test code must not
            be able to accidentally hit prod when the env is
            misconfigured.

    Example:
        >>> from katana_public_api_client.testing import make_test_client
        >>> async with make_test_client() as client:
        ...     # All calls go to the test tenant.
        ...     ...
    """
    env_values = dotenv_values()
    api_key = _read_test_env("KATANA_TEST_API_KEY", env_values)
    if not api_key:
        raise RuntimeError(
            "KATANA_TEST_API_KEY is not set. make_test_client() will NOT "
            "fall back to KATANA_API_KEY — that fallback would let test "
            "code accidentally hit the production tenant. Set "
            "KATANA_TEST_API_KEY in your environment (see .env.example) "
            "or skip the test/probe."
        )

    base_url = (
        _read_test_env("KATANA_TEST_BASE_URL", env_values) or _DEFAULT_TEST_BASE_URL
    )

    return KatanaClient(api_key=api_key, base_url=base_url, **kwargs)
