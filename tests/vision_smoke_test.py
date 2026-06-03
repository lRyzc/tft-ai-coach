from __future__ import annotations

import cv2
import numpy as np

from tft_ai_coach.data.ddragon import load_current_index, update_static_data
from tft_ai_coach.paths import DDRAGON_DIR
from tft_ai_coach.vision import VisionPipeline
from tft_ai_coach.vision.layout import DEFAULT_16_9


def main() -> None:
    index = update_static_data(download_icons=True, icon_kinds={"champions"})
    selected = index["records"]["champions"][:5]
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    for slot, record in enumerate(selected, start=1):
        region = DEFAULT_16_9.regions[f"shop_slot_{slot}"]
        x, y, w, h = region.scale(1920, 1080)
        icon = cv2.imread(
            str(DDRAGON_DIR / index["version"] / "icons" / record["image_group"] / record["image_file"]),
            cv2.IMREAD_COLOR,
        )
        assert icon is not None, record["name"]
        resized = cv2.resize(icon, (w, h), interpolation=cv2.INTER_AREA)
        frame[y : y + h, x : x + w] = resized

    pipeline = VisionPipeline()
    state = pipeline.analyze(frame)
    expected = [record["name"] for record in selected]
    assert state.shop == expected, {"expected": expected, "actual": state.shop, "debug": pipeline.debug["shop"]}
    print("vision smoke ok", state.shop)


if __name__ == "__main__":
    main()
