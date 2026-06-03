from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tft_ai_coach.models import DetectedEntity, GameState
from tft_ai_coach.vision.layout import DEFAULT_16_9, LayoutProfile
from tft_ai_coach.vision.ocr import ChampionNameReader
from tft_ai_coach.vision.templates import TemplateMatcher, matches_to_debug

SHOP_VISUAL_CONFIDENCE_THRESHOLD = 0.68
SHOP_VISUAL_MARGIN_THRESHOLD = 0.035
SHOP_OCR_CONFIDENCE_THRESHOLD = 0.78


@dataclass(slots=True)
class VisionPipeline:
    layout: LayoutProfile = DEFAULT_16_9
    champion_matcher: TemplateMatcher | None = None
    name_reader: ChampionNameReader | None = None
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
            visual_best = matches[0] if matches else None
            visual_second = matches[1] if len(matches) > 1 else None
            ocr_match = self._name_reader().read_shop_card(crop)
            visual_margin = (
                visual_best.confidence - visual_second.confidence
                if visual_best is not None and visual_second is not None
                else visual_best.confidence if visual_best is not None else 0.0
            )
            visual_strong = bool(visual_best and visual_best.confidence >= 0.85 and visual_margin >= 0.1)
            ocr_valid = bool(
                ocr_match
                and ocr_match.normalized_length >= 3
                and ocr_match.score >= SHOP_OCR_CONFIDENCE_THRESHOLD
            )
            use_ocr = bool(ocr_valid and not visual_strong)
            use_visual = bool(
                visual_best
                and visual_best.confidence >= SHOP_VISUAL_CONFIDENCE_THRESHOLD
                and visual_margin >= SHOP_VISUAL_MARGIN_THRESHOLD
            )
            accepted = use_ocr or use_visual
            detected_name = ocr_match.name if use_ocr and ocr_match is not None else visual_best.name if visual_best else ""
            confidence = ocr_match.score if use_ocr and ocr_match is not None else visual_best.confidence if visual_best else 0.0
            source = "shop_name_ocr" if use_ocr else "shop_template"
            self.debug["shop"].append(
                {
                    "slot": slot_index,
                    "box": [x, y, w, h],
                    "accepted": accepted,
                    "detected_name": detected_name,
                    "source": source if accepted else "",
                    "confidence": confidence,
                    "visual_margin": round(visual_margin, 4),
                    "ocr": {
                        "raw_text": ocr_match.raw_text,
                        "name": ocr_match.name,
                        "score": ocr_match.score,
                        "normalized_length": ocr_match.normalized_length,
                    }
                    if ocr_match is not None
                    else None,
                    "top_candidates": matches_to_debug(matches),
                }
            )
            if detected_name and accepted:
                detected_shop.append(detected_name)
                state.detections.append(
                    DetectedEntity(
                        name=detected_name,
                        confidence=confidence,
                        source=source,
                        extra={
                            "slot": slot_index,
                            "visual_id": visual_best.id if visual_best else "",
                            "visual_cost": visual_best.cost if visual_best else None,
                        },
                    )
                )
        state.shop = detected_shop

    def _champion_matcher(self) -> TemplateMatcher:
        if self.champion_matcher is None:
            self.champion_matcher = TemplateMatcher.from_current_data("champions")
        return self.champion_matcher

    def _name_reader(self) -> ChampionNameReader:
        if self.name_reader is None:
            names = [template.name for template in self._champion_matcher().templates]
            self.name_reader = ChampionNameReader(names)
        return self.name_reader

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
