from __future__ import annotations

import json
import shutil
from pathlib import Path

from tft_ai_coach.models import CompDefinition
from tft_ai_coach.paths import META_DIR, ensure_dirs


def _meta_path() -> Path:
    return META_DIR / "comps.json"


def ensure_meta_file() -> Path:
    ensure_dirs()
    path = _meta_path()
    if not path.exists():
        example = META_DIR / "comps.example.json"
        repo_example = Path(__file__).resolve().parents[3] / "data" / "meta" / "comps.example.json"
        if example.exists():
            shutil.copyfile(example, path)
        elif repo_example.exists():
            shutil.copyfile(repo_example, path)
        else:
            path.write_text(json.dumps({"patch": "manual", "comps": []}, indent=2), encoding="utf-8")
    return path


def load_comps() -> list[CompDefinition]:
    path = ensure_meta_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    comps: list[CompDefinition] = []
    for raw in payload.get("comps", []):
        core_units = list(raw.get("core_units", []))
        carry_units = list(raw.get("carry_units", []))
        core_items = list(raw.get("core_items", []))
        comps.append(
            CompDefinition(
                id=raw.get("id", raw.get("name", "").lower().replace(" ", "-")),
                name=raw.get("name", "Unnamed"),
                tier=raw.get("tier", "B"),
                style=raw.get("style", "flex"),
                difficulty=raw.get("difficulty", "Medium"),
                tempo=raw.get("tempo", ""),
                stats=dict(raw.get("stats", {})),
                core_units=core_units,
                carry_units=carry_units,
                early_units=list(raw.get("early_units", [])),
                mid_units=list(raw.get("mid_units", [])),
                alternative_units=list(raw.get("alternative_units", [])),
                carousel_priority=list(raw.get("carousel_priority", [])),
                core_items=core_items,
                item_builds=_item_builds(raw, carry_units, core_items),
                carry_order=list(raw.get("carry_order", carry_units)),
                star_targets={name: int(value) for name, value in raw.get("star_targets", {}).items()},
                item_tags=list(raw.get("item_tags", [])),
                augment_keywords=list(raw.get("augment_keywords", [])),
                augment_tiers={key: list(value) for key, value in raw.get("augment_tiers", {}).items()},
                synergies=list(raw.get("synergies", [])),
                positioning=_positioning(raw, core_units),
                leveling_guide=list(raw.get("leveling_guide", [])),
                guide=raw.get("guide", ""),
                economy_plan=raw.get("economy_plan", ""),
                leveling_plan=dict(raw.get("leveling_plan", {})),
                notes=list(raw.get("notes", [])),
            )
        )
    return comps


def _item_builds(raw: dict, carry_units: list[str], core_items: list[str]) -> dict[str, list[str]]:
    explicit = raw.get("item_builds", {})
    if explicit:
        return {name: list(items) for name, items in explicit.items()}
    builds: dict[str, list[str]] = {}
    for index, carry in enumerate(carry_units[:3]):
        if index == 0:
            builds[carry] = core_items[:3]
        elif index == 1:
            builds[carry] = core_items[1:3] or core_items[:2]
        else:
            builds[carry] = core_items[:2]
    return builds


def _positioning(raw: dict, core_units: list[str]) -> dict[str, tuple[int, int]]:
    explicit = raw.get("positioning", {})
    if explicit:
        return {name: tuple(value) for name, value in explicit.items()}
    positions: dict[str, tuple[int, int]] = {}
    for index, unit in enumerate(core_units[:9]):
        row = 3 if index < 3 else 2 if index < 6 else 0
        col = 2 + (index % 3) * 2
        positions[unit] = (row, col)
    return positions
