from __future__ import annotations

from tft_ai_coach.models import CompDefinition, GameState


def stage_number(stage: str) -> int:
    try:
        return int(stage.split("-")[0])
    except Exception:
        return 0


def phase_name(state: GameState) -> str:
    major = stage_number(state.stage)
    if major <= 2:
        return "Early"
    if major <= 4:
        return "Mid"
    return "Late"


def phase_units(comp: CompDefinition, state: GameState) -> list[str]:
    phase = phase_name(state)
    if phase == "Early":
        return comp.early_units or comp.mid_units or comp.core_units
    if phase == "Mid":
        return comp.mid_units or comp.core_units
    return comp.core_units


def phase_plan(comp: CompDefinition, state: GameState) -> str:
    major = stage_number(state.stage)
    if major and str(major) in comp.leveling_plan:
        return comp.leveling_plan[str(major)]
    phase = phase_name(state)
    units = ", ".join(phase_units(comp, state)[:4])
    if phase == "Early":
        return f"Monte base com {units}; compre pares sem quebrar economia."
    if phase == "Mid":
        return f"Transicione para {units}; estabilize antes de pensar no cap final."
    return f"Feche o cap com {units}; converta gold em upgrades finais."


def stage_label(stage: str) -> str:
    if not stage:
        return "live"
    major = stage_number(stage)
    if major <= 2:
        return f"{stage} Early"
    if major <= 4:
        return f"{stage} Mid"
    return f"{stage} Late"
