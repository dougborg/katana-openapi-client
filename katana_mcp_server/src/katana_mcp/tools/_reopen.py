"""Close-state snapshots for the reopen → modify → restore pattern.

The composite ``correct_<entity>`` tools (``correct_manufacturing_order``,
``correct_sales_order``) edit records that have already reached a terminal
status (DONE / DELIVERED) without losing the original close-state metadata.

This module owns the **what to capture and replay** — it doesn't run any
API calls. The composite tools in ``foundation/corrections.py`` consume
these snapshots, build ``ActionSpec`` lists, and execute them via the
existing ``_modification_dispatch`` machinery.

State-machine quirks the snapshots paper over:

- **MO**: ``done_date`` can only be set once status is ``DONE``; combined
  status+date PATCH calls fail because validation runs *before* the status
  change is applied. After reverting, productions are auto-reversed by
  Katana, so re-creating them is part of the restore. ``MOProductionAdd``
  takes ``completed_quantity`` (singular create body field) but the
  persisted entity stores it as ``quantity``.
- **SO**: a DELIVERED SO can't be edited; reopening means deleting the
  fulfillments (which empties the 200 body — callers must use
  ``is_success`` instead of ``unwrap``) and patching status back to PENDING.
  Restore means re-creating each fulfillment with its original
  ``picked_date``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderProduction,
    ManufacturingOrderStatus,
    SalesOrder,
    SalesOrderFulfillment,
    SalesOrderStatus,
    UpdateSalesOrderStatus,
)

# ============================================================================
# Manufacturing order snapshots
# ============================================================================


# MO statuses where the record is treated as "closed" — entry conditions for
# ``correct_manufacturing_order``. PARTIALLY_COMPLETED is included because
# Katana can land an MO there when productions don't carry ``is_final=True``;
# the operator-perceived state is still "shipped, fix me".
MO_CLOSED_STATUSES: frozenset[str] = frozenset(
    {
        ManufacturingOrderStatus.DONE.value,
        ManufacturingOrderStatus.PARTIALLY_COMPLETED.value,
    }
)

# Status to revert to when reopening — clears the close-state and lets
# Katana auto-reverse the productions.
MO_REOPEN_STATUS: str = ManufacturingOrderStatus.IN_PROGRESS.value

# Status to restore to once edits and re-productions land.
MO_RESTORE_STATUS: str = ManufacturingOrderStatus.DONE.value


@dataclass(frozen=True)
class MOProductionSnapshot:
    """Restorable shape of a single production record on an MO.

    Captured by reading the persisted entity (``ManufacturingOrderProduction``);
    replayed via the create-production POST body (``completed_quantity``,
    ``completed_date``, ``serial_numbers``) plus a follow-up PATCH that sets
    ``production_date`` exactly. Two-step replay matches the operator-proven
    sequence in the original Shopify SP73000→SP73001 correction: Katana
    stamps the create with server-time, so the explicit PATCH is what
    actually backdates the production.
    """

    completed_quantity: float
    production_date: datetime | None
    serial_numbers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MOCloseState:
    """Snapshot of an MO's close-state metadata, captured before reopen."""

    status: str
    done_date: datetime | None
    productions: list[MOProductionSnapshot]


def _serial_numbers_to_strs(value: Any) -> list[str]:
    """Extract serial-number strings from an attrs ``list[SerialNumber]``.

    The persisted entity carries ``SerialNumber`` objects; the create-body
    field accepts a flat ``list[str]``. UNSET / None / missing
    ``serial_number`` field on an item all fall through to "skip".
    """
    items = unwrap_unset(value, None)
    if not items:
        return []
    out: list[str] = []
    for item in items:
        sn = unwrap_unset(getattr(item, "serial_number", UNSET), None)
        if isinstance(sn, str) and sn:
            out.append(sn)
    return out


def snapshot_mo_close_state(
    mo: ManufacturingOrder,
    productions: list[ManufacturingOrderProduction],
) -> MOCloseState:
    """Build an :class:`MOCloseState` from a fetched MO + its productions."""
    status_enum = unwrap_unset(mo.status, None)
    status = status_enum.value if status_enum is not None else ""
    done_date = unwrap_unset(mo.done_date, None)

    snapshots: list[MOProductionSnapshot] = []
    for prod in productions:
        qty = unwrap_unset(prod.quantity, None)
        if qty is None or qty <= 0:
            # Reverted/empty productions are skipped — only meaningful
            # production records get replayed.
            continue
        snapshots.append(
            MOProductionSnapshot(
                completed_quantity=float(qty),
                production_date=unwrap_unset(prod.production_date, None),
                serial_numbers=_serial_numbers_to_strs(prod.serial_numbers),
            )
        )

    return MOCloseState(status=status, done_date=done_date, productions=snapshots)


# ============================================================================
# Sales order snapshots
# ============================================================================


# SO statuses where the record is treated as "closed" — entry condition for
# ``correct_sales_order``.
SO_CLOSED_STATUSES: frozenset[str] = frozenset({SalesOrderStatus.DELIVERED.value})

# Status to revert to when reopening. Note this references
# ``UpdateSalesOrderStatus`` (the write enum) since ``PENDING`` is only a
# valid input — the persisted ``SalesOrderStatus`` enum doesn't include it.
# Fulfillments must be deleted first or Katana rejects the patch.
SO_REOPEN_STATUS: str = UpdateSalesOrderStatus.PENDING.value

# Status to restore to once edits and re-fulfillment land.
SO_RESTORE_STATUS: str = UpdateSalesOrderStatus.DELIVERED.value


@dataclass(frozen=True)
class SOFulfillmentRowSnapshot:
    """Restorable row inside a fulfillment — references an SO row + qty."""

    sales_order_row_id: int
    quantity: float


@dataclass(frozen=True)
class SOFulfillmentSnapshot:
    """Restorable shape of a single fulfillment on an SO.

    Captured before delete, replayed via the create-fulfillment POST body.
    SO row IDs are preserved across the reopen (we only patch row fields,
    never delete/add rows in ``correct_sales_order``), so the
    ``sales_order_row_id`` references stay valid.
    """

    status: str
    picked_date: datetime | None
    conversion_rate: float | None
    conversion_date: datetime | None
    tracking_number: str | None
    tracking_url: str | None
    tracking_carrier: str | None
    tracking_method: str | None
    rows: list[SOFulfillmentRowSnapshot] = field(default_factory=list)


@dataclass(frozen=True)
class SOCloseState:
    """Snapshot of an SO's close-state metadata, captured before reopen."""

    status: str
    picked_date: datetime | None
    delivery_date: datetime | None
    fulfillments: list[SOFulfillmentSnapshot]
    fulfillment_ids: list[int]


def _fulfillment_rows_from_attrs(value: Any) -> list[SOFulfillmentRowSnapshot]:
    """Extract row snapshots from an attrs ``list[SalesOrderFulfillmentRow]``."""
    items = unwrap_unset(value, None)
    if not items:
        return []
    out: list[SOFulfillmentRowSnapshot] = []
    for item in items:
        row_id = unwrap_unset(getattr(item, "sales_order_row_id", UNSET), None)
        qty = unwrap_unset(getattr(item, "quantity", UNSET), None)
        if not isinstance(row_id, int) or qty is None:
            continue
        out.append(
            SOFulfillmentRowSnapshot(sales_order_row_id=row_id, quantity=float(qty))
        )
    return out


def _fulfillment_snapshot(fulfillment: SalesOrderFulfillment) -> SOFulfillmentSnapshot:
    status_enum = unwrap_unset(fulfillment.status, None)
    status = status_enum.value if status_enum is not None else ""
    return SOFulfillmentSnapshot(
        status=status,
        picked_date=unwrap_unset(fulfillment.picked_date, None),
        conversion_rate=unwrap_unset(fulfillment.conversion_rate, None),
        conversion_date=unwrap_unset(fulfillment.conversion_date, None),
        tracking_number=unwrap_unset(fulfillment.tracking_number, None),
        tracking_url=unwrap_unset(fulfillment.tracking_url, None),
        tracking_carrier=unwrap_unset(fulfillment.tracking_carrier, None),
        tracking_method=unwrap_unset(fulfillment.tracking_method, None),
        rows=_fulfillment_rows_from_attrs(
            getattr(fulfillment, "sales_order_fulfillment_rows", UNSET)
        ),
    )


def snapshot_so_close_state(
    so: SalesOrder,
    fulfillments: list[SalesOrderFulfillment],
) -> SOCloseState:
    """Build an :class:`SOCloseState` from a fetched SO + its fulfillments."""
    status_enum = unwrap_unset(so.status, None)
    status = status_enum.value if status_enum is not None else ""
    return SOCloseState(
        status=status,
        picked_date=unwrap_unset(so.picked_date, None),
        delivery_date=unwrap_unset(so.delivery_date, None),
        fulfillments=[_fulfillment_snapshot(f) for f in fulfillments],
        fulfillment_ids=[f.id for f in fulfillments if isinstance(f.id, int)],
    )
