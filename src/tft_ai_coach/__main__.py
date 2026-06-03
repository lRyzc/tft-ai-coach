from __future__ import annotations

import sys
from pathlib import Path


def _add_local_dependency_path() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pydeps = project_root / "work" / "pydeps"
    if pydeps.exists():
        sys.path.insert(0, str(pydeps))


_add_local_dependency_path()

from tft_ai_coach.ui.app import main


if __name__ == "__main__":
    main()

