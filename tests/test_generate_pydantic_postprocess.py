"""Regression tests for the generate_pydantic_models.py post-processors.

The post-processors transform datamodel-codegen output into the final
``Cached*`` SQLModel classes. These tests pin the rewrite behavior so a
future codegen tooling change that subtly shifts the generated text
pattern doesn't silently disable the transform.

Loads ``scripts/generate_pydantic_models.py`` via ``importlib`` so the
test doesn't need ``sys.path`` manipulation.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_pydantic_models.py"
)


def _load_module() -> ModuleType:
    import sys

    name = "generate_pydantic_under_test"
    spec = importlib.util.spec_from_file_location(name, _SCRIPT_PATH)
    if spec is None or spec.loader is None:
        msg = f"Could not load module from {_SCRIPT_PATH}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    # Register in ``sys.modules`` so ``@dataclass`` (and any other
    # decorator that looks up ``sys.modules[cls.__module__]``) can find
    # the loader-attached classes during class-body execution.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen() -> ModuleType:
    return _load_module()


def _make_cls(gen: ModuleType, name: str, body: str) -> Any:
    """Build a ClassInfo with the given body wrapped in a class header."""
    source = f"class {name}(DeletableEntity, table=True):\n{body}"
    return gen.ClassInfo(
        name=name,
        source=source,
        bases=["DeletableEntity"],
        line_start=1,
        line_end=source.count("\n") + 1,
    )


# ─── wrap_cache_fields_in_mapped ────────────────────────────────────────


def test_wrap_simple_scalar(gen: ModuleType) -> None:
    """Bare scalar field → ``Annotated[Mapped[int], Field(...)]``."""
    # ``CACHE_TABLES`` is a dict keyed by un-prefixed entity name; pick
    # any real cache class so ``_cached_name`` resolves it for the pass.
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    id: Annotated[int, SQLField(primary_key=True, description="x")]\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Annotated[Mapped[int], SQLField(" in out.source


def test_wrap_union(gen: ModuleType) -> None:
    """Union (``T | None``) types are wrapped intact."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    deleted_at: Annotated[datetime | None, Field(description="x")] = None\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Mapped[datetime | None]" in out.source


def test_wrap_single_bracket_generic(gen: ModuleType) -> None:
    """Single-level generic (``list["X"]``) is wrapped correctly."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    rows: Annotated[list["RowSchema"], Field(description="x")] = None\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert 'Mapped[list["RowSchema"]]' in out.source


def test_wrap_two_level_generic(gen: ModuleType) -> None:
    """Two-level generic (``Optional[list["X"]]``) — the regex's documented depth limit."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    items: Annotated[Optional[list["X"]], Field(description="x")] = None\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert 'Mapped[Optional[list["X"]]]' in out.source


def test_wrap_relationship(gen: ModuleType) -> None:
    """Relationship fields get ``Mapped[]`` on the outer type."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    rows: list["CachedRow"] = Relationship(back_populates="parent")\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert 'Mapped[list["CachedRow"]] = Relationship(' in out.source


def test_skips_non_cache_class(gen: ModuleType) -> None:
    """Non-cache classes are left untouched."""
    cls = gen.ClassInfo(
        name="NotACache",
        source=(
            "class NotACache(KatanaPydanticBase):\n"
            '    id: Annotated[int, Field(description="x")]\n'
        ),
        bases=["KatanaPydanticBase"],
        line_start=1,
        line_end=2,
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Mapped[" not in out.source
    assert out.source == cls.source


def test_includes_entity_base_classes(gen: ModuleType) -> None:
    """Shared entity bases (BaseEntity, DeletableEntity, etc.) get wrapping
    too — without this, inherited ``deleted_at`` / ``created_at`` would
    stay un-wrapped and call sites would still need ``col()``."""
    base_name = next(iter(gen.ENTITY_BASE_CLASSES))
    cls = gen.ClassInfo(
        name=base_name,
        source=(
            f"class {base_name}(KatanaPydanticBase):\n"
            '    deleted_at: Annotated[datetime | None, Field(description="x")] = None\n'
        ),
        bases=["KatanaPydanticBase"],
        line_start=1,
        line_end=2,
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Mapped[datetime | None]" in out.source


def test_raises_on_unwrappable_deep_nesting(gen: ModuleType) -> None:
    """Three-level nesting exceeds the regex depth → assertion fires.

    Pin the failure mode: the regex handles up to two levels of bracket
    nesting (``Optional[list[X]]`` works, ``dict[str, dict[int, list[X]]]``
    doesn't). Rather than silently emit unwrapped fields, the pass
    raises ``GenerationError`` so a future spec addition that introduces
    this shape is caught immediately.
    """
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        # Three levels: dict -> list -> dict
        '    nested: Annotated[dict[str, list[dict[int, str]]], Field(description="x")]\n',
    )
    with pytest.raises(gen.GenerationError, match="missed an Annotated"):
        gen.wrap_cache_fields_in_mapped([cls])
