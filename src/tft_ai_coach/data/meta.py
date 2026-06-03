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
        comps.append(
            CompDefinition(
                id=raw.get("id", raw.get("name", "").lower().replace(" ", "-")),
                name=raw.get("name", "Unnamed"),
                tier=raw.get("tier", "B"),
                style=raw.get("style", "flex"),
                core_units=list(raw.get("core_units", [])),
                carry_units=list(raw.get("carry_units", [])),
                early_units=list(raw.get("early_units", [])),
                mid_units=list(raw.get("mid_units", [])),
                alternative_units=list(raw.get("alternative_units", [])),
                carousel_priority=list(raw.get("carousel_priority", [])),
                core_items=list(raw.get("core_items", [])),
                item_tags=list(raw.get("item_tags", [])),
                augment_keywords=list(raw.get("augment_keywords", [])),
                economy_plan=raw.get("economy_plan", ""),
                leveling_plan=dict(raw.get("leveling_plan", {})),
                notes=list(raw.get("notes", [])),
            )
        )
    return comps
