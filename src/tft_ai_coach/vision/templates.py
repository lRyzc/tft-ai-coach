from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tft_ai_coach.data.ddragon import load_current_index
from tft_ai_coach.paths import DDRAGON_DIR


@dataclass(frozen=True, slots=True)
class VisualTemplate:
    name: str
    id: str
    kind: str
    path: Path
    image: np.ndarray
    cost: int | None = None


@dataclass(frozen=True, slots=True)
class VisualMatch:
    name: str
    id: str
    score: float
    confidence: float
    cost: int | None = None


class TemplateMatcher:
    def __init__(self, templates: list[VisualTemplate]) -> None:
        self.templates = templates

    @classmethod
    def from_current_data(cls, kind: str = "champions") -> "TemplateMatcher":
        return cls(load_templates(kind))

    def best_match(self, crop: np.ndarray, limit: int = 5) -> list[VisualMatch]:
        if crop.size == 0 or not self.templates:
            return []
        scored = [_score_template(crop, template) for template in self.templates]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]


@lru_cache(maxsize=8)
def load_templates(kind: str = "champions") -> list[VisualTemplate]:
    index = load_current_index()
    version = index["version"]
    records = index["records"].get(kind, [])
    templates: list[VisualTemplate] = []
    for record in records:
        image_group = record.get("image_group")
        image_file = record.get("image_file")
        if not image_group or not image_file:
            continue
        path = DDRAGON_DIR / version / "icons" / image_group / image_file
        if not path.exists():
            continue
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            continue
        templates.append(
            VisualTemplate(
                name=record["name"],
                id=record["id"],
                kind=kind,
                path=path,
                image=image,
                cost=record.get("cost"),
            )
        )
    return templates


def _score_template(crop: np.ndarray, template: VisualTemplate) -> VisualMatch:
    candidate = _normalize_card_art(crop)
    target = _normalize_card_art(template.image)
    ncc = _correlation(candidate, target)
    hist = _histogram_similarity(candidate, target)
    score = (0.52 * hist) + (0.48 * ncc)
    score = max(0.0, min(1.0, score))
    return VisualMatch(
        name=template.name,
        id=template.id,
        score=round(score, 4),
        confidence=round(score, 4),
        cost=template.cost,
    )


def _normalize_card_art(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return np.zeros((128, 256, 3), dtype=np.uint8)

    # Shop cards include a name/cost strip at the bottom. Keeping mostly the art
    # makes Data Dragon portraits more comparable to live shop crops.
    art_h = max(1, int(h * 0.78))
    art = image[:art_h, :]
    return cv2.resize(art, (256, 128), interpolation=cv2.INTER_AREA)


def _correlation(candidate: np.ndarray, target: np.ndarray) -> float:
    candidate_gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    candidate_gray = cv2.equalizeHist(candidate_gray)
    target_gray = cv2.equalizeHist(target_gray)
    result = cv2.matchTemplate(candidate_gray, target_gray, cv2.TM_CCOEFF_NORMED)
    return float((result[0][0] + 1.0) / 2.0)


def _histogram_similarity(candidate: np.ndarray, target: np.ndarray) -> float:
    candidate_hsv = cv2.cvtColor(candidate, cv2.COLOR_BGR2HSV)
    target_hsv = cv2.cvtColor(target, cv2.COLOR_BGR2HSV)
    candidate_hist = cv2.calcHist([candidate_hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    target_hist = cv2.calcHist([target_hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(candidate_hist, candidate_hist, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(target_hist, target_hist, 0, 1, cv2.NORM_MINMAX)
    similarity = cv2.compareHist(candidate_hist, target_hist, cv2.HISTCMP_CORREL)
    return float((similarity + 1.0) / 2.0)


def matches_to_debug(matches: list[VisualMatch]) -> list[dict[str, Any]]:
    return [
        {
            "name": match.name,
            "id": match.id,
            "score": match.score,
            "confidence": match.confidence,
            "cost": match.cost,
        }
        for match in matches
    ]
