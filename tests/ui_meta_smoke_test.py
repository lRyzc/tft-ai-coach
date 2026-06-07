import tkinter as tk

from tft_ai_coach.ui.app import CoachApp


def main() -> None:
    app = CoachApp()
    comp = next(item for item in app.comps if item.id == "stay-groovy")
    assert app._champion_record("Nunu") is not None
    assert app._item_photo("Infinity Edge", 17) is not None
    assert app._item_photo("Guinsoo's Rageblade", 17) is not None
    for meta_comp in app.comps:
        for carry in meta_comp.carry_units:
            assert meta_comp.item_builds.get(carry), f"{meta_comp.name} missing items for {carry}"
    costs = [app._champion_cost(unit) or 0 for unit in app._display_units(comp)[:4]]
    assert costs == sorted(costs, reverse=True)

    parent = tk.Frame(app.root)
    parent.pack()
    dummy = tk.Frame(parent)
    dummy.pack()
    app._toggle_comp_guide(parent, comp, dummy)
    app.root.update()
    assert app.selected_guide_comp_id == "stay-groovy"
    app.root.destroy()
    print("ui meta smoke ok")


if __name__ == "__main__":
    main()
