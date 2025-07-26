import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchStockUpdate")


@_attrs_define
class BatchStockUpdate:
    """
    Example:
        {'batch_number': 'BAT-1', 'expiration_date': '2020-10-23T10:37:05.085Z', 'batch_created_date':
            '2020-10-23T10:37:05.085Z', 'variant_id': 1, 'batch_barcode': '0040'}
    """

    batch_number: str
    variant_id: int
    expiration_date: Unset | datetime.datetime = UNSET
    batch_created_date: Unset | datetime.datetime = UNSET
    batch_barcode: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_number = self.batch_number

        variant_id = self.variant_id

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

        field_dict.update(
            {
                "batch_number": batch_number,
                "variant_id": variant_id,
            }
        )
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
        batch_number = d.pop("batch_number")

        variant_id = d.pop("variant_id")

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
            variant_id=variant_id,
            expiration_date=expiration_date,
            batch_created_date=batch_created_date,
            batch_barcode=batch_barcode,
        )

        return batch_stock_update
