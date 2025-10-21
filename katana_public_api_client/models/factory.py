import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.factory_legal_address import FactoryLegalAddress


T = TypeVar("T", bound="Factory")


@_attrs_define
class Factory:
    """Factory configuration object (singleton resource without ID)

    Example:
        {'legal_address': {'line_1': 'Peetri 7', 'line_2': 'Apartment 1', 'city': 'Tallinn', 'state': 'State', 'zip':
            '10411', 'country': 'Estonia'}, 'legal_name': 'Legal name', 'display_name': 'Display name',
            'base_currency_code': 'USD', 'default_so_delivery_time': '2021-10-13T15:31:48.490Z', 'default_po_lead_time':
            '2021-10-13T15:31:48.490Z', 'default_manufacturing_location_id': 1, 'default_purchases_location_id': 1,
            'default_sales_location_id': 1, 'inventory_closing_date': '2022-01-28T23:59:59.000Z'}
    """

    display_name: str
    base_currency_code: str
    name: Unset | str = UNSET
    address: None | Unset | str = UNSET
    currency: Unset | str = UNSET
    timezone: Unset | str = UNSET
    legal_address: Union[Unset, "FactoryLegalAddress"] = UNSET
    legal_name: Unset | str = UNSET
    default_so_delivery_time: Unset | datetime.datetime = UNSET
    default_po_lead_time: Unset | datetime.datetime = UNSET
    default_manufacturing_location_id: Unset | int = UNSET
    default_purchases_location_id: Unset | int = UNSET
    default_sales_location_id: Unset | int = UNSET
    inventory_closing_date: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        base_currency_code = self.base_currency_code

        name = self.name

        address: None | Unset | str
        if isinstance(self.address, Unset):
            address = UNSET
        else:
            address = self.address

        currency = self.currency

        timezone = self.timezone

        legal_address: Unset | dict[str, Any] = UNSET
        if not isinstance(self.legal_address, Unset):
            legal_address = self.legal_address.to_dict()

        legal_name = self.legal_name

        default_so_delivery_time: Unset | str = UNSET
        if not isinstance(self.default_so_delivery_time, Unset):
            default_so_delivery_time = self.default_so_delivery_time.isoformat()

        default_po_lead_time: Unset | str = UNSET
        if not isinstance(self.default_po_lead_time, Unset):
            default_po_lead_time = self.default_po_lead_time.isoformat()

        default_manufacturing_location_id = self.default_manufacturing_location_id

        default_purchases_location_id = self.default_purchases_location_id

        default_sales_location_id = self.default_sales_location_id

        inventory_closing_date: Unset | str = UNSET
        if not isinstance(self.inventory_closing_date, Unset):
            inventory_closing_date = self.inventory_closing_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "display_name": display_name,
                "base_currency_code": base_currency_code,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if address is not UNSET:
            field_dict["address"] = address
        if currency is not UNSET:
            field_dict["currency"] = currency
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if legal_address is not UNSET:
            field_dict["legal_address"] = legal_address
        if legal_name is not UNSET:
            field_dict["legal_name"] = legal_name
        if default_so_delivery_time is not UNSET:
            field_dict["default_so_delivery_time"] = default_so_delivery_time
        if default_po_lead_time is not UNSET:
            field_dict["default_po_lead_time"] = default_po_lead_time
        if default_manufacturing_location_id is not UNSET:
            field_dict["default_manufacturing_location_id"] = (
                default_manufacturing_location_id
            )
        if default_purchases_location_id is not UNSET:
            field_dict["default_purchases_location_id"] = default_purchases_location_id
        if default_sales_location_id is not UNSET:
            field_dict["default_sales_location_id"] = default_sales_location_id
        if inventory_closing_date is not UNSET:
            field_dict["inventory_closing_date"] = inventory_closing_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.factory_legal_address import FactoryLegalAddress

        d = dict(src_dict)
        display_name = d.pop("display_name")

        base_currency_code = d.pop("base_currency_code")

        name = d.pop("name", UNSET)

        def _parse_address(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        address = _parse_address(d.pop("address", UNSET))

        currency = d.pop("currency", UNSET)

        timezone = d.pop("timezone", UNSET)

        _legal_address = d.pop("legal_address", UNSET)
        legal_address: Unset | FactoryLegalAddress
        if isinstance(_legal_address, Unset):
            legal_address = UNSET
        else:
            legal_address = FactoryLegalAddress.from_dict(_legal_address)

        legal_name = d.pop("legal_name", UNSET)

        _default_so_delivery_time = d.pop("default_so_delivery_time", UNSET)
        default_so_delivery_time: Unset | datetime.datetime
        if isinstance(_default_so_delivery_time, Unset):
            default_so_delivery_time = UNSET
        else:
            default_so_delivery_time = isoparse(_default_so_delivery_time)

        _default_po_lead_time = d.pop("default_po_lead_time", UNSET)
        default_po_lead_time: Unset | datetime.datetime
        if isinstance(_default_po_lead_time, Unset):
            default_po_lead_time = UNSET
        else:
            default_po_lead_time = isoparse(_default_po_lead_time)

        default_manufacturing_location_id = d.pop(
            "default_manufacturing_location_id", UNSET
        )

        default_purchases_location_id = d.pop("default_purchases_location_id", UNSET)

        default_sales_location_id = d.pop("default_sales_location_id", UNSET)

        _inventory_closing_date = d.pop("inventory_closing_date", UNSET)
        inventory_closing_date: Unset | datetime.datetime
        if isinstance(_inventory_closing_date, Unset):
            inventory_closing_date = UNSET
        else:
            inventory_closing_date = isoparse(_inventory_closing_date)

        factory = cls(
            display_name=display_name,
            base_currency_code=base_currency_code,
            name=name,
            address=address,
            currency=currency,
            timezone=timezone,
            legal_address=legal_address,
            legal_name=legal_name,
            default_so_delivery_time=default_so_delivery_time,
            default_po_lead_time=default_po_lead_time,
            default_manufacturing_location_id=default_manufacturing_location_id,
            default_purchases_location_id=default_purchases_location_id,
            default_sales_location_id=default_sales_location_id,
            inventory_closing_date=inventory_closing_date,
        )

        factory.additional_properties = d
        return factory

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
