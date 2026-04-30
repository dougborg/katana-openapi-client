"""Tests for the derived-field registry and dispatch-layer check."""

import pytest
from katana_mcp.tools._derived_fields import (
    DERIVED_FIELDS,
    DerivedFieldError,
    check_derived_fields,
)
from katana_mcp.tools._modification import FieldChange


def _change(field: str, *, new=None, is_added: bool = False) -> FieldChange:
    """Build a minimal FieldChange for tests."""
    return FieldChange(field=field, new=new, is_added=is_added)


class TestRegistryShape:
    def test_purchase_order_update_row_includes_landed_cost(self):
        """Regression: ``landed_cost`` is the field that triggered this work."""
        po_map = DERIVED_FIELDS["purchase_order"]["update_row"]
        assert "landed_cost" in po_map
        # A workaround hint must be set so the user gets a path forward
        assert po_map["landed_cost"] is not None
        assert "add_additional_costs" in po_map["landed_cost"]

    def test_workaround_hints_are_strings_or_none(self):
        for entity_map in DERIVED_FIELDS.values():
            for op_map in entity_map.values():
                for hint in op_map.values():
                    assert hint is None or isinstance(hint, str)


class TestCheckDerivedFields:
    def test_raises_for_landed_cost_on_po_update_row(self):
        with pytest.raises(DerivedFieldError, match="landed_cost"):
            check_derived_fields(
                entity_type="purchase_order",
                operation="update_row",
                target_id=555,
                diff=[_change("landed_cost", new=100.0)],
            )

    def test_error_message_names_target_id(self):
        with pytest.raises(DerivedFieldError, match=r"\(target 555\)"):
            check_derived_fields(
                entity_type="purchase_order",
                operation="update_row",
                target_id=555,
                diff=[_change("landed_cost", new=100.0)],
            )

    def test_error_message_includes_workaround_hint(self):
        with pytest.raises(DerivedFieldError, match="add_additional_costs"):
            check_derived_fields(
                entity_type="purchase_order",
                operation="update_row",
                target_id=1,
                diff=[_change("landed_cost", new=50.0)],
            )

    def test_does_not_raise_for_legitimate_po_row_update(self):
        check_derived_fields(
            entity_type="purchase_order",
            operation="update_row",
            target_id=555,
            diff=[
                _change("quantity", new=15),
                _change("price_per_unit", new=12.50),
            ],
        )

    def test_does_not_raise_for_unknown_entity_type(self):
        # Unknown entity types pass through — registry is opt-in per entity
        check_derived_fields(
            entity_type="unknown_entity",
            operation="update_row",
            target_id=1,
            diff=[_change("landed_cost", new=100)],
        )

    def test_does_not_raise_for_unknown_operation(self):
        # Unknown operations pass through — registry is opt-in per operation
        check_derived_fields(
            entity_type="purchase_order",
            operation="some_other_op",
            target_id=1,
            diff=[_change("landed_cost", new=100)],
        )

    def test_does_not_raise_on_empty_diff(self):
        check_derived_fields(
            entity_type="purchase_order",
            operation="update_row",
            target_id=1,
            diff=[],
        )

    def test_fails_fast_on_first_match(self):
        """Two derived fields in the same diff — only the first surfaces."""
        with pytest.raises(DerivedFieldError, match="landed_cost"):
            check_derived_fields(
                entity_type="purchase_order",
                operation="update_row",
                target_id=1,
                diff=[
                    _change("landed_cost", new=100.0),
                    _change("total", new=999.0),
                ],
            )

    def test_handles_target_id_none(self):
        """Create-style actions have target_id=None; the message omits the
        target suffix rather than rendering ``(target None)``."""
        with pytest.raises(DerivedFieldError) as exc_info:
            check_derived_fields(
                entity_type="purchase_order",
                operation="update_row",
                target_id=None,
                diff=[_change("landed_cost", new=100.0)],
            )
        assert "(target" not in str(exc_info.value)

    def test_derived_field_error_subclasses_value_error(self):
        """Raising ``DerivedFieldError`` surfaces through the standard
        ``except ValueError`` handler used by tool wrappers."""
        try:
            check_derived_fields(
                entity_type="purchase_order",
                operation="update_row",
                target_id=1,
                diff=[_change("landed_cost", new=10.0)],
            )
        except ValueError as exc:
            assert isinstance(exc, DerivedFieldError)
        else:
            pytest.fail("Expected DerivedFieldError to be raised")
