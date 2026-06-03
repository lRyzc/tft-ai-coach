from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import unicodedata

import cv2
import numpy as np

from tft_ai_coach.models import DecisionOption, DetectedEntity, GameState
from tft_ai_coach.vision.layout import DEFAULT_16_9, LayoutProfile
from tft_ai_coach.vision.ocr import ChampionNameReader, read_text
from tft_ai_coach.vision.templates import TemplateMatcher, matches_to_debug

SHOP_VISUAL_CONFIDENCE_THRESHOLD = 0.68
SHOP_VISUAL_MARGIN_THRESHOLD = 0.035
SHOP_OCR_CONFIDENCE_THRESHOLD = 0.78
SHOP_OCR_VISUAL_AGREEMENT_THRESHOLD = 0.65


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
        self._detect_numbers_and_round(frame, state)
        self._detect_decision_context(frame, state)
        self._detect_augments(frame, state)
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
            ocr_visual_agree = bool(
                ocr_match
                and visual_best
                and ocr_match.name == visual_best.name
                and ocr_match.normalized_length >= 3
                and ocr_match.score >= SHOP_OCR_VISUAL_AGREEMENT_THRESHOLD
                and visual_best.confidence >= 0.55
            )
            use_ocr = bool((ocr_valid and not visual_strong) or ocr_visual_agree)
            use_visual = bool(
                visual_best
                and visual_best.confidence >= SHOP_VISUAL_CONFIDENCE_THRESHOLD
                and visual_margin >= SHOP_VISUAL_MARGIN_THRESHOLD
            )
            accepted = use_ocr or use_visual
            detected_name = ocr_match.name if use_ocr and ocr_match is not None else visual_best.name if visual_best else ""
            confidence = ocr_match.score if use_ocr and ocr_match is not None else visual_best.confidence if visual_best else 0.0
            source = "shop_ocr_visual_agree" if ocr_visual_agree else "shop_name_ocr" if use_ocr else "shop_template"
            self.debug["shop"].append(
                {
                    "slot": slot_index,
                    "box": [x, y, w, h],
                    "accepted": accepted,
                    "detected_name": detected_name,
                    "source": source if accepted else "",
                    "confidence": confidence,
                    "visual_margin": round(visual_margin, 4),
                    "ocr_visual_agree": ocr_visual_agree,
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

    def _detect_numbers_and_round(self, frame: np.ndarray, state: GameState) -> None:
        state.stage = self._read_region_text(frame, "stage", "0123456789-", scale=4)
        gold_text = self._read_region_text(frame, "gold", "0123456789", scale=5)
        level_text = self._read_region_text(frame, "level", "0123456789Nv.", scale=4)
        state.gold = _first_int(gold_text)
        state.level = _first_int(level_text)
        self.debug["hud"] = {"stage": state.stage, "gold_text": gold_text, "level_text": level_text}

    def _detect_decision_context(self, frame: np.ndarray, state: GameState) -> None:
        banner = self._read_region_text(frame, "decision_banner", scale=3, psm=6)
        reward_banner = self._read_region_text(frame, "reward_banner", scale=3, psm=6)
        normalized = _fold(f"{banner} {reward_banner}")
        context = "game"
        options: list[str] = []
        slots: list[DecisionOption] = []
        champion_names = [template.name for template in self._champion_matcher().templates]
        if "divindade" in normalized or "oferece" in normalized:
            context = "divinity_choice"
            slots = self._read_divinity_slots(frame, champion_names)
            options = [slot.name for slot in slots] or _known_names_in_text(banner, champion_names)
        elif "concede" in normalized or "presente" in normalized or "despedida" in normalized:
            context = "reward_choice"
            slots = self._read_reward_slots(frame, champion_names)
            options = [slot.name for slot in slots]
        state.screen_context = context
        state.decision_text = " ".join(part for part in [banner, reward_banner] if part)
        state.decision_options = options
        state.decision_slots = slots
        self.debug["decision_context"] = {
            "banner": banner,
            "reward_banner": reward_banner,
            "context": context,
            "options": options,
            "slots": [
                {
                    "slot": slot.slot,
                    "name": slot.name,
                    "kind": slot.kind,
                    "region": list(slot.region),
                    "item": slot.item,
                    "confidence": slot.confidence,
                    "source": slot.source,
                }
                for slot in slots
            ],
        }

    def _read_divinity_slots(self, frame: np.ndarray, champion_names: list[str]) -> list[DecisionOption]:
        slots: list[DecisionOption] = []
        for slot in range(1, 3):
            name_text = self._read_region_text(frame, f"divinity_slot_{slot}_name", scale=4, psm=7)
            name, score = _best_known_name(name_text, champion_names)
            if name:
                slots.append(
                    DecisionOption(
                        slot=slot,
                        name=name,
                        kind="divinity",
                        region=_region_tuple(self.layout.regions[f"divinity_slot_{slot}_card"]),
                        confidence=score,
                        source="divinity_name_ocr",
                    )
                )
        return slots

    def _read_reward_slots(self, frame: np.ndarray, champion_names: list[str]) -> list[DecisionOption]:
        matcher = self._champion_matcher()
        height, width = frame.shape[:2]
        slots: list[DecisionOption] = []
        for slot in range(1, 4):
            text = self._read_region_text(frame, f"reward_slot_{slot}_name", scale=3, psm=6)
            ocr_name, ocr_score = _best_known_name(text, champion_names)
            icon_region = self.layout.regions[f"reward_slot_{slot}_icon"]
            x, y, w, h = icon_region.scale(width, height)
            crop = frame[y : y + h, x : x + w]
            matches = matcher.best_match(crop, limit=2)
            visual = matches[0] if matches else None
            use_visual = bool(visual and visual.confidence >= 0.56 and visual.confidence >= ocr_score)
            name = visual.name if use_visual and visual is not None else ocr_name
            confidence = visual.confidence if use_visual and visual is not None else ocr_score
            source = "reward_icon_template" if use_visual else "reward_name_ocr"
            if name:
                slots.append(
                    DecisionOption(
                        slot=slot,
                        name=name,
                        kind="reward",
                        region=_region_tuple(self.layout.regions[f"reward_slot_{slot}_card"]),
                        confidence=confidence,
                        source=source,
                    )
                )
        return slots

    def _detect_augments(self, frame: np.ndarray, state: GameState) -> None:
        title = self._read_region_text(frame, "augment_title", scale=3)
        title_lower = title.lower()
        is_augment_screen = "escolha" in title_lower or "choose" in title_lower
        self.debug["augment_screen"] = {"title": title, "active": is_augment_screen}
        if not is_augment_screen:
            state.augments = []
            self.debug["augments"] = []
            return

        state.screen_context = "augment_choice"
        state.decision_text = title
        state.decision_slots = []

        augments: list[str] = []
        debug: list[dict[str, str]] = []
        for slot in range(1, 4):
            region_name = f"augment_slot_{slot}_name"
            text = self._read_region_text(frame, region_name, scale=3)
            cleaned = _clean_augment_text(text)
            debug.append({"slot": str(slot), "raw": text, "cleaned": cleaned})
            if cleaned and len(cleaned) >= 3:
                augments.append(cleaned)
                state.decision_slots.append(
                    DecisionOption(
                        slot=slot,
                        name=cleaned,
                        kind="augment",
                        region=_region_tuple(self.layout.regions[f"augment_slot_{slot}_card"]),
                        confidence=0.65,
                        source="augment_name_ocr",
                    )
                )
        state.augments = augments
        self.debug["augments"] = debug

    def _read_region_text(
        self,
        frame: np.ndarray,
        region_name: str,
        whitelist: str = "",
        scale: int = 3,
        psm: int = 7,
    ) -> str:
        region = self.layout.regions[region_name]
        height, width = frame.shape[:2]
        x, y, w, h = region.scale(width, height)
        crop = frame[y : y + h, x : x + w]
        if crop.size == 0:
            return ""
        return read_text(crop, psm=psm, whitelist=whitelist, scale=scale)

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


def _first_int(value: str) -> int | None:
    digits = "".join(ch if ch.isdigit() else " " for ch in value).split()
    if not digits:
        return None
    try:
        return int(digits[0])
    except ValueError:
        return None


def _clean_augment_text(value: str) -> str:
    blocked = ["unlock", "plus", "tier", "recommended", "augment"]
    cleaned = value.strip()
    lower = cleaned.lower()
    if any(word in lower for word in blocked):
        return ""
    return cleaned


def _known_names_in_text(text: str, names: list[str]) -> list[str]:
    normalized = _fold(text)
    found: list[str] = []
    for name in names:
        if _fold(name) in normalized:
            found.append(name)
    return found


def _best_known_name(text: str, names: list[str]) -> tuple[str, float]:
    normalized_text = _fold(text)
    if not normalized_text:
        return "", 0.0
    best_name = ""
    best_score = 0.0
    for name in names:
        score = 1.0 if _fold(name) in normalized_text else 0.0
        if score == 0.0:
            from rapidfuzz import fuzz

            score = fuzz.WRatio(normalized_text, _fold(name)) / 100
        if score > best_score:
            best_name = name
            best_score = float(score)
    if best_score < 0.70:
        return "", best_score
    return best_name, round(best_score, 4)


def _region_tuple(region) -> tuple[float, float, float, float]:
    return (region.x, region.y, region.w, region.h)


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed.lower() if ch.isalnum())
