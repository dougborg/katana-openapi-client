import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="BatchStockUpdate")


@_attrs_define
class BatchStockUpdate:
    """Request payload for updating batch properties and tracking information

    Example:
        {'batch_number': 'BAT-2024-001-UPDATED', 'expiration_date': '2025-12-31T23:59:59.000Z', 'batch_barcode':
            '0317-V2'}

    Attributes:
        batch_number (Union[Unset, str]): Updated batch number
        expiration_date (Union[Unset, datetime.datetime]): Updated expiration date (ISO 8601)
        batch_created_date (Union[Unset, datetime.datetime]): Updated batch creation date (ISO 8601)
        batch_barcode (Union[None, Unset, str]): Updated barcode for the batch
    """

    batch_number: Unset | str = UNSET
    expiration_date: Unset | datetime.datetime = UNSET
    batch_created_date: Unset | datetime.datetime = UNSET
    batch_barcode: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_number = self.batch_number

        expiration_date: Unset | str = UNSET
        if not isinstance(self.expiration_date, Unset):
            expiration_date = self.expiration_date.isoformat()

        batch_created_date: Unset | str = UNSET
        if not isinstance(self.batch_created_date, Unset):
            batch_created_date = self.batch_created_date.isoformat()

        batch_barcode: None | Unset | str
        if isinstance(self.batch_barcode, Unset):
            batch_barcode = UNSET
        else:
            batch_barcode = self.batch_barcode

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if batch_number is not UNSET:
            field_dict["batch_number"] = batch_number
        if expiration_date is not UNSET:
            field_dict["expiration_date"] = expiration_date
        if batch_created_date is not UNSET:
            field_dict["batch_created_date"] = batch_created_date
        if batch_barcode is not UNSET:
            field_dict["batch_barcode"] = batch_barcode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_number = d.pop("batch_number", UNSET)

        _expiration_date = d.pop("expiration_date", UNSET)
        expiration_date: Unset | datetime.datetime
        if isinstance(_expiration_date, Unset):
            expiration_date = UNSET
        else:
            expiration_date = isoparse(_expiration_date)

        _batch_created_date = d.pop("batch_created_date", UNSET)
        batch_created_date: Unset | datetime.datetime
        if isinstance(_batch_created_date, Unset):
            batch_created_date = UNSET
        else:
            batch_created_date = isoparse(_batch_created_date)

        def _parse_batch_barcode(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        batch_barcode = _parse_batch_barcode(d.pop("batch_barcode", UNSET))

        batch_stock_update = cls(
            batch_number=batch_number,
            expiration_date=expiration_date,
            batch_created_date=batch_created_date,
            batch_barcode=batch_barcode,
        )

        return batch_stock_update
