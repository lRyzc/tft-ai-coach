from __future__ import annotations

from tft_ai_coach.advisor.economy import economy_advice
from tft_ai_coach.models import GameState


def main() -> None:
    win = economy_advice(
        GameState(stage="2-5", level=5, gold=52, xp_current=10, xp_needed=20, streak_count=4, streak_type="win")
    )
    assert "winstreak" in win or "upar" in win, win

    loss = economy_advice(GameState(stage="3-2", level=6, gold=28, health=48, streak_count=4, streak_type="loss"))
    assert "sangramento" in loss or "role" in loss, loss

    low_hp = economy_advice(GameState(stage="4-2", level=7, gold=25, health=31))
    assert "vida baixa" in low_hp or "estabilizar" in low_hp, low_hp

    print("economy smoke ok")


if __name__ == "__main__":
    main()
