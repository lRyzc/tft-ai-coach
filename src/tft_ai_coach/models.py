from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DetectedEntity:
    name: str
    confidence: float = 1.0
    source: str = "manual"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DecisionOption:
    slot: int
    name: str
    kind: str
    region: tuple[float, float, float, float]
    item: str = ""
    confidence: float = 1.0
    source: str = "vision"


@dataclass(slots=True)
class GameState:
    stage: str = ""
    level: int | None = None
    gold: int | None = None
    health: int | None = None
    xp_current: int | None = None
    xp_needed: int | None = None
    streak_count: int | None = None
    streak_type: str = ""
    shop_odds: list[int] = field(default_factory=list)
    screen_context: str = "game"
    decision_text: str = ""
    decision_options: list[str] = field(default_factory=list)
    decision_slots: list[DecisionOption] = field(default_factory=list)
    board: list[str] = field(default_factory=list)
    bench: list[str] = field(default_factory=list)
    shop: list[str] = field(default_factory=list)
    items: list[str] = field(default_factory=list)
    augments: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    detections: list[DetectedEntity] = field(default_factory=list)

    @property
    def owned_units(self) -> list[str]:
        return self.board + self.bench


@dataclass(slots=True)
class CompDefinition:
    id: str
    name: str
    tier: str = "B"
    style: str = "flex"
    difficulty: str = "Medium"
    tempo: str = ""
    stats: dict[str, str] = field(default_factory=dict)
    core_units: list[str] = field(default_factory=list)
    carry_units: list[str] = field(default_factory=list)
    early_units: list[str] = field(default_factory=list)
    mid_units: list[str] = field(default_factory=list)
    alternative_units: list[str] = field(default_factory=list)
    carousel_priority: list[str] = field(default_factory=list)
    core_items: list[str] = field(default_factory=list)
    item_builds: dict[str, list[str]] = field(default_factory=dict)
    carry_order: list[str] = field(default_factory=list)
    star_targets: dict[str, int] = field(default_factory=dict)
    item_tags: list[str] = field(default_factory=list)
    augment_keywords: list[str] = field(default_factory=list)
    augment_tiers: dict[str, list[str]] = field(default_factory=dict)
    synergies: list[str] = field(default_factory=list)
    positioning: dict[str, tuple[int, int]] = field(default_factory=dict)
    leveling_guide: list[dict[str, str]] = field(default_factory=list)
    guide: str = ""
    economy_plan: str = ""
    leveling_plan: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Recommendation:
    comp: CompDefinition
    score: float
    reasons: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
