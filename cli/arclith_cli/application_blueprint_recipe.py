from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from arclith_cli.application_blueprints import (
    application_blueprint_digest,
    application_parameters_digest,
    canonical_blueprint_parameters,
    get_application_blueprint,
)
from arclith_cli.blueprint_generation import (
    add_application_blueprint_cmd,
    create_entity_with_application_blueprint,
    plan_application_profile_for_new_entity,
)
from arclith_cli.core_scaffold import add_entity_cmd
from arclith_cli.project_paths import detect_project_paths
from arclith_cli.recipe_models import RecipeError
from arclith_cli.application_blueprint_recipe_models import MigrateBlueprintRecipeArgs
from arclith_cli.state_machine_entity import render_state_machine_entity
from arclith_cli.state_machine_migration import plan_state_machine_migration
from arclith_cli.state_machine_migration_publisher import apply_state_machine_migration
from arclith_cli.state_machine_spec import StateMachineSpec

ApplicationBlueprintRecipeHandler = Callable[[Path, dict[str, Any]], None]

APPLICATION_BLUEPRINT_RECIPE_COMMANDS = frozenset(
    {"add-entity", "add-blueprint", "migrate-blueprint"}
)


def replay_application_blueprint_step(
    command: str,
    target_dir: Path,
    args: dict[str, Any],
) -> None:
    """Replay entity and application-blueprint recipe operations."""
    try:
        handler = _APPLICATION_BLUEPRINT_RECIPE_HANDLERS[command]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported application blueprint recipe command: {command}"
        ) from exc
    handler(target_dir, args)


def is_application_blueprint_recipe_command(command: str) -> bool:
    """Return whether a command is replayed by the application-blueprint module."""

    return command in APPLICATION_BLUEPRINT_RECIPE_COMMANDS


def validate_application_blueprint_recipe_step(
    command: str,
    args: dict[str, Any],
) -> None:
    """Preflight one application-blueprint recipe step before any write."""

    if command == "add-entity":
        validate_application_recipe_metadata(str(args.get("profile", "minimal")), args)
        return
    if command == "add-blueprint":
        validate_application_recipe_metadata(required_recipe_blueprint_name(args), args)
        return
    if command == "migrate-blueprint":
        migration = parse_migrate_blueprint_recipe_args(args)
        validate_application_recipe_metadata(
            migration.blueprint,
            migration.model_dump(mode="python"),
        )
        return
    raise ValueError(f"Unsupported application blueprint recipe command: {command}")


def replay_add_entity_step(target_dir: Path, args: dict[str, Any]) -> None:
    """Replay entity creation, including an optional application profile."""
    entity = str(args["entity"])
    profile = str(args.get("profile", "minimal"))
    validate_application_recipe_metadata(profile, args)
    raw_parameters = args.get("parameters")
    parameters = raw_parameters if isinstance(raw_parameters, dict) else None
    blueprint_plan = plan_application_profile_for_new_entity(
        target_dir,
        profile_name=profile,
        entity_name=entity,
        parameters=parameters,
    )
    entity_content = None
    if blueprint_plan is not None and blueprint_plan.blueprint.name == "state-machine":
        entity_content = render_state_machine_entity(
            detect_project_paths(target_dir),
            blueprint_plan.entity,
            StateMachineSpec.from_parameters(blueprint_plan.parameters),
        )
    if blueprint_plan is not None:
        create_entity_with_application_blueprint(
            blueprint_plan,
            entity_name=entity,
            entity_content=entity_content,
        )
    else:
        add_entity_cmd(project_dir=target_dir, entity_name=entity)


def replay_add_blueprint_step(target_dir: Path, args: dict[str, Any]) -> None:
    """Replay a standalone application-blueprint decision."""
    feature = args.get("feature")
    blueprint_name = required_recipe_blueprint_name(args)
    validate_application_recipe_metadata(blueprint_name, args)
    raw_parameters = args.get("parameters")
    parameters = raw_parameters if isinstance(raw_parameters, dict) else None
    add_application_blueprint_cmd(
        project_dir=target_dir,
        blueprint_name=blueprint_name,
        entity_name=None if args.get("no_entity") is True else str(args["entity"]),
        feature_name=str(feature) if feature else None,
        dry_run=False,
        parameters=parameters,
    )


def replay_migrate_blueprint_step(target_dir: Path, args: dict[str, Any]) -> None:
    """Replay one explicit additive state-machine migration."""

    migration = parse_migrate_blueprint_recipe_args(args)
    validate_application_recipe_metadata(
        migration.blueprint,
        migration.model_dump(mode="python"),
    )
    plan = plan_state_machine_migration(
        target_dir,
        entity_name=migration.entity,
        feature_name=migration.feature,
        parameters=migration.parameters,
    )
    previous_digests = plan.previous_manifest.digests
    if (
        previous_digests is None
        or previous_digests.parameters != migration.from_parameters_digest
    ):
        raise RecipeError("Recipe state-machine migration source digest does not match")
    apply_state_machine_migration(plan)


def parse_migrate_blueprint_recipe_args(
    args: Mapping[str, Any],
) -> MigrateBlueprintRecipeArgs:
    """Parse persisted migration arguments into the strict replay contract."""

    try:
        return MigrateBlueprintRecipeArgs.model_validate(args)
    except ValidationError as exc:
        raise RecipeError(
            "Invalid state-machine migration recipe arguments: " + str(exc)
        ) from exc


def required_recipe_blueprint_name(args: dict[str, Any]) -> str:
    """Return a statically valid blueprint name from recorded recipe metadata."""

    blueprint_name = args.get("blueprint")
    if not isinstance(blueprint_name, str) or not blueprint_name.strip():
        raise RecipeError(
            "Recipe add-blueprint step requires a non-empty string 'blueprint'"
        )
    return blueprint_name


def validate_application_recipe_metadata(
    blueprint_name: str,
    args: dict[str, Any],
) -> None:
    """Reject recorded template or parameter drift before replay writes."""

    if blueprint_name == "minimal":
        blueprint_metadata = {
            "blueprint",
            "blueprint_version",
            "operations",
            "parameters",
            "parameters_digest",
            "template_digest",
        } & args.keys()
        if blueprint_metadata:
            raise RecipeError(
                "Minimal application profile cannot include blueprint metadata: "
                + ", ".join(sorted(blueprint_metadata))
            )
        return
    try:
        blueprint = get_application_blueprint(blueprint_name)
    except ValueError as exc:
        raise RecipeError(
            f"Recipe references an invalid blueprint {blueprint_name!r}: {exc}"
        ) from exc
    recorded_template = args.get("template_digest")
    recorded_parameters = args.get("parameters_digest")
    required_parameterized_metadata = {
        "blueprint_version",
        "operations",
        "parameters_digest",
        "template_digest",
    }
    missing_metadata = {
        key
        for key in required_parameterized_metadata
        if key not in args or args[key] is None
    }
    if blueprint.parameterized and missing_metadata:
        raise RecipeError(
            f"Parameterized blueprint {blueprint.name!r} replay requires complete "
            "metadata: " + ", ".join(sorted(required_parameterized_metadata))
        )
    raw_parameters = args.get("parameters")
    try:
        parameters = canonical_blueprint_parameters(blueprint, raw_parameters)
    except ValueError as exc:
        raise RecipeError(
            f"Blueprint {blueprint.name!r} has invalid recorded parameters: {exc}"
        ) from exc
    expected_operations = blueprint.operations
    if blueprint.name == "state-machine":
        expected_operations = StateMachineSpec.from_parameters(parameters).operations
    if blueprint.name in {"job", "workflow"}:
        _validate_job_target(args, blueprint.name)
    if blueprint.name == "synchronization":
        entity = args.get("entity")
        if not isinstance(entity, str) or not entity.strip() or args.get("no_entity", False) is not False:
            raise RecipeError("Synchronization requires an entity-scoped recipe target")
    recorded_version = args.get("blueprint_version")
    if "blueprint_version" in args and (
        type(recorded_version) is not int or recorded_version != blueprint.version
    ):
        raise RecipeError(
            f"Blueprint {blueprint.name!r} version drift: recorded "
            f"{recorded_version!r}, current {blueprint.version!r}"
        )
    recorded_operations = args.get("operations")
    if "operations" in args and recorded_operations != list(expected_operations):
        raise RecipeError(
            f"Blueprint {blueprint.name!r} operations drift: recorded "
            f"{recorded_operations!r}, current {list(expected_operations)!r}"
        )
    expected_template = application_blueprint_digest(blueprint)
    if recorded_template is not None and recorded_template != expected_template:
        raise RecipeError(
            f"Blueprint {blueprint.name!r} template digest drift: "
            f"recorded {recorded_template!r}, current {expected_template!r}"
        )
    expected_parameters = application_parameters_digest(blueprint, parameters)
    if recorded_parameters is not None and recorded_parameters != expected_parameters:
        raise RecipeError(
            f"Blueprint {blueprint.name!r} parameters digest drift: "
            f"recorded {recorded_parameters!r}, current {expected_parameters!r}"
        )


def _validate_job_target(args: dict[str, Any], blueprint_name: str = "job") -> None:
    if type(args.get("target_version")) is not int or args["target_version"] != 1:
        raise RecipeError(f"{blueprint_name} recipe requires target_version integer 1")
    entity = args.get("entity")
    standalone = args.get("no_entity")
    if standalone is True:
        if "entity" in args or not isinstance(args.get("feature"), str) or not args["feature"].strip():
            raise RecipeError(f"Standalone {blueprint_name} requires --feature and excludes --entity")
    elif "no_entity" in args or not isinstance(entity, str) or not entity.strip():
        raise RecipeError(f"{blueprint_name} recipe requires exactly one entity or no_entity=true target")


_APPLICATION_BLUEPRINT_RECIPE_HANDLERS: dict[str, ApplicationBlueprintRecipeHandler] = {
    "add-entity": replay_add_entity_step,
    "add-blueprint": replay_add_blueprint_step,
    "migrate-blueprint": replay_migrate_blueprint_step,
}
