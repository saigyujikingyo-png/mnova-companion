"""Validate every public input/output schema and report actual catalog size."""

import json

from jsonschema import Draft202012Validator

from mnova_companion.contracts import INPUTS, OUTPUTS
from mnova_companion.execution import (
    BuildProfile,
    Dispatch,
    EvidenceFile,
    ExecutionIdentity,
    ExecutorHandshake,
    Receipt,
)

total = 0
for name in INPUTS:
    for schema in (INPUTS[name].model_json_schema(), OUTPUTS[name].model_json_schema()):
        Draft202012Validator.check_schema(schema)
        assert schema["type"] == "object"
        assert schema.get("additionalProperties") is False
        total += len(json.dumps(schema, separators=(",", ":")).encode())
print(f"PASS: {len(INPUTS)} tool contracts; {total} UTF-8 schema bytes (not billing tokens).")
internal = (BuildProfile, Dispatch, EvidenceFile, ExecutionIdentity, ExecutorHandshake, Receipt)
for model in internal:
    schema = model.model_json_schema()
    Draft202012Validator.check_schema(schema)
    assert schema["type"] == "object"
    assert schema.get("additionalProperties") is False
print(f"PASS: {len(internal)} internal P0 schemas; fake execution only, no added MCP tools.")
print("Scope: declared contracts only; run tests and smoke_mcp for result/transport coverage.")
