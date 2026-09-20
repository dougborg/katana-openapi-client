from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.customer_search_filter_and_item import CustomerSearchFilterAndItem
    from ..models.customer_search_filter_or_item import CustomerSearchFilterOrItem
    from ..models.search_comparator import SearchComparator


T = TypeVar("T", bound="CustomerSearchFilter")


@_attrs_define
class CustomerSearchFilter:
    """Filter clause for ``POST /customers/search``. Only the fields listed
    here may appear; unknown fields are rejected with 422. Custom field
    values are addressable via ``custom_fields.<uuid>`` keys.
    """

    and_: list[CustomerSearchFilterAndItem] | Unset = UNSET
    or_: list[CustomerSearchFilterOrItem] | Unset = UNSET
    category: bool | float | SearchComparator | str | Unset | None = UNSET
    comment: bool | float | SearchComparator | str | Unset | None = UNSET
    company: bool | float | SearchComparator | str | Unset | None = UNSET
    created_at: bool | float | SearchComparator | str | Unset | None = UNSET
    currency: bool | float | SearchComparator | str | Unset | None = UNSET
    default_billing_id: bool | float | SearchComparator | str | Unset | None = UNSET
    default_shipping_id: bool | float | SearchComparator | str | Unset | None = UNSET
    email: bool | float | SearchComparator | str | Unset | None = UNSET
    first_name: bool | float | SearchComparator | str | Unset | None = UNSET
    id: bool | float | SearchComparator | str | Unset | None = UNSET
    last_name: bool | float | SearchComparator | str | Unset | None = UNSET
    name: bool | float | SearchComparator | str | Unset | None = UNSET
    phone: bool | float | SearchComparator | str | Unset | None = UNSET
    reference_id: bool | float | SearchComparator | str | Unset | None = UNSET
    updated_at: bool | float | SearchComparator | str | Unset | None = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.search_comparator import SearchComparator

        and_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.and_, Unset):
            and_ = []
            for and_item_data in self.and_:
                and_item = and_item_data.to_dict()
                and_.append(and_item)

        or_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.or_, Unset):
            or_ = []
            for or_item_data in self.or_:
                or_item = or_item_data.to_dict()
                or_.append(or_item)

        category: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.category, Unset):
            category = UNSET
        elif isinstance(self.category, SearchComparator):
            category = self.category.to_dict()
        else:
            category = self.category

        comment: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.comment, Unset):
            comment = UNSET
        elif isinstance(self.comment, SearchComparator):
            comment = self.comment.to_dict()
        else:
            comment = self.comment

        company: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.company, Unset):
            company = UNSET
        elif isinstance(self.company, SearchComparator):
            company = self.company.to_dict()
        else:
            company = self.company

        created_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, SearchComparator):
            created_at = self.created_at.to_dict()
        else:
            created_at = self.created_at

        currency: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.currency, Unset):
            currency = UNSET
        elif isinstance(self.currency, SearchComparator):
            currency = self.currency.to_dict()
        else:
            currency = self.currency

        default_billing_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.default_billing_id, Unset):
            default_billing_id = UNSET
        elif isinstance(self.default_billing_id, SearchComparator):
            default_billing_id = self.default_billing_id.to_dict()
        else:
            default_billing_id = self.default_billing_id

        default_shipping_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.default_shipping_id, Unset):
            default_shipping_id = UNSET
        elif isinstance(self.default_shipping_id, SearchComparator):
            default_shipping_id = self.default_shipping_id.to_dict()
        else:
            default_shipping_id = self.default_shipping_id

        email: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.email, Unset):
            email = UNSET
        elif isinstance(self.email, SearchComparator):
            email = self.email.to_dict()
        else:
            email = self.email

        first_name: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        elif isinstance(self.first_name, SearchComparator):
            first_name = self.first_name.to_dict()
        else:
            first_name = self.first_name

        id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, SearchComparator):
            id = self.id.to_dict()
        else:
            id = self.id

        last_name: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        elif isinstance(self.last_name, SearchComparator):
            last_name = self.last_name.to_dict()
        else:
            last_name = self.last_name

        name: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.name, Unset):
            name = UNSET
        elif isinstance(self.name, SearchComparator):
            name = self.name.to_dict()
        else:
            name = self.name

        phone: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.phone, Unset):
            phone = UNSET
        elif isinstance(self.phone, SearchComparator):
            phone = self.phone.to_dict()
        else:
            phone = self.phone

        reference_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.reference_id, Unset):
            reference_id = UNSET
        elif isinstance(self.reference_id, SearchComparator):
            reference_id = self.reference_id.to_dict()
        else:
            reference_id = self.reference_id

        updated_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, SearchComparator):
            updated_at = self.updated_at.to_dict()
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if and_ is not UNSET:
            field_dict["and"] = and_
        if or_ is not UNSET:
            field_dict["or"] = or_
        if category is not UNSET:
            field_dict["category"] = category
        if comment is not UNSET:
            field_dict["comment"] = comment
        if company is not UNSET:
            field_dict["company"] = company
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if currency is not UNSET:
            field_dict["currency"] = currency
        if default_billing_id is not UNSET:
            field_dict["default_billing_id"] = default_billing_id
        if default_shipping_id is not UNSET:
            field_dict["default_shipping_id"] = default_shipping_id
        if email is not UNSET:
            field_dict["email"] = email
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if id is not UNSET:
            field_dict["id"] = id
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if name is not UNSET:
            field_dict["name"] = name
        if phone is not UNSET:
            field_dict["phone"] = phone
        if reference_id is not UNSET:
            field_dict["reference_id"] = reference_id
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer_search_filter_and_item import (
            CustomerSearchFilterAndItem,
        )
        from ..models.customer_search_filter_or_item import (
            CustomerSearchFilterOrItem,
        )
        from ..models.search_comparator import SearchComparator

        d = dict(src_dict)
        _and_ = d.pop("and", UNSET)
        and_: list[CustomerSearchFilterAndItem] | Unset = UNSET
        if _and_ is not UNSET:
            and_ = []
            for and_item_data in _and_:
                and_item = CustomerSearchFilterAndItem.from_dict(
                    cast(Mapping[str, Any], and_item_data)
                )

                and_.append(and_item)

        _or_ = d.pop("or", UNSET)
        or_: list[CustomerSearchFilterOrItem] | Unset = UNSET
        if _or_ is not UNSET:
            or_ = []
            for or_item_data in _or_:
                or_item = CustomerSearchFilterOrItem.from_dict(
                    cast(Mapping[str, Any], or_item_data)
                )

                or_.append(or_item)

        def _parse_category(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        category = _parse_category(d.pop("category", UNSET))

        def _parse_comment(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_company(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_created_at(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_currency(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_default_billing_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        default_billing_id = _parse_default_billing_id(
            d.pop("default_billing_id", UNSET)
        )

        def _parse_default_shipping_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        default_shipping_id = _parse_default_shipping_id(
            d.pop("default_shipping_id", UNSET)
        )

        def _parse_email(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_first_name(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_last_name(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_name(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_phone(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_reference_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        reference_id = _parse_reference_id(d.pop("reference_id", UNSET))

        def _parse_updated_at(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        customer_search_filter = cls(
            and_=and_,
            or_=or_,
            category=category,
            comment=comment,
            company=company,
            created_at=created_at,
            currency=currency,
            default_billing_id=default_billing_id,
            default_shipping_id=default_shipping_id,
            email=email,
            first_name=first_name,
            id=id,
            last_name=last_name,
            name=name,
            phone=phone,
            reference_id=reference_id,
            updated_at=updated_at,
        )

        customer_search_filter.additional_properties = d
        return customer_search_filter

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
