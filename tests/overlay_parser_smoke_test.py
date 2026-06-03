from __future__ import annotations

from tft_ai_coach.ui.overlay import _parse_overlay_text


def main() -> None:
    parsed = _parse_overlay_text(
        "TFT AI Coach | 5-7 Late\n"
        "Comp: AD Flex (A)\n"
        "Loja: Illaoi, Aurelion Sol, Tahm Kench, Caitlyn, Briar\n"
    )
    shop = parsed["shop"]
    assert "Illaoi" in shop
    assert "A. Sol" in shop
    assert "Tahm" in shop
    assert "Caitlyn" in shop
    assert "Briar" in shop
    print("overlay parser ok", shop)


if __name__ == "__main__":
    main()
