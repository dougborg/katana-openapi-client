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

    Attributes:
        id (int): Unique identifier for the stock transfer
        stock_transfer_number (str): Human-readable reference number for tracking the transfer
        source_location_id (int): ID of the source location where stock is being transferred from
        target_location_id (int): ID of the destination location where stock is being transferred to
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
        status (Union[Unset, StockTransferStatus]): Current status of the stock transfer workflow
        transfer_date (Union[Unset, datetime.datetime]): Date and time when the transfer was executed
        additional_info (Union[None, Unset, str]): Optional notes or comments about the transfer purpose
        stock_transfer_rows (Union[Unset, list['StockTransferRow']]): Line items detailing the products and quantities
            being transferred
    """

    id: int
    stock_transfer_number: str
    source_location_id: int
    target_location_id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    status: Unset | StockTransferStatus = UNSET
    transfer_date: Unset | datetime.datetime = UNSET
    additional_info: None | Unset | str = UNSET
    stock_transfer_rows: Unset | list["StockTransferRow"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        stock_transfer_number = self.stock_transfer_number

        source_location_id = self.source_location_id

        target_location_id = self.target_location_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        transfer_date: Unset | str = UNSET
        if not isinstance(self.transfer_date, Unset):
            transfer_date = self.transfer_date.isoformat()

        additional_info: None | Unset | str
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        stock_transfer_rows: Unset | list[dict[str, Any]] = UNSET
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
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        _status = d.pop("status", UNSET)
        status: Unset | StockTransferStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = StockTransferStatus(_status)

        _transfer_date = d.pop("transfer_date", UNSET)
        transfer_date: Unset | datetime.datetime
        if isinstance(_transfer_date, Unset):
            transfer_date = UNSET
        else:
            transfer_date = isoparse(_transfer_date)

        def _parse_additional_info(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        stock_transfer_rows = []
        _stock_transfer_rows = d.pop("stock_transfer_rows", UNSET)
        for stock_transfer_rows_item_data in _stock_transfer_rows or []:
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
