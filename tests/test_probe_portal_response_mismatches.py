"""Keep missing and rare live cases from becoming false confirmations."""

from collections import defaultdict

from jsonschema import Draft202012Validator
from referencing import Registry
from scripts.probe_portal_response_mismatches import ABSENT, Audit, values_at


def test_values_at_samples_all_rows_without_inventing_empty_samples():
    assert values_at({"data": []}, ["data", 0, "value"]) == []
    assert values_at(
        {"data": [{"value": None}, {}, {"value": "1"}]}, ["data", 0, "value"]
    ) == [None, ABSENT, "1"]


def report_for(schema, portal, live, *, endpoint="/sample"):
    audit = Audit.__new__(Audit)
    audit.spec = {"components": {}}
    audit.registry = Registry()
    audit.findings = [
        {"method": "GET", "endpoint": endpoint, "status": 200, "field_path": []}
    ]
    audit.errors = list(Draft202012Validator(schema).iter_errors(portal))
    audit.samples = defaultdict(list, {("GET", endpoint): live})
    audit.requests = []
    audit.factory = {}
    audit.cleanup = None
    return audit.report()["findings"][0]["verdict"]


def test_integer_samples_cannot_disprove_null_case():
    assert (
        report_for({"type": "integer"}, None, [123])
        == "unverified_null_case_not_observed"
    )


def test_empty_samples_do_not_confirm_a_schema():
    assert report_for({"type": "string"}, 1.2, []) == "unverified_no_samples"


def test_observed_live_numeric_drift_is_confirmed():
    assert report_for({"type": "string"}, 1.2, [3.14]) == "local_schema_wrong"


def test_another_enum_member_cannot_disprove_failure_reason():
    assert (
        report_for({"enum": ["DUPLICATE", "MISSING"]}, "NOT_IN_STOCK", ["MISSING"])
        == "unverified_enum_case_not_observed"
    )


def test_union_checks_disputed_leaf_without_blaming_unrelated_live_errors():
    schema = {
        "oneOf": [
            {
                "properties": {
                    "landed_cost": {"type": "number"},
                    "kind": {"const": "regular"},
                    "note": {"type": "string"},
                }
            },
            {
                "properties": {
                    "landed_cost": {"type": "number"},
                    "kind": {"const": "outsourced"},
                }
            },
        ]
    }
    assert (
        report_for(
            schema,
            {"kind": "regular", "landed_cost": "1"},
            [{"kind": "regular", "landed_cost": 1, "note": 123}],
            endpoint="/purchase_orders",
        )
        == "portal_example_wrong"
    )


def test_null_can_expose_local_gap_even_without_nonnull_sample():
    assert report_for({"type": "string"}, 1.2, [None]) == "local_schema_wrong"


def test_new_union_mismatches_remain_visible_without_aborting_report():
    assert (
        report_for({"oneOf": [{"type": "integer"}, {"type": "string"}]}, 1.2, [1])
        == "unverified_unsupported_union"
    )
