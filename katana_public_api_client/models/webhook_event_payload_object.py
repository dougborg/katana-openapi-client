from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="WebhookEventPayloadObject")


@_attrs_define
class WebhookEventPayloadObject:
    """The object affected by this event. Contains id, status and href to retrieve the resource.

    Notes:
    - href property doesn't apply to deleted events (e.g., sales_order.deleted, product_recipe_row.deleted)
    - status field appears in examples but is not documented in official Katana API docs

        Attributes:
            id (str): Unique identifier of the affected resource Example: 12345.
            status (str): Current status of the affected resource.
                Note: This field appears in webhook payload examples but is not documented
                in the official Katana API documentation. The actual values and format
                may vary by resource type and may not be reliable for programmatic use. Example: DELIVERED.
            href (Union[Unset, str]): API endpoint URL to retrieve the full resource (not available for deleted events)
                Example: https://api.katanamrp.com/v1/sales_orders/12345.
    """

    id: str
    status: str
    href: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status = self.status

        href = self.href

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "status": status,
            }
        )
        if href is not UNSET:
            field_dict["href"] = href

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        status = d.pop("status")

        href = d.pop("href", UNSET)

        webhook_event_payload_object = cls(
            id=id,
            status=status,
            href=href,
        )

        webhook_event_payload_object.additional_properties = d
        return webhook_event_payload_object

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
