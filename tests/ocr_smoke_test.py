from __future__ import annotations

import cv2
import numpy as np

from tft_ai_coach.vision.ocr import ChampionNameReader


def main() -> None:
    image = np.full((180, 260, 3), (20, 20, 20), dtype=np.uint8)
    cv2.putText(image, "Illaoi", (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA)
    reader = ChampionNameReader(["Illaoi", "Caitlyn", "Briar", "Teemo"])
    match = reader.read_shop_card(image)
    assert match is not None, "OCR should produce a text candidate"
    assert match.name == "Illaoi", match
    print("ocr smoke ok", match.raw_text, match.name, match.score)


if __name__ == "__main__":
    main()
