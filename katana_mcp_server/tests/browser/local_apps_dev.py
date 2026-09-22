"""Run FastMCP's Apps preview with a pinned, same-origin JavaScript bridge.

FastMCP 4.0.3 downloads ``app-bridge.js`` from npm during startup and leaves
the MCP client imports pointed at esm.sh. Browser render tests need the same
bridge and client implementations without runtime network access, so this
small launcher replaces only those module-loading seams. FastMCP continues to
provide the host page, MCP proxy, iframe lifecycle, and AppBridge wiring.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any, cast

from fastmcp.cli import apps_dev

_ASSET_DIR = Path(__file__).with_name("assets")
_BRIDGE_BUNDLE = _ASSET_DIR / "bridge.bundle.js"
_EXPECTED_FASTMCP_EXT_APPS_VERSION = "1.0.1"
_EXPECTED_FASTMCP_SDK_VERSION = "1.25.2"

_REMOTE_IMPORTS = """\
    import {{ AppBridge, PostMessageTransport%s }}
      from \"/js/app-bridge.js\";
    import {{ Client }}
      from \"https://esm.sh/@modelcontextprotocol/sdk@{mcp_sdk_version}/client/index.js\";
    import {{ StreamableHTTPClientTransport }}
      from \"https://esm.sh/@modelcontextprotocol/sdk@{mcp_sdk_version}/client/streamableHttp.js\";"""

_LOCAL_IMPORTS = """\
    import {{
      AppBridge,
      PostMessageTransport%s,
      Client,
      StreamableHTTPClientTransport,
    }} from \"/js/app-bridge.js\";"""


def _read_bridge_bundle() -> str:
    """Return the checked-in bundle or fail with its reproducible build command."""
    try:
        bundle = _BRIDGE_BUNDLE.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Pinned browser bridge asset is missing: {_BRIDGE_BUNDLE}. "
            "Rebuild it with `npm ci && npm run build` in "
            f"{_ASSET_DIR}."
        ) from exc
    if not bundle.strip():
        raise RuntimeError(f"Pinned browser bridge asset is empty: {_BRIDGE_BUNDLE}")
    return bundle


def _replace_remote_imports(template: str, *, tool_uri_helper: bool) -> str:
    """Replace FastMCP's known CDN imports, refusing silent upstream drift."""
    suffix = ", getToolUiResourceUri" if tool_uri_helper else ""
    remote = _REMOTE_IMPORTS % suffix
    if template.count(remote) != 1:
        raise RuntimeError(
            "FastMCP's Apps host imports changed; update local_apps_dev.py "
            "instead of falling back to runtime CDN modules."
        )
    return template.replace(remote, _LOCAL_IMPORTS % suffix)


def configure_local_bridge() -> str:
    """Patch FastMCP's asset loader and templates to use the local bundle."""
    if apps_dev._EXT_APPS_VERSION != _EXPECTED_FASTMCP_EXT_APPS_VERSION:
        raise RuntimeError(
            "FastMCP's ext-apps version changed from "
            f"{_EXPECTED_FASTMCP_EXT_APPS_VERSION} to "
            f"{apps_dev._EXT_APPS_VERSION}; rebuild and review the pinned bundle."
        )
    if apps_dev._MCP_SDK_VERSION != _EXPECTED_FASTMCP_SDK_VERSION:
        raise RuntimeError(
            "FastMCP's MCP SDK version changed from "
            f"{_EXPECTED_FASTMCP_SDK_VERSION} to {apps_dev._MCP_SDK_VERSION}; "
            "rebuild and review the pinned bundle."
        )

    bundle = _read_bridge_bundle()
    # These are deliberate runtime seams in FastMCP's preview launcher. The
    # cast keeps static analysis from treating its template constants as
    # immutable LiteralString values while retaining ordinary assignments.
    mutable_apps_dev = cast(Any, apps_dev)
    mutable_apps_dev._HOST_SHELL = _replace_remote_imports(
        apps_dev._HOST_SHELL, tool_uri_helper=False
    )
    mutable_apps_dev._HOST_HTML_TEMPLATE = _replace_remote_imports(
        apps_dev._HOST_HTML_TEMPLATE, tool_uri_helper=True
    )

    async def load_local_bridge(_version: str, _sdk_version: str) -> tuple[str, str]:
        return bundle, "{}"

    mutable_apps_dev._fetch_app_bridge_bundle = load_local_bridge
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("server_spec")
    parser.add_argument("--mcp-port", type=int, required=True)
    parser.add_argument("--dev-port", type=int, required=True)
    args = parser.parse_args()

    configure_local_bridge()
    asyncio.run(
        apps_dev.run_dev_apps(
            args.server_spec,
            mcp_port=args.mcp_port,
            dev_port=args.dev_port,
            reload=False,
            log_panel=True,
        )
    )


if __name__ == "__main__":
    main()
