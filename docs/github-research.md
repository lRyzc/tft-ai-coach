# GitHub Research

## Best Candidates

| Repository | Fit | License | Notes |
| --- | --- | --- | --- |
| `jfd02/TFT-OCR-BOT` | Screen OCR and TFT state tracking reference | GPL-3.0 | Strongest evidence that OCR/window capture can read round, level, gold, shop, items, board, and bench. It is archived and bot-oriented, so we should not copy code into this private app unless we accept GPL obligations. |
| `Uranium2/tft_augments_helper` | Augment OCR and overlay ideas | MIT | Useful for augment round detection, OCR cleanup, fuzzy text matching, and overlay refresh loop. Small and rough, but reusable if we keep attribution. |
| `Pompeiro/TFT-DSS` | Shop recommendation logic and old window capture examples | MIT | Useful conceptually for scoring shop units by pool/traits/classes. Old set data and UI, but the direction matches our recommender. |
| `tacticians-academy/teamfight-simulator` | Combat simulation inspiration | ISC in `package.json` | Useful later for board strength and fight odds. Current public code focuses old sets and needs lots of work for current patches. |

## Decision

Start a clean Python app and borrow ideas, not whole architecture:

- Use MIT/ISC projects only when direct code reuse is worth it.
- Treat GPL OCR bot as research only for now.
- Keep capture, recognition, meta data, recommendation, and overlay as separate modules.
- Add a later bridge to a real simulator after the screen-state pipeline is stable.

## Product Gap

I did not find an open-source project that already combines:

- current-patch data updater
- TFT screen recognition
- personal live coach
- overlay
- post-game review
- combat odds

So our best route is a custom app that integrates useful ideas from the research list.

