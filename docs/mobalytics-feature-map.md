# Mobalytics Feature Map

This app uses Mobalytics as a product benchmark, not as copied code, branding, assets, or private data.

## Observed Mobalytics TFT Features

Based on the current public Mobalytics pages checked on 2026-06-03:

- In-game TFT companion/overlay.
- Automatic augment suggestions.
- Challenger/expert-curated team comps.
- Comp guides for early game, mid game, and first-place/end-game execution.
- Shop highlights for champions that are core to the selected comp.
- Item cheat sheets and champion item recommendations.
- Lobby/opponent scouting.
- Import custom/community team comps into the overlay.
- Strategic gameplan widget.
- Carousel item priority.
- Alternative units/options when the perfect line does not appear.
- Leveling/economy guide by stage.
- Customizable overlay widgets, favorite comp, and overlay scale.
- Desktop app auto-starts/appears when the TFT match starts.
- Windows-only current TFT companion using Overwolf.

Sources:

- https://mobalytics.gg/tft/glp/app-download
- https://mobalytics.gg/blog/tft/how-to-use-the-mobalytics-tft-overlay/
- https://support.mobalytics.gg/hc/en-us/articles/360050449572-How-do-I-turn-on-my-TFT-overlay
- https://www.overwolf.com/app/mobalytics

## Our Equivalent Modules

| Mobalytics-like feature | Our module | Status |
| --- | --- | --- |
| Meta comps | `data/meta`, `advisor` | Starter schema exists |
| Comp guide | `data/meta` | Expanded schema planned |
| Shop highlights | `vision` + `advisor` | State/manual now, vision later |
| Item cheat sheet | `data/ddragon`, `data/meta` | Static data exists |
| Augment suggestions | `vision`, `advisor` | Schema support next |
| Leveling guide | `advisor` | Rule engine next |
| Carousel priority | `data/meta`, `advisor` | Schema support next |
| Lobby scouting | `vision` | Later |
| Import custom comps | `data/meta` | JSON import now |
| Overlay customization | `ui/overlay` | Basic overlay exists |
| Auto open on match | `capture` + app lifecycle | Later |

## Our Additions

- Screen-vision based personal coach without Overwolf.
- Explanations for every recommendation.
- Snapshot timeline and post-game review.
- Scenario lab for pivots, roll-downs, and item slams.
- Personal learning profile from the user's own games.
- Combat odds and positioning review after the base recognizer is reliable.

