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


# A representative typed-object _parse_* helper as openapi-python-client
# emits it. Used as the input fixture for several tests below.
_TYPED_PARSER_INPUT = """\
class SalesOrder:
    @classmethod
    def from_dict(cls, src_dict):
        d = dict(src_dict)

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

# A nullable-string parser (no nested-object alternative). Should NOT be
# patched — empty-dict-as-null is meaningless for ``str``.
_NULLABLE_STRING_PARSER_INPUT = """\
class SalesOrder:
    @classmethod
    def from_dict(cls, src_dict):
        d = dict(src_dict)

        def _parse_customer_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_ref = _parse_customer_ref(d.pop("customer_ref", UNSET))
"""

# Multi-variant oneOf where ``None`` is NOT a valid return type. Should
# NOT be patched — returning ``None`` would violate the declared union.
_MULTI_VARIANT_ONEOF_INPUT = """\
class VariantResponse:
    @classmethod
    def from_dict(cls, src_dict):
        d = dict(src_dict)

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


def _patch(regen: Any, content: str) -> tuple[str, int]:
    """Run the post-processor's core text rewrite on ``content``."""
    return regen._insert_empty_dict_normalization(
        content,
        regen.re.compile(
            r"        def _parse_\w+\(data: object\) -> [^\n]+\n"
            r"            if data is None:\n"
            r"                return data\n"
            r"            if isinstance\(data, Unset\):\n"
            r"                return data\n",
        ),
        early_return_block=(
            "            # Empty dict → None (Katana wire quirk; see #509).\n"
            "            if isinstance(data, dict) and not data:\n"
            "                return None\n"
        ),
        marker_comment="# Empty dict → None (Katana wire quirk; see #509).",
    )


def test_inserts_normalization_into_typed_object_parser(regen: Any) -> None:
    """Header-matching typed-object helper gets the early-return inserted."""
    output, count = _patch(regen, _TYPED_PARSER_INPUT)
    assert count == 1
    assert "# Empty dict → None (Katana wire quirk; see #509)." in output
    # The early-return must appear after the Unset check and before the try.
    unset_idx = output.index("if isinstance(data, Unset):")
    early_idx = output.index("if isinstance(data, dict) and not data:")
    try_idx = output.index("try:")
    assert unset_idx < early_idx < try_idx


def test_does_not_patch_nullable_string_parser(regen: Any) -> None:
    """Helpers without ``<Class>.from_dict()`` shouldn't be patched —
    empty-dict-as-null is meaningless for ``str``."""
    output, count = _patch(regen, _NULLABLE_STRING_PARSER_INPUT)
    assert count == 0
    assert output == _NULLABLE_STRING_PARSER_INPUT


def test_does_not_patch_multi_variant_oneof_without_none(regen: Any) -> None:
    """Helpers whose return type doesn't include ``None`` shouldn't be
    patched — returning ``None`` would violate the union (e.g.
    ``Material | Product | Unset``). The header-match requires a
    ``if data is None`` check, which these helpers don't have."""
    output, count = _patch(regen, _MULTI_VARIANT_ONEOF_INPUT)
    assert count == 0
    assert output == _MULTI_VARIANT_ONEOF_INPUT


def test_idempotent_on_already_patched_input(regen: Any) -> None:
    """Re-running the post-processor on its own output is a no-op."""
    once, first_count = _patch(regen, _TYPED_PARSER_INPUT)
    twice, second_count = _patch(regen, once)
    assert first_count == 1
    assert second_count == 0
    assert twice == once


def test_function_body_end_uses_indentation(regen: Any) -> None:
    """Body-end detection must respect the function's indentation, not
    look ahead to the next ``def`` keyword anywhere — otherwise it
    would mistakenly include sibling code at the parent classmethod
    indent (where ``<Class>.from_dict()`` calls live for list parsers)
    and produce false-positive matches."""
    sample = (
        "            return cast(None | str | Unset, data)\n"
        "\n"
        "        customer_ref = _parse_customer_ref(d.pop('customer_ref', UNSET))\n"
        "\n"
        "        # Sibling code that calls SalesOrderRow.from_dict — must NOT\n"
        "        # be considered part of the previous _parse_* body.\n"
        "        for r in rows:\n"
        "            row = SalesOrderRow.from_dict(r)\n"
    )
    end = regen._function_body_end(sample, 0)
    body = sample[:end]
    # Body should stop before the ``customer_ref = ...`` line at 8-space
    # indent, well before the SalesOrderRow.from_dict call.
    assert "from_dict" not in body
    assert "_parse_customer_ref" not in body  # the assignment
