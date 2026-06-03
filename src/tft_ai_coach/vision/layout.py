from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Region:
    name: str
    x: float
    y: float
    w: float
    h: float

    def scale(self, width: int, height: int) -> tuple[int, int, int, int]:
        return (
            int(self.x * width),
            int(self.y * height),
            int(self.w * width),
            int(self.h * height),
        )


@dataclass(frozen=True, slots=True)
class LayoutProfile:
    name: str
    aspect_ratio: str
    regions: dict[str, Region]


DEFAULT_16_9 = LayoutProfile(
    name="default-16-9",
    aspect_ratio="16:9",
    regions={
        "stage": Region("stage", 0.392, 0.009, 0.061, 0.024),
        "decision_banner": Region("decision_banner", 0.350, 0.065, 0.370, 0.060),
        "gold": Region("gold", 0.492, 0.812, 0.035, 0.035),
        "level": Region("level", 0.160, 0.807, 0.050, 0.050),
        "shop": Region("shop", 0.250, 0.908, 0.519, 0.083),
        "shop_slot_1": Region("shop_slot_1", 0.250, 0.908, 0.103, 0.083),
        "shop_slot_2": Region("shop_slot_2", 0.354, 0.908, 0.103, 0.083),
        "shop_slot_3": Region("shop_slot_3", 0.458, 0.908, 0.103, 0.083),
        "shop_slot_4": Region("shop_slot_4", 0.562, 0.908, 0.103, 0.083),
        "shop_slot_5": Region("shop_slot_5", 0.666, 0.908, 0.103, 0.083),
        "bench": Region("bench", 0.190, 0.600, 0.550, 0.125),
        "board": Region("board", 0.270, 0.360, 0.445, 0.265),
        "augments": Region("augments", 0.200, 0.400, 0.600, 0.220),
        "augment_title": Region("augment_title", 0.425, 0.170, 0.180, 0.075),
        "augment_slot_1_name": Region("augment_slot_1_name", 0.220, 0.485, 0.170, 0.075),
        "augment_slot_2_name": Region("augment_slot_2_name", 0.415, 0.485, 0.170, 0.075),
        "augment_slot_3_name": Region("augment_slot_3_name", 0.635, 0.485, 0.190, 0.075),
    },
)
