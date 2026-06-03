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
class GameState:
    stage: str = ""
    level: int | None = None
    gold: int | None = None
    health: int | None = None
    screen_context: str = "game"
    decision_text: str = ""
    decision_options: list[str] = field(default_factory=list)
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
    item_tags: list[str] = field(default_factory=list)
    augment_keywords: list[str] = field(default_factory=list)
    economy_plan: str = ""
    leveling_plan: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Recommendation:
    comp: CompDefinition
    score: float
    reasons: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
