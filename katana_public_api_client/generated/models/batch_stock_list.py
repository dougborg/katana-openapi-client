from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_stock import BatchStock


T = TypeVar("T", bound="BatchStockList")


@_attrs_define
class BatchStockList:
    """
    Example:
        {'data': [{'batch_id': 1109, 'batch_number': 'B2', 'batch_created_date': '2020-09-29T11:40:29.628Z',
            'expiration_date': '2021-04-30T10:35:00.000Z', 'location_id': 1433, 'variant_id': 350880, 'quantity_in_stock':
            '10.00000', 'batch_barcode': '0317'}]}

    Attributes:
        data (Union[Unset, list['BatchStock']]):
    """

    data: Unset | list["BatchStock"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_stock import BatchStock

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = BatchStock.from_dict(data_item_data)

            data.append(data_item)

        batch_stock_list = cls(
            data=data,
        )

        batch_stock_list.additional_properties = d
        return batch_stock_list

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
