"""Real-filesystem checks for bounded, immutable-source artifact handling."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mnova_companion.artifact_store import ArtifactStore, ArtifactStoreError


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "store"
        self.store = ArtifactStore(self.root)

    def source(self, name: str = "sample.mnova", data: bytes = b"raw-data") -> Path:
        path = self.base / "inputs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def output(self, name: str = "result.mnova", data: bytes = b"native-result") -> Path:
        path = self.root / "outputs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_single_file_stages_copy_and_keeps_private_paths_out_of_manifest(self) -> None:
        source = self.source("sample α.mnova", b"abc")
        result = self.store.stage(source)
        self.assertRegex(result["source_id"], r"^src_[0-9a-f]{32}$")
        self.assertEqual(result["total_bytes"], 3)
        self.assertEqual(
            result["files"],
            [
                {
                    "path": "sample α.mnova",
                    "size_bytes": 3,
                    "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                }
            ],
        )
        staged = self.store.resolve(result["source_id"], "sample α.mnova")
        self.assertTrue(staged.is_relative_to(self.root.resolve()))
        self.assertNotEqual(staged, source)
        self.assertEqual(staged.read_bytes(), b"abc")
        self.assertEqual(source.read_bytes(), b"abc")
        self.assertNotIn(str(self.base), json.dumps(result))

    def test_bruker_directory_keeps_relative_paths_and_recovers_after_restart(self) -> None:
        source = self.source("experiment/1/fid", b"fid-bytes").parents[1]
        self.source("experiment/1/acqus", b"##$SFO1= 400.13")
        self.source("experiment/1/pdata/1/procs", b"##$SF= 400.13")
        before = {
            p.relative_to(source).as_posix(): p.read_bytes()
            for p in source.rglob("*")
            if p.is_file()
        }
        result = self.store.stage(source)
        self.assertEqual([item["path"] for item in result["files"]], sorted(before))
        self.assertEqual(result["total_bytes"], sum(map(len, before.values())))
        reopened = ArtifactStore(self.root)
        for item in result["files"]:
            expected = before[item["path"]]
            self.assertEqual(item["sha256"], hashlib.sha256(expected).hexdigest())
            self.assertEqual(
                reopened.resolve(result["source_id"], item["path"]).read_bytes(), expected
            )
            self.assertEqual((source / item["path"]).read_bytes(), expected)

    def test_manifest_digest_depends_on_content_and_not_opaque_source_id(self) -> None:
        source = self.source()
        first = self.store.stage(source)
        second = self.store.stage(source)
        self.assertNotEqual(first["source_id"], second["source_id"])
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        source.write_bytes(b"new-data")
        self.assertNotEqual(first["manifest_sha256"], self.store.stage(source)["manifest_sha256"])

    def test_byte_and_file_limits_publish_no_incomplete_manifest(self) -> None:
        directory = self.source("limited/a", b"123").parent
        self.source("limited/b", b"456")
        for limits in ({"max_files": 1}, {"max_bytes": 5}):
            with self.subTest(limits=limits):
                store = ArtifactStore(self.root, **limits)
                with self.assertRaises(ArtifactStoreError):
                    store.stage(directory)
                self.assertEqual(list(self.root.rglob("manifest.json")), [])
        self.assertEqual((directory / "a").read_bytes(), b"123")

    def test_oversized_single_file_is_rejected_and_exact_bound_is_accepted(self) -> None:
        source = self.source(data=b"12345")
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(self.root, max_bytes=4).stage(source)
        self.assertEqual(ArtifactStore(self.root, max_bytes=5).stage(source)["total_bytes"], 5)

    def test_missing_empty_or_self_containing_source_is_rejected(self) -> None:
        empty = self.base / "empty"
        empty.mkdir()
        for source in (self.base / "missing", empty, self.root, self.base):
            with self.subTest(source=source.name), self.assertRaises(ArtifactStoreError):
                self.store.stage(source)

    def test_invalid_limits_are_rejected(self) -> None:
        for options in (
            {"max_files": 0},
            {"max_files": True},
            {"max_bytes": -1},
            {"max_bytes": 1.5},
        ):
            with self.subTest(options=options), self.assertRaises(ArtifactStoreError):
                ArtifactStore(self.root, **options)

    def test_failed_publish_does_not_leave_a_manifest_or_change_raw_input(self) -> None:
        source = self.source(data=b"untouched")
        with mock.patch(
            "mnova_companion.artifact_store.os.replace", side_effect=OSError("simulated disk error")
        ):
            with self.assertRaises(ArtifactStoreError):
                self.store.stage(source)
        self.assertEqual(list(self.root.rglob("manifest.json")), [])
        self.assertEqual(source.read_bytes(), b"untouched")

    def test_resolve_rejects_path_traversal_and_non_manifest_files(self) -> None:
        result = self.store.stage(self.source())
        for path in (
            "../sample.mnova",
            "a/../../sample.mnova",
            "/sample.mnova",
            "C:/sample.mnova",
            "C:sample.mnova",
            "\\\\server\\share",
            "a\\b",
            "a//b",
            "./sample.mnova",
            "sample.mnova/",
            "sample.mnova:secret",
            "not-listed.mnova",
            "",
            ".",
            "a\x00b",
        ):
            with self.subTest(path=path), self.assertRaises(ArtifactStoreError):
                self.store.resolve(result["source_id"], path)

    def test_resolve_rejects_modified_staged_content(self) -> None:
        result = self.store.stage(self.source(data=b"before"))
        staged = self.store.resolve(result["source_id"], "sample.mnova")
        staged.write_bytes(b"after!")
        with self.assertRaises(ArtifactStoreError):
            self.store.resolve(result["source_id"], "sample.mnova")

    def test_register_metadata_and_read_survive_restart_without_private_paths(self) -> None:
        output = self.output("editable α.mnova", b"native-result")
        result = self.store.register(output, job_id="job-123", role="native_document")
        self.assertRegex(result["artifact_id"], r"^art_[0-9a-f]{32}$")
        self.assertEqual(result["file_name"], output.name)
        self.assertEqual(result["size_bytes"], 13)
        self.assertEqual(result["sha256"], hashlib.sha256(b"native-result").hexdigest())
        self.assertEqual(result["media_type"], "application/octet-stream")
        self.assertEqual(result["job_id"], "job-123")
        self.assertEqual(result["role"], "native_document")
        self.assertNotIn(str(self.base), json.dumps(result))
        reopened = ArtifactStore(self.root)
        self.assertEqual(reopened.metadata(result["artifact_id"]), result)
        self.assertEqual(reopened.read(result["artifact_id"]), b"native-result")
        result["sha256"] = "0" * 64
        self.assertNotEqual(reopened.metadata(result["artifact_id"])["sha256"], result["sha256"])

    def test_common_media_types_are_explicit(self) -> None:
        for extension, media_type in (
            (".csv", "text/csv"),
            (".pdf", "application/pdf"),
            (".png", "image/png"),
            (".json", "application/json"),
        ):
            with self.subTest(extension=extension):
                result = self.store.register(self.output("result" + extension), "job-1", "export")
                self.assertEqual(result["media_type"], media_type)

    def test_list_artifacts_is_sorted_filterable_and_uses_only_registry(self) -> None:
        first = self.store.register(self.output("first.mnova"), "job-a", "native_document")
        second = self.store.register(self.output("second.pdf"), "job-b", "export")
        third = self.store.register(self.output("third.csv"), "job-a", "table")
        self.output("unregistered.json", b"not-json")
        reopened = ArtifactStore(self.root)
        expected = sorted([first, second, third], key=lambda item: item["artifact_id"])
        self.assertEqual(reopened.list_artifacts(), expected)
        self.assertEqual(
            reopened.list_artifacts("job-a"),
            [item for item in expected if item["job_id"] == "job-a"],
        )
        self.assertEqual(reopened.list_artifacts("job-missing"), [])
        with self.assertRaises(ArtifactStoreError):
            reopened.list_artifacts("../job-a")

    def test_list_artifacts_has_a_bounded_registry_limit(self) -> None:
        self.store.register(self.output("first.mnova"), "job-a", "native_document")
        self.store.register(self.output("second.mnova"), "job-b", "native_document")
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(self.root, max_files=1).list_artifacts()

    def test_artifact_read_rejects_hash_change_even_when_size_is_unchanged(self) -> None:
        output = self.output(data=b"before")
        result = self.store.register(output, "job-1", "native_document")
        output.write_bytes(b"after!")
        with self.assertRaises(ArtifactStoreError):
            self.store.read(result["artifact_id"])

    def test_register_rejects_outside_directory_or_oversized_output(self) -> None:
        for path in (self.source(), self.root, self.root / "missing"):
            with self.subTest(path=path.name), self.assertRaises(ArtifactStoreError):
                self.store.register(path, "job-1", "native_document")
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(self.root, max_bytes=2).register(
                self.output(), "job-1", "native_document"
            )

    def test_invalid_identifiers_are_rejected(self) -> None:
        for identifier in ("../secret", "", "art_" + "g" * 32, "src_" + "0" * 32, "C:/secret"):
            with self.subTest(identifier=identifier), self.assertRaises(ArtifactStoreError):
                self.store.read(identifier)
        with self.assertRaises(ArtifactStoreError):
            self.store.resolve("../secret", "file")
        for job_id, role in (("../job", "output"), ("job-1", ""), ("job-1", "a\nb")):
            with self.subTest(job_id=job_id, role=role), self.assertRaises(ArtifactStoreError):
                self.store.register(self.output(), job_id, role)

    def test_tampered_persistent_metadata_cannot_escape_store(self) -> None:
        result = self.store.register(self.output(), "job-1", "native_document")
        record = next(self.root.rglob(result["artifact_id"] + ".json"))
        payload = json.loads(record.read_text(encoding="utf-8"))
        payload["relative_path"] = "../inputs/sample.mnova"
        record.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(self.root).read(result["artifact_id"])

    def test_tampered_source_manifest_is_rejected_after_restart(self) -> None:
        result = self.store.stage(self.source())
        manifest = next(self.root.rglob("manifest.json"))
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["files"][0]["path"] = "../outside"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(self.root).resolve(result["source_id"], "sample.mnova")

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_actual_windows_junction_and_linked_parent_are_rejected(self) -> None:
        source = self.source()
        junction = self.root / "junction"
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(source.parent)],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if result.returncode:
            self.skipTest(f"Creating a junction is unavailable: exit {result.returncode}")
        self.addCleanup(junction.rmdir)
        for path in (junction, junction / source.name):
            with self.subTest(path=path.name), self.assertRaises(ArtifactStoreError):
                self.store.stage(path)
        with self.assertRaises(ArtifactStoreError):
            self.store.register(junction / source.name, "job-1", "native_document")
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(junction / "store")
        self.assertEqual(source.read_bytes(), b"raw-data")

    def test_links_and_linked_parents_are_rejected(self) -> None:
        source = self.source()
        linked_file = self.base / "linked-file"
        linked_directory = self.base / "linked-directory"
        try:
            linked_file.symlink_to(source)
            linked_directory.symlink_to(source.parent, target_is_directory=True)
        except OSError as error:
            error_code = error.winerror if os.name == "nt" else error.errno
            self.skipTest(f"Creating a symlink is unavailable: {error_code}")
        for path in (linked_file, linked_directory / source.name):
            with self.subTest(path=path.name), self.assertRaises(ArtifactStoreError):
                self.store.stage(path)
        nested = source.parent / "nested-link"
        nested.symlink_to(source)
        with self.assertRaises(ArtifactStoreError):
            self.store.stage(source.parent)
        output_link = self.root / "output-link"
        output_link.symlink_to(source)
        with self.assertRaises(ArtifactStoreError):
            self.store.register(output_link, "job-1", "native_document")

    def test_windows_reparse_attribute_is_rejected_without_following_it(self) -> None:
        source = self.source()
        original_lstat = Path.lstat

        def reparse_lstat(path: Path, *args: object, **kwargs: object) -> object:
            observed = original_lstat(path, *args, **kwargs)
            if path != source:
                return observed
            proxy = mock.Mock(wraps=observed)
            for field in ("st_mode", "st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns"):
                setattr(proxy, field, getattr(observed, field))
            proxy.st_file_attributes = 0x400
            return proxy

        with mock.patch.object(Path, "lstat", reparse_lstat), self.assertRaises(ArtifactStoreError):
            self.store.stage(source)


@unittest.skipUnless(os.name == "nt", "Windows short-path aliases")
class WindowsShortPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mnova alias regression ")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.directory = self.base / "Store With Spaces"
        self.directory.mkdir()

    def short_path(self, path: Path) -> Path:
        function = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
        function.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        function.restype = ctypes.c_uint32
        capacity = function(str(path), None, 0)
        if not capacity:
            self.skipTest("The filesystem does not expose Windows short-path aliases")
        buffer = ctypes.create_unicode_buffer(capacity)
        written = function(str(path), buffer, capacity)
        self.assertGreater(written, 0)
        self.assertLess(written, capacity)
        short = Path(buffer.value)
        if short == path:
            self.skipTest("The filesystem did not create a distinct short-path alias")
        self.assertTrue(path.samefile(short))
        return short

    def test_short_parent_creates_store_and_preserves_stage_and_restart(self) -> None:
        short_parent = self.short_path(self.directory)
        long_root = self.directory / "new store"
        store = ArtifactStore(short_parent / "new store")
        self.assertEqual(store.root, long_root.resolve())
        source = self.base / "Input With Spaces.mnova"
        source.write_bytes(b"raw-source")
        staged = store.stage(self.short_path(source))
        self.assertEqual(staged["files"][0]["path"], source.name)
        self.assertEqual(
            store.resolve(staged["source_id"], source.name).read_bytes(), b"raw-source"
        )
        output = long_root / "Output With Spaces.mnova"
        output.write_bytes(b"native-output")
        artifact = store.register(self.short_path(output), "job-1", "native_document")
        reopened = ArtifactStore(long_root)
        self.assertEqual(reopened.read(artifact["artifact_id"]), b"native-output")
        self.assertEqual(reopened.metadata(artifact["artifact_id"])["file_name"], output.name)

    def test_short_output_alias_belongs_to_existing_long_path_store(self) -> None:
        store = ArtifactStore(self.directory)
        output = self.directory / "Output With Spaces.mnova"
        output.write_bytes(b"native-output")
        artifact = store.register(self.short_path(output), "job-1", "native_document")
        self.assertEqual(store.read(artifact["artifact_id"]), b"native-output")

    def test_short_source_alias_cannot_contain_store(self) -> None:
        store = ArtifactStore(self.directory)
        (self.directory / "sample.mnova").write_bytes(b"raw-source")
        with self.assertRaises(ArtifactStoreError) as raised:
            store.stage(self.short_path(self.directory))
        self.assertEqual(raised.exception.code, "INVALID_PATH")
        self.assertEqual(list((self.directory / "sources").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
