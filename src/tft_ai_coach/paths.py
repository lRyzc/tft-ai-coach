from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DDRAGON_DIR = DATA_DIR / "ddragon"
META_DIR = DATA_DIR / "meta"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
SCREENSHOT_DIR = DATA_DIR / "screenshots"
RUNTIME_DIR = DATA_DIR / "runtime"


def ensure_dirs() -> None:
    for path in [DATA_DIR, DDRAGON_DIR, META_DIR, SNAPSHOT_DIR, SCREENSHOT_DIR, RUNTIME_DIR]:
        path.mkdir(parents=True, exist_ok=True)

