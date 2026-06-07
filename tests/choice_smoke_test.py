from __future__ import annotations

from tft_ai_coach.advisor import CoachEngine, compact_overlay_summary
from tft_ai_coach.advisor.choices import best_decision_option, ranked_decision_options
from tft_ai_coach.data.meta import load_comps
from tft_ai_coach.models import DecisionOption, GameState


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

    reward_state = GameState(
        stage="2-4",
        screen_context="reward_choice",
        decision_slots=[
            DecisionOption(1, "Miss Fortune", "reward", (0.274, 0.824, 0.116, 0.165)),
            DecisionOption(2, "Ornn", "reward", (0.398, 0.824, 0.116, 0.165)),
            DecisionOption(3, "Jinx", "reward", (0.522, 0.824, 0.116, 0.165)),
        ],
    )
    reward_recs = engine.recommend(reward_state)
    option, reason = best_decision_option(reward_state, reward_recs)
    assert option is not None
    assert option.region[2] > 0
    assert reason

    shop_state = GameState(
        stage="2-5",
        level=5,
        gold=26,
        shop=["Briar", "Leona", "Gnar", "Maokai", "Gnar"],
        decision_slots=[
            DecisionOption(1, "Briar", "shop", (0.250, 0.908, 0.103, 0.083)),
            DecisionOption(2, "Leona", "shop", (0.354, 0.908, 0.103, 0.083)),
            DecisionOption(3, "Gnar", "shop", (0.458, 0.908, 0.103, 0.083)),
            DecisionOption(4, "Maokai", "shop", (0.562, 0.908, 0.103, 0.083)),
            DecisionOption(5, "Gnar", "shop", (0.666, 0.908, 0.103, 0.083)),
        ],
    )
    shop_recs = engine.recommend(shop_state)
    shop_targets = ranked_decision_options(shop_state, shop_recs)
    assert not shop_targets

    focused_shop_state = GameState(
        stage="2-5",
        level=5,
        gold=26,
        board=["Miss Fortune"],
        shop=["Briar", "Leona", "Gnar", "Maokai", "Gnar"],
        decision_slots=shop_state.decision_slots,
    )
    focused_shop_recs = engine.recommend(focused_shop_state)
    focused_shop_targets = ranked_decision_options(focused_shop_state, focused_shop_recs)
    assert focused_shop_targets
    assert focused_shop_targets[0][0].name == "Maokai", focused_shop_targets
    print("choice smoke ok")


if __name__ == "__main__":
    main()
