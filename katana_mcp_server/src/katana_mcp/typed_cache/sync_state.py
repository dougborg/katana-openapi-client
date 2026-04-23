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

    __tablename__ = "sync_state"

    entity_type: str = Field(primary_key=True)
    last_synced: datetime
    row_count: int = 0
