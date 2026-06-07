from __future__ import annotations

from tft_ai_coach.advisor import CoachEngine
from tft_ai_coach.data.meta import load_comps
from tft_ai_coach.models import GameState


def main() -> None:
    comps = load_comps()
    assert comps, "starter comps should load"
    engine = CoachEngine(comps)
    recs = engine.recommend(
        GameState(
            stage="3-2",
            level=6,
            gold=42,
            board=["Ezreal", "Leona"],
            bench=["Xayah"],
            shop=["Graves", "Morgana"],
            items=["B.F. Sword", "Recurve Bow"],
        )
    )
    assert recs, "recommendations should be produced"
    assert recs[0].score > 0

    noisy_shop_recs = engine.recommend(GameState(stage="2-5", shop=["Nunu", "Vex", "Bard"]))
    assert noisy_shop_recs[0].comp.id == "groovians", noisy_shop_recs[0].comp.name
    print("smoke ok", recs[0].comp.name, recs[0].score)


if __name__ == "__main__":
    main()
