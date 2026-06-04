from __future__ import annotations

from tft_ai_coach.models import GameState


def economy_alert(state: GameState) -> str:
    stage = _stage_number(state.stage)
    gold = state.gold
    level = state.level
    health = state.health
    streak = state.streak_count or 0

    if health is not None and health <= 30 and stage >= 4:
        return "ALERTA: role agora para estabilizar"
    if _can_buy_level(state) and gold is not None and gold >= 20 and stage in {2, 3, 4}:
        return "ALERTA: upar nivel e manter tempo"
    if stage <= 2 and gold is not None and gold >= 20 and streak < 3:
        return "ALERTA: segurar juros"
    if stage == 3 and level is not None and level < 6 and gold is not None and gold >= 24:
        return "ALERTA: preparar level 6"
    if stage == 4 and level is not None and level < 8 and gold is not None and gold >= 40:
        return "ALERTA: subir 8 antes do rolldown"
    if stage >= 4 and gold is not None and gold <= 20:
        return "ALERTA: roll curto por upgrade"
    if streak >= 3 and state.streak_type == "win":
        return "ALERTA: preservar winstreak"
    if streak >= 3 and state.streak_type == "loss":
        return "ALERTA: loss streak controlada, nao quebrar econ"
    return "ALERTA: jogar board forte"


def economy_advice(state: GameState) -> str:
    stage = _stage_number(state.stage)
    gold = state.gold
    level = state.level
    health = state.health
    streak = state.streak_count or 0
    streak_type = state.streak_type

    if gold is None and level is None:
        return "Economia: aguardando leitura de gold/level."

    if health is not None and health <= 35 and stage >= 4:
        return "Economia: vida baixa; role para estabilizar antes de greed/level."

    if streak >= 3 and streak_type == "win":
        if _can_buy_level(state) and gold is not None and gold >= 20:
            return "Economia: winstreak forte; upar para preservar streak parece bom."
        return "Economia: preserve winstreak, compre upgrades sem quebrar juros chave."

    if streak >= 3 and streak_type == "loss":
        if gold is not None and gold >= 40 and stage <= 3:
            return "Economia: loss streak controlada; segure juros e prepare spike."
        if health is not None and health <= 55:
            return "Economia: loss streak perigosa; role leve para parar sangramento."

    if stage <= 2:
        if _can_buy_level(state) and gold is not None and gold >= 14 and streak_type == "win":
            return "Economia: upar para manter pressao e chegar no proximo breakpoint."
        if gold is not None and gold >= 20:
            return "Economia: segure juros; compre pares bons sem quebrar gold."
        return "Economia: jogue board forte, compre pares e evite rolar cedo."

    if stage == 3:
        if level is not None and level < 6 and _can_buy_level(state) and gold is not None and gold >= 24:
            return "Economia: compre XP para level 6 e estabilize o mid game."
        if level is not None and level < 6:
            return "Economia: prepare level 6; role pouco, so se o board estiver fraco."
        if gold is not None and gold >= 40:
            return "Economia: boa reserva; pense em level 7/8 antes de rolar pesado."
        return "Economia: estabilize se estiver perdendo muito HP, senao mantenha juros."

    if stage == 4:
        if health is not None and health <= 50 and gold is not None and gold >= 20:
            return "Economia: HP pede forca agora; role por upgrades da linha."
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


def _can_buy_level(state: GameState) -> bool:
    if state.xp_current is None or state.xp_needed is None:
        return False
    needed_xp = max(0, state.xp_needed - state.xp_current)
    if needed_xp == 0:
        return False
    gold = state.gold or 0
    return needed_xp <= 8 and gold >= needed_xp
