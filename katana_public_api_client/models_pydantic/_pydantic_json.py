"""Pydantic-aware SQLAlchemy JSON TypeDecorator.

This module provides ``PydanticJSON``, a drop-in replacement for
``sqlalchemy.JSON`` that serializes pydantic ``BaseModel`` instances and any
nested non-JSON-native scalars (``datetime``, ``Decimal``, ``UUID``, etc.)
via :func:`pydantic_core.to_jsonable_python` before handing the value to the
database driver.

Problem solved
--------------
SQLAlchemy's stock ``JSON`` column type delegates serialization to
``json.dumps``, which doesn't know how to handle pydantic model instances or
``datetime`` / ``Decimal`` / ``UUID`` values.

Two failure modes both flow through this column type:

1. **Live pydantic instances at flush time.** Generated cache classes
   (``Cached<Name>``) preserve their typed pydantic annotations on
   JSON-stored fields (e.g. ``serial_numbers: list[SerialNumber]``). The
   ``model_dump → model_validate`` round-trip in ``_attrs_*_to_cached``
   re-instantiates nested dicts back into their pydantic types, so by flush
   time SQLAlchemy may hold live pydantic instances rather than plain
   dicts.

2. **Plain dicts containing non-JSON-native scalars.** When the cache row
   is itself ``model_dump``'d (e.g. by ``_bulk_upsert`` calling
   ``model_dump(include=column_names)`` in default ``mode="python"``), the
   nested JSON-column field can land back as a list of plain dicts whose
   leaves still hold live ``datetime`` / ``Decimal`` instances. These also
   need to be coerced to JSON-safe primitives before ``json.dumps``.

Both shapes are handled uniformly by routing the value through
``pydantic_core.to_jsonable_python``, which recursively walks dicts, lists,
and pydantic models and emits ISO-8601 strings, decimals-as-strings, and
the rest of pydantic's standard JSON serialization rules.

``PydanticJSON`` fixes the latent class of bugs affecting every
``CACHE_JSON_COLUMNS`` field that carries nested pydantic models or
datetime-bearing nested dicts. It is used by the generator
(``inject_json_columns`` in ``scripts/generate_pydantic_models.py``) and
therefore applies equally to any downstream consumer that writes these
cache tables — not just the MCP server.

Read path
---------
Reads are returned as-is (plain Python scalars / dicts / lists from
``json.loads``).  The consuming layer (SQLModel / pydantic ``model_validate``)
re-types them as needed, which is the same behaviour the stock ``JSON``
column already produces.
"""

from pydantic_core import to_jsonable_python
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class PydanticJSON(TypeDecorator):
    """SQLAlchemy JSON column that serializes pydantic models correctly.

    Drop-in replacement for ``Column(JSON)`` on cache-table fields whose
    Python type annotation is a pydantic model or a list thereof.

    On write (``process_bind_param``), the value is recursively walked via
    :func:`pydantic_core.to_jsonable_python` so nested pydantic
    ``BaseModel`` instances become plain dicts and any nested non-JSON-
    native scalars (``datetime``, ``Decimal``, ``UUID``, etc.) become their
    canonical pydantic JSON projection (ISO-8601 strings, etc.). On read
    the value is returned unchanged (a plain dict/list from
    ``json.loads``).
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: object, dialect: object) -> object:
        """Serialize pydantic models and nested non-JSON scalars to JSON-safe primitives.

        ``None`` short-circuits so SQLAlchemy stores ``NULL`` rather than
        the JSON literal ``null`` for unset columns.
        """
        if value is None:
            return None
        return to_jsonable_python(value)
