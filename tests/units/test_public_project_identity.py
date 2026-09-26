from __future__ import annotations

from pathlib import Path

import tomllib
import yaml

PROJECT_ROOT = Path(__file__).parents[2]
PUBLIC_TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".yaml", ".yml"}
PUBLIC_TEXT_ROOTS = (
    PROJECT_ROOT / "arclith",
    PROJECT_ROOT / "cli",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "plugins",
)


def _public_text_files() -> list[Path]:
    files = [
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "SKILLS.md",
        PROJECT_ROOT / "mkdocs.yml",
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / ".claude-plugin" / "marketplace.json",
    ]
    files.extend(
        path
        for root in PUBLIC_TEXT_ROOTS
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in PUBLIC_TEXT_SUFFIXES
        and path.name not in {"uv.lock"}
    )
    return sorted(set(files))


def test_public_files_do_not_reference_the_previous_repository_owner() -> None:
    previous_owner = "karned" + "-rekipe"
    offenders = [
        path.relative_to(PROJECT_ROOT)
        for path in _public_text_files()
        if previous_owner in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_package_and_documentation_metadata_use_the_canonical_urls() -> None:
    package = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    cli_package = tomllib.loads(
        (PROJECT_ROOT / "cli" / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    mkdocs = yaml.safe_load(
        (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    )

    expected = {
        "Homepage": "https://arclith.karned.bzh/",
        "Repository": "https://github.com/karned-agency/arclith",
    }
    for key, value in expected.items():
        assert package["urls"][key] == value
        assert cli_package["urls"][key] == value
    assert mkdocs["site_url"] == "https://arclith.karned.bzh/"
    assert mkdocs["repo_url"] == "https://github.com/karned-agency/arclith"
    assert (PROJECT_ROOT / "docs" / "CNAME").read_text().strip() == (
        "arclith.karned.bzh"
    )
