"""Explicit, additive migrations for generated state-machine features."""

from __future__ import annotations

import keyword
from dataclasses import dataclass, replace
from pathlib import Path

from arclith_cli.application_blueprint_files import with_package_initializers
from arclith_cli.application_blueprints import (
    application_blueprint_digest,
    application_parameters_digest,
    get_application_blueprint,
    render_application_blueprint,
)
from arclith_cli.atomic_writes import (
    FilePublication,
    replace_text_file_if_unchanged,
    write_new_text_file,
)
from arclith_cli.entity_scanner import EntityInfo, scan_blueprint_models
from arclith_cli.feature_manifest import (
    FeatureDigests,
    FeatureManifest,
    load_feature_manifest,
    render_feature_manifest,
)
from arclith_cli.project_paths import detect_project_paths
from arclith_cli.rename import EntityNames
from arclith_cli.state_machine_spec import StateMachineSpec

MIGRATION_KIND = "state-machine-additive-transitions-v1"


@dataclass(frozen=True)
class StateMachineMigrationPlan:
    """One preflighted update from a generated matrix to an additive successor."""

    project_dir: Path
    feature: str
    entity: EntityInfo
    previous_manifest: FeatureManifest
    target_manifest: FeatureManifest
    manifest_path: Path
    creations: dict[Path, str]
    replacements: dict[Path, tuple[bytes, str]]
    preserved: tuple[Path, ...]


def plan_state_machine_migration(
    project_dir: Path,
    *,
    entity_name: str,
    feature_name: str | None,
    parameters: dict[str, object],
) -> StateMachineMigrationPlan:
    """Plan an additive transition migration without touching project files.

    Existing transition semantics, states and the generated template must stay
    intact.  Shared generated files are only eligible for replacement when they
    exactly match their previous canonical rendering, so project-owned changes
    cannot be overwritten accidentally.
    """

    blueprint = get_application_blueprint("state-machine")
    entity = _require_entity(project_dir, entity_name)
    feature = _feature_name(feature_name or entity.snake)
    manifest_path = project_dir / ".arclith" / "features" / f"{feature}.yaml"
    previous = load_feature_manifest(manifest_path)
    _validate_previous_manifest(previous, blueprint.name, blueprint.version, entity, feature)

    previous_spec = StateMachineSpec.from_parameters(previous.parameters)
    if previous.operations != previous_spec.operations:
        raise ValueError(
            "State-machine migration requires manifest operations to match its parameters"
        )
    target_spec = StateMachineSpec.from_parameters(parameters)
    _validate_additive_transition_migration(previous_spec, target_spec)

    paths = detect_project_paths(project_dir)
    previous_files = with_package_initializers(
        paths,
        render_application_blueprint(
            blueprint,
            paths,
            entity,
            feature,
            previous_spec.to_parameters(),
            creating_entity=False,
        ),
    )
    target_files = with_package_initializers(
        paths,
        render_application_blueprint(
            blueprint,
            paths,
            entity,
            feature,
            target_spec.to_parameters(),
            creating_entity=False,
        ),
    )
    removed = set(previous_files) - set(target_files)
    if removed:
        labels = ", ".join(
            str(path.relative_to(project_dir)) for path in sorted(removed)
        )
        raise ValueError(f"Additive state-machine migration would remove files: {labels}")

    creations: dict[Path, str] = {}
    replacements: dict[Path, tuple[bytes, str]] = {}
    preserved: list[Path] = []
    for path, target_content in target_files.items():
        previous_content = previous_files.get(path)
        if previous_content is None:
            if path.exists():
                raise ValueError(
                    "Migration target already exists before creation: "
                    f"{path.relative_to(project_dir)}"
                )
            creations[path] = target_content
            continue
        if target_content == previous_content:
            preserved.append(path)
            continue
        _require_canonical_file(
            path,
            expected=previous_content.encode("utf-8"),
            project_dir=project_dir,
        )
        replacements[path] = (previous_content.encode("utf-8"), target_content)

    target_parameters_digest = application_parameters_digest(
        blueprint,
        target_spec.to_parameters(),
    )
    if target_parameters_digest is None:  # pragma: no cover - state-machine is parameterized
        raise RuntimeError("State-machine migration requires a parameters digest")
    target_manifest = replace(
        previous,
        operations=target_spec.operations,
        parameters=target_spec.to_parameters(),
        digests=FeatureDigests(
            template=application_blueprint_digest(blueprint),
            parameters=target_parameters_digest,
        ),
    )
    _require_canonical_file(
        manifest_path,
        expected=render_feature_manifest(previous).encode("utf-8"),
        project_dir=project_dir,
    )
    replacements[manifest_path] = (
        render_feature_manifest(previous).encode("utf-8"),
        render_feature_manifest(target_manifest),
    )
    return StateMachineMigrationPlan(
        project_dir=project_dir,
        feature=feature,
        entity=entity,
        previous_manifest=previous,
        target_manifest=target_manifest,
        manifest_path=manifest_path,
        creations=creations,
        replacements=replacements,
        preserved=tuple(sorted(preserved)),
    )


def apply_state_machine_migration(
    plan: StateMachineMigrationPlan,
) -> tuple[Path, ...]:
    """Apply a fully preflighted migration and compensate partial publication."""

    created: list[FilePublication] = []
    replaced: list[tuple[Path, bytes, str, FilePublication]] = []
    try:
        for path, content in plan.creations.items():
            created.append(write_new_text_file(path, content))
        for path, (expected, content) in plan.replacements.items():
            publication = replace_text_file_if_unchanged(
                path,
                expected=expected,
                content=content,
            )
            replaced.append((path, expected, content, publication))
    except Exception:
        _restore_replacements(replaced)
        _remove_creations(created, plan.creations)
        raise
    return tuple((*plan.creations, *plan.replacements))


def _validate_previous_manifest(
    manifest: FeatureManifest,
    blueprint_name: str,
    blueprint_version: int,
    entity: EntityInfo,
    feature: str,
) -> None:
    if manifest.feature != feature:
        raise ValueError("State-machine migration feature does not match its manifest")
    if manifest.entity is None or manifest.entity.name != entity.pascal:
        raise ValueError("State-machine migration entity does not match its manifest")
    if manifest.blueprint.name != blueprint_name or manifest.blueprint.version != blueprint_version:
        raise ValueError("State-machine migration requires the installed state-machine blueprint")
    if manifest.parameters is None or manifest.digests is None:
        raise ValueError("State-machine migration requires a parameterized feature manifest")
    expected_template = application_blueprint_digest(get_application_blueprint(blueprint_name))
    if manifest.digests.template != expected_template:
        raise ValueError(
            "State-machine migration requires the current renderer to match the "
            "installed feature template digest"
        )


def _validate_additive_transition_migration(
    previous: StateMachineSpec,
    target: StateMachineSpec,
) -> None:
    if previous.state_field != target.state_field:
        raise ValueError("State-machine migration cannot change state_field")
    if previous.initial_state != target.initial_state:
        raise ValueError("State-machine migration cannot change initial_state")
    if previous.states != target.states:
        raise ValueError(
            "State-machine migration supports transitions between existing states only"
        )
    target_by_name = {transition.name: transition for transition in target.transitions}
    for transition in previous.transitions:
        if target_by_name.get(transition.name) != transition:
            raise ValueError(
                "State-machine migration cannot remove or alter an existing transition: "
                f"{transition.name}"
            )
    additions = tuple(
        transition
        for transition in target.transitions
        if transition.name not in {item.name for item in previous.transitions}
    )
    if not additions:
        raise ValueError("State-machine migration must add at least one transition")


def _require_entity(project_dir: Path, raw_name: str) -> EntityInfo:
    normalized = EntityNames.from_input(raw_name.strip())
    entity = next(
        (
            candidate
            for candidate in scan_blueprint_models(project_dir)
            if candidate.pascal == normalized.pascal or candidate.snake == normalized.snake
        ),
        None,
    )
    if entity is None:
        raise ValueError(f"State-machine migration entity was not found: {raw_name}")
    return entity


def _feature_name(raw: str) -> str:
    feature = raw.strip().lower().replace("-", "_")
    if not feature.isidentifier() or feature.startswith("_") or keyword.iskeyword(feature):
        raise ValueError(f"Invalid public feature name: {raw!r}")
    return feature


def _require_canonical_file(path: Path, *, expected: bytes, project_dir: Path) -> None:
    if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
        raise ValueError(
            "State-machine migration preserves developer-owned files; restore the "
            "canonical generated file or migrate its change manually: "
            f"{path.relative_to(project_dir)}"
        )


def _restore_replacements(
    replaced: list[tuple[Path, bytes, str, FilePublication]],
) -> None:
    for path, expected, content, publication in reversed(replaced):
        try:
            identity = path.lstat()
            if (identity.st_dev, identity.st_ino) != (publication.device, publication.inode):
                continue
            replace_text_file_if_unchanged(
                path,
                expected=content.encode("utf-8"),
                content=expected.decode("utf-8"),
            )
        except (OSError, ValueError):
            continue


def _remove_creations(
    created: list[FilePublication],
    contents: dict[Path, str],
) -> None:
    for publication in reversed(created):
        try:
            identity = publication.path.lstat()
            if (identity.st_dev, identity.st_ino) != (publication.device, publication.inode):
                continue
            if publication.path.read_text(encoding="utf-8") != contents[publication.path]:
                continue
            publication.path.unlink()
        except OSError:
            continue
