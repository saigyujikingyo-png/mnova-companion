import math

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from mnova_companion.contracts import OUTPUTS, Error, Quantity


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_nonfinite_scientific_values_rejected(value):
    with pytest.raises(ValidationError):
        Quantity(value=value, unit="ppm", availability="available")


def test_missing_quantity_is_not_zero():
    with pytest.raises(ValidationError):
        Quantity(value=None, unit="ppm", availability="available")
    with pytest.raises(ValidationError):
        Quantity(value=0.0, unit="ppm", availability="unavailable", reason="not reported")
    valid = Quantity(value=None, unit="ppm", availability="unavailable", reason="not reported")
    assert valid.value is None


@pytest.mark.parametrize("name,model", OUTPUTS.items())
def test_every_tool_has_valid_meaningful_error_output_schema(name, model):
    schema = model.model_json_schema()
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    value = model(
        operation=name,
        request_id="req1",
        observed_at="2026-09-15T00:00:00Z",
        request_status="error",
        summary="Native output could not be validated",
        evidence_scope=["output_contract"],
        error=Error(
            code="OUTPUT_CONTRACT_INVALID",
            message="Known native job remains recorded",
            recovery="Read and reconcile the job; do not repeat the write",
        ),
    )
    Draft202012Validator(schema).validate(value.model_dump(mode="json"))
    with pytest.raises(ValidationError):
        model.model_validate({**value.model_dump(), "request_status": "ok"})


def test_missing_success_data_and_unknown_fields_fail():
    common = dict(
        operation="mnova_status",
        request_id="r1",
        observed_at="2026-09-15T00:00:00Z",
        request_status="ok",
        summary="",
        evidence_scope=["metadata"],
    )
    with pytest.raises(ValidationError):
        OUTPUTS["mnova_status"](**common)
    with pytest.raises(ValidationError):
        Error(code="BUSY", message="busy", recovery="read status", secret="extra")
