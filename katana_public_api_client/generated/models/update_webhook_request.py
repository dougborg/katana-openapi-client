from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.webhook_event import WebhookEvent
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateWebhookRequest")


@_attrs_define
class UpdateWebhookRequest:
    url: str
    subscribed_events: list[WebhookEvent]
    enabled: Unset | bool = UNSET
    description: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        subscribed_events = []
        for subscribed_events_item_data in self.subscribed_events:
            subscribed_events_item = subscribed_events_item_data.value
            subscribed_events.append(subscribed_events_item)

        enabled = self.enabled

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "url": url,
                "subscribed_events": subscribed_events,
            }
        )
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        subscribed_events = []
        _subscribed_events = d.pop("subscribed_events")
        for subscribed_events_item_data in _subscribed_events:
            subscribed_events_item = WebhookEvent(subscribed_events_item_data)

            subscribed_events.append(subscribed_events_item)

        enabled = d.pop("enabled", UNSET)

        description = d.pop("description", UNSET)

        update_webhook_request = cls(
            url=url,
            subscribed_events=subscribed_events,
            enabled=enabled,
            description=description,
        )

        return update_webhook_request
