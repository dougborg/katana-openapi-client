"""Runtime identity shim for ``sqlalchemy.orm.Mapped``.

The generated ``Cached*`` classes wrap each field type in ``Mapped[T]`` so
type checkers see ``CachedX.field`` as ``InstrumentedAttribute[T]`` (which
exposes ``.in_/.is_/.desc/.ilike``). At runtime, however, SQLModel +
pydantic 2.13 reject ``Mapped[T]`` as a field type — pydantic's schema
generator can't unwrap it, so class definition raises
``PydanticSchemaGenerationError``.

This shim resolves the conflict by being a *runtime identity* version of
``Mapped``: at type-check time, ``Mapped`` resolves to the real
``sqlalchemy.orm.Mapped``; at runtime, ``Mapped[T]`` returns ``T`` itself
via ``__class_getitem__``. The generated ``Annotated[Mapped[T], Field(...)]``
shape therefore evaluates to ``Annotated[T, Field(...)]`` at runtime —
identical to the pre-shim behavior — while the type checker sees the
descriptor-bearing ``Mapped[T]`` shape.

Why a shim instead of natively typing fields as ``Mapped[T]``: SQLModel
0.0.38 + pydantic 2.13 don't yet support that form, and the workarounds
(``arbitrary_types_allowed=True`` plus per-field ``sa_type=`` overrides)
re-implement SQLModel's existing type inference at every field. The shim
is a 10-line solution that disappears once SQLModel ships native
``Mapped[T]`` support.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped as Mapped
else:

    class Mapped:
        """Runtime identity — ``Mapped[T]`` returns ``T``."""

        def __class_getitem__(cls, item: object) -> object:
            return item


__all__ = ["Mapped"]
