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
    from ..models.stock_transfer_row import StockTransferRow


T = TypeVar("T", bound="StockTransfer")


@_attrs_define
class StockTransfer:
    """Inventory transfer record for moving stock between different warehouse locations or facilities

    Example:
        {'id': 1, 'stock_transfer_number': 'ST-1', 'source_location_id': 1, 'target_location_id': 2, 'transfer_date':
            '2021-10-06T11:47:13.846Z', 'order_created_date': '2021-10-01T11:47:13.846Z', 'expected_arrival_date':
            '2021-10-20T11:47:13.846Z', 'additional_info': 'transfer additional info', 'stock_transfer_rows': [{'id': 1,
            'variant_id': 1, 'quantity': 100, 'cost_per_unit': 123.45, 'batch_transactions': [{'batch_id': 1, 'quantity':
            50}, {'batch_id': 2, 'quantity': 50}], 'deleted_at': None}, {'id': 2, 'variant_id': 2, 'quantity': 150,
            'cost_per_unit': 234.56, 'batch_transactions': [{'batch_id': 3, 'quantity': 150}], 'deleted_at': None}],
            'created_at': '2021-10-06T11:47:13.846Z', 'updated_at': '2021-10-06T11:47:13.846Z', 'deleted_at': None}
    """

    id: int
    stock_transfer_number: str
    source_location_id: int
    target_location_id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    status: str | Unset = UNSET
    transfer_date: datetime.datetime | Unset = UNSET
    order_created_date: datetime.datetime | None | Unset = UNSET
    expected_arrival_date: datetime.datetime | None | Unset = UNSET
    additional_info: None | str | Unset = UNSET
    stock_transfer_rows: list[StockTransferRow] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        stock_transfer_number = self.stock_transfer_number

        source_location_id = self.source_location_id

        target_location_id = self.target_location_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        status = self.status

        transfer_date: str | Unset = UNSET
        if not isinstance(self.transfer_date, Unset):
            transfer_date = self.transfer_date.isoformat()

        order_created_date: None | str | Unset
        if isinstance(self.order_created_date, Unset):
            order_created_date = UNSET
        elif isinstance(self.order_created_date, datetime.datetime):
            order_created_date = self.order_created_date.isoformat()
        else:
            order_created_date = self.order_created_date

        expected_arrival_date: None | str | Unset
        if isinstance(self.expected_arrival_date, Unset):
            expected_arrival_date = UNSET
        elif isinstance(self.expected_arrival_date, datetime.datetime):
            expected_arrival_date = self.expected_arrival_date.isoformat()
        else:
            expected_arrival_date = self.expected_arrival_date

        additional_info: None | str | Unset
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        stock_transfer_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.stock_transfer_rows, Unset):
            stock_transfer_rows = []
            for stock_transfer_rows_item_data in self.stock_transfer_rows:
                stock_transfer_rows_item = stock_transfer_rows_item_data.to_dict()
                stock_transfer_rows.append(stock_transfer_rows_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "stock_transfer_number": stock_transfer_number,
                "source_location_id": source_location_id,
                "target_location_id": target_location_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if status is not UNSET:
            field_dict["status"] = status
        if transfer_date is not UNSET:
            field_dict["transfer_date"] = transfer_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if stock_transfer_rows is not UNSET:
            field_dict["stock_transfer_rows"] = stock_transfer_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stock_transfer_row import StockTransferRow

        d = dict(src_dict)
        id = d.pop("id")

        stock_transfer_number = d.pop("stock_transfer_number")

        source_location_id = d.pop("source_location_id")

        target_location_id = d.pop("target_location_id")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        status = d.pop("status", UNSET)

        _transfer_date = d.pop("transfer_date", UNSET)
        transfer_date: datetime.datetime | Unset
        if isinstance(_transfer_date, Unset):
            transfer_date = UNSET
        else:
            transfer_date = isoparse(_transfer_date)

        def _parse_order_created_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                order_created_date_type_0 = isoparse(data)

                return order_created_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        order_created_date = _parse_order_created_date(
            d.pop("order_created_date", UNSET)
        )

        def _parse_expected_arrival_date(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expected_arrival_date_type_0 = isoparse(data)

                return expected_arrival_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        expected_arrival_date = _parse_expected_arrival_date(
            d.pop("expected_arrival_date", UNSET)
        )

        def _parse_additional_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        _stock_transfer_rows = d.pop("stock_transfer_rows", UNSET)
        stock_transfer_rows: list[StockTransferRow] | Unset = UNSET
        if _stock_transfer_rows is not UNSET:
            stock_transfer_rows = []
            for stock_transfer_rows_item_data in _stock_transfer_rows:
                stock_transfer_rows_item = StockTransferRow.from_dict(
                    stock_transfer_rows_item_data
                )

                stock_transfer_rows.append(stock_transfer_rows_item)

        stock_transfer = cls(
            id=id,
            stock_transfer_number=stock_transfer_number,
            source_location_id=source_location_id,
            target_location_id=target_location_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            status=status,
            transfer_date=transfer_date,
            order_created_date=order_created_date,
            expected_arrival_date=expected_arrival_date,
            additional_info=additional_info,
            stock_transfer_rows=stock_transfer_rows,
        )

        stock_transfer.additional_properties = d
        return stock_transfer

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
