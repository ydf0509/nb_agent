"""SkillManager — 发现、加载与匹配 SKILL.md 技能文档。"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_BUILTIN_DIR = Path(__file__).resolve().parent / "builtin"

_GLOBAL_DIRS = [
    Path.home() / ".nb_agent" / "skills",
    Path.home() / ".agents" / "skills",
]

_PROJECT_DIR_NAMES = [
    Path(".nb_agent") / "skills",
    Path(".agents") / "skills",
]


@dataclass(frozen=True)
class SkillRecord:
    name: str
    description: str
    paths: tuple[str, ...]
    skill_path: Path
    source: str
    disable_model_invocation: bool = False


def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter separated by ``---`` from markdown body."""
    text = content.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    body = parts[2].lstrip("\n")
    return metadata, body


def _read_frontmatter(skill_path: Path) -> dict[str, Any]:
    try:
        content = skill_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    metadata, _ = _split_frontmatter(content)
    return metadata


def _normalize_paths(raw_paths: Any) -> tuple[str, ...]:
    if raw_paths is None:
        return ()
    if isinstance(raw_paths, str):
        items = [part.strip() for part in raw_paths.split(",")]
    elif isinstance(raw_paths, list):
        items = [str(part).strip() for part in raw_paths]
    else:
        return ()
    return tuple(item for item in items if item)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    normalized = pattern.replace("\\", "/")
    parts: list[str] = []
    i = 0
    while i < len(normalized):
        char = normalized[i]
        if char == "*":
            if i + 1 < len(normalized) and normalized[i + 1] == "*":
                parts.append(".*")
                i += 2
                if i < len(normalized) and normalized[i] == "/":
                    i += 1
                continue
            parts.append("[^/]*")
            i += 1
            continue
        if char == "?":
            parts.append("[^/]")
        else:
            parts.append(re.escape(char))
        i += 1
    return re.compile(f"^{''.join(parts)}$")


def _path_matches_glob(file_path: str, pattern: str) -> bool:
    normalized_path = file_path.replace("\\", "/").lstrip("./")
    normalized_pattern = pattern.replace("\\", "/").lstrip("./")
    if not normalized_path or not normalized_pattern:
        return False

    path = Path(normalized_path)
    if path.match(normalized_pattern):
        return True

    if normalized_pattern.startswith("**/"):
        suffix = normalized_pattern[3:]
        if fnmatch.fnmatch(path.name, suffix):
            return True

    if "**" in normalized_pattern or "/" in normalized_pattern:
        return bool(_glob_to_regex(normalized_pattern).fullmatch(normalized_path))

    return fnmatch.fnmatch(path.name, normalized_pattern) or fnmatch.fnmatch(
        normalized_path,
        normalized_pattern,
    )


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob("*/SKILL.md") if path.is_file())


class SkillManager:
    """Manage progressive disclosure of SKILL.md instructions."""

    def __init__(self, project_root: Path | None = None) -> None:
        self._project_root = project_root or Path.cwd()
        self._skills: dict[str, SkillRecord] = {}

    def discover(self) -> None:
        """Scan builtin, global, cross-platform, and project skill directories."""
        discovered: dict[str, SkillRecord] = {}

        scan_targets: list[tuple[str, Path]] = [("builtin", _BUILTIN_DIR)]
        for gdir in _GLOBAL_DIRS:
            scan_targets.append(("global", gdir))
        for pdir_name in _PROJECT_DIR_NAMES:
            scan_targets.append(("project", self._project_root / pdir_name))

        for source, root in scan_targets:
            for skill_path in _iter_skill_files(root):
                metadata = _read_frontmatter(skill_path)
                name = metadata.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue

                description = metadata.get("description", "")
                if not isinstance(description, str):
                    description = str(description)

                dmi = metadata.get("disable-model-invocation", False)
                if not isinstance(dmi, bool):
                    dmi = str(dmi).lower() in ("true", "1", "yes")

                record = SkillRecord(
                    name=name.strip(),
                    description=description.strip(),
                    paths=_normalize_paths(metadata.get("paths")),
                    skill_path=skill_path,
                    source=source,
                    disable_model_invocation=dmi,
                )
                discovered[record.name] = record

        self._skills = discovered

    def get_manifest(self) -> list[dict[str, str]]:
        """Return auto-invocable skills (exclude disable-model-invocation=true)."""
        return [
            {"name": record.name, "description": record.description}
            for record in sorted(self._skills.values(), key=lambda item: item.name)
            if not record.disable_model_invocation
        ]

    def get_all_skills(self) -> list[dict[str, str]]:
        """Return all skills including manual-only ones."""
        return [
            {
                "name": record.name,
                "description": record.description,
                "manual_only": record.disable_model_invocation,
            }
            for record in sorted(self._skills.values(), key=lambda item: item.name)
        ]

    def view_skill(self, skill_name: str) -> dict[str, Any]:
        """Load the full SKILL.md content for a skill."""
        record = self._skills.get(skill_name)
        if record is None:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found.",
                "available_skills": sorted(self._skills),
            }

        try:
            raw_content = record.skill_path.read_text(encoding="utf-8")
        except OSError as exc:
            return {
                "success": False,
                "error": f"Failed to read skill '{skill_name}': {exc}",
            }

        metadata, body = _split_frontmatter(raw_content)
        return {
            "success": True,
            "name": record.name,
            "description": record.description,
            "paths": list(record.paths),
            "source": record.source,
            "skill_path": str(record.skill_path),
            "content": body.strip(),
            "raw_content": raw_content,
            "metadata": metadata,
        }

    def match_skills(self, file_paths: list[str]) -> list[str]:
        """Return skill names whose ``paths`` globs match any given file path."""
        if not file_paths:
            return []

        matched: list[str] = []
        for record in sorted(self._skills.values(), key=lambda item: item.name):
            if not record.paths:
                continue
            if any(
                _path_matches_glob(file_path, pattern)
                for file_path in file_paths
                for pattern in record.paths
            ):
                matched.append(record.name)
        return matched

    def get_view_skill_schema(self) -> dict[str, Any]:
        """Return the OpenAI function schema for the ``view_skill`` tool."""
        return {
            "type": "function",
            "function": {
                "name": "view_skill",
                "description": (
                    "Load the full instructions for a skill by name. "
                    "Use this when a task matches a skill listed in the manifest."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "The skill name from the manifest.",
                        }
                    },
                    "required": ["skill_name"],
                },
            },
        }
