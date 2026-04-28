"""Pydantic-aware SQLAlchemy JSON TypeDecorator.

This module provides ``PydanticJSON``, a drop-in replacement for
``sqlalchemy.JSON`` that serializes pydantic ``BaseModel`` instances via
``model_dump(mode='json')`` before handing the value to the database
driver.

Problem solved
--------------
SQLAlchemy's stock ``JSON`` column type delegates serialization to
``json.dumps``, which doesn't know how to handle pydantic model instances.
Generated cache classes (``Cached<Name>``) preserve their typed pydantic
annotations on JSON-stored fields (e.g. ``serial_numbers:
list[SerialNumber]``).  The ``model_dump → model_validate`` round-trip in
``_attrs_*_to_cached`` re-instantiates nested dicts back into their pydantic
types, so by flush time SQLAlchemy holds live pydantic instances, not plain
dicts.

``PydanticJSON`` fixes the latent class of bugs affecting every
``CACHE_JSON_COLUMNS`` field that carries nested pydantic models.  It is
used by the generator (``inject_json_columns`` in
``scripts/generate_pydantic_models.py``) and therefore applies equally to
any downstream consumer that writes these cache tables — not just the MCP
server.

Read path
---------
Reads are returned as-is (plain Python scalars / dicts / lists from
``json.loads``).  The consuming layer (SQLModel / pydantic ``model_validate``)
re-types them as needed, which is the same behaviour the stock ``JSON``
column already produces.
"""

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class PydanticJSON(TypeDecorator):
    """SQLAlchemy JSON column that serializes pydantic models correctly.

    Drop-in replacement for ``Column(JSON)`` on cache-table fields whose
    Python type annotation is a pydantic model or a list thereof.

    On write (``process_bind_param``), any ``BaseModel`` instance is
    recursively dumped to a plain JSON-serializable dict via
    ``model_dump(mode='json')``.  On read the value is returned unchanged
    (a plain dict/list from ``json.loads``).
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: object, dialect: object) -> object:
        """Serialize pydantic models to JSON-safe dicts before writing."""
        if value is None:
            return None
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, list):
            return [
                v.model_dump(mode="json") if isinstance(v, BaseModel) else v
                for v in value
            ]
        return value
