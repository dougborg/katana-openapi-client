from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.webhook_event import WebhookEvent

if TYPE_CHECKING:
    from ..models.webhook_event_payload_object import WebhookEventPayloadObject


T = TypeVar("T", bound="WebhookEventPayload")


@_attrs_define
class WebhookEventPayload:
    """Webhook event payload structure sent to registered webhook endpoints.
    Contains information about the event and the affected resource.

        Example:
            {'resource_type': 'sales_order', 'action': 'sales_order.delivered', 'webhook_id': 123, 'object': {'id': '12345',
                'status': 'DELIVERED', 'href': 'https://api.katanamrp.com/v1/sales_orders/12345'}}
    """

    resource_type: str
    action: WebhookEvent
    webhook_id: int
    object_: "WebhookEventPayloadObject"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource_type = self.resource_type

        action = self.action.value

        webhook_id = self.webhook_id

        object_ = self.object_.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "resource_type": resource_type,
                "action": action,
                "webhook_id": webhook_id,
                "object": object_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_event_payload_object import WebhookEventPayloadObject

        d = dict(src_dict)
        resource_type = d.pop("resource_type")

        action = WebhookEvent(d.pop("action"))

        webhook_id = d.pop("webhook_id")

        object_ = WebhookEventPayloadObject.from_dict(d.pop("object"))

        webhook_event_payload = cls(
            resource_type=resource_type,
            action=action,
            webhook_id=webhook_id,
            object_=object_,
        )

        webhook_event_payload.additional_properties = d
        return webhook_event_payload

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
