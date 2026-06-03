from __future__ import annotations

from tft_ai_coach.models import GameState


def economy_advice(state: GameState) -> str:
    stage = _stage_number(state.stage)
    gold = state.gold
    level = state.level

    if gold is None and level is None:
        return "Economia: aguardando leitura de gold/level."

    if stage <= 2:
        if gold is not None and gold >= 20:
            return "Economia: segure juros; compre pares bons sem quebrar gold."
        return "Economia: jogue board forte, compre pares e evite rolar cedo."

    if stage == 3:
        if level is not None and level < 6:
            return "Economia: prepare level 6; role pouco, so se o board estiver fraco."
        if gold is not None and gold >= 40:
            return "Economia: boa reserva; pense em level 7/8 antes de rolar pesado."
        return "Economia: estabilize se estiver perdendo muito HP, senao mantenha juros."

    if stage == 4:
        if level is not None and level < 8 and gold is not None and gold >= 40:
            return "Economia: subir 8 parece melhor que rolar fundo agora."
        if gold is not None and gold <= 20:
            return "Economia: role apenas para estabilizar upgrades chave."
        return "Economia: busque upgrades da linha principal sem zerar sem motivo."

    if gold is not None and gold >= 30:
        return "Economia: converta gold em upgrades finais e posicionamento."
    return "Economia: priorize upgrades imediatos; late game nao perdoa board fraco."


def _stage_number(stage: str) -> int:
    try:
        return int(stage.split("-")[0])
    except Exception:
        return 0
