"""Atomic, no-replace writes for generated project files."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class FilePublication:
    """Identity of one file atomically published by this process."""

    path: Path
    device: int
    inode: int


def write_new_text_file(path: Path, content: str) -> FilePublication:
    """Publish complete UTF-8 content only if ``path`` is still absent."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = -1
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        stream = os.fdopen(descriptor, mode="w", encoding="utf-8", newline="")
        descriptor = -1
        with stream:
            _write_and_sync(stream, content)
        temporary_path.chmod(0o644)
        identity = temporary_path.lstat()
        # A hard link publishes the complete inode atomically and, unlike
        # os.replace(), fails if a concurrent writer already created ``path``.
        os.link(temporary_path, path)
        return FilePublication(
            path=path,
            device=identity.st_dev,
            inode=identity.st_ino,
        )
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                # Cleanup is best-effort and must not hide the write outcome.
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                # A leaked hidden temporary is safer than masking the primary result.
                pass


def replace_text_file_if_unchanged(
    path: Path,
    *,
    expected: bytes,
    content: str,
) -> FilePublication:
    """Publish a complete replacement after rechecking its planned bytes.

    Blueprint migrations are explicit updates, unlike initial scaffolding where a
    no-replace hard link is sufficient.  The caller supplies the exact snapshot
    it planned against; a locally edited or replaced target observed before
    publication is refused rather than overwritten silently.
    """

    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Migration target must be a regular file: {path}")
    if path.read_bytes() != expected:
        raise ValueError(f"File changed after migration planning; rerun the command: {path}")

    descriptor = -1
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        stream = os.fdopen(descriptor, mode="w", encoding="utf-8", newline="")
        descriptor = -1
        with stream:
            _write_and_sync(stream, content)
        temporary_path.chmod(0o644)
        if path.read_bytes() != expected:
            raise ValueError(
                f"File changed after migration planning; rerun the command: {path}"
            )
        os.replace(temporary_path, path)
        identity = path.lstat()
        return FilePublication(
            path=path,
            device=identity.st_dev,
            inode=identity.st_ino,
        )
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def _write_and_sync(stream: TextIO, content: str) -> None:
    stream.write(content)
    stream.flush()
    os.fsync(stream.fileno())
