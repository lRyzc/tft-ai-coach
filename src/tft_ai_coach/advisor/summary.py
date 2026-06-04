from __future__ import annotations

from tft_ai_coach.advisor.choices import choice_summary
from tft_ai_coach.advisor.economy import economy_advice
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
        f"Comp: {top.comp.name} ({top.comp.tier})",
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
        lines.append(f"Late: {', '.join(top.comp.core_units[:5]) or '-'}")

    return "\n".join(lines[:10])
