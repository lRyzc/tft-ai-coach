from __future__ import annotations

from tft_ai_coach.advisor import CoachEngine, compact_overlay_summary
from tft_ai_coach.data.meta import load_comps
from tft_ai_coach.models import GameState


def main() -> None:
    engine = CoachEngine(load_comps())
    divinity_state = GameState(
        stage="1-1",
        screen_context="divinity_choice",
        decision_text="Kayle oferece itens e Ekko oferece flashbacks",
        decision_options=["Kayle", "Ekko"],
    )
    divinity_text = compact_overlay_summary(divinity_state, engine.recommend(divinity_state))
    assert "Divindade" in divinity_text
    assert "Kayle" in divinity_text

    augment_state = GameState(
        stage="2-1",
        screen_context="augment_choice",
        augments=["Trabalho em Equipe", "Bando de Ladroes", "Abra o Caminho"],
    )
    augment_text = compact_overlay_summary(augment_state, engine.recommend(augment_state))
    assert "Augments" in augment_text
    assert "Bando de Ladroes" in augment_text
    print("choice smoke ok")


if __name__ == "__main__":
    main()
