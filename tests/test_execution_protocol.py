"""Portable wire and witness boundaries; no vendor import or application execution."""

import errno
import hashlib
import json
import time

import pytest

from mnova_companion.execution import (
    MAX_WIRE_BYTES,
    BuildProfile,
    Dispatch,
    EvidenceFile,
    ExecutorHandshake,
    Receipt,
    wire_bytes,
)
from mnova_companion.jobs import JobStore


class HookedList(list):
    def forbidden(self):
        pytest.fail("Wire rejection invoked a user-defined hook")

    __repr__ = __iter__ = forbidden


@pytest.mark.parametrize(
    "bad",
    [
        object(),
        memoryview(b"data"),
        RuntimeError("untrusted"),
        HookedList(),
        float("nan"),
        float("inf"),
        -float("inf"),
        {1: "bad key"},
    ],
)
def test_wire_rejects_non_json_without_object_hooks(bad):
    with pytest.raises(ValueError):
        wire_bytes({"value": bad})


def test_wire_structure_and_byte_limits():
    value = {"values": [None, True, 1, 1.5], "unit": "ppm"}
    assert json.loads(wire_bytes(value)) == value
    nested = None
    for _ in range(17):
        nested = [nested]
    for invalid in (
        nested,
        [None] * 10000,
        "x" * (MAX_WIRE_BYTES + 1),
        "é" * MAX_WIRE_BYTES,
        2**63,
    ):
        with pytest.raises(ValueError):
            wire_bytes(invalid)


@pytest.fixture
def setup(tmp_path):
    profile = BuildProfile(
        profile_id="fake", build_fingerprint="a" * 64, mode="portable_fake", operations=["probe"]
    )
    handshake = ExecutorHandshake(
        executor_session_id="session",
        process_instance_id="process",
        build_profile_id="fake",
        build_fingerprint="a" * 64,
        isolation_id="isolated",
        mode="portable_fake",
    )
    store = JobStore(tmp_path)
    job = store.submit(
        "request", {"operation": "probe", "document_id": "doc", "expected_revision": 1}
    )
    return store, profile, handshake, job


@pytest.mark.parametrize(
    "model,changes",
    [
        (Dispatch, {"deadline": True}),
        (Dispatch, {"deadline": "123"}),
        (Dispatch, {"request": {"object": object()}}),
        (Dispatch, {"extra": 1}),
        (Receipt, {"sequence": True}),
        (Receipt, {"sequence": "1"}),
        (Receipt, {"result": {"buffer": memoryview(b"x")}}),
        (Receipt, {"extra": 1}),
    ],
)
def test_dispatch_and_receipt_are_strict(setup, model, changes):
    store, profile, handshake, job = setup
    dispatch = store.prepare_job(
        job["job_id"], profile=profile, handshake=handshake, deadline=time.time() + 60
    )
    values = (
        dispatch.model_dump()
        if model is Dispatch
        else {"identity": dispatch.identity, "sequence": 1, "phase": "native_returned"}
    )
    with pytest.raises(ValueError):
        model.model_validate(values | changes)


@pytest.mark.parametrize(
    "target,changes",
    [
        ("profile", {"mode": "diagnostic_candidate"}),
        ("profile", {"mode": "native_accepted"}),
        ("handshake", {"mode": "native_accepted"}),
        ("handshake", {"build_profile_id": "other"}),
        ("handshake", {"build_fingerprint": "b" * 64}),
        ("profile", {"operations": ["other"]}),
    ],
)
def test_ineligible_profile_has_no_lease_or_attempt(setup, target, changes):
    store, profile, handshake, job = setup
    if target == "profile":
        profile = profile.model_copy(update=changes)
    else:
        handshake = handshake.model_copy(update=changes)
    with pytest.raises(ValueError):
        store.prepare_job(
            job["job_id"], profile=profile, handshake=handshake, deadline=time.time() + 60
        )
    record = store.read(job["job_id"])
    assert record["state"] == "queued" and record["execution"] is None
    assert not (store.root / "native.lock").exists()


@pytest.mark.parametrize("path", ["../x", "/x", "C:/x", "a:b", r"a\b", "./x", "a//b", "", "x\0y"])
def test_evidence_paths_cannot_escape(path):
    with pytest.raises(ValueError):
        EvidenceFile(relative_path=path, size_bytes=2, sha256="a" * 64)


@pytest.mark.parametrize("change", [{"size_bytes": 3}, {"sha256": "0" * 64}])
def test_materialized_evidence_checks_size_and_hash(tmp_path, change):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "witness.json").write_bytes(b"{}")
    metadata = dict(
        relative_path="nested/witness.json", size_bytes=2, sha256=hashlib.sha256(b"{}").hexdigest()
    )
    assert EvidenceFile(**metadata).read_verified(tmp_path) == {}
    with pytest.raises(ValueError):
        EvidenceFile(**(metadata | change)).read_verified(tmp_path)


def test_evidence_symlink_outside_root_is_rejected(tmp_path):
    directory = tmp_path / "evidence"
    directory.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"{}")
    try:
        (directory / "link.json").symlink_to(outside)
    except OSError as exc:
        if exc.errno in {errno.EPERM, errno.EACCES} or getattr(exc, "winerror", None) == 1314:
            pytest.skip("OS token cannot create the symlink fixture")
        raise
    evidence = EvidenceFile(
        relative_path="link.json", size_bytes=2, sha256=hashlib.sha256(b"{}").hexdigest()
    )
    with pytest.raises(ValueError):
        evidence.read_verified(directory)
    assert outside.read_bytes() == b"{}"
