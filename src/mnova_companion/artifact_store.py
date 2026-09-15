"""Bounded file staging and verified artifacts, without native/scientific APIs.

The caller authorizes the explicit input path before calling ``stage``. The
store never discovers inputs outside that selected file/directory. Its root
must be private to the current user; it is not a sandbox for hostile processes
with permission to concurrently replace that user's directories or metadata.

Source manifests contain only relative names. Their digest covers canonical
UTF-8 JSON for ``files`` and ``total_bytes`` (sorted keys, compact separators,
unescaped Unicode), independent of the newly assigned source ID. Artifact
records also persist only paths relative to the store, allowing restart.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import BinaryIO

_CHUNK_BYTES = 1024 * 1024
_MAX_METADATA_BYTES = 1024 * 1024
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_MEDIA_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class ArtifactStoreError(ValueError):
    """A bounded public error; messages never contain private absolute paths."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _fail(code: str, message: str) -> None:
    raise ArtifactStoreError(code, message)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _relative(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        _fail("INVALID_PATH", "A bounded relative file path is required.")
    parts = value.split("/")
    if (
        len(parts) > 64
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).drive
        or "\\" in value
        or any(ord(char) < 32 for char in value)
        or any(
            part in ("", ".", "..") or ":" in part or part.endswith((".", " ")) for part in parts
        )
    ):
        _fail("INVALID_PATH", "The relative file path is unsafe.")
    for part in parts:
        stem = part.split(".", 1)[0].upper()
        if stem in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"(?:COM|LPT)[1-9]", stem):
            _fail("INVALID_PATH", "A reserved file name is unsupported.")
    return value


def _identifier(value: str, prefix: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(prefix + r"_[0-9a-f]{32}", value):
        _fail("INVALID_ARGUMENT", "The identifier is invalid.")
    return value


def _label(value: str) -> str:
    if not isinstance(value, str) or not _LABEL.fullmatch(value):
        _fail("INVALID_ARGUMENT", "A bounded job or role identifier is required.")
    return value


def _absolute(path: Path) -> Path:
    path = Path(path)
    if ".." in path.parts:
        _fail("INVALID_PATH", "Parent-directory traversal is unsupported.")
    return path.absolute()


def _no_links(path: Path, *, missing_ok: bool = False) -> os.stat_result | None:
    """Check every lexical component before resolving, including parent links."""
    observed = None
    for component in (*reversed(path.parents), path):
        try:
            observed = component.lstat()
        except FileNotFoundError:
            if missing_ok:
                return None
            _fail("NOT_FOUND", "The selected file or directory is unavailable.")
        if (
            stat.S_ISLNK(observed.st_mode)
            or getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT
        ):
            _fail("INVALID_PATH", "Symbolic links and reparse points are unsupported.")
        if component != path and not stat.S_ISDIR(observed.st_mode):
            _fail("INVALID_PATH", "A parent path is not a directory.")
    return observed


def _same_snapshot(first: os.stat_result, second: os.stat_result) -> bool:
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    # On Windows 3.12, lstat and fstat can expose different ctime meanings
    # (creation time versus metadata-change time) for the same open file.
    if os.name != "nt":
        fields += ("st_ctime_ns",)
    return all(getattr(first, key) == getattr(second, key) for key in fields)


@contextmanager
def _io_errors() -> Iterator[None]:
    try:
        yield
    except ArtifactStoreError:
        raise
    except OSError:
        raise ArtifactStoreError(
            "STORAGE_ERROR", "The file operation could not be completed."
        ) from None


class ArtifactStore:
    """A private file store; all public result values are plain JSON dictionaries."""

    def __init__(
        self, root: Path, max_files: int = 1000, max_bytes: int = 256 * 1024 * 1024
    ) -> None:
        if (
            type(max_files) is not int
            or type(max_bytes) is not int
            or max_files < 1
            or max_bytes < 1
        ):
            _fail("INVALID_ARGUMENT", "File and byte limits must be positive integers.")
        self.max_files = max_files
        self.max_bytes = max_bytes
        self.root = _absolute(root)
        with _io_errors():
            _no_links(self.root, missing_ok=True)
            self.root.mkdir(parents=True, exist_ok=True)
            self._check_root()
            self._directory(self.root / "sources")
            self._directory(self.root / "artifact_metadata")

    def _check_root(self) -> None:
        observed = _no_links(self.root)
        if observed is None or not stat.S_ISDIR(observed.st_mode):
            _fail("INVALID_PATH", "The store root must be a directory.")

    def _inside(self, path: Path, *, missing_ok: bool = False) -> Path:
        self._check_root()
        path = _absolute(path)
        if not path.is_relative_to(self.root):
            _fail("INVALID_PATH", "The artifact must be inside the store root.")
        if path != self.root:
            _relative(path.relative_to(self.root).as_posix())
        _no_links(path, missing_ok=missing_ok)
        if not path.resolve(strict=not missing_ok).is_relative_to(self.root):
            _fail("INVALID_PATH", "The artifact escaped the store root.")
        return path

    def _directory(self, path: Path) -> None:
        self._inside(path, missing_ok=True)
        path.mkdir(parents=True, exist_ok=True)
        observed = _no_links(path)
        if observed is None or not stat.S_ISDIR(observed.st_mode):
            _fail("INVALID_PATH", "A store directory is unavailable.")

    @contextmanager
    def _reader(self, path: Path, expected: os.stat_result | None = None) -> Iterator[BinaryIO]:
        before = _no_links(path)
        if before is None or not stat.S_ISREG(before.st_mode):
            _fail("INVALID_PATH", "Only regular files are supported.")
        if expected is not None and not _same_snapshot(before, expected):
            _fail("SOURCE_CHANGED", "The selected file changed during staging.")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or not _same_snapshot(before, opened):
                _fail("SOURCE_CHANGED", "The file changed while it was being opened.")
            yield stream
            after = _no_links(path)
            if (
                after is None
                or not _same_snapshot(before, os.fstat(stream.fileno()))
                or not _same_snapshot(before, after)
            ):
                _fail("SOURCE_CHANGED", "The file changed during the read.")

    def _digest(
        self,
        path: Path,
        *,
        expected: os.stat_result | None = None,
        destination: Path | None = None,
        collect: bool = False,
    ) -> tuple[int, str, bytes]:
        total = 0
        digest = hashlib.sha256()
        content = bytearray()
        with self._reader(path, expected) as reader:
            writer = destination.open("xb") if destination is not None else None
            try:
                while chunk := reader.read(_CHUNK_BYTES):
                    total += len(chunk)
                    if total > self.max_bytes:
                        _fail("LIMIT_EXCEEDED", "The file exceeds the configured byte limit.")
                    digest.update(chunk)
                    if writer is not None:
                        writer.write(chunk)
                    if collect:
                        content.extend(chunk)
                if writer is not None:
                    writer.flush()
                    os.fsync(writer.fileno())
            finally:
                if writer is not None:
                    writer.close()
        return total, digest.hexdigest(), bytes(content)

    def _inventory(self, source: Path) -> list[tuple[str, Path, os.stat_result]]:
        source_stat = _no_links(source)
        if source_stat is None:
            _fail("NOT_FOUND", "The selected source is unavailable.")
        if stat.S_ISREG(source_stat.st_mode):
            candidates = [(_relative(source.name), source, source_stat)]
        elif stat.S_ISDIR(source_stat.st_mode):
            candidates = []
            pending = [source]
            entries_seen = 0
            byte_total = 0
            while pending:
                directory = pending.pop()
                _no_links(directory)
                with os.scandir(directory) as entries:
                    for entry in entries:
                        entries_seen += 1
                        if entries_seen > self.max_files * 8 + 64:
                            _fail(
                                "LIMIT_EXCEEDED", "The source contains too many directory entries."
                            )
                        path = directory / entry.name
                        relative = _relative(path.relative_to(source).as_posix())
                        observed = _no_links(path)
                        if observed is not None and stat.S_ISDIR(observed.st_mode):
                            pending.append(path)
                        elif observed is not None and stat.S_ISREG(observed.st_mode):
                            candidates.append((relative, path, observed))
                            byte_total += observed.st_size
                            if len(candidates) > self.max_files or byte_total > self.max_bytes:
                                _fail(
                                    "LIMIT_EXCEEDED",
                                    "The source exceeds the configured file or byte limit.",
                                )
                        else:
                            _fail("INVALID_PATH", "The source contains a non-regular file.")
        else:
            _fail("INVALID_PATH", "Only regular files and directories are supported.")
        if not candidates:
            _fail("INVALID_ARGUMENT", "The source contains no files.")
        if (
            len(candidates) > self.max_files
            or sum(item[2].st_size for item in candidates) > self.max_bytes
        ):
            _fail("LIMIT_EXCEEDED", "The source exceeds the configured file or byte limit.")
        return sorted(candidates, key=lambda item: item[0])

    def _atomic_json(self, path: Path, payload: dict) -> None:
        self._inside(path, missing_ok=True)
        data = _canonical(payload)
        if len(data) > _MAX_METADATA_BYTES:
            _fail("LIMIT_EXCEEDED", "The metadata exceeds the supported size limit.")
        temporary = path.parent / ("tmp_" + uuid.uuid4().hex + ".json")
        try:
            with temporary.open("xb") as writer:
                writer.write(data)
                writer.flush()
                os.fsync(writer.fileno())
            self._inside(path, missing_ok=True)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                self._inside(temporary)
                temporary.unlink()

    def _load_json(self, path: Path) -> dict:
        self._inside(path)
        with self._reader(path) as reader:
            data = reader.read(_MAX_METADATA_BYTES + 1)
        if len(data) > _MAX_METADATA_BYTES:
            _fail("INVALID_METADATA", "The stored metadata exceeds the supported limit.")
        try:
            result = json.loads(data)
        except (ValueError, UnicodeError, RecursionError):
            _fail("INVALID_METADATA", "The stored metadata is invalid.")
        if not isinstance(result, dict):
            _fail("INVALID_METADATA", "The stored metadata must be an object.")
        return result

    def stage(self, source: Path) -> dict:
        """Copy an authorized source, then atomically publish its complete manifest."""
        with _io_errors():
            self._check_root()
            source = _absolute(source)
            _no_links(source)
            if self.root.is_relative_to(source):
                _fail("INVALID_PATH", "The input directory cannot contain the store itself.")
            inventory = self._inventory(source)
            source_id = "src_" + uuid.uuid4().hex
            parent = self.root / "sources"
            self._directory(parent)
            staging = parent / ("pending_" + uuid.uuid4().hex)
            self._directory(staging / "data")
            try:
                files = []
                total = 0
                for relative, source_path, observed in inventory:
                    destination = staging / "data" / relative
                    self._directory(destination.parent)
                    size, digest, _ = self._digest(
                        source_path, expected=observed, destination=destination
                    )
                    total += size
                    if total > self.max_bytes:
                        _fail("LIMIT_EXCEEDED", "The source exceeds the configured byte limit.")
                    read_size, read_digest, _ = self._digest(destination)
                    if (read_size, read_digest) != (size, digest):
                        _fail("INTEGRITY_ERROR", "The staged file failed its integrity check.")
                    files.append({"path": relative, "size_bytes": size, "sha256": digest})
                # Detect changes to an earlier file or directory membership before publishing.
                final_inventory = self._inventory(source)
                if len(inventory) != len(final_inventory) or any(
                    first[:2] != last[:2] or not _same_snapshot(first[2], last[2])
                    for first, last in zip(inventory, final_inventory, strict=True)
                ):
                    _fail("SOURCE_CHANGED", "The selected source changed during staging.")
                body = {"files": files, "total_bytes": total}
                manifest = {
                    "source_id": source_id,
                    **body,
                    "manifest_sha256": hashlib.sha256(_canonical(body)).hexdigest(),
                }
                self._atomic_json(staging / "manifest.json", manifest)
                destination = self._inside(parent / source_id, missing_ok=True)
                os.replace(staging, destination)
                return manifest
            finally:
                if staging.exists():
                    # Never recursively remove a computed path without checking its final target.
                    checked = self._inside(staging)
                    if checked.parent == parent and checked.name.startswith("pending_"):
                        shutil.rmtree(checked)

    def _source_manifest(self, source_id: str) -> dict:
        _identifier(source_id, "src")
        payload = self._load_json(self.root / "sources" / source_id / "manifest.json")
        if (
            set(payload) != {"source_id", "files", "total_bytes", "manifest_sha256"}
            or payload["source_id"] != source_id
            or not isinstance(payload["files"], list)
            or not 1 <= len(payload["files"]) <= self.max_files
            or type(payload["total_bytes"]) is not int
            or not 0 <= payload["total_bytes"] <= self.max_bytes
            or not isinstance(payload["manifest_sha256"], str)
            or not _SHA256.fullmatch(payload["manifest_sha256"])
        ):
            _fail("INVALID_METADATA", "The stored source manifest is invalid.")
        seen = []
        total = 0
        for item in payload["files"]:
            if not isinstance(item, dict) or set(item) != {"path", "size_bytes", "sha256"}:
                _fail("INVALID_METADATA", "A source manifest entry is invalid.")
            seen.append(_relative(item["path"]))
            self._file_fields(item)
            total += item["size_bytes"]
        if seen != sorted(set(seen)) or total != payload["total_bytes"]:
            _fail("INVALID_METADATA", "The source manifest has inconsistent entries.")
        body = {"files": payload["files"], "total_bytes": total}
        if hashlib.sha256(_canonical(body)).hexdigest() != payload["manifest_sha256"]:
            _fail("INTEGRITY_ERROR", "The source manifest failed its integrity check.")
        return payload

    def _file_fields(self, metadata: dict) -> None:
        if (
            type(metadata["size_bytes"]) is not int
            or not 0 <= metadata["size_bytes"] <= self.max_bytes
            or not isinstance(metadata["sha256"], str)
            or not _SHA256.fullmatch(metadata["sha256"])
        ):
            _fail("INVALID_METADATA", "The stored file metadata is invalid.")

    def resolve(self, source_id: str, relative_path: str) -> Path:
        """Return an internal path only for a listed, unchanged staged file."""
        with _io_errors():
            relative_path = _relative(relative_path)
            manifest = self._source_manifest(source_id)
            item = next((item for item in manifest["files"] if item["path"] == relative_path), None)
            if item is None:
                _fail("NOT_FOUND", "The requested file is not listed in this source manifest.")
            path = self._inside(self.root / "sources" / source_id / "data" / relative_path)
            size, digest, _ = self._digest(path)
            if (size, digest) != (item["size_bytes"], item["sha256"]):
                _fail("INTEGRITY_ERROR", "The staged file failed its integrity check.")
            return path

    def register(self, path: Path, job_id: str, role: str) -> dict:
        """Record a complete output file inside the root, without modifying it."""
        _label(job_id)
        _label(role)
        with _io_errors():
            path = self._inside(path)
            size, digest, _ = self._digest(path)
            artifact_id = "art_" + uuid.uuid4().hex
            metadata = {
                "artifact_id": artifact_id,
                "file_name": path.name,
                "size_bytes": size,
                "sha256": digest,
                "media_type": _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream"),
                "job_id": job_id,
                "role": role,
            }
            record = {
                "version": 1,
                "relative_path": path.relative_to(self.root).as_posix(),
                "metadata": metadata,
            }
            self._atomic_json(self.root / "artifact_metadata" / (artifact_id + ".json"), record)
            return metadata

    def _artifact_record(self, artifact_id: str) -> tuple[Path, dict]:
        _identifier(artifact_id, "art")
        record = self._load_json(self.root / "artifact_metadata" / (artifact_id + ".json"))
        if (
            set(record) != {"version", "relative_path", "metadata"}
            or type(record["version"]) is not int
            or record["version"] != 1
        ):
            _fail("INVALID_METADATA", "The stored artifact record is invalid.")
        relative = _relative(record["relative_path"])
        metadata = record["metadata"]
        if (
            not isinstance(metadata, dict)
            or set(metadata)
            != {"artifact_id", "file_name", "size_bytes", "sha256", "media_type", "job_id", "role"}
            or metadata["artifact_id"] != artifact_id
            or metadata["file_name"] != PurePosixPath(relative).name
            or metadata["media_type"]
            != _MEDIA_TYPES.get(PurePosixPath(relative).suffix.lower(), "application/octet-stream")
        ):
            _fail("INVALID_METADATA", "The stored artifact metadata is invalid.")
        self._file_fields(metadata)
        _label(metadata["job_id"])
        _label(metadata["role"])
        path = self._inside(self.root / relative)
        return path, metadata

    def metadata(self, artifact_id: str) -> dict:
        """Return the registration snapshot; ``read`` verifies current bytes."""
        with _io_errors():
            _, metadata = self._artifact_record(artifact_id)
            return metadata

    def list_artifacts(self, job_id: str | None = None) -> list[dict]:
        """List validated registration snapshots, sorted by opaque artifact ID.

        Only the store's flat metadata registry is enumerated. The registry is
        bounded by ``max_files`` records; this is an initial small-store API,
        not an unbounded catalog. The caller may paginate the returned list.
        """
        if job_id is not None:
            _label(job_id)
        with _io_errors():
            registry = self._inside(self.root / "artifact_metadata")
            identifiers = []
            with os.scandir(registry) as entries:
                for index, entry in enumerate(entries):
                    if index >= self.max_files * 2 + 64:
                        _fail("LIMIT_EXCEEDED", "The artifact registry has too many entries.")
                    if re.fullmatch(r"art_[0-9a-f]{32}\.json", entry.name):
                        identifiers.append(entry.name[:-5])
                        if len(identifiers) > self.max_files:
                            _fail(
                                "LIMIT_EXCEEDED", "The artifact registry exceeds the listing limit."
                            )
            result = []
            for artifact_id in sorted(identifiers):
                metadata = self.metadata(artifact_id)
                if job_id is None or metadata["job_id"] == job_id:
                    result.append(metadata)
            return result

    def read(self, artifact_id: str) -> bytes:
        """Read bounded bytes and reject changes against the registered hash/size."""
        with _io_errors():
            path, metadata = self._artifact_record(artifact_id)
            size, digest, content = self._digest(path, collect=True)
            if (size, digest) != (metadata["size_bytes"], metadata["sha256"]):
                _fail("INTEGRITY_ERROR", "The artifact failed its integrity check.")
            return content
