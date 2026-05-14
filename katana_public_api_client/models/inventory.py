from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.location import Location
    from ..models.variant import Variant
    from ..models.variant_default_storage_bin_link_response import (
        VariantDefaultStorageBinLinkResponse,
    )


T = TypeVar("T", bound="Inventory")


@_attrs_define
class Inventory:
    """Represents the current inventory state for a specific product variant at a location.
    Includes stock levels, commitments, expectations, and financial information.

        Example:
            {'variant_id': 3001, 'location_id': 1, 'safety_stock_level': '25.0', 'reorder_point': '25.0', 'average_cost':
                '15.50', 'value_in_stock': '2325.00', 'quantity_in_stock': '150.0', 'quantity_committed': '25.0',
                'quantity_expected': '50.0', 'quantity_missing_or_excess': '0.0', 'quantity_potential': '175.0'}
    """

    variant_id: int
    location_id: int
    reorder_point: str
    average_cost: str
    value_in_stock: str
    quantity_in_stock: str
    quantity_committed: str
    quantity_expected: str
    quantity_missing_or_excess: str
    quantity_potential: None | str
    safety_stock_level: str | Unset = UNSET
    variant: Variant | Unset = UNSET
    location: Location | Unset = UNSET
    archived_at: datetime.datetime | None | Unset = UNSET
    default_storage_bin: None | Unset | VariantDefaultStorageBinLinkResponse = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.variant_default_storage_bin_link_response import (
            VariantDefaultStorageBinLinkResponse,
        )

        variant_id = self.variant_id

        location_id = self.location_id

        reorder_point = self.reorder_point

        average_cost = self.average_cost

        value_in_stock = self.value_in_stock

        quantity_in_stock = self.quantity_in_stock

        quantity_committed = self.quantity_committed

        quantity_expected = self.quantity_expected

        quantity_missing_or_excess = self.quantity_missing_or_excess

        quantity_potential: None | str
        quantity_potential = self.quantity_potential

        safety_stock_level = self.safety_stock_level

        variant: dict[str, Any] | Unset = UNSET
        if not isinstance(self.variant, Unset):
            variant = self.variant.to_dict()

        location: dict[str, Any] | Unset = UNSET
        if not isinstance(self.location, Unset):
            location = self.location.to_dict()

        archived_at: None | str | Unset
        if isinstance(self.archived_at, Unset):
            archived_at = UNSET
        elif isinstance(self.archived_at, datetime.datetime):
            archived_at = self.archived_at.isoformat()
        else:
            archived_at = self.archived_at

        default_storage_bin: dict[str, Any] | None | Unset
        if isinstance(self.default_storage_bin, Unset):
            default_storage_bin = UNSET
        elif isinstance(self.default_storage_bin, VariantDefaultStorageBinLinkResponse):
            default_storage_bin = self.default_storage_bin.to_dict()
        else:
            default_storage_bin = self.default_storage_bin

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "reorder_point": reorder_point,
                "average_cost": average_cost,
                "value_in_stock": value_in_stock,
                "quantity_in_stock": quantity_in_stock,
                "quantity_committed": quantity_committed,
                "quantity_expected": quantity_expected,
                "quantity_missing_or_excess": quantity_missing_or_excess,
                "quantity_potential": quantity_potential,
            }
        )
        if safety_stock_level is not UNSET:
            field_dict["safety_stock_level"] = safety_stock_level
        if variant is not UNSET:
            field_dict["variant"] = variant
        if location is not UNSET:
            field_dict["location"] = location
        if archived_at is not UNSET:
            field_dict["archived_at"] = archived_at
        if default_storage_bin is not UNSET:
            field_dict["default_storage_bin"] = default_storage_bin

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.location import Location
        from ..models.variant import Variant
        from ..models.variant_default_storage_bin_link_response import (
            VariantDefaultStorageBinLinkResponse,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        reorder_point = d.pop("reorder_point")

        average_cost = d.pop("average_cost")

        value_in_stock = d.pop("value_in_stock")

        quantity_in_stock = d.pop("quantity_in_stock")

        quantity_committed = d.pop("quantity_committed")

        quantity_expected = d.pop("quantity_expected")

        quantity_missing_or_excess = d.pop("quantity_missing_or_excess")

        def _parse_quantity_potential(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        quantity_potential = _parse_quantity_potential(d.pop("quantity_potential"))

        safety_stock_level = d.pop("safety_stock_level", UNSET)

        _variant = d.pop("variant", UNSET)
        variant: Variant | Unset
        if isinstance(_variant, Unset):
            variant = UNSET
        else:
            variant = Variant.from_dict(_variant)

        _location = d.pop("location", UNSET)
        location: Location | Unset
        if isinstance(_location, Unset):
            location = UNSET
        else:
            location = Location.from_dict(_location)

        def _parse_archived_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                archived_at_type_0 = isoparse(data)

                return archived_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        archived_at = _parse_archived_at(d.pop("archived_at", UNSET))

        def _parse_default_storage_bin(
            data: object,
        ) -> None | Unset | VariantDefaultStorageBinLinkResponse:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                default_storage_bin_type_0 = (
                    VariantDefaultStorageBinLinkResponse.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return default_storage_bin_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | VariantDefaultStorageBinLinkResponse, data)

        default_storage_bin = _parse_default_storage_bin(
            d.pop("default_storage_bin", UNSET)
        )

        inventory = cls(
            variant_id=variant_id,
            location_id=location_id,
            reorder_point=reorder_point,
            average_cost=average_cost,
            value_in_stock=value_in_stock,
            quantity_in_stock=quantity_in_stock,
            quantity_committed=quantity_committed,
            quantity_expected=quantity_expected,
            quantity_missing_or_excess=quantity_missing_or_excess,
            quantity_potential=quantity_potential,
            safety_stock_level=safety_stock_level,
            variant=variant,
            location=location,
            archived_at=archived_at,
            default_storage_bin=default_storage_bin,
        )

        inventory.additional_properties = d
        return inventory

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
