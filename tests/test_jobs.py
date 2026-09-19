import concurrent.futures
import subprocess
import sys
import time
import uuid

import pytest

from mnova_companion.execution import PHASES, BuildProfile, ExecutorHandshake, Receipt
from mnova_companion.jobs import JobConflict, JobStore


def prepare(store, key="once"):
    profile = BuildProfile(
        profile_id="fake", build_fingerprint="a" * 64, mode="portable_fake", operations=["probe"]
    )
    handshake = ExecutorHandshake(
        executor_session_id=uuid.uuid4().hex,
        process_instance_id=uuid.uuid4().hex,
        build_profile_id="fake",
        build_fingerprint="a" * 64,
        isolation_id="test",
        mode="portable_fake",
    )
    job = store.submit(
        key, {"operation": "probe", "document_id": "fixture", "expected_revision": 1}
    )
    dispatch = store.prepare_job(
        job["job_id"], profile=profile, handshake=handshake, deadline=time.time() + 60
    )
    return dispatch, profile, handshake


def dispatch_and_finish(store, dispatch, profile, handshake):
    assert store.dispatch_once(dispatch, profile=profile, handshake=handshake, observed_revision=1)
    for sequence, phase in enumerate(PHASES, 1):
        store.record_receipt(
            Receipt(
                identity=dispatch.identity,
                sequence=sequence,
                phase=phase,
                effects="known",
                cleanup="complete",
                result={"fake_outcome": "completed"},
            )
        )
    return store.complete(dispatch.identity)


def test_idempotency_survives_restart_and_rejects_changed_request(tmp_path):
    first = JobStore(tmp_path).submit("request-1", {"operation": "probe"})
    second = JobStore(tmp_path).submit("request-1", {"operation": "probe"})
    assert second["job_id"] == first["job_id"]
    with pytest.raises(JobConflict):
        JobStore(tmp_path).submit("request-1", {"operation": "save"})


def test_only_one_native_job_claimed_across_stores(tmp_path):
    def claim(index):
        try:
            prepare(JobStore(tmp_path), f"r-{index}")
            return True
        except JobConflict:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, range(2)))
    assert sum(claims) == 1
    store = JobStore(tmp_path)
    assert sorted(store.read(p.stem)["state"] for p in store.records.glob("*.json")) == [
        "queued",
        "running",
    ]


def test_unknown_outcome_retains_lease_and_does_not_repeat(tmp_path):
    store = JobStore(tmp_path)
    dispatch, profile, handshake = prepare(store)
    assert store.dispatch_once(dispatch, profile=profile, handshake=handshake, observed_revision=1)
    store.mark_unknown(dispatch.identity, "No receipt after fake dispatch")
    assert not JobStore(tmp_path).dispatch_once(
        dispatch, profile=profile, handshake=handshake, observed_revision=1
    )
    with pytest.raises(JobConflict):
        prepare(store, "new-key")
    with pytest.raises(JobConflict):
        store.complete(dispatch.identity)
    assert store.submit("once", dispatch.request)["state"] == "outcome_unknown"
    assert (tmp_path / "native.lock").exists()


def test_cancel_queued_and_running_have_different_semantics(tmp_path):
    store = JobStore(tmp_path)
    queued = store.submit("queued", {"operation": "probe"})
    assert store.cancel(queued["job_id"])["state"] == "cancelled"
    dispatch, profile, handshake = prepare(store, "running")
    assert store.dispatch_once(dispatch, profile=profile, handshake=handshake, observed_revision=1)
    assert store.cancel(dispatch.identity.job_id)["state"] == "cancel_requested"
    assert (tmp_path / "native.lock").exists()
    for sequence, phase in enumerate(PHASES, 1):
        store.record_receipt(
            Receipt(
                identity=dispatch.identity,
                sequence=sequence,
                phase=phase,
                effects="known",
                cleanup="complete",
                result={"fake": True},
            )
        )
    store.complete(dispatch.identity)
    assert store.read(dispatch.identity.job_id)["state"] == "succeeded"
    assert not (tmp_path / "native.lock").exists()


def test_terminal_job_is_not_overwritten_and_ids_cannot_escape(tmp_path):
    store = JobStore(tmp_path)
    dispatch, profile, handshake = prepare(store, "good")
    result = dispatch_and_finish(store, dispatch, profile, handshake)
    assert store.complete(dispatch.identity) == result
    with pytest.raises(JobConflict):
        store.record_receipt(
            Receipt(
                identity=dispatch.identity,
                sequence=4,
                phase="post_scope_verified",
                effects="known",
                cleanup="complete",
                result={"fake_outcome": "different"},
            )
        )
    assert store.read(dispatch.identity.job_id)["result"] == {"fake_outcome": "completed"}
    with pytest.raises(ValueError):
        store.read("../../private")


def test_metadata_lock_releases_after_process_crash(tmp_path):
    code = (
        "import os,sys; from pathlib import Path; from mnova_companion.jobs import JobStore; "
        "store=JobStore(Path(sys.argv[1])); guard=store._guard(); guard.__enter__(); os._exit(0)"
    )
    subprocess.run([sys.executable, "-c", code, str(tmp_path)], check=True, timeout=10)
    job = JobStore(tmp_path).submit("after-crash", {"operation": "probe"})
    assert job["state"] == "queued"
