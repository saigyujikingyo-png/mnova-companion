import concurrent.futures
import subprocess
import sys

import pytest

from mnova_companion.jobs import JobConflict, JobStore


def test_idempotency_survives_restart_and_rejects_changed_request(tmp_path):
    first = JobStore(tmp_path).submit("request-1", {"operation": "probe"})
    second = JobStore(tmp_path).submit("request-1", {"operation": "probe"})
    assert second["job_id"] == first["job_id"]
    with pytest.raises(JobConflict):
        JobStore(tmp_path).submit("request-1", {"operation": "save"})


def test_only_one_native_job_claimed_across_stores(tmp_path):
    store = JobStore(tmp_path)
    jobs = [store.submit(f"r-{n}", {"operation": "probe"}) for n in range(2)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda j: JobStore(tmp_path).claim(j["job_id"]), jobs))
    assert sum(claims) == 1
    assert sorted(store.read(j["job_id"])["state"] for j in jobs) == ["queued", "running"]


def test_unknown_outcome_retains_lease_and_does_not_repeat(tmp_path):
    store = JobStore(tmp_path)
    job = store.submit("once", {"operation": "save"})
    assert store.claim(job["job_id"])
    store.mark_unknown(job["job_id"], "No receipt after native launch")
    assert not JobStore(tmp_path).claim(job["job_id"])
    other = store.submit("next", {"operation": "probe"})
    assert not store.claim(other["job_id"])
    assert store.submit("once", {"operation": "save"})["state"] == "outcome_unknown"


def test_cancel_queued_and_running_have_different_semantics(tmp_path):
    store = JobStore(tmp_path)
    queued = store.submit("queued", {"operation": "probe"})
    assert store.cancel(queued["job_id"])["state"] == "cancelled"
    assert not store.claim(queued["job_id"])
    running = store.submit("running", {"operation": "save"})
    assert store.claim(running["job_id"])
    assert store.cancel(running["job_id"])["state"] == "cancel_requested"
    assert (tmp_path / "native.lock").exists()
    store.complete(running["job_id"], {"native_outcome": "completed"})
    assert store.read(running["job_id"])["state"] == "succeeded"
    assert not (tmp_path / "native.lock").exists()


def test_terminal_job_is_not_overwritten_and_ids_cannot_escape(tmp_path):
    store = JobStore(tmp_path)
    job = store.submit("good", {"operation": "probe"})
    assert store.claim(job["job_id"])
    store.complete(job["job_id"], {"native_outcome": "completed"})
    with pytest.raises(JobConflict):
        store.complete(job["job_id"], {"native_outcome": "different"})
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
