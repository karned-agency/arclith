from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parents[2]
PLUGIN_ROOT = PROJECT_ROOT / "plugins" / "arclith"
EXPECTED_SKILLS = {
    "arclith",
    "arclith-agent",
    "arclith-api",
    "arclith-audit",
    "arclith-deploy",
}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_skill(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    match = re.fullmatch(r"---\n(.*?)\n---\n(.*)", text, flags=re.DOTALL)
    assert match is not None, f"invalid SKILL.md frontmatter in {path}"
    metadata = yaml.safe_load(match.group(1))
    assert isinstance(metadata, dict)
    return metadata, match.group(2)


def test_agent_plugin_manifests_share_identity_and_version() -> None:
    portable = _load_json(PLUGIN_ROOT / "plugin.json")
    codex = _load_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
    claude = _load_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")

    assert portable["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert {portable["name"], codex["name"], claude["name"]} == {"arclith"}
    assert {portable["version"], codex["version"], claude["version"]} == {"0.1.0"}
    assert portable["license"] == codex["license"] == claude["license"]


def test_agent_plugin_marketplaces_reference_the_packaged_plugin() -> None:
    codex_marketplace = _load_json(
        PROJECT_ROOT / ".agents" / "plugins" / "marketplace.json"
    )
    claude_marketplace = _load_json(
        PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
    )

    assert codex_marketplace["name"] == "arclith"
    assert codex_marketplace["plugins"][0]["name"] == "arclith"  # type: ignore[index]
    assert (
        codex_marketplace["plugins"][0]["source"]["path"]  # type: ignore[index]
        == "./plugins/arclith"
    )
    assert claude_marketplace["name"] == "arclith"
    assert claude_marketplace["plugins"][0]["name"] == "arclith"  # type: ignore[index]
    assert (
        claude_marketplace["plugins"][0]["source"]  # type: ignore[index]
        == "./plugins/arclith"
    )


def test_agent_skills_are_portable_and_complete() -> None:
    skill_files = sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md"))

    assert {path.parent.name for path in skill_files} == EXPECTED_SKILLS
    for path in skill_files:
        metadata, body = _load_skill(path)
        assert metadata["name"] == path.parent.name
        assert isinstance(metadata["description"], str)
        assert metadata["description"].strip()
        assert len(metadata["description"]) <= 1024
        assert metadata["license"] == "Apache-2.0"
        assert "TODO" not in body
        assert not re.search(r"\b(?:Codex|Claude)\b", body)

        for reference in re.findall(r"\]\((references/[^)]+)\)", body):
            assert (path.parent / reference).is_file(), (
                f"missing reference {reference} from {path}"
            )


def test_add_adapter_dry_runs_are_non_interactive() -> None:
    guidance_files = [
        *PLUGIN_ROOT.glob("skills/*/SKILL.md"),
        *PLUGIN_ROOT.glob("skills/*/references/*.md"),
    ]

    for path in guidance_files:
        text = path.read_text(encoding="utf-8")
        commands = re.findall(
            r"arclith-cli add-adapter(?:(?!arclith-cli).)*?--dry-run",
            text,
            flags=re.DOTALL,
        )
        for command in commands:
            assert "--yes" in command, (
                f"non-interactive add-adapter preview lacks --yes in {path}"
            )
