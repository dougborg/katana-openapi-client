"""Example repairs retain upstream evidence and cannot hide unverified drift."""

import copy
import json

import pytest
from scripts.response_example_corrections import apply_corrections, example_digest
from scripts.validate_response_examples import (
    DEFAULT_CORRECTIONS,
    DEFAULT_LOCAL,
    DEFAULT_README,
    format_report,
    load_yaml_spec,
    validate,
)


def sample(tmp_path, *, example=None, field_path=None, observed_types=None):
    example = {"amount": 1} if example is None else example
    field_path = ["amount"] if field_path is None else field_path
    observed_types = {"string": 1} if observed_types is None else observed_types
    portal = {
        "paths": {
            "/sample": {
                "get": {
                    "responses": {
                        "200": {"content": {"application/json": {"example": example}}}
                    }
                }
            }
        }
    }
    evidence = {
        "live_schema_errors": [],
        "requests": [{"method": "GET", "endpoint": "/sample", "status": 200}],
        "findings": [
            {
                "finding": 1,
                "method": "GET",
                "endpoint": "/sample",
                "status": 200,
                "field_path": field_path,
                "observed_types": observed_types,
            }
        ],
    }
    (tmp_path / "evidence.json").write_text(json.dumps(evidence))
    manifest = {
        "evidence": "evidence.json",
        "corrections": [
            {
                "method": "GET",
                "endpoint": "/sample",
                "status": "200",
                "media_type": "application/json",
                "upstream_sha256": example_digest(example),
                "patches": [
                    {
                        "finding": 1,
                        "field_path": field_path,
                        "example_path": field_path,
                        "value": "1",
                    }
                ],
            }
        ],
    }
    return portal, manifest


def test_repairs_copy_examples_and_preserve_the_upstream_snapshot(tmp_path):
    portal, manifest = sample(tmp_path)
    original = copy.deepcopy(portal)
    corrected, count = apply_corrections(portal, manifest, directory=tmp_path)
    assert count == 1
    assert portal == original
    assert corrected["paths"]["/sample"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"] == {"amount": "1"}


def test_upstream_changes_require_fresh_review(tmp_path):
    portal, manifest = sample(tmp_path)
    portal["paths"]["/sample"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]["amount"] = 2
    with pytest.raises(ValueError, match="Stale correction example"):
        apply_corrections(portal, manifest, directory=tmp_path)


@pytest.mark.parametrize("observed_types", [{}, {"null": 1}, {"string": 0}])
def test_missing_or_incompatible_live_values_cannot_justify_repairs(
    tmp_path, observed_types
):
    portal, manifest = sample(tmp_path, observed_types=observed_types)
    with pytest.raises(ValueError, match="matching live field evidence"):
        apply_corrections(portal, manifest, directory=tmp_path)


def test_evidence_for_one_field_cannot_repair_another(tmp_path):
    portal, manifest = sample(tmp_path)
    manifest["corrections"][0]["patches"][0]["example_path"] = ["other"]
    with pytest.raises(ValueError, match="matching live field evidence"):
        apply_corrections(portal, manifest, directory=tmp_path)


def test_wrapper_repairs_cannot_remove_records(tmp_path):
    portal, manifest = sample(
        tmp_path, example=[{"id": 1}], field_path=[], observed_types={"object": 1}
    )
    manifest["corrections"][0]["patches"][0]["value"] = {"data": []}
    with pytest.raises(ValueError, match="preserve every array record"):
        apply_corrections(portal, manifest, directory=tmp_path)


def test_failed_requests_cannot_justify_response_corrections(tmp_path):
    portal, manifest = sample(tmp_path)
    path = tmp_path / "evidence.json"
    evidence = json.loads(path.read_text())
    evidence["requests"][0]["status"] = 422
    path.write_text(json.dumps(evidence))
    with pytest.raises(ValueError, match="successful live request"):
        apply_corrections(portal, manifest, directory=tmp_path)


def test_null_repairs_only_claim_the_observed_state(tmp_path):
    portal, manifest = sample(tmp_path, observed_types={"null": 1})
    manifest["corrections"][0]["patches"][0]["value"] = None
    corrected, _ = apply_corrections(portal, manifest, directory=tmp_path)
    assert (
        corrected["paths"]["/sample"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["example"]["amount"]
        is None
    )


def test_recorded_repairs_keep_accounting_cases_and_new_drift_visible():
    local = load_yaml_spec(DEFAULT_LOCAL)
    portal = load_yaml_spec(DEFAULT_README)
    raw = validate(local, portal)
    corrected, count = apply_corrections(
        portal,
        load_yaml_spec(DEFAULT_CORRECTIONS),
        directory=DEFAULT_CORRECTIONS.parent,
    )
    report = validate(local, corrected)
    report.corrections_applied = count
    report.raw_upstream_failures = len(raw.failures)
    assert len(raw.failures) == 62
    assert count == 61
    assert len(report.failures) == 2
    assert {failure.path for failure in report.failures} == {
        "/purchase_order_accounting_metadata"
    }
    assert not report.ok
    assert "Raw upstream failures: **62**" in format_report(report)

    corrected["paths"]["/sales_order_rows"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]["data"][0]["quantity"] = "unexpected string"
    new_report = validate(local, corrected)
    assert len(new_report.failures) == 3
    assert any(
        failure.error_path == "/data/0/quantity" for failure in new_report.failures
    )
