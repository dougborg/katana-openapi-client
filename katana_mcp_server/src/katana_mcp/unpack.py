"""Unpack decorator for flattening Pydantic models into tool parameters.

This module provides a decorator that allows tools to use Pydantic models for
validation while exposing flattened parameters to the MCP protocol, working around
Claude Code's parameter serialization issues with nested objects.

The flattened signature also carries each field's full metadata — description and
constraints — into the MCP tool schema, by re-wrapping every param annotation as
``Annotated[type, FieldInfo]`` (see ``unpack_pydantic_params``). So the decorator is
both a protocol workaround and the source of tool-schema documentation (#930).

Usage:
    from typing import Annotated
    from pydantic import BaseModel, Field
    from katana_mcp.unpack import Unpack, unpack_pydantic_params

    class MyRequest(BaseModel):
        name: str = Field(..., description="Item name")
        limit: int = Field(default=10, description="Max results")

    @unpack_pydantic_params
    async def my_tool(
        request: Annotated[MyRequest, Unpack()],
        context: Context
    ) -> MyResponse:
        # request is a MyRequest instance with validated fields
        ...

The decorator transforms the function signature so FastMCP sees individual
parameters (name, limit) instead of a nested request object, while the function
body still receives a properly validated Pydantic model instance.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from copy import copy
from typing import Annotated, Any, cast, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from katana_mcp.logging import get_logger

logger = get_logger(__name__)


class Unpack:
    """Marker class to indicate a Pydantic model should be unpacked into flat parameters.

    Use with typing.Annotated to mark which parameters should be unpacked:
        request: Annotated[MyRequest, Unpack()]
    """

    pass


def _reconstruct_model_kwargs(
    unpack_mapping: dict[str, tuple[type[BaseModel], list[str]]],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Collapse flat field kwargs back into the unpacked Pydantic model instances.

    For each unpacked parameter, pulls its declared fields out of ``kwargs``,
    constructs + validates the model, and returns a new kwargs dict with the flat
    fields replaced by the reconstructed model instance. Any ``ValidationError``
    raised by model construction propagates to the caller unchanged.

    Only declared fields are collected into the model payload, so an unknown
    top-level kwarg never reaches model construction — which is why
    ``extra="forbid"`` on the dispatcher request model does NOT fire on
    MCP-protocol traffic: the model simply doesn't see the extra key. (FastMCP's
    TypeAdapter against the flattened function signature rejects unknown top-level
    args even earlier, before this helper runs.) The dispatcher-level
    ``extra="forbid"`` is defense in depth for direct Python callers (tests,
    internal ``_impl`` calls); the load-bearing forbid for wire-level silent drops
    lives on the nested sub-payload models — see #487.

    Note an unknown kwarg is NOT silently dropped from the call: it isn't a
    declared field of any model, so it stays in the returned dict and is forwarded
    to the wrapped function, where it surfaces as a ``TypeError`` (unexpected
    keyword argument). That loud failure is intentional — a silent drop is the
    failure mode #487 exists to prevent.
    """
    reconstructed = kwargs.copy()
    for original_param_name, (model_class, field_names) in unpack_mapping.items():
        model_data = {
            field_name: kwargs[field_name]
            for field_name in field_names
            if field_name in kwargs
        }
        model_instance = model_class(**model_data)
        reconstructed = {k: v for k, v in reconstructed.items() if k not in field_names}
        reconstructed[original_param_name] = model_instance
    return reconstructed


def unpack_pydantic_params(func: Callable) -> Callable:
    """Decorator that unpacks Pydantic model parameters into individual fields.

    This decorator scans the function signature for parameters annotated with
    Annotated[ModelClass, Unpack()], extracts the Pydantic model fields, and
    creates a new function that accepts those fields as individual parameters.

    At runtime, the individual parameters are collected and used to construct
    the Pydantic model instance, which is then passed to the original function.

    Args:
        func: The function to decorate. Should have at least one parameter
              annotated with Annotated[BaseModel, Unpack()].

    Returns:
        A wrapped function with flattened parameters that reconstructs the
        Pydantic model at runtime.

    Raises:
        TypeError: If the unpacked parameter is not a Pydantic BaseModel subclass.
        pydantic.ValidationError: If the collected parameters don't pass validation.

    Example:
        @unpack_pydantic_params
        async def search_items(
            request: Annotated[SearchRequest, Unpack()],
            context: Context
        ) -> SearchResponse:
            # request is a validated SearchRequest instance
            return await search_impl(request, context)

        # FastMCP sees: search_items(query: str, limit: int, context: Context)
        # Function receives: request=SearchRequest(query="...", limit=20)
    """
    sig = inspect.signature(func)
    new_params = []
    unpack_mapping: dict[str, tuple[type[BaseModel], list[str]]] = {}

    # Get type hints to resolve string annotations (from __future__ import
    # annotations). NameError is the typical failure when a forward ref can't
    # be resolved at decoration time; TypeError surfaces from malformed
    # annotations. Both fall back to raw annotations cleanly, but log so the
    # silent-fallback behavior is observable.
    try:
        type_hints = get_type_hints(func, include_extras=True)
    except (NameError, TypeError) as exc:
        logger.debug(
            "get_type_hints_failed_falling_back_to_empty_hint_dict",
            func=repr(func),
            error=str(exc),
        )
        type_hints = {}

    # Track if we've added any KEYWORD_ONLY params
    # If we have, all subsequent params must also be KEYWORD_ONLY
    has_keyword_only = False

    # Scan parameters to find ones marked with Unpack()
    for param_name, param in sig.parameters.items():
        # Use resolved type hint if available, otherwise use raw annotation
        annotation = type_hints.get(param_name, param.annotation)

        # Check if this is Annotated[SomeModel, Unpack()]
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            if len(args) >= 2 and any(isinstance(arg, Unpack) for arg in args[1:]):
                # Found an unpacked parameter
                model_class = args[0]

                if not (
                    inspect.isclass(model_class) and issubclass(model_class, BaseModel)
                ):
                    raise TypeError(
                        f"Parameter '{param_name}' with Unpack() must be a Pydantic BaseModel, "
                        f"got {model_class}"
                    )

                # Extract fields from the Pydantic model
                # Store fields to add them in correct order later
                unpacked_fields = []
                for field_name, field_info in model_class.model_fields.items():
                    # Re-wrap the bare type in ``Annotated[type, <metadata>]`` so the
                    # field's description, constraints (ge/le/min_length/...), and
                    # examples ride along into FastMCP's schema generator. Using the
                    # bare ``field_info.annotation`` dropped all of it, leaving every
                    # flattened param undocumented in the tool schema (#930).
                    #
                    # We embed a *copy* of the FieldInfo with its default cleared:
                    # the ``default=`` on the ``inspect.Parameter`` below is the single
                    # source of the default. Leaving both in place makes pydantic raise
                    # "cannot specify both default and default_factory" for any field
                    # using ``default_factory`` (e.g. ``Field(default_factory=list)``).
                    #
                    # ``copy`` is shallow, so the copy's ``.metadata`` list aliases the
                    # original ``model_fields`` entry; re-bind it to a fresh list so a
                    # downstream mutation of one can never corrupt the class's field.
                    metadata = copy(field_info)
                    metadata.metadata = list(field_info.metadata)
                    metadata.default = PydanticUndefined
                    metadata.default_factory = None
                    field_annotation = Annotated[field_info.annotation, metadata]

                    # Handle default values - convert PydanticUndefined to inspect.Parameter.empty
                    if field_info.default is not PydanticUndefined:
                        field_default = field_info.default
                    elif field_info.default_factory is not None:
                        # Pydantic factories can accept zero args or one
                        # (validated_data). Prefer zero-arg invocation and fall
                        # back to passing an empty validated-data dict. Built-in
                        # types like `list` / `dict` don't have an introspectable
                        # signature, so try the call directly.
                        factory: Any = field_info.default_factory
                        try:
                            field_default = factory()
                        except TypeError:
                            try:
                                field_default = factory({})
                            except TypeError:
                                field_default = inspect.Parameter.empty
                    else:
                        field_default = inspect.Parameter.empty

                    # Use KEYWORD_ONLY to avoid parameter ordering issues
                    # This allows unpacked params to work with other params like Context
                    new_param = inspect.Parameter(
                        name=field_name,
                        kind=inspect.Parameter.KEYWORD_ONLY,
                        default=field_default,
                        annotation=field_annotation,
                    )
                    unpacked_fields.append(new_param)

                # Add all unpacked fields
                new_params.extend(unpacked_fields)
                has_keyword_only = True

                # Remember this mapping for runtime reconstruction
                unpack_mapping[param_name] = (
                    model_class,
                    list(model_class.model_fields.keys()),
                )
                continue

        # Keep non-unpacked parameters, but if we've added KEYWORD_ONLY params
        # before this, we need to make this KEYWORD_ONLY too
        # Also ensure the annotation is the resolved type (not a string from __future__ annotations)
        # This is critical for FastMCP's create_function_without_params to work correctly
        resolved_annotation = type_hints.get(param_name, param.annotation)
        if has_keyword_only and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            new_params.append(
                param.replace(
                    kind=inspect.Parameter.KEYWORD_ONLY, annotation=resolved_annotation
                )
            )
        else:
            new_params.append(param.replace(annotation=resolved_annotation))

    # Create new signature with flattened parameters
    new_sig = sig.replace(parameters=new_params)

    # Create wrapper functions that reconstruct models at runtime. Both share the
    # same reconstruction logic (_reconstruct_model_kwargs); they differ only in
    # await — async tools get the coroutine wrapper, sync tools the plain one.
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        reconstructed_kwargs = _reconstruct_model_kwargs(unpack_mapping, kwargs)
        return await func(*args, **reconstructed_kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        reconstructed_kwargs = _reconstruct_model_kwargs(unpack_mapping, kwargs)
        return func(*args, **reconstructed_kwargs)

    # Choose wrapper based on whether original function is async
    wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    # Update wrapper signature to show flattened parameters. ``functools.wraps``
    # types ``wrapper`` as a ``_Wrapped`` partial that doesn't expose
    # ``__signature__`` statically, but ``inspect`` reads it from the runtime
    # attribute, so cast through ``Any`` to silence the static checker on the
    # write — the runtime attribute is real and used by ``inspect.signature``.
    cast(Any, wrapper).__signature__ = new_sig

    # CRITICAL: Also update __annotations__ so get_type_hints() sees the flattened params
    # This is required for FastMCP's ParsedFunction.from_function() to work correctly
    # We must use resolved type hints (not raw string annotations from __future__ annotations)
    new_annotations = {}
    for param_name, param in new_sig.parameters.items():
        if param.annotation != inspect.Parameter.empty:
            # Prefer resolved type hint over raw annotation (handles forward references)
            new_annotations[param_name] = type_hints.get(param_name, param.annotation)
    if new_sig.return_annotation != inspect.Signature.empty:
        new_annotations["return"] = type_hints.get("return", new_sig.return_annotation)
    wrapper.__annotations__ = new_annotations

    # Python 3.14+ (PEP 749): functools.wraps copies __annotate__ from the original
    # function — override it to return the flattened annotations instead.
    from katana_mcp._fastmcp_patches import _pin_annotate

    _pin_annotate(wrapper, new_annotations)

    return wrapper


__all__ = ["Unpack", "unpack_pydantic_params"]
