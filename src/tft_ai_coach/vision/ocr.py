from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from rapidfuzz import fuzz

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

DEFAULT_TESSERACT_PATH = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")


@dataclass(frozen=True, slots=True)
class OcrMatch:
    raw_text: str
    name: str
    score: float
    normalized_length: int


class ChampionNameReader:
    def __init__(self, champion_names: list[str]) -> None:
        self.champion_names = champion_names
        self._normalized_names = {name: _normalize(name) for name in champion_names}
        if pytesseract is not None and DEFAULT_TESSERACT_PATH.exists():
            pytesseract.pytesseract.tesseract_cmd = str(DEFAULT_TESSERACT_PATH)

    @property
    def available(self) -> bool:
        return pytesseract is not None and DEFAULT_TESSERACT_PATH.exists()

    def read_shop_card(self, crop: np.ndarray) -> OcrMatch | None:
        if not self.available or crop.size == 0:
            return None
        text = self._read_text(_name_strip(crop))
        if not text:
            return None
        best_name = ""
        best_score = 0.0
        normalized_text = _normalize(text)
        if not normalized_text:
            return None
        for name, normalized_name in self._normalized_names.items():
            score = fuzz.WRatio(normalized_text, normalized_name)
            if score > best_score:
                best_name = name
                best_score = float(score)
        if not best_name:
            return None
        return OcrMatch(
            raw_text=text,
            name=best_name,
            score=round(best_score / 100, 4),
            normalized_length=len(normalized_text),
        )

    def _read_text(self, image: np.ndarray) -> str:
        return read_text(
            image,
            psm=7,
            whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'",
            scale=3,
        )


def read_text(image: np.ndarray, psm: int = 7, whitelist: str = "", scale: int = 3) -> str:
    if pytesseract is None:
        return ""
    if DEFAULT_TESSERACT_PATH.exists():
        pytesseract.pytesseract.tesseract_cmd = str(DEFAULT_TESSERACT_PATH)
    processed = _preprocess_text(image, scale=scale)
    config = f"--psm {psm}"
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"
    text = pytesseract.image_to_string(processed, config=config)
    return " ".join(text.replace("\n", " ").split())


def _name_strip(crop: np.ndarray) -> np.ndarray:
    height, width = crop.shape[:2]
    y1 = int(height * 0.60)
    return crop[y1:height, 0:width]


def _preprocess_name_strip(image: np.ndarray) -> np.ndarray:
    return _preprocess_text(image, scale=3)


def _preprocess_text(image: np.ndarray, scale: int = 3) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return threshold


def _normalize(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())
