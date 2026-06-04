from __future__ import annotations

from tft_ai_coach.advisor.choices import choice_summary
from tft_ai_coach.advisor.economy import economy_advice, economy_alert
from tft_ai_coach.advisor.phase import phase_name, phase_plan, phase_units, stage_label
from tft_ai_coach.models import GameState, Recommendation


def compact_overlay_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    if not recommendations:
        return "TFT AI Coach\nAguardando comp/meta."

    top = recommendations[0]
    current_stage_label = stage_label(state.stage)
    current_phase = phase_name(state)
    current_units = phase_units(top.comp, state)
    shop_line = ", ".join(state.shop) if state.shop else "loja nao lida"
    decision_line = choice_summary(state, recommendations)
    augment_line = decision_line or (", ".join(state.augments[:3]) if state.augments else "sem escolha especial na tela")

    lines = [
        f"TFT AI Coach | {current_stage_label}",
        economy_alert(state),
        f"Comp: {top.comp.name} ({top.comp.tier})",
        f"Estado: {_state_context(state)}",
        f"Plano: {current_phase} - {', '.join(current_units[:5]) or '-'}",
        f"Loja: {shop_line}",
        economy_advice(state),
        f"Escolha: {augment_line}",
    ]

    if decision_line:
        lines.append(f"Agora: {decision_line}")
    elif current_units:
        lines.append(f"Agora: {phase_plan(top.comp, state)}")
    elif top.actions:
        lines.append(f"Agora: {top.actions[0]}")
    if top.reasons:
        lines.append(f"Por que: {top.reasons[0]}")

    if top.comp.early_units or top.comp.mid_units or top.comp.core_units:
        lines.append(f"Early: {', '.join(top.comp.early_units[:4]) or '-'}")
        lines.append(f"Mid: {', '.join(top.comp.mid_units[:4]) or '-'}")
        lines.append(f"Late: {', '.join(top.comp.core_units[:6]) or '-'}")

    return "\n".join(lines[:10])


def _state_context(state: GameState) -> str:
    chunks: list[str] = []
    if state.health is not None:
        chunks.append(f"HP {state.health}")
    if state.gold is not None:
        chunks.append(f"{state.gold}g")
    if state.level is not None:
        chunks.append(f"Lv {state.level}")
    if state.xp_current is not None and state.xp_needed is not None:
        chunks.append(f"XP {state.xp_current}/{state.xp_needed}")
    if state.streak_count is not None:
        prefix = "W" if state.streak_type == "win" else "L" if state.streak_type == "loss" else "S"
        chunks.append(f"{prefix}{state.streak_count}")
    if state.shop_odds:
        chunks.append("Odds " + "/".join(str(value) for value in state.shop_odds[:5]))
    return " | ".join(chunks) if chunks else "lendo HUD"
