from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.custom_field_entity_type import CustomFieldEntityType
from ..models.custom_field_type import CustomFieldType

if TYPE_CHECKING:
    from ..models.custom_field_options import CustomFieldOptions


T = TypeVar("T", bound="CustomFieldDefinition")


@_attrs_define
class CustomFieldDefinition:
    """A partner-defined custom field that callers register once via
    ``POST /custom_field_definitions`` and then attach values for on a
    sales order (or sales order row) through that resource's
    ``custom_fields`` property, keyed by this definition's ``id``
    (UUID).

    Scope today: ``entity_type`` is limited to ``SalesOrder`` /
    ``SalesOrderRow`` (see ``CustomFieldEntityType``). A factory may
    hold at most **50 definitions**. ``field_type``, ``entity_type``,
    and ``source`` are **immutable** after creation; only ``label``,
    ``description``, and ``options`` may be updated.

        Example:
            {'id': '0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef', 'label': 'Channel', 'field_type': 'shortText', 'entity_type':
                'SalesOrder', 'source': 'your-integration', 'description': 'Customer-facing sales channel classification',
                'options': None, 'created_at': '2026-05-14T10:00:00Z', 'updated_at': '2026-05-14T10:00:00Z', 'deleted_at': None}
    """

    id: UUID
    label: str
    field_type: CustomFieldType
    entity_type: CustomFieldEntityType
    source: str
    description: None | str | Unset = UNSET
    options: CustomFieldOptions | None | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.custom_field_options import CustomFieldOptions

        id = str(self.id)

        label = self.label

        field_type = self.field_type.value

        entity_type = self.entity_type.value

        source = self.source

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, CustomFieldOptions):
            options = self.options.to_dict()
        else:
            options = self.options

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

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "label": label,
                "field_type": field_type,
                "entity_type": entity_type,
                "source": source,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if options is not UNSET:
            field_dict["options"] = options
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field_options import CustomFieldOptions

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        label = d.pop("label")

        field_type = CustomFieldType(d.pop("field_type"))

        entity_type = CustomFieldEntityType(d.pop("entity_type"))

        source = d.pop("source")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_options(data: object) -> CustomFieldOptions | None | Unset:
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
                options_type_0 = CustomFieldOptions.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CustomFieldOptions | None | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = datetime.datetime.fromisoformat(_updated_at)

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

        custom_field_definition = cls(
            id=id,
            label=label,
            field_type=field_type,
            entity_type=entity_type,
            source=source,
            description=description,
            options=options,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        return custom_field_definition
