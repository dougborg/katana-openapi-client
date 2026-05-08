"""Pytest fixtures for browser-based render tests.

Spins up ``fastmcp dev apps`` against the local ``render_test_server`` and
provides a Playwright ``page`` for the test, plus a helper to navigate to
named card scenarios. Skips automatically when Playwright isn't installed
or the bundled Chromium isn't available.

Uses the raw ``playwright`` sync API rather than pytest-playwright to
avoid pytest-base-url's ``base_url`` fixture colliding with our
integration tests' same-name fixture.

Setup (one-time per dev):
    uv run playwright install chromium
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote

import httpx
import pytest

pytest.importorskip("playwright", reason="playwright package not installed")
pytest.importorskip("playwright.sync_api")
from playwright.sync_api import (
    Browser,
    Error as PlaywrightError,
    Page,
    sync_playwright,
)

_SERVER_FILE = Path(__file__).parent / "render_test_server.py"
_DEV_PORT = 18876
_MCP_PORT = 18877


def _port_free(port: int) -> bool:
    """Probe if a TCP port is free on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _wait_http_ok(url: str, timeout: float = 30.0) -> bool:
    """Poll an URL until it responds (any non-connection-error response)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx.get(url, timeout=1.0)
            return True
        except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException):
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def apps_dev_server() -> Iterator[str]:
    """Start the fastmcp ``apps_dev`` preview server (and the underlying user
    MCP server) in a subprocess, yielding the dev URL.

    Session-scoped so all browser tests share one server. The first call
    pays the spin-up cost (~10s including app-bridge.js fetch from npm);
    subsequent tests are immediate.
    """
    if not _port_free(_DEV_PORT) or not _port_free(_MCP_PORT):
        pytest.skip(
            f"Ports {_DEV_PORT}/{_MCP_PORT} not free — likely an apps_dev "
            f"server already running. Stop it before running browser tests."
        )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "fastmcp.cli",
            "dev",
            "apps",
            f"{_SERVER_FILE}:mcp",
            "--mcp-port",
            str(_MCP_PORT),
            "--dev-port",
            str(_DEV_PORT),
            "--no-reload",
        ],
        env={**os.environ, "FASTMCP_LOG_LEVEL": "WARNING"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=sys.platform != "win32",
    )

    dev_url = f"http://127.0.0.1:{_DEV_PORT}"
    try:
        if not _wait_http_ok(dev_url, timeout=30.0):
            pytest.fail(
                f"apps_dev server did not start on {dev_url} within 30s. "
                f"Check that ``uv run fastmcp dev apps`` works manually."
            )
        yield dev_url
    finally:
        # Kill the entire process group — apps_dev spawns child processes
        # for the user MCP server, and killing only the top-level would
        # leak ports.
        if proc.poll() is None:
            try:
                if sys.platform != "win32":
                    os.killpg(os.getpgid(proc.pid), 15)
                else:
                    proc.kill()
            except (ProcessLookupError, PermissionError):
                proc.kill()
            try:
                proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                proc.kill()


@pytest.fixture(scope="session")
def playwright_browser() -> Iterator[Browser]:
    """Launch a single headless Chromium for the entire test session.

    Skips the test if Chromium isn't installed locally — the browser
    suite is opt-in and only runs after ``playwright install chromium``.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except PlaywrightError as exc:
            pytest.skip(
                f"Chromium not available — run `uv run playwright install "
                f"chromium` first ({exc})"
            )
            return  # pytest.skip raises; this is unreachable but appeases the type checker
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture
def page(playwright_browser: Browser) -> Iterator[Page]:
    """Per-test Playwright page."""
    page = playwright_browser.new_page()
    yield page
    page.close()


@pytest.fixture
def render_scenario(apps_dev_server: str, page: Page):
    """Helper that navigates to ``/launch?tool=render_scenario&args=...`` and
    returns the iframe FrameLocator after waiting for it to render.
    """

    def _go(scenario_name: str, *, wait_ms: int = 8000):
        url = f"{apps_dev_server}/launch?tool=render_scenario&args=" + quote(
            json.dumps({"name": scenario_name})
        )
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # The iframe needs time for app-bridge handshake + renderer mount +
        # tool-result push. 8s is comfortable in CI.
        page.wait_for_timeout(wait_ms)
        return page.frame_locator("#app-frame")

    return _go
