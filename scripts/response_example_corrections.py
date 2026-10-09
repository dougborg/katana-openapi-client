"""Apply live-evidenced example repairs without modifying upstream snapshots."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def example_digest(example: Any) -> str:
    """Pin the complete public example so upstream changes require fresh review."""
    encoded = json.dumps(example, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return "array" if isinstance(value, list) else "object"


def apply_corrections(
    portal: dict[str, Any], manifest: dict[str, Any], *, directory: Path
) -> tuple[dict[str, Any], int]:
    """Repair only pinned fields with matching successful live observations.

    Values remain public documentation examples, not recorded tenant payloads.
    An observation establishes the replacement's JSON type, not its literal value.
    Null replacements specifically illustrate the observed lifecycle state.
    Missing samples, stale pins, and missing evidence fail rather than being skipped.
    """
    evidence = json.loads((directory / manifest["evidence"]).read_text())
    if evidence["live_schema_errors"]:
        raise ValueError("Correction evidence contains live response schema errors")
    findings = {item["finding"]: item for item in evidence["findings"]}
    corrected = copy.deepcopy(portal)
    seen: set[tuple[str, str, str, str]] = set()
    count = 0
    for entry in manifest["corrections"]:
        method, endpoint, status, media = (
            entry[key] for key in ("method", "endpoint", "status", "media_type")
        )
        key = (method, endpoint, status, media)
        if key in seen:
            raise ValueError(f"Duplicate correction: {key}")
        seen.add(key)
        try:
            content = corrected["paths"][endpoint][method.lower()]["responses"][status][
                "content"
            ][media]
        except KeyError as exc:
            raise ValueError(f"Stale correction endpoint: {key}") from exc
        if example_digest(content["example"]) != entry["upstream_sha256"]:
            raise ValueError(f"Stale correction example: {key}")
        prefix: list[str] = []
        original = content["example"]
        if isinstance(original, dict) and len(original) == 1:
            label = next(iter(original))
            if isinstance(original[label], dict) and any(
                word in label.lower() for word in ("example", "response", "sample")
            ):
                prefix = [label]
        for patch in entry["patches"]:
            finding = findings[patch["finding"]]
            evidence_path = finding.get("evidence_field_path", finding["field_path"])
            if (
                (finding["method"], finding["endpoint"], str(finding["status"]))
                != (method, endpoint, status)
                or evidence_path != patch["field_path"]
                or patch["example_path"] != prefix + evidence_path
                or json_type(patch["value"]) not in finding["observed_types"]
                or finding["observed_types"][json_type(patch["value"])] < 1
            ):
                raise ValueError(
                    f"Correction lacks matching live field evidence: {key}"
                )
            if not any(
                (request["method"], request["endpoint"], str(request["status"]))
                == (method, endpoint, status)
                for request in evidence["requests"]
            ):
                raise ValueError(f"Correction lacks a successful live request: {key}")
            target = content["example"]
            path = patch["example_path"]
            if not path:
                if not isinstance(target, list) or patch["value"] != {"data": target}:
                    raise ValueError(
                        "Root corrections must preserve every array record"
                    )
                content["example"] = copy.deepcopy(patch["value"])
            else:
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = copy.deepcopy(patch["value"])
            count += 1
    return corrected, count
