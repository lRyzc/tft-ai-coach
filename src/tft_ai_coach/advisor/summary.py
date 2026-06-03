from __future__ import annotations

from tft_ai_coach.advisor.economy import economy_advice
from tft_ai_coach.models import GameState, Recommendation


def compact_overlay_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    if not recommendations:
        return "TFT AI Coach\nAguardando comp/meta."

    top = recommendations[0]
    stage_label = _stage_label(state.stage)
    shop_line = ", ".join(state.shop) if state.shop else "loja nao lida"
    augment_line = ", ".join(state.augments[:3]) if state.augments else "sem augment na tela"

    lines = [
        f"TFT AI Coach | {stage_label}",
        f"Comp: {top.comp.name} ({top.comp.tier})",
        f"Loja: {shop_line}",
        economy_advice(state),
        f"Augments: {augment_line}",
    ]

    if top.actions:
        lines.append(f"Agora: {top.actions[0]}")
    if top.reasons:
        lines.append(f"Por que: {top.reasons[0]}")

    if top.comp.early_units or top.comp.mid_units or top.comp.core_units:
        lines.append(f"Early: {', '.join(top.comp.early_units[:4]) or '-'}")
        lines.append(f"Mid: {', '.join(top.comp.mid_units[:4]) or '-'}")
        lines.append(f"Late: {', '.join(top.comp.core_units[:5]) or '-'}")

    return "\n".join(lines[:10])


def _stage_label(stage: str) -> str:
    if not stage:
        return "live"
    try:
        major = int(stage.split("-")[0])
    except Exception:
        return stage
    if major <= 2:
        return f"{stage} Early"
    if major <= 4:
        return f"{stage} Mid"
    return f"{stage} Late"
