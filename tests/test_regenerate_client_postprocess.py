"""Regression tests for the regenerate_client.py post-processors.

The post-processors normalize quirks in the openapi-python-client output
(see #509 for the empty-dict-as-null normalization). These tests pin
the rewrite behavior so a future codegen tooling change that subtly
shifts the generated text pattern doesn't silently disable the fix.

Loads ``scripts/regenerate_client.py`` via ``importlib`` so the test
doesn't need ``sys.path`` manipulation or ``# type: ignore`` markers.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "regenerate_client.py"
)


def _load_regenerate_client() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "regenerate_client_under_test", _SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        msg = f"Could not load module from {_SCRIPT_PATH}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def regen() -> ModuleType:
    return _load_regenerate_client()


def _wrap_in_class(parser_body: str) -> str:
    """Wrap a ``_parse_*`` helper body in the surrounding class scaffolding
    that the openapi-python-client generator emits."""
    return (
        "class SalesOrder:\n"
        "    @classmethod\n"
        "    def from_dict(cls, src_dict):\n"
        "        d = dict(src_dict)\n"
        "\n"
        f"{parser_body}"
    )


_TYPED_PARSER = _wrap_in_class(
    """\
        def _parse_shipping_fee(data: object) -> None | SalesOrderShippingFee | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                shipping_fee_type_0 = SalesOrderShippingFee.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return shipping_fee_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SalesOrderShippingFee | Unset, data)

        shipping_fee = _parse_shipping_fee(d.pop("shipping_fee", UNSET))
"""
)

_NULLABLE_STRING_PARSER = _wrap_in_class(
    """\
        def _parse_customer_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_ref = _parse_customer_ref(d.pop("customer_ref", UNSET))
"""
)

_MULTI_VARIANT_ONEOF_PARSER = _wrap_in_class(
    """\
        def _parse_product_or_material(data: object) -> Material | Product | Unset:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                product_or_material_type_0 = Product.from_dict(
                    cast(Mapping[str, Any], data)
                )
                return product_or_material_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            product_or_material_type_1 = Material.from_dict(
                cast(Mapping[str, Any], data)
            )
            return product_or_material_type_1

        product_or_material = _parse_product_or_material(
            d.pop("product_or_material", UNSET)
        )
"""
)


@pytest.mark.parametrize(
    ("label", "source", "expected_count"),
    [
        ("typed_object_parser", _TYPED_PARSER, 1),
        ("nullable_string_parser", _NULLABLE_STRING_PARSER, 0),
        ("multi_variant_oneof_without_none", _MULTI_VARIANT_ONEOF_PARSER, 0),
    ],
)
def test_eligibility(regen: Any, label: str, source: str, expected_count: int) -> None:
    """Only typed-object parsers with ``None`` allowed get patched."""
    output, count = regen._insert_empty_dict_normalization(source)
    assert count == expected_count, label
    if expected_count == 0:
        assert output == source, f"{label} should be unmodified"
    else:
        assert regen._EMPTY_DICT_MARKER in output, label


def test_inserts_at_correct_position(regen: Any) -> None:
    """Early-return lands after the Unset check and before the try block."""
    output, _ = regen._insert_empty_dict_normalization(_TYPED_PARSER)
    unset_idx = output.index("if isinstance(data, Unset):")
    early_idx = output.index("if isinstance(data, dict) and not data:")
    try_idx = output.index("try:")
    assert unset_idx < early_idx < try_idx


def test_idempotent_on_already_patched_input(regen: Any) -> None:
    once, first_count = regen._insert_empty_dict_normalization(_TYPED_PARSER)
    twice, second_count = regen._insert_empty_dict_normalization(once)
    assert first_count == 1
    assert second_count == 0
    assert twice == once


def test_function_body_end_uses_indentation(regen: Any) -> None:
    # If the body-end walker looked for the next ``def`` keyword anywhere
    # rather than detecting the parent classmethod's indent, it would
    # reach into sibling code (``SalesOrderRow.from_dict`` here) and
    # produce false-positive eligibility matches on nullable-string parsers.
    sample = (
        "            return cast(None | str | Unset, data)\n"
        "\n"
        "        customer_ref = _parse_customer_ref(d.pop('customer_ref', UNSET))\n"
        "\n"
        "        for r in rows:\n"
        "            row = SalesOrderRow.from_dict(r)\n"
    )
    end = regen._function_body_end(sample, 0)
    body = sample[:end]
    assert "from_dict" not in body
    assert "_parse_customer_ref" not in body
