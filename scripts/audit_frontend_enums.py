#!/usr/bin/env python3
"""Audit the hand-maintained ecommerce deep-link platform set against Katana's
live frontend ``EcommerceIntegrationType`` enum.

``katana_mcp.web_urls._ECOMMERCE_TEMPLATES`` is transcribed by hand from
Katana's frontend (it's the only authoritative source — no API exposes the
deep-linkable platform set). This script re-checks the *keys* of that map
against the live frontend enum so the transcription can't silently rot when
Katana adds or renames an ecommerce platform.

How it finds the enum (slug-agnostic, only the CDN host + micro-frontend name
are pinned):

1. Fetch the ``sales-mf`` module-federation container ``remoteEntry.js`` at a
   stable, unhashed path — it carries the webpack chunk-id→content-hash map.
2. Resolve the current ``katana-npm`` chunk filename from that map and fetch it.
3. Regex the ``EcommerceIntegrationType`` enum members out of the chunk.
4. Diff the enum's string values against
   ``katana_mcp.web_urls.RECOGNIZED_ECOMMERCE_TYPES``.

Falls back to the ``header-mf`` container if ``sales-mf`` is unreachable (it
carries the same enum). **This is a soft-fail audit:** any network error,
chunk-resolution miss, or regex-parse failure is reported and exits **0** — a
Katana frontend deploy rotates chunk hashes constantly and the CDN host can
change, and none of that should break CI. Pass ``--strict`` to exit 1 when a
genuine *drift* (not unreachability) is detected, for on-demand gating.

This script is intentionally **not** part of ``regenerate-all`` — it targets a
live, ever-moving frontend, not a pinned spec input.

Usage:

    uv run python scripts/audit_frontend_enums.py
    uv run python scripts/audit_frontend_enums.py --json
    uv run poe audit-frontend-enums
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field

import httpx
from katana_mcp.web_urls import RECOGNIZED_ECOMMERCE_TYPES

# The CloudFront distribution + micro-frontends that carry the enum. These are
# the only pinned assumptions; if Katana rotates the distribution host the audit
# soft-fails (and logs the host so a silent-forever audit is noticeable). The
# ``remoteEntry.js`` path under each is stable and unhashed.
CDN_HOST = "https://d2ymm186steve7.cloudfront.net"
# (micro-frontend name, sub-path prefix on the CDN). sales-mf is primary
# (it hosts the EcomLink component + enum); header-mf is the fallback (enum only).
MICRO_FRONTENDS: tuple[tuple[str, str], ...] = (
    ("sales-mf", "sales-mf"),
    ("header-mf", "header-mf"),
)
HTTP_TIMEOUT = 20.0

# Matches the minified ``function(e){e.Shopify="shopify",...}(a||(t.EcommerceIntegrationType=a={}))``
# IIFE, anchored on the EcommerceIntegrationType binding so the look-alike
# PascalCase import-status enum in header-mf (bound to ``({})``, not to
# EcommerceIntegrationType) is never matched. Group 1 = the IIFE param, group 2
# = the member-assignment body.
_ENUM_IIFE_RE = re.compile(
    r"function\((\w+)\)\{([^{}]*?)\}\([^)]*?EcommerceIntegrationType"
)
# Within a matched body, pull each ``<param>.Member="value"`` pair.
_MEMBER_RE_TMPL = r'{param}\.(\w+)="([^"]*)"'
# remoteEntry chunk maps.
_NAME_MAP_RE = re.compile(r'(\d+):"(npm\.[a-zA-Z0-9._-]*katana-npm[a-zA-Z0-9._-]*)"')
_HASH_MAP_RE = re.compile(r'(\d+):"([0-9a-f]{16,})"')


@dataclass
class AuditResult:
    """Outcome of one audit run."""

    reachable: bool = False
    source: str | None = None  # which MF + chunk url the enum came from
    frontend_values: set[str] = field(default_factory=set)
    expected_values: set[str] = field(
        default_factory=lambda: set(RECOGNIZED_ECOMMERCE_TYPES)
    )
    notes: list[str] = field(default_factory=list)

    @property
    def added(self) -> set[str]:
        """Platforms the frontend has that we don't (the actionable case)."""
        return self.frontend_values - self.expected_values

    @property
    def removed(self) -> set[str]:
        """Platforms we have that the frontend no longer lists."""
        return self.expected_values - self.frontend_values

    @property
    def has_drift(self) -> bool:
        return self.reachable and bool(self.added or self.removed)


def _fetch_text(url: str, client: httpx.Client) -> str | None:
    """GET ``url`` and return its body, or ``None`` on any error."""
    try:
        resp = client.get(url, timeout=HTTP_TIMEOUT)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    return resp.text


def resolve_katana_npm_chunk_url(remote_entry_js: str, base: str) -> str | None:
    """Resolve the current ``katana-npm`` chunk URL from a remoteEntry body.

    Returns ``None`` if the chunk can't be located (the soft-fail trigger).
    """
    names = dict(_NAME_MAP_RE.findall(remote_entry_js))
    hashes = dict(_HASH_MAP_RE.findall(remote_entry_js))
    for chunk_id, name in names.items():
        digest = hashes.get(chunk_id)
        if digest:
            return f"{base}/{name}.{digest}.chunk.js"
    return None


def extract_ecommerce_enum(chunk_js: str) -> dict[str, str] | None:
    """Extract the ``EcommerceIntegrationType`` members from a chunk body.

    Returns ``{Member: "value"}`` or ``None`` when the enum can't be found.
    """
    match = _ENUM_IIFE_RE.search(chunk_js)
    if match is None:
        return None
    param, body = match.group(1), match.group(2)
    member_re = re.compile(_MEMBER_RE_TMPL.format(param=re.escape(param)))
    members = dict(member_re.findall(body))
    return members or None


def _audit_one_mf(
    mf_name: str, sub_path: str, client: httpx.Client, result: AuditResult
) -> bool:
    """Try one micro-frontend; on success populate ``result`` and return True."""
    base = f"{CDN_HOST}/{sub_path}"
    remote_entry = _fetch_text(f"{base}/remoteEntry.js", client)
    if remote_entry is None:
        result.notes.append(f"{mf_name}: remoteEntry.js unreachable")
        return False
    chunk_url = resolve_katana_npm_chunk_url(remote_entry, base)
    if chunk_url is None:
        result.notes.append(f"{mf_name}: could not resolve katana-npm chunk")
        return False
    chunk = _fetch_text(chunk_url, client)
    if chunk is None:
        result.notes.append(f"{mf_name}: chunk unreachable ({chunk_url})")
        return False
    enum = extract_ecommerce_enum(chunk)
    if enum is None:
        result.notes.append(f"{mf_name}: EcommerceIntegrationType not found in chunk")
        return False
    result.reachable = True
    result.source = chunk_url
    result.frontend_values = set(enum.values())
    return True


def audit(client: httpx.Client | None = None) -> AuditResult:
    """Run the audit, trying each micro-frontend until one yields the enum."""
    result = AuditResult()
    owns_client = client is None
    client = client or httpx.Client(follow_redirects=True)
    try:
        for mf_name, sub_path in MICRO_FRONTENDS:
            if _audit_one_mf(mf_name, sub_path, client, result):
                break
    finally:
        if owns_client:
            client.close()
    return result


def format_markdown(result: AuditResult) -> str:
    lines = ["# Frontend ecommerce-enum drift audit", ""]
    if not result.reachable:
        lines.append("**Could not reach the live frontend enum (soft-fail).**")
        lines.append(f"- CDN host: {CDN_HOST}")
        for note in result.notes:
            lines.append(f"- {note}")
        lines.append("")
        lines.append("No conclusion drawn — re-run later or verify manually.")
        return "\n".join(lines)

    lines.append(f"- Source: {result.source}")
    lines.append(f"- Frontend enum values: {sorted(result.frontend_values)}")
    lines.append(f"- Our recognized set: {sorted(result.expected_values)}")
    lines.append("")
    if not result.has_drift:
        lines.append("✅ No drift — the hand-maintained set matches the frontend.")
        return "\n".join(lines)

    lines.append("⚠️ **Drift detected.**")
    if result.added:
        lines.append(
            f"- Frontend ADDED (we should add a template): {sorted(result.added)}"
        )
    if result.removed:
        lines.append(
            f"- We have but frontend dropped (verify before removing): "
            f"{sorted(result.removed)}"
        )
    lines.append("")
    lines.append(
        "Update `_ECOMMERCE_TEMPLATES` in `katana_mcp_server/.../web_urls.py` "
        "(grab any new template from the EcomLink component) and re-run."
    )
    return "\n".join(lines)


def format_json(result: AuditResult) -> str:
    return json.dumps(
        {
            "reachable": result.reachable,
            "source": result.source,
            "frontend_values": sorted(result.frontend_values),
            "expected_values": sorted(result.expected_values),
            "added": sorted(result.added),
            "removed": sorted(result.removed),
            "has_drift": result.has_drift,
            "notes": result.notes,
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on genuine drift (not on unreachability). For CI gating.",
    )
    args = parser.parse_args(argv)

    result = audit()
    print(format_json(result) if args.json else format_markdown(result))

    if args.strict and result.has_drift:
        return 1
    # Soft-fail: unreachable / parse failure / non-strict drift all exit 0.
    return 0


if __name__ == "__main__":
    sys.exit(main())
