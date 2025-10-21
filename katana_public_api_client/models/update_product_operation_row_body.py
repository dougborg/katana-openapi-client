from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateProductOperationRowBody")


@_attrs_define
class UpdateProductOperationRowBody:
    """
    Attributes:
        sequence (Union[Unset, int]): Operation sequence
        notes (Union[Unset, str]): Operation notes
    """

    sequence: Unset | int = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        sequence = self.sequence

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if sequence is not UNSET:
            field_dict["sequence"] = sequence
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sequence = d.pop("sequence", UNSET)

        notes = d.pop("notes", UNSET)

        update_product_operation_row_body = cls(
            sequence=sequence,
            notes=notes,
        )

        return update_product_operation_row_body
