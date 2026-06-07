from __future__ import annotations

from collections import Counter

from rapidfuzz import fuzz

from tft_ai_coach.models import CompDefinition, GameState, Recommendation

TIER_WEIGHT = {"S": 18, "A": 12, "B": 7, "C": 2}


class CoachEngine:
    def __init__(self, comps: list[CompDefinition]) -> None:
        self.comps = comps

    def recommend(self, state: GameState, limit: int = 3) -> list[Recommendation]:
        recommendations = [self._score_comp(comp, state) for comp in self.comps]
        recommendations.sort(key=lambda item: item.score, reverse=True)
        return recommendations[:limit]

    def _score_comp(self, comp: CompDefinition, state: GameState) -> Recommendation:
        score = float(TIER_WEIGHT.get(comp.tier.upper(), 5))
        reasons: list[str] = []
        actions: list[str] = []
        owned = _normalized_counter(state.owned_units)
        shop = _normalized_counter(state.shop)
        items = [item.lower() for item in state.items]
        augments = [augment.lower() for augment in state.augments]
        has_build_signal = bool(owned or items or augments)

        owned_hits = _matches(comp.core_units, owned)
        if owned_hits:
            gain = 14 * len(owned_hits)
            score += gain
            reasons.append(f"Voce ja tem {', '.join(owned_hits)} para essa linha.")

        shop_hits = _matches(comp.core_units, shop)
        if shop_hits:
            shop_weight = 8 if has_build_signal else 0
            score += shop_weight * len(shop_hits)
            actions.append(f"Comprar/segurar da loja: {', '.join(shop_hits)}.")
            if not has_build_signal:
                reasons.append("Loja lida sem board confiavel; nao vou pivotar so por essas pecas.")

        carry_hits = _matches(comp.carry_units, owned)
        if carry_hits:
            score += 10 * len(carry_hits)
            reasons.append(f"Carry possivel ja apareceu: {', '.join(carry_hits)}.")

        stage = _stage_number(state.stage)
        if stage <= 2:
            early_hits = _matches(comp.early_units, owned)
            if early_hits:
                score += 6 * len(early_hits)
                reasons.append(f"Early game encaixa com {', '.join(early_hits)}.")
        elif stage == 3:
            mid_hits = _matches(comp.mid_units, owned)
            if mid_hits:
                score += 6 * len(mid_hits)
                reasons.append(f"Mid game ja tem base com {', '.join(mid_hits)}.")

        item_hits = _keyword_hits(comp.item_tags, items)
        if item_hits:
            score += 7 * len(item_hits)
            reasons.append(f"Itens/componentes combinam com {', '.join(sorted(item_hits))}.")

        core_item_hits = _keyword_hits(comp.core_items, items)
        if core_item_hits:
            score += 10 * len(core_item_hits)
            reasons.append(f"Item core ja aponta para {', '.join(sorted(core_item_hits))}.")

        augment_hits = _keyword_hits(comp.augment_keywords, augments)
        if augment_hits:
            score += 9 * len(augment_hits)
            reasons.append(f"Augments conversam com {', '.join(sorted(augment_hits))}.")

        if state.gold is not None:
            if state.gold >= 50:
                score += 4
                actions.append("Economia forte: preserve juros antes de rolar pesado.")
            elif state.gold <= 10 and _stage_number(state.stage) >= 4:
                actions.append("Pouco gold para o stage: priorize estabilizar com pares baratos.")

        if state.level is not None:
            if state.level >= 8 and comp.style == "flex":
                score += 5
                reasons.append("Level alto favorece linha flex com upgrades caros.")
            elif state.level <= 6 and comp.style == "stabilize":
                score += 4

        missing = [unit for unit in comp.core_units if _norm(unit) not in owned and _norm(unit) not in shop]
        if missing:
            actions.append(f"Procurar proximos encaixes: {', '.join(missing[:4])}.")

        if comp.alternative_units:
            actions.append(f"Alternativas se nao bater: {', '.join(comp.alternative_units[:4])}.")

        if comp.carousel_priority:
            actions.append(f"Carrossel: priorize {', '.join(comp.carousel_priority[:3])}.")

        if comp.economy_plan:
            actions.append(comp.economy_plan)
        if stage and comp.leveling_plan:
            stage_key = str(stage)
            if stage_key in comp.leveling_plan:
                actions.append(comp.leveling_plan[stage_key])
        actions.extend(comp.notes[:2])

        if not reasons:
            reasons.append("Linha viavel por tier/meta, mas ainda falta sinal forte do board.")

        return Recommendation(comp=comp, score=round(score, 2), reasons=reasons, actions=actions)


def _stage_number(stage: str) -> int:
    try:
        return int(stage.split("-")[0])
    except Exception:
        return 0


def _norm(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _normalized_counter(values: list[str]) -> Counter[str]:
    return Counter(_norm(value) for value in values if value.strip())


def _matches(names: list[str], candidates: Counter[str]) -> list[str]:
    hits: list[str] = []
    for name in names:
        normalized = _norm(name)
        if normalized in candidates:
            hits.append(name)
    return hits


def _keyword_hits(keywords: list[str], values: list[str]) -> set[str]:
    hits: set[str] = set()
    for keyword in keywords:
        keyword_l = keyword.lower()
        for value in values:
            if keyword_l in value or fuzz.partial_ratio(keyword_l, value) >= 88:
                hits.add(keyword)
    return hits
