from __future__ import annotations

import unicodedata

from rapidfuzz import fuzz

from tft_ai_coach.models import CompDefinition, DecisionOption, GameState, Recommendation


DIVINITY_NOTES = {
    "Kayle": ("A", ["items", "tempo", "flex"], "itens cedo deixam qualquer linha mais estavel"),
    "Ekko": ("A", ["economy", "tempo", "reroll"], "flashbacks tendem a abrir mais flexibilidade"),
    "Lissandra": ("A", ["ap", "control", "utility"], "boa ponte para linhas AP/utilidade"),
    "Pantheon": ("B", ["frontline", "defense"], "seguro quando falta linha de frente"),
    "Samira": ("A", ["ad", "tempo"], "forte sinal para AD/tempo"),
    "Nami": ("A", ["ap", "utility"], "boa quando a loja aponta para utilidade/AP"),
    "Ornn": ("S", ["frontline", "items", "late"], "frontline e itens escalam muito bem"),
}


AUGMENT_NOTES = {
    "Trabalho em Equipe": ("B", ["econ", "tempo"], "valor ok, mas menos direcional"),
    "Bando de Ladroes": ("A", ["items", "tempo"], "item extra acelera board e flex"),
    "Abra o Caminho": ("A", ["items", "scaling"], "bom quando a linha quer escalar dano"),
    "Corrosao": ("B", ["combat", "frontline"], "combate aceitavel se seu board bate de frente"),
    "A Torre": ("B", ["combat", "scaling"], "pede tempo de luta e board estavel"),
    "Vitalidade Vampirica": ("C", ["combat", "sustain"], "depende muito do dano atual"),
}


def choice_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    if state.screen_context == "divinity_choice":
        return divinity_summary(state, recommendations)
    if state.screen_context == "augment_choice":
        return augment_summary(state, recommendations)
    if state.screen_context == "reward_choice":
        return reward_summary(state, recommendations)
    return ""


def best_decision_option(state: GameState, recommendations: list[Recommendation]) -> tuple[DecisionOption | None, str]:
    ranked = ranked_decision_options(state, recommendations, limit=1)
    if not ranked:
        return None, choice_summary(state, recommendations)
    return ranked[0]


def ranked_decision_options(
    state: GameState,
    recommendations: list[Recommendation],
    limit: int = 3,
) -> list[tuple[DecisionOption, str]]:
    if not state.decision_slots:
        return []
    comp = recommendations[0].comp if recommendations else None
    scored = [(option, _score_option(option, comp)) for option in state.decision_slots]
    scored = [(option, score) for option, score in scored if score >= _minimum_score(option)]
    scored.sort(key=lambda item: item[1], reverse=True)
    if not scored:
        return []
    if scored[0][0].kind != "shop":
        scored = scored[:1]
    output: list[tuple[DecisionOption, str]] = []
    for index, (option, _score) in enumerate(scored[:limit]):
        runner_up = scored[index + 1][0].name if index == 0 and len(scored) > 1 else ""
        output.append((option, _option_reason(option, comp, runner_up)))
    return output


def divinity_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    options = [slot.name for slot in state.decision_slots] or state.decision_options or _extract_known_options(
        state.decision_text, DIVINITY_NOTES
    )
    if not options:
        if state.decision_text:
            return f"Divindade: lendo opcoes ({state.decision_text[:52]})"
        return "Divindade: aguardando opcoes"

    comp = recommendations[0].comp if recommendations else None
    ranked = sorted(options, key=lambda name: _score_divinity(name, comp), reverse=True)
    best = ranked[0]
    tier, _tags, reason = DIVINITY_NOTES.get(best, ("B", [], "melhor encaixe geral agora"))
    if len(ranked) > 1:
        return f"Divindade: escolha {best} ({tier}) > {ranked[1]} - {reason}."
    return f"Divindade: escolha {best} ({tier}) - {reason}."


def augment_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    if not state.augments:
        return "Augments: tela detectada, lendo nomes"
    comp = recommendations[0].comp if recommendations else None
    ranked = sorted(state.augments, key=lambda name: _score_augment(name, comp), reverse=True)
    best = ranked[0]
    tier, tags, reason = _augment_note(best)
    tag_line = f" [{', '.join(tags[:2])}]" if tags else ""
    if len(ranked) > 1:
        return f"Augments: escolha {best} ({tier}){tag_line} > {ranked[1]} - {reason}."
    return f"Augments: escolha {best} ({tier}){tag_line} - {reason}."


def reward_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    if not state.decision_slots:
        return "Recompensa: lendo campeoes/itens"
    best, reason = best_decision_option(state, recommendations)
    if best is None:
        return "Recompensa: aguardando leitura"
    return f"Recompensa: escolha {reason}"


def _score_divinity(name: str, comp: CompDefinition | None) -> float:
    tier, tags, _reason = DIVINITY_NOTES.get(name, ("B", [], ""))
    score = _tier_score(tier)
    if comp is None:
        return score
    comp_words = _comp_words(comp)
    score += 6 * len(set(tags) & comp_words)
    if _norm(name) in {_norm(unit) for unit in comp.core_units + comp.carry_units + comp.early_units}:
        score += 5
    return score


def _score_augment(name: str, comp: CompDefinition | None) -> float:
    tier, tags, _reason = _augment_note(name)
    score = _tier_score(tier)
    if comp is None:
        return score
    comp_words = _comp_words(comp)
    score += 5 * len(set(tags) & comp_words)
    for keyword in comp.augment_keywords + comp.item_tags:
        if fuzz.partial_ratio(_norm(keyword), _norm(name)) >= 82:
            score += 4
    return score


def _score_option(option: DecisionOption, comp: CompDefinition | None) -> float:
    if option.kind == "shop":
        return _score_shop(option, comp) + option.confidence
    if option.kind == "divinity":
        return _score_divinity(option.name, comp) + option.confidence
    if option.kind == "augment":
        return _score_augment(option.name, comp) + option.confidence
    if option.kind == "reward":
        return _score_reward(option, comp) + option.confidence
    return option.confidence


def _minimum_score(option: DecisionOption) -> float:
    if option.kind == "shop":
        return 14.0
    return 0.01


def _option_reason(option: DecisionOption, comp: CompDefinition | None, runner_up: str = "") -> str:
    if option.kind == "shop":
        return _shop_reason(option, comp)
    if option.kind == "divinity":
        tier, _tags, reason = DIVINITY_NOTES.get(option.name, ("B", [], "melhor encaixe geral agora"))
        label = f"{option.name} ({tier})"
        if runner_up:
            label += f" > {runner_up}"
        return f"{label}: {reason}"
    if option.kind == "augment":
        tier, tags, reason = _augment_note(option.name)
        tag_line = f" [{', '.join(tags[:2])}]" if tags else ""
        label = f"{option.name} ({tier}){tag_line}"
        if runner_up:
            label += f" > {runner_up}"
        return f"{label}: {reason}"
    if option.kind == "reward":
        reason = _reward_reason(option, comp)
        label = option.name
        if option.item:
            label += f" + {option.item}"
        if runner_up:
            label += f" > {runner_up}"
        return f"{label}: {reason}"
    return option.name


def _score_shop(option: DecisionOption, comp: CompDefinition | None) -> float:
    if comp is None:
        return 0.0
    normalized = _norm(option.name)
    score = 0.0
    if normalized in {_norm(unit) for unit in comp.carry_units}:
        score += 32
    if normalized in {_norm(unit) for unit in comp.core_units}:
        score += 24
    if normalized in {_norm(unit) for unit in comp.mid_units}:
        score += 16
    if normalized in {_norm(unit) for unit in comp.early_units}:
        score += 12
    if normalized in {_norm(unit) for unit in comp.alternative_units}:
        score += 8
    return score


def _shop_reason(option: DecisionOption, comp: CompDefinition | None) -> str:
    if comp is None:
        return f"{option.name}: comprar se for upgrade ou par"
    normalized = _norm(option.name)
    if normalized in {_norm(unit) for unit in comp.carry_units}:
        return f"{option.name}: comprar, carry chave da {comp.name}"
    if normalized in {_norm(unit) for unit in comp.core_units}:
        return f"{option.name}: comprar, entra na comp {comp.name}"
    if normalized in {_norm(unit) for unit in comp.mid_units}:
        return f"{option.name}: comprar, estabiliza o mid game"
    if normalized in {_norm(unit) for unit in comp.early_units}:
        return f"{option.name}: comprar/segurar, bom early da linha"
    if normalized in {_norm(unit) for unit in comp.alternative_units}:
        return f"{option.name}: segurar como alternativa"
    return f"{option.name}: comprar apenas se fizer par"


def _score_reward(option: DecisionOption, comp: CompDefinition | None) -> float:
    if comp is None:
        return 8.0
    normalized = _norm(option.name)
    score = 6.0
    core = {_norm(unit) for unit in comp.core_units}
    carries = {_norm(unit) for unit in comp.carry_units}
    early = {_norm(unit) for unit in comp.early_units}
    mid = {_norm(unit) for unit in comp.mid_units}
    alternatives = {_norm(unit) for unit in comp.alternative_units}
    if normalized in carries:
        score += 26
    if normalized in core:
        score += 18
    if normalized in mid:
        score += 10
    if normalized in early:
        score += 8
    if normalized in alternatives:
        score += 6
    return score


def _reward_reason(option: DecisionOption, comp: CompDefinition | None) -> str:
    if comp is None:
        return "melhor leitura geral agora"
    normalized = _norm(option.name)
    if normalized in {_norm(unit) for unit in comp.carry_units}:
        return f"e carry/peca chave da {comp.name}"
    if normalized in {_norm(unit) for unit in comp.core_units}:
        return f"entra direto na composicao {comp.name}"
    if normalized in {_norm(unit) for unit in comp.mid_units}:
        return f"fortalece seu mid game na linha {comp.name}"
    if normalized in {_norm(unit) for unit in comp.alternative_units}:
        return f"boa alternativa se a linha principal nao bater"
    return f"mais coerente com o plano atual: {comp.name}"


def _augment_note(name: str) -> tuple[str, list[str], str]:
    normalized = _norm(name)
    for known_name, note in AUGMENT_NOTES.items():
        if normalized.startswith(_norm(known_name)) or fuzz.partial_ratio(normalized, _norm(known_name)) >= 84:
            return note
    return ("B", [], "sem leitura de tier especifica ainda; usar encaixe com a comp")


def _comp_words(comp: CompDefinition) -> set[str]:
    words = {comp.style.lower(), comp.tempo.lower()}
    words.update(tag.lower() for tag in comp.item_tags)
    words.update(tag.lower() for tag in comp.augment_keywords)
    return {word for word in words if word}


def _extract_known_options(text: str, table: dict[str, tuple[str, list[str], str]]) -> list[str]:
    normalized_text = _norm(text)
    found: list[str] = []
    for name in table:
        if _norm(name) in normalized_text:
            found.append(name)
    return found


def _tier_score(tier: str) -> float:
    return {"S": 30.0, "A": 22.0, "B": 14.0, "C": 5.0}.get(tier.upper(), 10.0)


def _norm(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in folded.lower() if ch.isalnum())
