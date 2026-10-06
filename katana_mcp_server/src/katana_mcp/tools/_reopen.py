"""Close-state snapshots for the reopen → modify → restore pattern.

The composite ``correct_<entity>`` tools (``correct_manufacturing_order``,
``correct_sales_order``, ``correct_purchase_order``) edit records that
have already reached a terminal status (DONE / DELIVERED / RECEIVED)
without losing the original close-state metadata.

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
- **PO**: a RECEIVED PO has rows whose ``quantity`` / ``variant_id`` /
  ``price_per_unit`` are immutable while ``received_date`` is non-null.
  Reverting status to ``NOT_RECEIVED`` (PATCH ``/purchase_orders/{id}``)
  undoes every receipt at once, returns all rows to ``default_group_id``,
  merges rows that are identical apart from quantity (same variant, price,
  tax rate, arrival date and location; the lowest id survives) and
  detaches additional cost rows from their groups; it is refused (422)
  while the PO is PARTIALLY_RECEIVED. Each ``POST /purchase_order_receive``
  call records one receipt group (``group_id``) and a partial quantity
  splits the row, keeping the original id on the open remnant. The
  correction therefore snapshots every row with its group, rebuilds the
  row structure after the revert and replays one receive call per original
  group (pinned live by ``tests/integration/test_po_receipt_groups_live.py``).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderProduction,
    ManufacturingOrderStatus,
    PurchaseOrderAdditionalCostRow,
    PurchaseOrderStatus,
    RegularPurchaseOrder,
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

    ``serial_numbers`` carries the integer ``SerialNumber.id`` values
    captured from the prior production — the production POST body wants
    pre-existing SN IDs (Katana silently drops unknown IDs, so capturing
    the ID rather than the human-readable serial string is what allows
    the restore to actually re-attach the original serials).
    """

    completed_quantity: float
    production_date: datetime | None
    serial_numbers: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class MOCloseState:
    """Snapshot of an MO's close-state metadata, captured before reopen."""

    status: str
    done_date: datetime | None
    productions: list[MOProductionSnapshot]


def _serial_numbers_to_ids(value: Any) -> list[int]:
    """Extract integer ``SerialNumber.id`` values from an attrs
    ``list[SerialNumber]``.

    The persisted entity carries ``SerialNumber`` objects; the create-body
    field accepts a flat ``list[int]`` of pre-existing SN IDs. UNSET /
    None / missing ``id`` field on an item all fall through to "skip".
    Spec drift fix in #790: the serial-number wire shape is integers, not
    strings — Katana silently drops unknown IDs (and silently drops every
    string that was previously passed through here).
    """
    items = unwrap_unset(value, None)
    if not items:
        return []
    out: list[int] = []
    for item in items:
        sn_id = unwrap_unset(getattr(item, "id", UNSET), None)
        if isinstance(sn_id, int):
            out.append(sn_id)
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
                serial_numbers=_serial_numbers_to_ids(prod.serial_numbers),
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


# ============================================================================
# Purchase order snapshots
# ============================================================================


# PO statuses where the record is treated as "closed" — entry conditions for
# ``correct_purchase_order``. PARTIALLY_RECEIVED is included alongside
# RECEIVED because partially-received POs have at least one row whose
# ``received_date`` is non-null, and that row is immutable until the PO is
# reverted to NOT_RECEIVED.
PO_CLOSED_STATUSES: frozenset[str] = frozenset(
    {
        PurchaseOrderStatus.RECEIVED.value,
        PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
    }
)

# Status to revert to when reopening — clears each row's ``received_date``
# so quantity / variant_id / price_per_unit become editable again. Per the
# OpenAPI spec on /purchase_order_receive: "Reverting the receive must also
# be done through that endpoint" (PATCH /purchase_orders/{id}).
PO_REOPEN_STATUS: str = PurchaseOrderStatus.NOT_RECEIVED.value

# Status to restore to once edits and re-receipt land. The receive endpoint
# auto-promotes to RECEIVED when every row is fully received, so this is
# only used as a target string for diff display, not for an explicit PATCH.
PO_RESTORE_STATUS: str = PurchaseOrderStatus.RECEIVED.value

# The row fields Katana compares when its revert merges rows: rows of one
# variant collapse into a single row only when all of these match (verified
# live: a different unit price or arrival date keeps the rows apart).
PORowMergeKey = tuple[int | None, float | None, int | None, datetime | None, int | None]


@dataclass(frozen=True)
class PORowBatchSnapshot:
    """Restorable shape of one batch transaction within a row receipt.

    Mirrors :class:`PurchaseOrderRowBatchTransactionsItem` on the wire.
    Replayed on the re-receive POST so batch-tracked materials land back
    on the original batch records. ``batch_id`` is ``None`` for the
    placeholder transaction Katana writes when a batch-tracked row is
    received without explicit batches; those are not replayed.
    """

    batch_id: int | None
    quantity: float


@dataclass(frozen=True)
class PORowSnapshot:
    """One purchase order row as it stood before the revert.

    Received rows (``received_date`` set) are replayed into their receipt
    group; open rows on a PARTIALLY_RECEIVED order are received temporarily
    so the revert is allowed, then left open again. The pricing, tax,
    arrival and location fields are what the revert's merge compares and
    what a re-created row needs to carry.
    """

    row_id: int
    variant_id: int | None
    quantity: float
    price_per_unit: float | None
    tax_rate_id: int | None
    purchase_uom: str | None
    purchase_uom_conversion_rate: float | None
    currency: str | None
    conversion_rate: float | None
    arrival_date: datetime | None
    location_id: int | None
    received_date: datetime | None
    group_id: int | None
    batch_transactions: tuple[PORowBatchSnapshot, ...] = ()

    @property
    def is_received(self) -> bool:
        return self.received_date is not None

    @property
    def merge_key(self) -> PORowMergeKey:
        """Rows sharing this key are merged into one by the revert."""
        return (
            self.variant_id,
            self.price_per_unit,
            self.tax_rate_id,
            self.arrival_date,
            self.location_id,
        )


@dataclass(frozen=True)
class POCostRowSnapshot:
    """An additional cost row attached to a receipt group.

    The revert moves these to the order's default group and the replay
    does not move them back, so the correction re-creates each one on the
    rebuilt group and deletes the original.
    """

    cost_row_id: int
    group_id: int
    additional_cost_id: int
    tax_rate_id: int
    price: float
    distribution_method: str | None
    reference: str | None
    currency: str | None = None
    currency_conversion_rate: float | None = None


@dataclass(frozen=True)
class POReceiptGroup:
    """One original receipt: the rows received in a single call."""

    group_id: int | None
    received_date: datetime
    rows: tuple[PORowSnapshot, ...]


@dataclass(frozen=True)
class POCloseState:
    """Snapshot of a PO's close-state metadata, captured before reopen.

    Receipt is the close-state: per-row ``received_date``, quantity and
    batch transactions, grouped by receipt group. Status is captured for
    round-tripping (so a PARTIALLY_RECEIVED PO isn't silently promoted to
    RECEIVED). Cost rows attached to receipt groups are captured because
    the revert detaches them.
    """

    status: str
    rows: tuple[PORowSnapshot, ...] = ()
    cost_rows: tuple[POCostRowSnapshot, ...] = ()
    # Cost rows on the receipt groups that lacked a field needed to
    # re-create them; the revert still detaches them, so they are reported.
    skipped_cost_row_ids: tuple[int, ...] = ()

    @property
    def received_rows(self) -> list[PORowSnapshot]:
        return [r for r in self.rows if r.is_received]

    @property
    def open_rows(self) -> list[PORowSnapshot]:
        return [r for r in self.rows if not r.is_received]

    def row(self, row_id: int) -> PORowSnapshot | None:
        return next((r for r in self.rows if r.row_id == row_id), None)

    def receipt_groups(self) -> list[POReceiptGroup]:
        """Received rows grouped by ``group_id``, oldest group first.

        Rows without a ``group_id`` fall back to one group per distinct
        ``received_date`` so separate receipts are never collapsed into one
        call. A group's date is its earliest row date; rows keep their own
        dates in the replay.
        """
        by_group: dict[object, list[PORowSnapshot]] = {}
        for row in self.received_rows:
            key: object = (
                ("group", row.group_id)
                if row.group_id is not None
                else ("date", row.received_date)
            )
            by_group.setdefault(key, []).append(row)
        groups = [
            POReceiptGroup(
                group_id=rows[0].group_id,
                received_date=min(r.received_date for r in rows if r.received_date),
                rows=tuple(rows),
            )
            for rows in by_group.values()
        ]
        return sorted(groups, key=lambda g: (g.received_date, g.group_id or 0))

    def predicted_merges(self) -> list[list[PORowSnapshot]]:
        """Rows the revert will merge, one list per merge key, lowest id first.

        Katana keeps the lowest row id of a merged set. Singletons are
        included so callers can treat every captured row uniformly.
        """
        by_key: dict[PORowMergeKey, list[PORowSnapshot]] = {}
        for row in sorted(self.rows, key=lambda r: r.row_id):
            by_key.setdefault(row.merge_key, []).append(row)
        return list(by_key.values())

    def cost_rows_for_group(self, group_id: int | None) -> list[POCostRowSnapshot]:
        if group_id is None:
            return []
        return [c for c in self.cost_rows if c.group_id == group_id]


def _batch_transactions_from_attrs(value: Any) -> tuple[PORowBatchSnapshot, ...]:
    """Extract batch-transaction snapshots from the persisted entity."""
    items = unwrap_unset(value, None)
    if not items:
        return ()
    out: list[PORowBatchSnapshot] = []
    for item in items:
        qty = unwrap_unset(getattr(item, "quantity", UNSET), None)
        batch_id = unwrap_unset(getattr(item, "batch_id", UNSET), None)
        if qty is None:
            continue
        out.append(
            PORowBatchSnapshot(
                batch_id=batch_id if isinstance(batch_id, int) else None,
                quantity=float(qty),
            )
        )
    return tuple(out)


def _optional_int(value: Any) -> int | None:
    value = unwrap_unset(value, None)
    return value if isinstance(value, int) else None


def _optional_float(value: Any) -> float | None:
    value = unwrap_unset(value, None)
    return float(value) if isinstance(value, int | float) else None


def _optional_str(value: Any) -> str | None:
    value = unwrap_unset(value, None)
    return value if isinstance(value, str) else None


def snapshot_po_row(row: Any) -> PORowSnapshot | None:
    """Capture one ``PurchaseOrderRow``; ``None`` for deleted rows and rows
    without id or quantity."""
    qty = unwrap_unset(getattr(row, "quantity", UNSET), None)
    row_id = unwrap_unset(getattr(row, "id", UNSET), None)
    if qty is None or qty <= 0 or not isinstance(row_id, int):
        return None
    if unwrap_unset(getattr(row, "deleted_at", UNSET), None) is not None:
        return None
    return PORowSnapshot(
        row_id=row_id,
        variant_id=_optional_int(getattr(row, "variant_id", UNSET)),
        quantity=float(qty),
        price_per_unit=_optional_float(getattr(row, "price_per_unit", UNSET)),
        tax_rate_id=_optional_int(getattr(row, "tax_rate_id", UNSET)),
        purchase_uom=_optional_str(getattr(row, "purchase_uom", UNSET)),
        purchase_uom_conversion_rate=_optional_float(
            getattr(row, "purchase_uom_conversion_rate", UNSET)
        ),
        currency=_optional_str(getattr(row, "currency", UNSET)),
        conversion_rate=_optional_float(getattr(row, "conversion_rate", UNSET)),
        arrival_date=unwrap_unset(getattr(row, "arrival_date", UNSET), None),
        location_id=_optional_int(getattr(row, "location_id", UNSET)),
        received_date=unwrap_unset(getattr(row, "received_date", UNSET), None),
        group_id=_optional_int(getattr(row, "group_id", UNSET)),
        batch_transactions=_batch_transactions_from_attrs(
            getattr(row, "batch_transactions", UNSET)
        ),
    )


def snapshot_po_cost_row(
    cost_row: PurchaseOrderAdditionalCostRow,
) -> POCostRowSnapshot | None:
    """Capture one additional cost row; ``None`` when a required field is missing."""
    group_id = _optional_int(cost_row.group_id)
    additional_cost_id = _optional_int(cost_row.additional_cost_id)
    tax_rate_id = _optional_int(cost_row.tax_rate_id)
    price = _optional_float(cost_row.price)
    if (
        group_id is None
        or additional_cost_id is None
        or tax_rate_id is None
        or price is None
    ):
        return None
    return POCostRowSnapshot(
        cost_row_id=cost_row.id,
        group_id=group_id,
        additional_cost_id=additional_cost_id,
        tax_rate_id=tax_rate_id,
        price=price,
        distribution_method=_optional_str(cost_row.distribution_method),
        reference=_optional_str(cost_row.reference),
        currency=_optional_str(cost_row.currency),
        currency_conversion_rate=_optional_float(cost_row.currency_conversion_rate),
    )


def snapshot_po_close_state(
    po: RegularPurchaseOrder,
    cost_rows: Sequence[PurchaseOrderAdditionalCostRow] = (),
) -> POCloseState:
    """Build a :class:`POCloseState` from a fetched PO and its cost rows.

    Every row is captured, received or open: the received ones are replayed
    into their groups, the open ones are needed to complete a
    PARTIALLY_RECEIVED order before the revert (which Katana otherwise
    refuses) and to rebuild the row structure afterwards. ``cost_rows`` are
    the additional cost rows attached to the captured receipt groups.
    """
    status_enum = unwrap_unset(po.status, None)
    status = status_enum.value if status_enum is not None else ""
    rows = [
        snapshot
        for row in (unwrap_unset(po.purchase_order_rows, None) or [])
        if (snapshot := snapshot_po_row(row)) is not None
    ]
    costs: list[POCostRowSnapshot] = []
    skipped: list[int] = []
    for cost_row in cost_rows:
        snapshot = snapshot_po_cost_row(cost_row)
        if snapshot is None:
            skipped.append(cost_row.id)
        else:
            costs.append(snapshot)
    return POCloseState(
        status=status,
        rows=tuple(rows),
        cost_rows=tuple(costs),
        skipped_cost_row_ids=tuple(skipped),
    )
