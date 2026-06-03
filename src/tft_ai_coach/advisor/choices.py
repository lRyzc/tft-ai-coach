from __future__ import annotations

import unicodedata

from rapidfuzz import fuzz

from tft_ai_coach.models import CompDefinition, GameState, Recommendation


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
    return ""


def divinity_summary(state: GameState, recommendations: list[Recommendation]) -> str:
    options = state.decision_options or _extract_known_options(state.decision_text, DIVINITY_NOTES)
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
