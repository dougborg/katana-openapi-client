"""Fast YAML loading for the large spec files in this repo.

``yaml.safe_load`` uses PyYAML's *pure-Python* loader even when the libyaml C
extension is installed — you have to ask for ``CSafeLoader`` explicitly. The
upstream portal spec is ~1.5 MB and the local OpenAPI spec ~0.9 MB, where the C
loader is ~7x faster (~920 ms → ~130 ms for the portal spec). That margin is
enough to keep the spec-audit tests comfortably under their 30s pytest-timeout
even on a contended CI runner, and it speeds the ``audit-spec`` / validation
CLIs (and therefore ``poe check``) for free.

Prefer the C loader when it's built; fall back to the pure-Python loader so the
code still works on a libyaml-less install.
"""

from __future__ import annotations

from typing import Any

import yaml

try:
    from yaml import CSafeLoader as _FastSafeLoader
except ImportError:  # pragma: no cover - libyaml not built into this PyYAML
    from yaml import SafeLoader as _FastSafeLoader


def safe_load_yaml(text: str) -> Any:
    """``yaml.safe_load`` equivalent, using libyaml's C loader when available."""
    return yaml.load(text, Loader=_FastSafeLoader)
