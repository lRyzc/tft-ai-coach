from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tft_ai_coach.models import DetectedEntity, GameState
from tft_ai_coach.vision.layout import DEFAULT_16_9, LayoutProfile
from tft_ai_coach.vision.templates import TemplateMatcher, matches_to_debug

SHOP_CONFIDENCE_THRESHOLD = 0.62


@dataclass(slots=True)
class VisionPipeline:
    layout: LayoutProfile = DEFAULT_16_9
    champion_matcher: TemplateMatcher | None = None
    debug: dict[str, Any] = field(default_factory=dict)

    def analyze(self, frame: np.ndarray) -> GameState:
        height, width = frame.shape[:2]
        state = GameState()
        self.debug = {"frame_size": [width, height], "regions": {}, "shop": []}
        for name, region in self.layout.regions.items():
            x, y, w, h = region.scale(width, height)
            crop = frame[y : y + h, x : x + w]
            self.debug["regions"][name] = {
                "box": [x, y, w, h],
                "mean_brightness": float(np.mean(crop)) if crop.size else 0.0,
            }

        self._detect_shop(frame, state)
        return state

    def _detect_shop(self, frame: np.ndarray, state: GameState) -> None:
        matcher = self._champion_matcher()
        if not matcher.templates:
            self.debug["shop_error"] = "No champion icon templates found. Run scripts/update_data.ps1 first."
            return

        height, width = frame.shape[:2]
        detected_shop: list[str] = []
        for slot_index in range(1, 6):
            region = self.layout.regions[f"shop_slot_{slot_index}"]
            x, y, w, h = region.scale(width, height)
            crop = frame[y : y + h, x : x + w]
            matches = matcher.best_match(crop)
            best = matches[0] if matches else None
            accepted = bool(best and best.confidence >= SHOP_CONFIDENCE_THRESHOLD)
            self.debug["shop"].append(
                {
                    "slot": slot_index,
                    "box": [x, y, w, h],
                    "accepted": accepted,
                    "top_candidates": matches_to_debug(matches),
                }
            )
            if best and accepted:
                detected_shop.append(best.name)
                state.detections.append(
                    DetectedEntity(
                        name=best.name,
                        confidence=best.confidence,
                        source="shop_template",
                        extra={"slot": slot_index, "id": best.id, "cost": best.cost},
                    )
                )
        state.shop = detected_shop

    def _champion_matcher(self) -> TemplateMatcher:
        if self.champion_matcher is None:
            self.champion_matcher = TemplateMatcher.from_current_data("champions")
        return self.champion_matcher

    def export_debug_crops(self, frame: np.ndarray, output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        height, width = frame.shape[:2]
        written: list[Path] = []
        for name, region in self.layout.regions.items():
            x, y, w, h = region.scale(width, height)
            crop = frame[y : y + h, x : x + w]
            if crop.size == 0:
                continue
            path = output_dir / f"{name}.png"
            cv2.imwrite(str(path), crop)
            written.append(path)
        return written

    @staticmethod
    def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
