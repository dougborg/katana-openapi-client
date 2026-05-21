"""Safety guard for spec-drift probe scripts.

The ``scripts/spec_drift_verify.py`` harness mints SDT-prefixed identities
and records every mutation in a ledger so cleanup can reverse it. Both
disciplines are opt-in — there's nothing at the wire boundary preventing
a probe from mutating a real customer record by accident (see issue #781
near-miss with ``#WEB20604``).

This module adds that boundary. ``SafeClient`` is a drop-in
``httpx.Client`` subclass that:

1. Refuses ``POST`` / ``PATCH`` / ``DELETE`` requests when the target
   record's identity field doesn't carry the ``SDT-`` prefix and the
   record's ID isn't in the local ledger. ``UnsafeMutationError`` is
   raised before the wire call.
2. Optionally fires per-endpoint **verify hooks** after a 2xx mutation
   response — used to assert that the wire result matches caller intent
   (e.g. ``POST /manufacturing_order_productions`` silently dropping
   unminted serial IDs returns 200 OK with ``serial_numbers: []``).
   Verify-hook failures raise ``SilentDropError``.

Both errors are ``RuntimeError`` subclasses so probes that want graceful
degradation can ``except`` them; the default behavior is "process dies,
operator sees the boundary log."

The ledger-membership lookup keys on ``(endpoint, entity_id)`` because
different Katana entities share ID spaces (a sales order and a material
can both have ID 42). The lookup builds an in-process set from
``read_ledger()`` at ``SafeClient`` construction time; ``record_artifact()``
keeps the in-memory set fresh as the run progresses.

Endpoints listed in ``NO_GET_BY_ID`` fall back to a ledger-only check —
no pre-fetch is possible (the live API only exposes list / parent-scoped
reads), so the only guard is "the parent record was created by this
run." Treat ``NO_GET_BY_ID`` as the source of truth and update it
directly when a new endpoint is observed to 404 on GET-by-id.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import httpx

# Identity field per top-level collection. ``None`` means the endpoint has
# no SDT-discoverable top-level identity on the request body — child /
# transactional collections that only carry FKs to a parent. POSTs to
# these endpoints fall back to the FK-in-ledger check via
# ``CHILD_PARENT_FIELDS`` below.
IDENTITY_FIELDS: dict[str, str | None] = {
    "/sales_orders": "order_no",
    "/manufacturing_orders": "order_no",
    "/purchase_orders": "order_no",
    "/stock_transfers": "stock_transfer_number",
    "/products": "name",
    "/materials": "name",
    "/services": "name",
    "/variants": "sku",
    "/suppliers": "name",
    "/customers": "name",
    "/locations": "name",
    "/bin_locations": "name",
    "/custom_field_definitions": "label",
    # ``Webhook.url`` must be ``https://…`` (Katana spec pattern), so it
    # can never carry the ``SDT-`` prefix. ``description`` is the only
    # taggable field on ``CreateWebhookRequest``. Listed in
    # ``IDENTITY_REQUIRED`` below — webhooks are an exception to the
    # standard "key-absent ⇒ permissive" path because they have
    # immediate live side effects (the URL starts receiving real tenant
    # events the moment POST returns 201, well before any cleanup).
    "/webhooks": "description",
    # Child / transactional endpoints — no top-level identity on the body.
    "/sales_order_rows": None,
    "/sales_order_fulfillments": None,
    "/manufacturing_order_recipe_rows": None,
    "/manufacturing_order_productions": None,
    "/stock_adjustments": None,
    "/variant_bin_locations": None,
}

# Endpoints where the identity field MUST be present and SDT-tagged.
# Standard endpoints (e.g. ``/sales_orders``) treat key-absent as
# "server will generate the identity" and lean permissive — the probe
# records the resulting ID into the ledger and subsequent mutations are
# ledger-protected. That's safe because a missing-identity record is
# just a row in Katana's DB until something mutates it.
#
# A webhook is different: the moment POST /webhooks returns 201,
# Katana starts delivering real tenant events to the caller-supplied
# URL (data exfiltration risk if the probe is pointing at an
# operator-controlled URL that's also serving real customer payloads).
# Cleanup deletes the row eventually, but during its lifetime the side
# effect is live. Fail closed when ``description`` is absent so probes
# must consciously tag every webhook.
IDENTITY_REQUIRED: frozenset[str] = frozenset({"/webhooks"})

# Invariant: every entry in ``IDENTITY_REQUIRED`` must map to a
# non-None field in ``IDENTITY_FIELDS``. Membership alone isn't enough
# — if a future change set ``IDENTITY_FIELDS[endpoint] = None`` (e.g.
# reclassifying it as a child / transactional endpoint with no
# top-level identity), the ``identity_field is not None`` short-circuit
# in ``_check_post_item`` would skip the entire required-identity
# branch, and the enforcement would silently never run on that
# endpoint. Enforced as a module-load runtime check (not ``assert``,
# because ``assert`` is stripped under ``-O`` / ``PYTHONOPTIMIZE``, and
# a safety guard's invariants must always fire).
_required_missing = IDENTITY_REQUIRED - IDENTITY_FIELDS.keys()
if _required_missing:
    raise RuntimeError(
        f"IDENTITY_REQUIRED entries missing from IDENTITY_FIELDS: {_required_missing}"
    )
_required_none = {ep for ep in IDENTITY_REQUIRED if IDENTITY_FIELDS.get(ep) is None}
if _required_none:
    raise RuntimeError(
        "IDENTITY_REQUIRED entries must map to a non-None identity field; "
        f"these are mapped to None: {_required_none}"
    )
del _required_missing, _required_none

# For endpoints whose POST body carries a parent FK rather than a
# top-level identity, this map names the FK field. The parent must
# already be in the ledger for the POST to be allowed (or
# ``allow_unsafe=True`` must be set at SafeClient construction).
CHILD_PARENT_FIELDS: dict[str, tuple[str, str]] = {
    "/sales_order_rows": ("sales_order_id", "/sales_orders"),
    "/sales_order_fulfillments": ("sales_order_id", "/sales_orders"),
    "/manufacturing_order_recipe_rows": (
        "manufacturing_order_id",
        "/manufacturing_orders",
    ),
    "/manufacturing_order_productions": (
        "manufacturing_order_id",
        "/manufacturing_orders",
    ),
    "/stock_adjustments": ("location_id", "/locations"),
    "/variant_bin_locations": ("variant_id", "/variants"),
}

# Endpoints where ``GET /<collection>/{id}`` returns 404 — the live API
# only exposes list / parent-scoped reads. For PATCH/DELETE against
# these, ledger membership is the only available guard.
NO_GET_BY_ID: frozenset[str] = frozenset(
    {
        "/stock_transfers",
        "/stock_adjustments",
        "/sales_order_rows",
        "/sales_order_fulfillments",
        "/manufacturing_order_recipe_rows",
        "/manufacturing_order_productions",
        "/variant_bin_locations",
    }
)

# Identity values matching this pattern are considered SDT-tagged. The
# probe scripts produce ``SDT-<yyyy-mm-dd>-<suffix>`` (via ``tagged()``)
# or ``[SDT-<yyyy-mm-dd>] <free text>`` (via ``label()``); both variants
# place the literal ``SDT-`` marker at the very start. Anchored to
# start-of-string so substrings like ``MySDT-foo`` don't slip through.
_SDT_RE = re.compile(r"^\[?SDT-")


def _is_sdt_tagged(value: Any) -> bool:
    """Return True if ``value`` is a string carrying an SDT- prefix.

    Accepts both ``tagged()`` form (bare ``SDT-…`` prefix) and ``label()``
    form (``[SDT-…] …`` wrapper). Non-string values return False.
    """
    if not isinstance(value, str):
        return False
    # ``.match()`` aligns with the anchored ``^\[?SDT-`` pattern —
    # ``.search()`` would silently work but mis-signals intent to readers.
    return _SDT_RE.match(value) is not None


class UnsafeMutationError(RuntimeError):
    """Raised when a mutation targets a non-SDT, non-ledger record.

    Attributes give the operator everything they need to triage:
    ``method`` (POST/PATCH/DELETE), ``endpoint`` (the collection path),
    ``target_id`` (the record being touched, ``None`` for POST),
    ``identity_field`` + ``identity_value`` for the field we inspected,
    and ``reason`` (free text describing which check failed).
    """

    def __init__(
        self,
        *,
        method: str,
        endpoint: str,
        target_id: str | int | None,
        identity_field: str | None,
        identity_value: Any,
        reason: str,
    ) -> None:
        self.method = method
        self.endpoint = endpoint
        self.target_id = target_id
        self.identity_field = identity_field
        self.identity_value = identity_value
        self.reason = reason
        target = f"/{target_id}" if target_id is not None else ""
        ident = (
            f" ({identity_field}={identity_value!r})"
            if identity_field is not None
            else ""
        )
        super().__init__(
            f"Refusing {method} {endpoint}{target}{ident}: {reason}. "
            "Set allow_unsafe=True on the SafeClient to bypass."
        )


class SilentDropError(RuntimeError):
    """Raised when a 2xx response contradicts the caller's intent.

    Sibling of ``UnsafeMutationError`` for the post-mutation verify hook.
    ``endpoint`` + ``method`` identify the call; ``reason`` is the
    hook's failure message (e.g. "requested 3 serials, response carries
    0"). The original request body and parsed response body are attached
    for debugging.
    """

    def __init__(
        self,
        *,
        method: str,
        endpoint: str,
        reason: str,
        request_body: Any = None,
        response_body: Any = None,
    ) -> None:
        self.method = method
        self.endpoint = endpoint
        self.reason = reason
        self.request_body = request_body
        self.response_body = response_body
        super().__init__(
            f"Silent drop on {method} {endpoint}: {reason}. "
            "The wire returned 2xx but the response state contradicts the request."
        )


VerifyHook = Callable[[httpx.Request, httpx.Response], None]


class SafeClient(httpx.Client):
    """``httpx.Client`` that refuses mutations against non-SDT records.

    Constructor takes the same args as ``httpx.Client`` plus:

    - ``allow_unsafe`` (default ``False``) — bypass all checks. Used
      internally by ``spec_drift_verify.cleanup()`` where the ledger
      already pre-vetted the targets, and by ``_resolve_factory_id()``
      where the call is read-only.
    - ``ledger_keys`` (default empty) — initial set of ``(endpoint,
      str(entity_id))`` tuples that count as "this run created it."
      ``register_artifact()`` extends the set live.

    Verify hooks register via ``register_verify(method, endpoint, hook)``
    and fire after a 2xx response. A hook raises ``SilentDropError`` to
    fail the run.
    """

    def __init__(
        self,
        *args: Any,
        allow_unsafe: bool = False,
        ledger_keys: set[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._allow_unsafe = allow_unsafe
        self._ledger_keys: set[tuple[str, str]] = set(ledger_keys or ())
        self._verify_hooks: dict[tuple[str, str], list[VerifyHook]] = {}

    # ------------------------------------------------------------------
    # Ledger membership — kept in sync by ``register_artifact`` calls
    # ------------------------------------------------------------------

    def register_artifact(self, endpoint: str, entity_id: int | str) -> None:
        """Record that ``entity_id`` at ``endpoint`` was created by this run.

        Called by ``spec_drift_verify.record_artifact()`` so subsequent
        PATCH/DELETE against the freshly-created record passes the
        ledger-membership check without a pre-fetch round-trip.
        """
        self._ledger_keys.add((endpoint, str(entity_id)))

    def in_ledger(self, endpoint: str, entity_id: int | str) -> bool:
        """Return True if ``(endpoint, entity_id)`` is in the local ledger."""
        return (endpoint, str(entity_id)) in self._ledger_keys

    # ------------------------------------------------------------------
    # Verify hooks — post-mutation assertions
    # ------------------------------------------------------------------

    def register_verify(
        self,
        method: str,
        endpoint: str,
        hook: VerifyHook,
    ) -> None:
        """Register ``hook`` to run after a 2xx ``METHOD endpoint`` response.

        Hooks only fire for **mutation** methods (``POST`` / ``PATCH`` /
        ``DELETE``) — the framework is designed for post-mutation
        silent-drop assertions, and reads are exempted in ``request()``
        so a hook registered on ``("GET", …)`` is silently inert.
        Register on a non-mutation method only as a no-op marker.

        Hook signature: ``(request, response) -> None``. Raise
        ``SilentDropError`` to fail; any other exception bubbles. Multiple
        hooks on the same ``(method, endpoint)`` run in registration order.
        """
        key = (method.upper(), endpoint)
        self._verify_hooks.setdefault(key, []).append(hook)

    # ------------------------------------------------------------------
    # Request interception
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        url: httpx.URL | str,
        **kwargs: Any,
    ) -> httpx.Response:
        method_upper = method.upper()
        is_mutation = method_upper in {"POST", "PATCH", "DELETE"}
        if is_mutation and not self._allow_unsafe:
            self._check_mutation(method_upper, url, kwargs)
        response = super().request(method, url, **kwargs)
        if is_mutation and 200 <= response.status_code < 300:
            self._run_verify_hooks(method_upper, url, response)
        return response

    # ------------------------------------------------------------------
    # Guard logic
    # ------------------------------------------------------------------

    def _check_mutation(
        self,
        method: str,
        url: httpx.URL | str,
        kwargs: dict[str, Any],
    ) -> None:
        endpoint, target_id = _split_path(url)
        if method == "POST":
            self._check_post(endpoint, kwargs)
            return
        # PATCH / DELETE — must have an ID
        if target_id is None:
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=None,
                identity_field=None,
                identity_value=None,
                reason=f"{method} requires a target ID in the path",
            )
        self._check_patch_or_delete(method, endpoint, target_id)

    def _check_post(self, endpoint: str, kwargs: dict[str, Any]) -> None:
        body = kwargs.get("json")
        if body is None:
            # No body or non-JSON body — probably a multipart upload; not
            # currently a probe pattern, refuse rather than guess.
            raise UnsafeMutationError(
                method="POST",
                endpoint=endpoint,
                target_id=None,
                identity_field=None,
                identity_value=None,
                reason="POST has no JSON body to inspect",
            )
        # Array bodies (some endpoints accept ``[{...}, ...]``) — inspect
        # every element. If any element fails, the whole POST fails.
        items: list[Any] = body if isinstance(body, list) else [body]
        for item in items:
            self._check_post_item(endpoint, item)

    def _check_post_item(self, endpoint: str, item: Any) -> None:
        if not isinstance(item, dict):
            raise UnsafeMutationError(
                method="POST",
                endpoint=endpoint,
                target_id=None,
                identity_field=None,
                identity_value=item,
                reason="POST body element is not a JSON object",
            )
        identity_field = IDENTITY_FIELDS.get(endpoint)
        if identity_field is not None:
            if identity_field not in item:
                # Standard endpoints: a key-absent identity is the
                # caller asking Katana to mint the field (e.g. SO
                # without ``order_no``). Lean permissive — the probe
                # records the created ID into the ledger and every
                # subsequent mutation is then guarded. (KEY-ABSENT only;
                # an explicit ``{order_no: None}`` falls through to the
                # SDT check below and fails closed, because explicit
                # null is a different caller intent.)
                #
                # Live-side-effect endpoints (``IDENTITY_REQUIRED``) opt
                # out: webhooks start delivering events immediately on
                # 201, so ``description`` must be present AND SDT-tagged
                # before the wire call.
                if endpoint in IDENTITY_REQUIRED:
                    raise UnsafeMutationError(
                        method="POST",
                        endpoint=endpoint,
                        target_id=None,
                        identity_field=identity_field,
                        identity_value=None,
                        reason=(
                            f"{endpoint} requires {identity_field} to be "
                            "present and SDT-tagged before POST (endpoint "
                            "has immediate live side effects)"
                        ),
                    )
                return
            value = item[identity_field]
            if not _is_sdt_tagged(value):
                raise UnsafeMutationError(
                    method="POST",
                    endpoint=endpoint,
                    target_id=None,
                    identity_field=identity_field,
                    identity_value=value,
                    reason=(
                        f"{identity_field}={value!r} has no SDT- prefix; "
                        "POST would land on a non-test record"
                    ),
                )
            return
        # No top-level identity. Try the parent-FK route.
        parent = CHILD_PARENT_FIELDS.get(endpoint)
        if parent is None:
            # Unknown endpoint — refuse rather than guess.
            raise UnsafeMutationError(
                method="POST",
                endpoint=endpoint,
                target_id=None,
                identity_field=None,
                identity_value=None,
                reason=(
                    f"endpoint {endpoint} is not in IDENTITY_FIELDS; "
                    "add it before mutating from a probe"
                ),
            )
        fk_field, parent_endpoint = parent
        fk_value = item.get(fk_field)
        if fk_value is None:
            raise UnsafeMutationError(
                method="POST",
                endpoint=endpoint,
                target_id=None,
                identity_field=fk_field,
                identity_value=None,
                reason=(
                    f"child POST is missing parent FK {fk_field!r}; "
                    "cannot verify parent is SDT-tagged"
                ),
            )
        if not self.in_ledger(parent_endpoint, fk_value):
            raise UnsafeMutationError(
                method="POST",
                endpoint=endpoint,
                target_id=None,
                identity_field=fk_field,
                identity_value=fk_value,
                reason=(
                    f"parent {parent_endpoint}/{fk_value} is not in the "
                    "local ledger — refuse to attach a child to a record "
                    "this run didn't create"
                ),
            )

    def _check_patch_or_delete(
        self,
        method: str,
        endpoint: str,
        target_id: str,
    ) -> None:
        if self.in_ledger(endpoint, target_id):
            return
        if endpoint in NO_GET_BY_ID:
            # No pre-fetch available; ledger membership is our only signal.
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=None,
                identity_value=None,
                reason=(
                    f"{endpoint} does not support GET-by-id and "
                    f"{target_id} is not in the local ledger"
                ),
            )
        identity_field = IDENTITY_FIELDS.get(endpoint)
        if identity_field is None:
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=None,
                identity_value=None,
                reason=(
                    f"endpoint {endpoint} has no known identity field; "
                    "refusing to verify via GET"
                ),
            )
        # Pre-fetch and check identity. ``send`` directly to skip the
        # request() override (read-only GET — no need to re-validate).
        try:
            req = self.build_request("GET", f"{endpoint}/{target_id}")
            response = self.send(req)
        except Exception as exc:
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=identity_field,
                identity_value=None,
                reason=f"pre-fetch GET failed: {exc!r}",
            ) from exc
        if response.status_code == 404:
            # DELETE is idempotent — let a 404 through so the caller can
            # record the "already gone" result. PATCH, by contrast, must
            # fail closed: a 404 means we never confirmed the target's
            # identity, so the SDT check never ran.
            if method == "DELETE":
                return
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=identity_field,
                identity_value=None,
                reason=(
                    "pre-fetch GET returned 404; PATCH cannot proceed "
                    "without identity-verifying the target (use "
                    "allow_unsafe=True if the ledger has pre-vetted it)"
                ),
            )
        if not response.is_success:
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=identity_field,
                identity_value=None,
                reason=f"pre-fetch GET returned {response.status_code}",
            )
        try:
            data = response.json()
        except Exception as exc:
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=identity_field,
                identity_value=None,
                reason=f"pre-fetch GET body not JSON: {exc!r}",
            ) from exc
        identity_value = data.get(identity_field) if isinstance(data, dict) else None
        if not _is_sdt_tagged(identity_value):
            raise UnsafeMutationError(
                method=method,
                endpoint=endpoint,
                target_id=target_id,
                identity_field=identity_field,
                identity_value=identity_value,
                reason=(
                    f"target {endpoint}/{target_id} has no SDT- prefix "
                    f"({identity_field}={identity_value!r}) "
                    "and is not in the local ledger"
                ),
            )

    def _run_verify_hooks(
        self,
        method: str,
        url: httpx.URL | str,
        response: httpx.Response,
    ) -> None:
        endpoint, _ = _split_path(url)
        hooks = self._verify_hooks.get((method, endpoint), [])
        if not hooks:
            return
        for hook in hooks:
            hook(response.request, response)


# ----------------------------------------------------------------------
# Path parsing
# ----------------------------------------------------------------------


def _split_path(url: httpx.URL | str) -> tuple[str, str | None]:
    """Return ``(collection, id)`` from a request URL.

    ``/sales_orders``       → ``("/sales_orders", None)``
    ``/sales_orders/42``    → ``("/sales_orders", "42")``
    ``/sales_orders/42/x``  → ``("/sales_orders", "42")`` — sub-resources
    fall through to the parent collection; not a current probe pattern.

    Both absolute and relative inputs are accepted: ``"sales_orders/42"``
    parses the same as ``"/sales_orders/42"``. Relative inputs reach this
    function when httpx attaches a base URL at send-time; the guard runs
    at request-build time on whatever the caller passed in.
    """
    if isinstance(url, httpx.URL):
        path = url.path
    else:
        # Accept absolute or relative URL strings.
        path = urlparse(str(url)).path if "://" in str(url) else str(url)
    # Drop query string, then strip the leading/trailing ``/`` so a
    # subsequent ``split('/')`` produces a stable shape regardless of
    # input form. (Repeated interior slashes like ``"a//b"`` are not
    # collapsed — Katana never emits them and the SafeClient mints all
    # mutation paths itself, so the case doesn't arise in practice.)
    path = path.split("?", 1)[0].strip("/")
    if not path:
        return ("", None)
    parts = path.split("/")
    # After ``strip('/')`` + ``split('/')``:
    # ``"sales_orders"``     -> ['sales_orders']
    # ``"sales_orders/42"``  -> ['sales_orders', '42']
    if len(parts) == 1:
        return ("/" + parts[0], None)
    return ("/" + parts[0], parts[1])


# ----------------------------------------------------------------------
# Discovery helper — pick SDT-tagged fixtures, never a real customer
# ----------------------------------------------------------------------


def discover_sdt_fixture(
    client: httpx.Client,
    endpoint: str,
    identity_field: str,
    *,
    limit: int = 50,
    max_pages: int = 5,
) -> dict[str, Any] | None:
    """Paginate ``endpoint`` and return the first SDT-tagged record.

    Use this in probe-script ``discover_fixtures()`` instead of "grab the
    first customer" — the latter is exactly the WEB20604 incident's root
    cause. Returns ``None`` when no SDT-tagged record exists; caller
    decides whether to create one or skip the probe.

    Filters client-side because Katana list filters are exact-match
    only; ``?order_no=SDT-…`` returns zero rows because no record's
    full order_no matches the prefix alone.
    """
    page = 1
    while page <= max_pages:
        resp = client.get(f"{endpoint}?limit={limit}&page={page}")
        if not resp.is_success:
            return None
        rows = resp.json().get("data", [])
        if not rows:
            return None
        for row in rows:
            if _is_sdt_tagged(row.get(identity_field)):
                return row
        if len(rows) < limit:
            return None
        page += 1
    return None


# ----------------------------------------------------------------------
# Example verify hook for the silent-drop concern (issue #781 follow-up)
# ----------------------------------------------------------------------


def verify_production_serial_numbers_match(
    request: httpx.Request,
    response: httpx.Response,
) -> None:
    """Verify ``POST /manufacturing_order_productions`` didn't drop serials.

    The live API returns 200 OK with ``serial_numbers: []`` when the
    posted serial IDs reference unminted SerialNumber records. Detect by
    comparing requested vs returned counts and raise ``SilentDropError``
    when they disagree.

    Probes register this via ``client.register_verify("POST",
    "/manufacturing_order_productions", verify_production_serial_numbers_match)``.
    """
    try:
        req_body = _decode_request_json(request)
    except ValueError:
        return  # not a JSON body — can't verify
    requested = req_body.get("serial_numbers") if isinstance(req_body, dict) else None
    if not isinstance(requested, list) or not requested:
        return  # caller didn't ask for serials → nothing to verify
    try:
        resp_body = response.json()
    except ValueError:
        return  # 2xx without JSON body — unusual; let caller assert shape
    landed = resp_body.get("serial_numbers") if isinstance(resp_body, dict) else None
    if not isinstance(landed, list):
        landed = []
    if len(landed) != len(requested):
        raise SilentDropError(
            method="POST",
            endpoint="/manufacturing_order_productions",
            reason=(
                f"requested {len(requested)} serial(s), "
                f"response carries {len(landed)} — Katana silently "
                "dropped unminted SerialNumber IDs"
            ),
            request_body=req_body,
            response_body=resp_body,
        )


def _decode_request_json(request: httpx.Request) -> Any:
    """Best-effort decode a request's body as JSON for verify hooks."""
    import json

    if request.content is None:
        raise ValueError("no request body")
    return json.loads(request.content)
