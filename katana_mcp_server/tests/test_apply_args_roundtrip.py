"""Structural guard: every preview builder must receive the original request.

Issue #845 traced to ``build_fulfill_preview_ui`` constructing its own
``FulfillOrderRequest`` from response fields rather than receiving the
original tool input. The reconstructed request only carried ``order_id``
/ ``order_type`` / ``preview``, so the rendered Confirm button's apply
payload defaulted ``completed_at`` / ``serial_numbers`` /
``acknowledge_inventory_ordering`` / ``rows`` to None on click —
silently completing the order at click-time ``now()`` rather than the
backdated timestamp the preview promised.

Eleven other preview builders avoided this bug by accepting
``confirm_request: BaseModel`` from the caller and forwarding it
to ``_build_apply_action`` verbatim. The pattern works by convention
— there's no compile-time guard. This module is the test-time guard.

What this module checks:

1. **No locally-constructed Request models inside builders.** Every
   ``build_*_ui`` function in ``prefab_ui.py`` must NOT construct a
   ``*Request(...)`` Pydantic model from response data. Use the
   ``confirm_request`` / ``request`` parameter the caller threads
   through. The only permitted exemption is a builder that already
   carries a recognized back-compat ``if isinstance(<x>, *Request):``
   guard — those builders are listed (and capped) by
   :func:`test_no_back_compat_fallbacks_in_builders`.

2. **Apply-rail tools must thread request through.** Every tool
   registered via ``register_preview_tool`` must call its
   ``to_tool_result`` / ``_*_to_tool_result`` helper with the original
   request — either positionally (``helper(response, request)``) or
   as a keyword (``request=request`` / ``confirm_request=request``).
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

PREFAB_UI = (
    Path(__file__).parent.parent / "src" / "katana_mcp" / "tools" / "prefab_ui.py"
)
FOUNDATION_DIR = (
    Path(__file__).parent.parent / "src" / "katana_mcp" / "tools" / "foundation"
)


_BuilderDef = ast.FunctionDef | ast.AsyncFunctionDef


def _iter_build_functions(tree: ast.Module) -> Iterator[_BuilderDef]:
    """Yield top-level ``build_*_ui`` functions (sync or async).

    A future builder that needs to await a cache fetch (``async def
    build_X_ui``) must still go through both AST guards, so accept
    ``AsyncFunctionDef`` here even though every builder today is sync.
    """
    for node in tree.body:
        if isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef
        ) and node.name.startswith("build_"):
            yield node


def _find_request_constructors(fn: _BuilderDef) -> list[ast.Call]:
    """Collect ``*Request(...)`` constructor calls inside a function body.

    Matches by class-name suffix ``Request`` — sufficient for every
    Pydantic input model in this repo today (FulfillOrderRequest,
    CreatePurchaseOrderRequest, etc.). A future non-``Request``-suffixed
    Pydantic input model (e.g. ``FulfillRowOverride``) reconstructed
    from response data would NOT be flagged by this check; add the
    class name to the suffix-set if needed.

    Exemption is whole-function-scoped: callers in
    :func:`test_builders_do_not_construct_local_request_models` skip
    the entire function when a back-compat guard is present (see
    :func:`_has_back_compat_isinstance_guard`).
    """

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.calls: list[ast.Call] = []

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else func.id
                if isinstance(func, ast.Name)
                else None
            )
            if name and name.endswith("Request"):
                self.calls.append(node)
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(fn)
    return visitor.calls


def _has_back_compat_isinstance_guard(fn: _BuilderDef) -> bool:
    """True when the function body contains an explicit
    ``if isinstance(<expr>, <X>Request[, …]):`` test — the documented
    shape of a back-compat fallback that reconstructs a Pydantic
    request from response data.

    The second-arg name MUST end in ``Request`` for the guard to
    fire — a bare ``if isinstance(x, dict):`` (the codebase's common
    input-shape narrowing pattern) does NOT count as an exemption,
    so unrelated isinstance checks can't accidentally exempt a
    builder from :func:`test_builders_do_not_construct_local_request_models`.

    Compound conditions (``isinstance(...) and …``) and the
    ``elif``/``not isinstance(...)`` forms are intentionally not
    matched — call out the back-compat shape with a plain
    ``if isinstance(request, FooRequest):`` so the intent is
    obvious to readers. See #845.
    """

    def _is_request_class_name(node: ast.expr) -> bool:
        # `isinstance(x, FooRequest)` — single class arg.
        if isinstance(node, ast.Name):
            return node.id.endswith("Request")
        # `isinstance(x, (FooRequest, BarRequest))` — tuple of classes.
        if isinstance(node, ast.Tuple):
            return any(
                isinstance(elt, ast.Name) and elt.id.endswith("Request")
                for elt in node.elts
            )
        return False

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.found = False

        def visit_If(self, node: ast.If) -> None:
            test = node.test
            if (
                isinstance(test, ast.Call)
                and isinstance(test.func, ast.Name)
                and test.func.id == "isinstance"
                and len(test.args) >= 2
                and _is_request_class_name(test.args[1])
            ):
                self.found = True
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(fn)
    return visitor.found


def test_builders_do_not_construct_local_request_models() -> None:
    """The fulfill_order regression (#845).

    A preview/apply builder must NOT construct ``*Request(...)`` from
    response data — the original request from the tool input has every
    field the user supplied, the reconstructed one only has whatever
    fields the builder remembers to forward. Forgetting a field
    silently defaults it at apply-click time.

    Exception: a back-compat fallback inside ``if isinstance(request,
    XRequest)`` is permitted (the fallback only runs when the caller
    didn't thread the original request, and that pre-fix path is
    intentionally kept for one release cycle).
    """
    source = PREFAB_UI.read_text()
    tree = ast.parse(source)

    offenders: list[str] = []
    for fn in _iter_build_functions(tree):
        if _has_back_compat_isinstance_guard(fn):
            continue
        for call in _find_request_constructors(fn):
            func = call.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else func.id
                if isinstance(func, ast.Name)
                else "?"
            )
            offenders.append(f"{fn.name}:{call.lineno} constructs {name}(...)")

    assert not offenders, (
        "Preview/apply builders must receive the original Pydantic Request "
        "from the caller (typically as ``confirm_request=request``) — not "
        "reconstruct one from response data. The reconstructed Request "
        "carries only whichever fields the builder remembers to forward, "
        "which silently defaults the rest at apply-click time (#845). "
        "Offenders:\n  " + "\n  ".join(offenders)
    )


def test_no_back_compat_fallbacks_in_builders() -> None:
    """The back-compat ``isinstance(request, *Request)`` fallback inside
    ``build_*_ui`` is permitted but should be temporary.

    This test caps the count: whatever fallbacks exist today are
    grandfathered; new ones must come with a planned removal. Bump the
    expected count when adding a fallback (which itself should only
    happen if you're staging a back-compat migration), and lower it as
    the fallbacks come off.
    """
    source = PREFAB_UI.read_text()
    tree = ast.parse(source)

    builders_with_fallback = [
        fn.name
        for fn in _iter_build_functions(tree)
        if _has_back_compat_isinstance_guard(fn)
    ]
    # `build_fulfill_preview_ui` carries a fallback while the migration
    # off the response-only signature settles. Every other builder
    # already requires the caller to thread the request through.
    expected = {"build_fulfill_preview_ui"}
    extras = set(builders_with_fallback) - expected
    missing = expected - set(builders_with_fallback)
    assert not extras, (
        f"New ``isinstance(request, *Request)`` back-compat fallback in: {sorted(extras)}. "
        f"If intentional, add the function name to ``expected`` and document the "
        f"migration plan. Each fallback is a future bug surface — see #845."
    )
    assert not missing, (
        f"Expected fallback in {sorted(missing)} but didn't find one. "
        f"If the fallback was removed (great!), drop the name from ``expected``."
    )


def _write_tool_names(tree: ast.Module) -> set[str]:
    """Collect the names of write tools — those registered via
    ``register_preview_tool(mcp, <fn>, …)``. Read-only tools
    (``mcp.tool(...)(fn)``) are exempt from the apply-args check.

    Accepts the tool fn passed either positionally (``args[1]``) or
    by keyword (``tool=<fn>`` or ``fn=<fn>``). Aliased imports of
    ``register_preview_tool`` aren't detected — call it by its
    canonical name in foundation modules.
    """

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.names: set[str] = set()

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else func.id
                if isinstance(func, ast.Name)
                else None
            )
            if name == "register_preview_tool":
                # Positional: register_preview_tool(mcp, <fn>, ...)
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Name):
                    self.names.add(node.args[1].id)
                # Keyword: register_preview_tool(mcp, tool=<fn>, ...) or fn=
                for kw in node.keywords:
                    if kw.arg in {"tool", "fn"} and isinstance(kw.value, ast.Name):
                        self.names.add(kw.value.id)
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(tree)
    return visitor.names


def _is_tool_result_helper(name: str | None) -> bool:
    """Match both the wrapped ``_*_to_tool_result`` helper and the
    bare ``to_tool_result`` helper, but NOT ``make_tool_result``.

    The bug class — preview/apply builders building a Confirm-button
    payload — manifests through whichever helper actually invokes a
    builder. In this codebase that's both shapes; ``make_tool_result``
    is a pure wire-envelope assembler that doesn't build apply
    actions, so it doesn't need request-threading.
    """
    if not name:
        return False
    if name == "to_tool_result":
        return True
    return name.endswith("_to_tool_result")


@pytest.mark.parametrize(
    "foundation_file",
    sorted(FOUNDATION_DIR.glob("*.py")),
    ids=lambda p: p.name,
)
def test_apply_rail_tools_thread_request_to_tool_result_helpers(
    foundation_file: Path,
) -> None:
    """Each ``to_tool_result`` / ``_*_to_tool_result`` helper called from a
    ``register_preview_tool`` write tool must receive the original request
    — positionally (``helper(response, request)``) or as a keyword
    (``request=request`` / ``confirm_request=request``).

    The fulfill_order regression (#845) traced to ``fulfill_order(...)``
    calling ``_fulfill_response_to_tool_result(response)`` — no request
    threaded through, so the builder had no choice but to reconstruct
    from response data. This test catches the same pattern across the
    foundation tree.
    """
    source = foundation_file.read_text()
    tree = ast.parse(source)
    write_tools = _write_tool_names(tree)
    if not write_tools:
        pytest.skip(f"{foundation_file.name}: no register_preview_tool callers")

    offenders: list[str] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.in_write_tool = False
            self.tool_name = ""

        def _enter_function(self, node: _BuilderDef) -> None:
            if node.name not in write_tools:
                self.generic_visit(node)
                return
            # Save and restore so a nested helper def inside a write
            # tool doesn't leave ``in_write_tool`` False on its way out
            # — the outer write tool's body after the nested def must
            # still be inspected.
            prior_flag = self.in_write_tool
            prior_name = self.tool_name
            self.in_write_tool = True
            self.tool_name = node.name
            self.generic_visit(node)
            self.in_write_tool = prior_flag
            self.tool_name = prior_name

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._enter_function(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # Sync write tools today don't exist, but the registry
            # accepts either shape; cover both for symmetry.
            self._enter_function(node)

        def visit_Call(self, node: ast.Call) -> None:
            if not self.in_write_tool:
                self.generic_visit(node)
                return
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else func.id
                if isinstance(func, ast.Name)
                else None
            )
            if _is_tool_result_helper(name):
                kw_names = {kw.arg for kw in node.keywords if kw.arg is not None}
                # Positional: helper(response, request, ...) — at least
                # two positional args signals intent to pass request.
                threaded_positionally = len(node.args) >= 2
                threaded_by_kw = "request" in kw_names or "confirm_request" in kw_names
                if not threaded_positionally and not threaded_by_kw:
                    offenders.append(
                        f"{self.tool_name}:{node.lineno} calls {name}(...) "
                        f"with only {len(node.args)} positional arg(s) and "
                        f"no ``request=`` / ``confirm_request=`` kwarg"
                    )
            self.generic_visit(node)

    Visitor().visit(tree)

    assert not offenders, (
        f"Write-tool {foundation_file.name} calls a to_tool_result helper "
        f"without threading the original request — the helper has no way to "
        f"propagate non-default args into the Confirm button's apply payload (#845). "
        f"Pass ``request`` positionally or as ``request=`` / ``confirm_request=`` kwarg. "
        f"Offenders:\n  " + "\n  ".join(offenders)
    )
