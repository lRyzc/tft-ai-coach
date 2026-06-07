from tft_ai_coach.models import CompDefinition, GameState, Recommendation
from tft_ai_coach.ui.app import CoachApp


def _rec(comp_id: str, score: float) -> Recommendation:
    return Recommendation(comp=CompDefinition(id=comp_id, name=comp_id, tier="S"), score=score)


def main() -> None:
    app = CoachApp()
    try:
        app.stable_comp_id = "groovians"
        stable = app._stable_recommendations([_rec("challenger", 32), _rec("groovians", 24)])
        assert stable[0].comp.id == "groovians"
        stable = app._stable_recommendations([_rec("challenger", 32), _rec("groovians", 24)])
        assert stable[0].comp.id == "groovians"
        stable = app._stable_recommendations([_rec("challenger", 32), _rec("groovians", 24)])
        assert stable[0].comp.id == "challenger"

        app.last_state = GameState(stage="2-5")
        assert app._stable_health(61, "2-5") is None
        assert app._stable_health(61, "2-5") == 61

        app.last_state = GameState(stage="3-2", health=52)
        assert app._stable_health(4, "3-2") == 52
        assert app._stable_health(4, "3-2") == 52
        assert app._stable_health(4, "3-2") == 4
    finally:
        app.root.destroy()
    print("live stability smoke ok")


if __name__ == "__main__":
    main()
