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
from ..models.stock_transfer_status import StockTransferStatus

if TYPE_CHECKING:
    from ..models.stock_transfer_row import StockTransferRow


T = TypeVar("T", bound="StockTransfer")


@_attrs_define
class StockTransfer:
    """Inventory transfer record for moving stock between different warehouse locations or facilities

    Example:
        {'id': 3001, 'stock_transfer_number': 'ST-2024-001', 'source_location_id': 1, 'target_location_id': 2, 'status':
            'COMPLETED', 'transfer_date': '2024-01-15T16:00:00.000Z', 'additional_info': 'Rebalancing inventory between
            warehouses', 'stock_transfer_rows': [{'id': 4001, 'variant_id': 2001, 'quantity': 50, 'batch_transactions':
            [{'batch_id': 5001, 'quantity': 30}, {'batch_id': 5002, 'quantity': 20}]}], 'created_at':
            '2024-01-15T16:00:00.000Z', 'updated_at': '2024-01-15T16:00:00.000Z', 'deleted_at': None}
    """

    id: int
    stock_transfer_number: str
    source_location_id: int
    target_location_id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    status: StockTransferStatus | Unset = UNSET
    transfer_date: datetime.datetime | Unset = UNSET
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

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        transfer_date: str | Unset = UNSET
        if not isinstance(self.transfer_date, Unset):
            transfer_date = self.transfer_date.isoformat()

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

        _status = d.pop("status", UNSET)
        status: StockTransferStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = StockTransferStatus(_status)

        _transfer_date = d.pop("transfer_date", UNSET)
        transfer_date: datetime.datetime | Unset
        if isinstance(_transfer_date, Unset):
            transfer_date = UNSET
        else:
            transfer_date = isoparse(_transfer_date)

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
