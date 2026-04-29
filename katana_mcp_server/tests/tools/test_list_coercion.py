"""Tests for the list-coercion BeforeValidator.

Real LLM call shapes that motivated this — both observed in production:

  Image #1 (the original bug): ``skus='WS74001,WS74002,WS73003,...,RY23LGFSP'``
    → Pydantic raised ``Input should be a valid list [type=list_type,
       input_type=str]`` and the tool call aborted.

  JSON-stringified variant: ``skus='["WS74001", "WS74002"]'``
    → Same failure mode.

Both should now recover transparently without losing data.
"""

from __future__ import annotations

from typing import Annotated

import pytest
from katana_mcp.tools.list_coercion import coerce_str_list_input
from pydantic import BaseModel, BeforeValidator, Field, ValidationError


class _RequestStub(BaseModel):
    """Mimics the shape of an LLM-facing request-model field."""

    skus: Annotated[list[str] | None, BeforeValidator(coerce_str_list_input)] = Field(
        default=None
    )
    ids: Annotated[list[int] | None, BeforeValidator(coerce_str_list_input)] = Field(
        default=None
    )


def _build(**kwargs: object) -> _RequestStub:
    """Use ``model_validate`` so we can pass string-typed inputs through the
    BeforeValidator without arguing with pyright about the field annotation.
    Mirrors how MCP/fastmcp actually constructs the request from the LLM-supplied
    JSON dict."""
    return _RequestStub.model_validate(kwargs)


def test_list_input_passes_through_unchanged():
    assert _build(skus=["A", "B", "C"]).skus == ["A", "B", "C"]


def test_csv_string_splits_into_list():
    assert _build(skus="WS74001,WS74002,WS73003").skus == [
        "WS74001",
        "WS74002",
        "WS73003",
    ]


def test_csv_string_strips_whitespace_and_drops_empty_fragments():
    assert _build(skus=" WS74001 , , WS74002 ,").skus == ["WS74001", "WS74002"]


def test_json_stringified_array_is_parsed():
    assert _build(skus='["WS74001", "WS74002"]').skus == ["WS74001", "WS74002"]


def test_json_stringified_array_with_ints_coerces_for_int_field():
    assert _build(ids="[101, 202, 303]").ids == [101, 202, 303]


def test_csv_string_of_ints_coerces_via_pydantic():
    # CSV path returns strings; pydantic's list[int] coerces each element.
    assert _build(ids="101,202,303").ids == [101, 202, 303]


def test_empty_string_yields_empty_list():
    assert _build(skus="").skus == []


def test_whitespace_only_string_yields_empty_list():
    assert _build(skus="   ").skus == []


def test_none_passes_through():
    assert _build(skus=None).skus is None


def test_omitted_field_keeps_default():
    assert _build().skus is None


def test_malformed_json_falls_back_to_csv_split():
    # Unclosed bracket — JSON parse fails, CSV split runs on the whole string.
    assert _build(skus="[WS74001,WS74002").skus == ["[WS74001", "WS74002"]


def test_non_list_json_falls_back_to_csv_split():
    # JSON parses but isn't a list — keep the string-y CSV path.
    assert _build(skus='{"key":"value"}').skus == ['{"key":"value"}']


def test_non_string_non_list_input_raises_normal_pydantic_error():
    # Don't mask genuinely wrong types — pydantic's diagnostic still fires.
    with pytest.raises(ValidationError):
        _build(skus=42)


def test_int_input_for_int_list_raises_normal_pydantic_error():
    # Same — a bare int for list[int] should still be a real error.
    with pytest.raises(ValidationError):
        _build(ids=42)


def test_single_value_string_no_comma_yields_one_item_list():
    # ``skus="WS74001"`` is the LLM's most innocent form of the bug.
    assert _build(skus="WS74001").skus == ["WS74001"]
