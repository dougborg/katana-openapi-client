from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.create_serial_number_failed_item import CreateSerialNumberFailedItem
    from ..models.serial_number import SerialNumber


T = TypeVar("T", bound="CreateSerialNumbersResponse")


@_attrs_define
class CreateSerialNumbersResponse:
    """Response from ``POST /serial_numbers``. The endpoint can partial-
    fail: any string the API rejects (DUPLICATE on the mint path,
    MISSING on the transfer path) lands in ``failed`` while the rest
    succeed. The call still returns 200 in the partial-failure case.

        Example:
            {'successful': [{'id': 886853, 'transaction_id': '0f054aa0-1234-5678-9abc-def012345678', 'serial_number':
                'KNF001234567', 'resource_type': 'ManufacturingOrder', 'resource_id': 16920710, 'transaction_date':
                '2024-01-15T08:00:00.000Z', 'quantity_change': 0}], 'failed': [{'serial_number': 'KNF001234568', 'reason':
                'DUPLICATE'}]}
    """

    successful: list[SerialNumber]
    failed: list[CreateSerialNumberFailedItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        successful = []
        for successful_item_data in self.successful:
            successful_item = successful_item_data.to_dict()
            successful.append(successful_item)

        failed = []
        for failed_item_data in self.failed:
            failed_item = failed_item_data.to_dict()
            failed.append(failed_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "successful": successful,
                "failed": failed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_serial_number_failed_item import (
            CreateSerialNumberFailedItem,
        )
        from ..models.serial_number import SerialNumber

        d = dict(src_dict)
        successful = []
        _successful = d.pop("successful")
        for successful_item_data in _successful:
            successful_item = SerialNumber.from_dict(
                cast(Mapping[str, Any], successful_item_data)
            )

            successful.append(successful_item)

        failed = []
        _failed = d.pop("failed")
        for failed_item_data in _failed:
            failed_item = CreateSerialNumberFailedItem.from_dict(
                cast(Mapping[str, Any], failed_item_data)
            )

            failed.append(failed_item)

        create_serial_numbers_response = cls(
            successful=successful,
            failed=failed,
        )

        create_serial_numbers_response.additional_properties = d
        return create_serial_numbers_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
