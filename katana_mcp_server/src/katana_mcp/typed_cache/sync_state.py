"""Per-entity sync watermarks for the #342 typed cache.

One ``SyncState`` row per cached entity type tracks the last successful
sync timestamp, which is passed back to Katana's ``updated_at_min``
parameter on the next incremental pull. A missing row means the cache
is cold for that entity; a present row means we can do a delta fetch.
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class SyncState(SQLModel, table=True):
    """Watermark row tracking last successful sync for one entity type."""

    # ``__tablename__`` is the SQLAlchemy declared-table-name directive.
    # SQLAlchemy's stubs type the inherited attribute as
    # ``declared_attr[str]`` — assigning a literal here is the canonical
    # SQLModel form (and matches every generated ``Cached*`` class), so
    # the type checker setting ``reportIncompatibleVariableOverride =
    # none`` in ``pyrightconfig.json`` allows the override.
    __tablename__ = "sync_state"

    entity_type: str = Field(primary_key=True)
    last_synced: datetime
    row_count: int = 0
