from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from tft_ai_coach.models import GameState
from tft_ai_coach.vision.layout import DEFAULT_16_9, LayoutProfile


@dataclass(slots=True)
class VisionPipeline:
    layout: LayoutProfile = DEFAULT_16_9
    debug: dict[str, Any] = field(default_factory=dict)

    def analyze(self, frame: np.ndarray) -> GameState:
        height, width = frame.shape[:2]
        self.debug = {"frame_size": [width, height], "regions": {}}
        for name, region in self.layout.regions.items():
            x, y, w, h = region.scale(width, height)
            crop = frame[y : y + h, x : x + w]
            self.debug["regions"][name] = {
                "box": [x, y, w, h],
                "mean_brightness": float(np.mean(crop)) if crop.size else 0.0,
            }

        # Real unit recognition lands here. The first version exposes calibrated
        # crops and keeps the state manual/editable so we can collect examples.
        return GameState()

    @staticmethod
    def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

