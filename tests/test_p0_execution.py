"""Portable P0 acceptance: real journals and fake effects, never a native application."""

import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time

import pytest

import mnova_companion.jobs as jobs_module
from mnova_companion.execution import (
    PHASES,
    BuildProfile,
    EvidenceFile,
    ExecutorHandshake,
    Receipt,
    receipt_digest,
)
from mnova_companion.jobs import JobConflict, JobStore


@pytest.fixture
def env(tmp_path):
    profile = BuildProfile(
        profile_id="fake-v1",
        build_fingerprint="a" * 64,
        mode="portable_fake",
        operations=["probe"],
    )
    handshake = ExecutorHandshake(
        executor_session_id="session-1",
        process_instance_id="process-1",
        build_profile_id=profile.profile_id,
        build_fingerprint=profile.build_fingerprint,
        isolation_id="isolated-fixture",
        mode="portable_fake",
    )
    return JobStore(tmp_path), profile, handshake


def prepare(env, key="first"):
    store, profile, handshake = env
    job = store.submit(key, {"operation": "probe", "document_id": "doc", "expected_revision": 1})
    return store.prepare_job(
        job["job_id"],
        profile=profile,
        handshake=handshake,
        deadline=time.time() + 60,
    )


def enter(env, dispatch):
    store, profile, handshake = env
    return store.dispatch_once(dispatch, profile=profile, handshake=handshake, observed_revision=1)


def receipt(dispatch, sequence, **changes):
    values = dict(identity=dispatch.identity, sequence=sequence, phase=PHASES[sequence - 1])
    if sequence == 4:
        values.update(effects="known", cleanup="complete", result={"fake_value": 42})
    return Receipt(**(values | changes))


def finish_receipts(store, dispatch, start=1):
    for sequence in range(start, 5):
        store.record_receipt(receipt(dispatch, sequence))


def witness(store, dispatch, kind="outcome"):
    value = {"scope": "portable_fake", "identity": dispatch.identity.model_dump(), "kind": kind}
    if kind == "outcome":
        value["receipt_digest"] = receipt_digest(
            store.read(dispatch.identity.job_id)["execution"]["receipts"]
        )
    else:
        value["executor_stopped"] = True
    raw = json.dumps(value).encode()
    directory = store.root / "evidence"
    directory.mkdir(exist_ok=True)
    (directory / f"{kind}.json").write_bytes(raw)
    return EvidenceFile(
        relative_path=f"{kind}.json", size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()
    )


def test_two_competing_consumers_produce_one_effect(env):
    dispatch = prepare(env)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        entered = list(pool.map(lambda _: enter(env, dispatch), range(2)))
    assert sum(entered) == 1
    assert env[0].read(dispatch.identity.job_id)["execution"]["consumed"]


def test_crash_after_consumption_cannot_repeat_effect_after_restart(env):
    store, profile, handshake = env
    dispatch = prepare(env)
    code = (
        "import os,sys; from pathlib import Path; "
        "from mnova_companion.jobs import JobStore; "
        "from mnova_companion.execution import Dispatch,BuildProfile,ExecutorHandshake; "
        "s=JobStore(Path(sys.argv[1])); d=Dispatch.model_validate_json(sys.argv[2]); "
        "p=BuildProfile.model_validate_json(sys.argv[3]); "
        "h=ExecutorHandshake.model_validate_json(sys.argv[4]); "
        "entered=s.dispatch_once(d,profile=p,handshake=h,observed_revision=1); "
        "(s.root/'effect.txt').write_text('one' if entered else 'unexpected'); os._exit(0)"
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(store.root),
            dispatch.model_dump_json(),
            profile.model_dump_json(),
            handshake.model_dump_json(),
        ],
        check=True,
        timeout=15,
    )
    restarted = (JobStore(store.root), profile, handshake)
    assert not enter(restarted, dispatch)
    assert (store.root / "effect.txt").read_text() == "one"
    assert (store.root / "native.lock").exists()


def test_unknown_rejects_completion_and_new_key_or_session(env):
    store, profile, handshake = env
    dispatch = prepare(env)
    assert enter(env, dispatch)
    finish_receipts(store, dispatch)
    store.mark_unknown(dispatch.identity, "unverified native release")
    with pytest.raises(JobConflict):
        store.complete(dispatch.identity)
    second = store.submit("different-key", dispatch.request)
    changed = handshake.model_copy(update={"executor_session_id": "session-2"})
    with pytest.raises(JobConflict):
        store.prepare_job(
            second["job_id"], profile=profile, handshake=changed, deadline=time.time() + 60
        )
    assert store.read(dispatch.identity.job_id)["state"] == "outcome_unknown"
    assert (store.root / "native.lock").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("executor_session_id", "stale"),
        ("process_instance_id", "stale"),
        ("attempt_id", "stale"),
        ("fencing_token", "stale"),
        ("build_fingerprint", "b" * 64),
    ],
)
def test_stale_dispatch_identity_never_consumes_attempt(env, field, value):
    dispatch = prepare(env)
    forged = dispatch.model_copy(
        update={"identity": dispatch.identity.model_copy(update={field: value})}
    )
    with pytest.raises((JobConflict, ValueError)):
        enter(env, forged)
    assert not env[0].read(dispatch.identity.job_id)["execution"]["consumed"]


@pytest.mark.parametrize("conflict", [False, True])
def test_out_of_order_or_conflicting_receipt_quarantines(env, conflict):
    store = env[0]
    dispatch = prepare(env)
    assert enter(env, dispatch)
    if conflict:
        store.record_receipt(receipt(dispatch, 1))
    bad = receipt(dispatch, 1, result={"conflict": True}) if conflict else receipt(dispatch, 2)
    try:
        store.record_receipt(bad)
    except (JobConflict, ValueError):
        pass
    record = store.read(dispatch.identity.job_id)
    assert record["state"] == "outcome_unknown"
    assert record["execution"]["quarantined"]
    assert (store.root / "native.lock").exists()


def test_late_complete_chain_requires_independent_reconciliation(env):
    store = env[0]
    dispatch = prepare(env)
    assert enter(env, dispatch)
    store.record_receipt(receipt(dispatch, 1))
    store.mark_unknown(dispatch.identity, "lost worker connection")
    finish_receipts(store, dispatch, start=2)
    record = store.read(dispatch.identity.job_id)
    assert record["state"] == "outcome_unknown"
    with pytest.raises(JobConflict):
        store.complete(dispatch.identity)
    evidence = witness(store, dispatch)
    tampered = evidence.model_copy(update={"sha256": "0" * 64})
    with pytest.raises(ValueError):
        store.reconcile_verified(
            dispatch.identity, expected_record_revision=record["record_revision"], evidence=tampered
        )
    assert store.read(dispatch.identity.job_id)["state"] == "outcome_unknown"
    assert (store.root / "native.lock").exists()
    with pytest.raises(JobConflict):
        store.reconcile_verified(
            dispatch.identity,
            expected_record_revision=record["record_revision"] - 1,
            evidence=evidence,
        )
    resolved = store.reconcile_verified(
        dispatch.identity, expected_record_revision=record["record_revision"], evidence=evidence
    )
    assert resolved["state"] == "succeeded"
    with pytest.raises(JobConflict):
        prepare(env, "after-resolution")
    store.retire_executor(dispatch.identity, evidence=witness(store, dispatch, "retirement"))
    with pytest.raises(JobConflict):
        prepare(env, "after-resolution")
    changed = env[2].model_copy(
        update={"executor_session_id": "session-2", "process_instance_id": "process-2"}
    )
    assert prepare((store, env[1], changed), "after-resolution").identity.job_id


@pytest.mark.parametrize("consumed", [False, True])
def test_cancel_distinguishes_before_and_after_entry(env, consumed):
    store = env[0]
    dispatch = prepare(env)
    if consumed:
        assert enter(env, dispatch)
    assert store.cancel(dispatch.identity.job_id)["state"] == "cancel_requested"
    assert not enter(env, dispatch)
    expected = "cancel_requested" if consumed else "cancelled"
    assert store.read(dispatch.identity.job_id)["state"] == expected
    assert (store.root / "native.lock").exists() is consumed


def test_journal_failure_prevents_entry(env, monkeypatch):
    dispatch = prepare(env)

    def fail_write(*args, **kwargs):
        raise OSError("injected journal failure")

    monkeypatch.setattr(jobs_module, "atomic_json", fail_write)
    effects = []
    with pytest.raises(OSError):
        if enter(env, dispatch):
            effects.append("must-not-run")
    assert effects == []
    assert (env[0].root / "native.lock").exists()


def test_legacy_unknown_record_remains_observable_and_locked(env):
    store, profile, handshake = env
    job = store.submit("legacy", {"operation": "probe"})
    legacy = {
        key: value
        for key, value in job.items()
        if key not in {"record_version", "record_revision", "execution"}
    }
    legacy.update(state="outcome_unknown", phase="reconciliation_required")
    (store.records / f"{job['job_id']}.json").write_text(json.dumps(legacy))
    (store.root / "native.lock").write_text(
        json.dumps({"job_id": job["job_id"], "pid": 0, "created_at": 0.0})
    )
    restarted = JobStore(store.root)
    assert restarted.read(job["job_id"])["state"] == "outcome_unknown"
    with pytest.raises(JobConflict):
        prepare((restarted, profile, handshake), key="new-after-legacy")
    assert (store.root / "native.lock").exists()


def test_retirement_does_not_resolve_past_effects_or_allow_new_session(env):
    store, profile, handshake = env
    dispatch = prepare(env)
    assert enter(env, dispatch)
    store.mark_unknown(dispatch.identity, "lost receipt")
    store.retire_executor(dispatch.identity, evidence=witness(store, dispatch, "retirement"))
    assert not (store.root / "native.lock").exists()
    record = store.read(dispatch.identity.job_id)
    assert record["state"] == "outcome_unknown"
    assert record["execution"]["retirement"]
    changed = handshake.model_copy(
        update={"executor_session_id": "new", "process_instance_id": "new"}
    )
    with pytest.raises(JobConflict):
        prepare((JobStore(store.root), profile, changed), "new-key-after-retirement")


def test_earlier_failure_cannot_be_overwritten_by_default_final_success(env):
    store = env[0]
    dispatch = prepare(env)
    assert enter(env, dispatch)
    store.record_receipt(receipt(dispatch, 1, outcome="failed"))
    store.record_receipt(receipt(dispatch, 2))
    store.record_receipt(receipt(dispatch, 3))
    with pytest.raises(JobConflict):
        store.record_receipt(receipt(dispatch, 4))
    assert store.read(dispatch.identity.job_id)["state"] == "outcome_unknown"
    with pytest.raises(JobConflict):
        store.complete(dispatch.identity)


def test_large_valid_receipts_remain_reconcilable(env):
    store = env[0]
    dispatch = prepare(env)
    assert enter(env, dispatch)
    for sequence in range(1, 5):
        store.record_receipt(receipt(dispatch, sequence, result={"copied_text": "x" * 40000}))
    store.mark_unknown(dispatch.identity, "worker disconnected before terminal publication")
    record = store.read(dispatch.identity.job_id)
    resolved = store.reconcile_verified(
        dispatch.identity,
        expected_record_revision=record["record_revision"],
        evidence=witness(store, dispatch),
    )
    assert resolved["state"] == "succeeded"


def test_prepare_publication_failure_leaves_conservative_lease(env, monkeypatch):
    store = env[0]
    job = store.submit(
        "interrupted-prepare",
        {
            "operation": "probe",
            "document_id": "doc",
            "expected_revision": 1,
        },
    )
    original = jobs_module.atomic_json
    with monkeypatch.context() as patch:
        patch.setattr(
            jobs_module, "atomic_json", lambda *args: (_ for _ in ()).throw(OSError("disk"))
        )
        with pytest.raises(OSError):
            store.prepare_job(
                job["job_id"], profile=env[1], handshake=env[2], deadline=time.time() + 60
            )
    assert jobs_module.atomic_json is original
    assert store.read(job["job_id"])["state"] == "queued"
    assert (store.root / "native.lock").exists()
    assert store.cancel(job["job_id"])["state"] == "outcome_unknown"
    with pytest.raises(JobConflict):
        prepare(env, "after-interrupted-prepare")


def test_failure_after_consumption_publication_never_replays(env, monkeypatch):
    dispatch = prepare(env)
    original = jobs_module.atomic_json

    def publish_then_fail(path, value):
        original(path, value)
        raise OSError("simulated disconnect after publication")

    effects = []
    with monkeypatch.context() as patch:
        patch.setattr(jobs_module, "atomic_json", publish_then_fail)
        with pytest.raises(OSError):
            if enter(env, dispatch):
                effects.append("effect")
    assert effects == []
    assert not enter((JobStore(env[0].root), env[1], env[2]), dispatch)
    assert env[0].outcome_certainty(env[0].read(dispatch.identity.job_id)) == "unknown"


@pytest.mark.parametrize("terminal", ["complete", "cancel", "stale_revision"])
def test_terminal_publication_before_unlink_is_repaired_without_dispatch(
    env, monkeypatch, terminal
):
    from pathlib import Path

    store, profile, handshake = env
    dispatch = prepare(env)
    if terminal == "complete":
        assert enter(env, dispatch)
        finish_receipts(store, dispatch)
    elif terminal == "cancel":
        store.cancel(dispatch.identity.job_id)
    original = Path.unlink

    def fail_release(path, *args, **kwargs):
        if path == store.root / "native.lock":
            raise OSError("interrupted before lease release")
        return original(path, *args, **kwargs)

    def finish():
        if terminal == "complete":
            return store.complete(dispatch.identity)
        return store.dispatch_once(
            dispatch,
            profile=profile,
            handshake=handshake,
            observed_revision=2 if terminal == "stale_revision" else 1,
        )

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", fail_release)
        with pytest.raises(OSError):
            finish()
    assert (store.root / "native.lock").exists()
    state = store.read(dispatch.identity.job_id)["state"]
    assert state in {"succeeded", "cancelled", "failed"}
    finish()
    assert store.read(dispatch.identity.job_id)["state"] == state
    assert not (store.root / "native.lock").exists()
    assert not enter(env, dispatch)


def test_conflict_in_other_job_blocks_already_prepared_dispatch(env):
    store = env[0]
    first = prepare(env)
    assert enter(env, first)
    finish_receipts(store, first)
    store.complete(first.identity)
    second = prepare(env, "second")
    with pytest.raises(JobConflict):
        store.record_receipt(receipt(first, 4, result={"contradicts_completed_result": True}))
    with pytest.raises(JobConflict):
        enter(env, second)
    assert not store.read(second.identity.job_id)["execution"]["consumed"]


@pytest.mark.parametrize("lock_text", ["{", '{"job_id":"legacy","pid":0,"created_at":0}'])
def test_corrupt_or_legacy_lease_cannot_be_stolen(env, lock_text):
    (env[0].root / "native.lock").write_text(lock_text)
    with pytest.raises(JobConflict):
        prepare(env)
    assert (env[0].root / "native.lock").read_text() == lock_text


@pytest.mark.parametrize("first_value,late_value", [(0, False), (1, True)])
def test_boolean_and_integer_receipts_are_different_json(env, first_value, late_value):
    store = env[0]
    dispatch = prepare(env)
    assert enter(env, dispatch)
    for sequence in range(1, 5):
        store.record_receipt(receipt(dispatch, sequence, result={"value": first_value}))
    store.complete(dispatch.identity)
    with pytest.raises(JobConflict):
        store.record_receipt(receipt(dispatch, 4, result={"value": late_value}))
    observed = store.read(dispatch.identity.job_id)
    assert type(observed["result"]["value"]) is int
    assert observed["execution"]["conflicts"]
    assert store.outcome_certainty(observed) == "unknown"


@pytest.mark.parametrize("completed_phases", range(5))
def test_interruption_at_each_phase_never_becomes_an_automatic_retry(env, completed_phases):
    store = env[0]
    dispatch = prepare(env)
    assert enter(env, dispatch)
    for sequence in range(1, completed_phases + 1):
        store.record_receipt(receipt(dispatch, sequence))
    store.mark_unknown(dispatch.identity, "interruption at a phase boundary")
    restarted = (JobStore(store.root), env[1], env[2])
    assert not enter(restarted, dispatch)
    with pytest.raises(JobConflict):
        prepare(restarted, "different-key")
    finish_receipts(store, dispatch, start=completed_phases + 1)
    with pytest.raises(JobConflict):
        store.complete(dispatch.identity)
    assert store.read(dispatch.identity.job_id)["state"] == "outcome_unknown"
    assert (store.root / "native.lock").exists()
