from tft_ai_coach.data.meta import load_comps


def main() -> None:
    comps = load_comps()
    groovians = next(comp for comp in comps if comp.id == "groovians")
    assert groovians.name == "Embalos no Espaco Ornn"
    assert groovians.carry_order[:3] == ["Samira", "Ornn", "Nami"]
    assert groovians.item_builds["Samira"] == ["Infinity Edge", "Last Whisper", "Guinsoo's Rageblade"]
    assert groovians.star_targets["Samira"] == 3
    assert groovians.positioning["Ornn"] == (3, 4)
    assert groovians.leveling_guide[0]["stage"] == "2-1"
    assert groovians.synergies
    print("meta guide smoke ok")


if __name__ == "__main__":
    main()
