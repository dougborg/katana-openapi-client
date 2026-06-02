from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="SearchComparator")


@_attrs_define
class SearchComparator:
    """Operator object for a search ``where`` predicate. Supply this only
    when you need something other than equality — for equality, pass a
    bare ``SearchScalarValue`` instead. Only the operators listed below
    are accepted; the server rejects any other key with 422.
    """

    neq: bool | float | None | str | Unset = UNSET
    gt: bool | float | None | str | Unset = UNSET
    gte: bool | float | None | str | Unset = UNSET
    lt: bool | float | None | str | Unset = UNSET
    lte: bool | float | None | str | Unset = UNSET
    inq: list[bool | float | None | str] | Unset = UNSET
    nin: list[bool | float | None | str] | Unset = UNSET
    between: list[bool | float | None | str] | Unset = UNSET
    like: str | Unset = UNSET
    ilike: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        neq: bool | float | None | str | Unset
        if isinstance(self.neq, Unset):
            neq = UNSET
        else:
            neq = self.neq

        gt: bool | float | None | str | Unset
        if isinstance(self.gt, Unset):
            gt = UNSET
        else:
            gt = self.gt

        gte: bool | float | None | str | Unset
        if isinstance(self.gte, Unset):
            gte = UNSET
        else:
            gte = self.gte

        lt: bool | float | None | str | Unset
        if isinstance(self.lt, Unset):
            lt = UNSET
        else:
            lt = self.lt

        lte: bool | float | None | str | Unset
        if isinstance(self.lte, Unset):
            lte = UNSET
        else:
            lte = self.lte

        inq: list[bool | float | None | str] | Unset = UNSET
        if not isinstance(self.inq, Unset):
            inq = []
            for inq_item_data in self.inq:
                inq_item: bool | float | None | str
                inq_item = inq_item_data
                inq.append(inq_item)

        nin: list[bool | float | None | str] | Unset = UNSET
        if not isinstance(self.nin, Unset):
            nin = []
            for nin_item_data in self.nin:
                nin_item: bool | float | None | str
                nin_item = nin_item_data
                nin.append(nin_item)

        between: list[bool | float | None | str] | Unset = UNSET
        if not isinstance(self.between, Unset):
            between = []
            for between_item_data in self.between:
                between_item: bool | float | None | str
                between_item = between_item_data
                between.append(between_item)

        like = self.like

        ilike = self.ilike

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if neq is not UNSET:
            field_dict["neq"] = neq
        if gt is not UNSET:
            field_dict["gt"] = gt
        if gte is not UNSET:
            field_dict["gte"] = gte
        if lt is not UNSET:
            field_dict["lt"] = lt
        if lte is not UNSET:
            field_dict["lte"] = lte
        if inq is not UNSET:
            field_dict["inq"] = inq
        if nin is not UNSET:
            field_dict["nin"] = nin
        if between is not UNSET:
            field_dict["between"] = between
        if like is not UNSET:
            field_dict["like"] = like
        if ilike is not UNSET:
            field_dict["ilike"] = ilike

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_neq(data: object) -> bool | float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | float | None | str | Unset, data)

        neq = _parse_neq(d.pop("neq", UNSET))

        def _parse_gt(data: object) -> bool | float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | float | None | str | Unset, data)

        gt = _parse_gt(d.pop("gt", UNSET))

        def _parse_gte(data: object) -> bool | float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | float | None | str | Unset, data)

        gte = _parse_gte(d.pop("gte", UNSET))

        def _parse_lt(data: object) -> bool | float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | float | None | str | Unset, data)

        lt = _parse_lt(d.pop("lt", UNSET))

        def _parse_lte(data: object) -> bool | float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | float | None | str | Unset, data)

        lte = _parse_lte(d.pop("lte", UNSET))

        _inq = d.pop("inq", UNSET)
        inq: list[bool | float | None | str] | Unset = UNSET
        if _inq is not UNSET:
            inq = []
            for inq_item_data in _inq:

                def _parse_inq_item(data: object) -> bool | float | None | str:
                    if data is None:
                        return data
                    return cast(bool | float | None | str, data)

                inq_item = _parse_inq_item(inq_item_data)

                inq.append(inq_item)

        _nin = d.pop("nin", UNSET)
        nin: list[bool | float | None | str] | Unset = UNSET
        if _nin is not UNSET:
            nin = []
            for nin_item_data in _nin:

                def _parse_nin_item(data: object) -> bool | float | None | str:
                    if data is None:
                        return data
                    return cast(bool | float | None | str, data)

                nin_item = _parse_nin_item(nin_item_data)

                nin.append(nin_item)

        _between = d.pop("between", UNSET)
        between: list[bool | float | None | str] | Unset = UNSET
        if _between is not UNSET:
            between = []
            for between_item_data in _between:

                def _parse_between_item(data: object) -> bool | float | None | str:
                    if data is None:
                        return data
                    return cast(bool | float | None | str, data)

                between_item = _parse_between_item(between_item_data)

                between.append(between_item)

        like = d.pop("like", UNSET)

        ilike = d.pop("ilike", UNSET)

        search_comparator = cls(
            neq=neq,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            inq=inq,
            nin=nin,
            between=between,
            like=like,
            ilike=ilike,
        )

        return search_comparator
