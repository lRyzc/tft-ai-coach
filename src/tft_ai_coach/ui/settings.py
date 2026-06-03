from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from tft_ai_coach.paths import RUNTIME_DIR, ensure_dirs


@dataclass(slots=True)
class OverlaySettings:
    compact_x: int | None = None
    compact_y: int | None = None
    compact_scale: float = 1.0
    show_compact_panel: bool = True
    show_choice_aura: bool = True


def load_overlay_settings() -> OverlaySettings:
    ensure_dirs()
    path = RUNTIME_DIR / "overlay_settings.json"
    if not path.exists():
        return OverlaySettings()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return OverlaySettings()
    return OverlaySettings(
        compact_x=_optional_int(payload.get("compact_x")),
        compact_y=_optional_int(payload.get("compact_y")),
        compact_scale=float(payload.get("compact_scale", 1.0) or 1.0),
        show_compact_panel=bool(payload.get("show_compact_panel", True)),
        show_choice_aura=bool(payload.get("show_choice_aura", True)),
    )


def save_overlay_settings(settings: OverlaySettings) -> None:
    ensure_dirs()
    path = RUNTIME_DIR / "overlay_settings.json"
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


def _optional_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None
