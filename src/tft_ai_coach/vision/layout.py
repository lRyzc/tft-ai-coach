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
        "reward_banner": Region("reward_banner", 0.240, 0.710, 0.440, 0.060),
        "gold": Region("gold", 0.492, 0.812, 0.035, 0.035),
        "level": Region("level", 0.160, 0.807, 0.050, 0.050),
        "xp": Region("xp", 0.191, 0.817, 0.050, 0.030),
        "shop_odds": Region("shop_odds", 0.245, 0.820, 0.155, 0.030),
        "streak": Region("streak", 0.542, 0.810, 0.060, 0.040),
        "health": Region("health", 0.928, 0.190, 0.040, 0.050),
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
        "augment_slot_1_card": Region("augment_slot_1_card", 0.198, 0.230, 0.185, 0.540),
        "augment_slot_2_card": Region("augment_slot_2_card", 0.407, 0.230, 0.185, 0.540),
        "augment_slot_3_card": Region("augment_slot_3_card", 0.616, 0.230, 0.185, 0.540),
        "augment_slot_1_name": Region("augment_slot_1_name", 0.220, 0.485, 0.170, 0.075),
        "augment_slot_2_name": Region("augment_slot_2_name", 0.415, 0.485, 0.170, 0.075),
        "augment_slot_3_name": Region("augment_slot_3_name", 0.635, 0.485, 0.190, 0.075),
        "divinity_slot_1_card": Region("divinity_slot_1_card", 0.315, 0.285, 0.175, 0.455),
        "divinity_slot_2_card": Region("divinity_slot_2_card", 0.510, 0.285, 0.175, 0.455),
        "divinity_slot_1_name": Region("divinity_slot_1_name", 0.352, 0.330, 0.095, 0.050),
        "divinity_slot_2_name": Region("divinity_slot_2_name", 0.547, 0.330, 0.095, 0.050),
        "reward_slot_1_card": Region("reward_slot_1_card", 0.274, 0.824, 0.116, 0.165),
        "reward_slot_2_card": Region("reward_slot_2_card", 0.398, 0.824, 0.116, 0.165),
        "reward_slot_3_card": Region("reward_slot_3_card", 0.522, 0.824, 0.116, 0.165),
        "reward_slot_1_icon": Region("reward_slot_1_icon", 0.314, 0.825, 0.038, 0.065),
        "reward_slot_2_icon": Region("reward_slot_2_icon", 0.438, 0.825, 0.038, 0.065),
        "reward_slot_3_icon": Region("reward_slot_3_icon", 0.562, 0.825, 0.038, 0.065),
        "reward_slot_1_name": Region("reward_slot_1_name", 0.292, 0.906, 0.085, 0.050),
        "reward_slot_2_name": Region("reward_slot_2_name", 0.416, 0.906, 0.085, 0.050),
        "reward_slot_3_name": Region("reward_slot_3_name", 0.540, 0.906, 0.085, 0.050),
    },
)
