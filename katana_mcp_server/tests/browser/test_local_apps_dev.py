"""Contract tests for the deterministic browser bridge launcher."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).with_name("local_apps_dev.py")
_SPEC = importlib.util.spec_from_file_location("local_apps_dev", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
local_apps_dev = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(local_apps_dev)


def test_local_bridge_replaces_every_runtime_cdn_import(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        local_apps_dev.apps_dev,
        "_HOST_SHELL",
        local_apps_dev.apps_dev._HOST_SHELL,
    )
    monkeypatch.setattr(
        local_apps_dev.apps_dev,
        "_HOST_HTML_TEMPLATE",
        local_apps_dev.apps_dev._HOST_HTML_TEMPLATE,
    )

    bundle = local_apps_dev.configure_local_bridge()

    assert "esm.sh" not in local_apps_dev.apps_dev._HOST_SHELL
    assert "esm.sh" not in local_apps_dev.apps_dev._HOST_HTML_TEMPLATE
    assert "AppBridge" in bundle
    assert 'from "/js/app-bridge.js"' in local_apps_dev.apps_dev._HOST_SHELL
    assert 'from "/js/app-bridge.js"' in local_apps_dev.apps_dev._HOST_HTML_TEMPLATE


def test_missing_local_bridge_fails_with_build_instructions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    missing = tmp_path / "bridge.bundle.js"
    monkeypatch.setattr(local_apps_dev, "_BRIDGE_BUNDLE", missing)

    with pytest.raises(RuntimeError, match=r"asset is missing.*npm ci.*npm run build"):
        local_apps_dev._read_bridge_bundle()
