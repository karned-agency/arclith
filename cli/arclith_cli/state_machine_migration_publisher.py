"""Filesystem publication and compensation for state-machine migrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from arclith_cli.atomic_writes import (
    FilePublication,
    replace_text_file_if_unchanged,
    write_new_text_file,
)
from arclith_cli.state_machine_migration import StateMachineMigrationPlan


@dataclass(frozen=True)
class StateMachineMigrationPublication:
    """Files published by one migration, retained for safe compensation."""

    plan: StateMachineMigrationPlan
    created: tuple[FilePublication, ...]
    replaced: tuple[FilePublication, ...]

    @property
    def changed(self) -> tuple[Path, ...]:
        """Return all paths published by the migration in write order."""

        return tuple(
            publication.path for publication in (*self.created, *self.replaced)
        )


def apply_state_machine_migration(
    plan: StateMachineMigrationPlan,
) -> StateMachineMigrationPublication:
    """Apply a fully preflighted migration and compensate partial publication."""

    created: list[FilePublication] = []
    replaced: list[FilePublication] = []
    try:
        for path, content in plan.creations.items():
            created.append(write_new_text_file(path, content))
        for path, (expected, content) in plan.replacements.items():
            replaced.append(
                replace_text_file_if_unchanged(
                    path,
                    expected=expected,
                    content=content,
                )
            )
    except Exception as exc:
        publication = StateMachineMigrationPublication(
            plan=plan,
            created=tuple(created),
            replaced=tuple(replaced),
        )
        _compensate_publication(publication, original_error=exc)
        raise
    return StateMachineMigrationPublication(
        plan=plan,
        created=tuple(created),
        replaced=tuple(replaced),
    )


def rollback_state_machine_migration(
    publication: StateMachineMigrationPublication,
) -> None:
    """Safely restore a successful migration after its recipe write fails."""

    _compensate_publication(publication, original_error=None)


def _compensate_publication(
    publication: StateMachineMigrationPublication,
    *,
    original_error: Exception | None,
) -> None:
    unresolved = [
        *_restore_replacements(publication),
        *_remove_creations(publication.created, publication.plan.creations),
    ]
    if unresolved:
        labels = ", ".join(
            str(path.relative_to(publication.plan.project_dir)) for path in unresolved
        )
        error = OSError(
            "State-machine migration could not be rolled back safely; inspect: "
            + labels
        )
        if original_error is not None:
            raise error from original_error
        raise error


def _restore_replacements(
    publication: StateMachineMigrationPublication,
) -> tuple[Path, ...]:
    unresolved: list[Path] = []
    for replaced in reversed(publication.replaced):
        path = replaced.path
        expected, content = publication.plan.replacements[path]
        try:
            identity = path.lstat()
            if (identity.st_dev, identity.st_ino) != (replaced.device, replaced.inode):
                unresolved.append(path)
                continue
            replace_text_file_if_unchanged(
                path,
                expected=content.encode("utf-8"),
                content=expected.decode("utf-8"),
            )
        except (OSError, ValueError):
            unresolved.append(path)
            continue
    return tuple(unresolved)


def _remove_creations(
    created: tuple[FilePublication, ...],
    contents: dict[Path, str],
) -> tuple[Path, ...]:
    unresolved: list[Path] = []
    for publication in reversed(created):
        try:
            identity = publication.path.lstat()
            if (identity.st_dev, identity.st_ino) != (
                publication.device,
                publication.inode,
            ):
                unresolved.append(publication.path)
                continue
            if (
                publication.path.read_text(encoding="utf-8")
                != contents[publication.path]
            ):
                unresolved.append(publication.path)
                continue
            publication.path.unlink()
        except OSError:
            unresolved.append(publication.path)
            continue
    return tuple(unresolved)
