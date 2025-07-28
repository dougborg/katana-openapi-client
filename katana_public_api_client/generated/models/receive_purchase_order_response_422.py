from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.receive_purchase_order_response_422_details_item import (
        ReceivePurchaseOrderResponse422DetailsItem,
    )


T = TypeVar("T", bound="ReceivePurchaseOrderResponse422")


@_attrs_define
class ReceivePurchaseOrderResponse422:
    status_code: Unset | float = UNSET
    name: Unset | str = UNSET
    message: Unset | str = UNSET
    code: Unset | str = UNSET
    details: Unset | list["ReceivePurchaseOrderResponse422DetailsItem"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status_code = self.status_code

        name = self.name

        message = self.message

        code = self.code

        details: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.details, Unset):
            details = []
            for details_item_data in self.details:
                details_item = details_item_data.to_dict()
                details.append(details_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status_code is not UNSET:
            field_dict["statusCode"] = status_code
        if name is not UNSET:
            field_dict["name"] = name
        if message is not UNSET:
            field_dict["message"] = message
        if code is not UNSET:
            field_dict["code"] = code
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.receive_purchase_order_response_422_details_item import (
            ReceivePurchaseOrderResponse422DetailsItem,
        )

        d = dict(src_dict)
        status_code = d.pop("statusCode", UNSET)

        name = d.pop("name", UNSET)

        message = d.pop("message", UNSET)

        code = d.pop("code", UNSET)

        details = []
        _details = d.pop("details", UNSET)
        for details_item_data in _details or []:
            details_item = ReceivePurchaseOrderResponse422DetailsItem.from_dict(
                details_item_data
            )

            details.append(details_item)

        receive_purchase_order_response_422 = cls(
            status_code=status_code,
            name=name,
            message=message,
            code=code,
            details=details,
        )

        receive_purchase_order_response_422.additional_properties = d
        return receive_purchase_order_response_422

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
