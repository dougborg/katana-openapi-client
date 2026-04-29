"""Coerce LLM-mistyped list inputs back into Python lists.

LLMs occasionally send list-typed tool arguments as a single string instead
of a JSON array. Two shapes are observed in the wild:

1. **Comma-separated values**: ``"WS74001,WS74002,WS73003"``
2. **JSON-stringified array**: ``'["WS74001", "WS74002"]'``

When this happens, pydantic raises ``Input should be a valid list
[type=list_type, input_type=str]``, the tool call fails, and the user has
to retry. The recovery is mechanical and lossless — split on commas (or
parse as JSON), strip whitespace, hand pydantic a real list. So we do it.

Usage on a request-model field — prefer the prebuilt aliases::

    from pydantic import Field
    from katana_mcp.tools.list_coercion import CoercedStrListOpt

    skus: CoercedStrListOpt = Field(
        default=None, description="Batch: list of SKUs to look up"
    )

Required (non-Optional) variants and the heterogeneous ``str | int`` shape
have aliases too — see below. Use the raw ``coerce_str_list_input``
validator directly only for one-off types that don't fit the aliases.

Apply only to **LLM-facing** request-model fields. Internal/response-side
list fields don't need it — pydantic-on-pydantic round-trips already use
real lists.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import BeforeValidator


def coerce_str_list_input(value: Any) -> Any:
    """Best-effort recovery of LLM-mistyped list arguments.

    - List input → returned unchanged.
    - String input → parsed as JSON if it looks like an array, otherwise
      split on commas with whitespace stripped. Empty strings yield ``[]``.
    - Anything else → returned unchanged so pydantic raises its normal
      type error (don't mask genuinely malformed input).
    """
    if not isinstance(value, str):
        return value

    s = value.strip()
    if not s:
        return []

    # JSON-stringified array: '[...]' — trust it if it parses to a list.
    if s.startswith("["):
        try:
            parsed = json.loads(s)
        except (json.JSONDecodeError, ValueError):
            pass
        else:
            if isinstance(parsed, list):
                return parsed

    # Fall back to CSV: split, strip, drop empty fragments.
    return [item.strip() for item in s.split(",") if item.strip()]


# Type aliases — collapse the per-field
# ``Annotated[list[X] | None, BeforeValidator(coerce_str_list_input)]`` boilerplate
# into a single readable token at the call site. ``Opt`` suffix marks the
# Optional/None-default variant; bare names are required (non-Optional).

CoercedStrList = Annotated[list[str], BeforeValidator(coerce_str_list_input)]
CoercedStrListOpt = Annotated[list[str] | None, BeforeValidator(coerce_str_list_input)]
CoercedIntList = Annotated[list[int], BeforeValidator(coerce_str_list_input)]
CoercedIntListOpt = Annotated[list[int] | None, BeforeValidator(coerce_str_list_input)]
CoercedStrIntList = Annotated[list[str | int], BeforeValidator(coerce_str_list_input)]
CoercedStrIntListOpt = Annotated[
    list[str | int] | None, BeforeValidator(coerce_str_list_input)
]
