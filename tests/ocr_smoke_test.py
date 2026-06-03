from __future__ import annotations

from pathlib import Path

import cv2

from tft_ai_coach.vision.ocr import ChampionNameReader


def main() -> None:
    sample = Path("data/screenshots/latest_regions/shop_slot_1.png")
    if not sample.exists():
        print("ocr smoke skipped: no live shop crop")
        return
    image = cv2.imread(str(sample), cv2.IMREAD_COLOR)
    reader = ChampionNameReader(["Aurora", "Rhaast", "Briar", "Teemo"])
    match = reader.read_shop_card(image)
    assert match is not None, "OCR should produce a text candidate"
    print("ocr smoke ok", match.raw_text, match.name, match.score)


if __name__ == "__main__":
    main()
