import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.webhook_event import WebhookEvent
from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookLogsExportRequest")


@_attrs_define
class WebhookLogsExportRequest:
    webhook_id: Unset | int = UNSET
    event: Unset | WebhookEvent = UNSET
    status_code: Unset | int = UNSET
    delivered: Unset | bool = UNSET
    created_at_min: Unset | datetime.datetime = UNSET
    created_at_max: Unset | datetime.datetime = UNSET

    def to_dict(self) -> dict[str, Any]:
        webhook_id = self.webhook_id

        event: Unset | str = UNSET
        if not isinstance(self.event, Unset):
            event = self.event.value

        status_code = self.status_code

        delivered = self.delivered

        created_at_min: Unset | str = UNSET
        if not isinstance(self.created_at_min, Unset):
            created_at_min = self.created_at_min.isoformat()

        created_at_max: Unset | str = UNSET
        if not isinstance(self.created_at_max, Unset):
            created_at_max = self.created_at_max.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if webhook_id is not UNSET:
            field_dict["webhook_id"] = webhook_id
        if event is not UNSET:
            field_dict["event"] = event
        if status_code is not UNSET:
            field_dict["status_code"] = status_code
        if delivered is not UNSET:
            field_dict["delivered"] = delivered
        if created_at_min is not UNSET:
            field_dict["created_at_min"] = created_at_min
        if created_at_max is not UNSET:
            field_dict["created_at_max"] = created_at_max

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        webhook_id = d.pop("webhook_id", UNSET)

        _event = d.pop("event", UNSET)
        event: Unset | WebhookEvent
        if isinstance(_event, Unset):
            event = UNSET
        else:
            event = WebhookEvent(_event)

        status_code = d.pop("status_code", UNSET)

        delivered = d.pop("delivered", UNSET)

        _created_at_min = d.pop("created_at_min", UNSET)
        created_at_min: Unset | datetime.datetime
        if isinstance(_created_at_min, Unset):
            created_at_min = UNSET
        else:
            created_at_min = isoparse(_created_at_min)

        _created_at_max = d.pop("created_at_max", UNSET)
        created_at_max: Unset | datetime.datetime
        if isinstance(_created_at_max, Unset):
            created_at_max = UNSET
        else:
            created_at_max = isoparse(_created_at_max)

        webhook_logs_export_request = cls(
            webhook_id=webhook_id,
            event=event,
            status_code=status_code,
            delivered=delivered,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
        )

        return webhook_logs_export_request
