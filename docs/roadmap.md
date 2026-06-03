# Roadmap

## Phase 1 - Local Skeleton

- App launches from `scripts/run.ps1`.
- Data updater downloads current TFT Data Dragon files and icons.
- User can list visible windows and capture a screenshot.
- User can enter board/shop/items manually and receive recommendations.
- Overlay shows current recommendation.

## Phase 2 - Vision MVP

- Calibrate a fixed 16:9 layout.
- Detect shop names with OCR.
- Detect gold, level, and stage.
- Save screenshots and detection results for debugging.
- Let the user correct detections to create training data.

## Phase 3 - Board State

- Detect bench and board slots.
- Detect item components and completed items.
- Detect augment choices.
- Build confidence scores for every detection.

## Phase 4 - Coach Brain

- Patch-versioned comp database.
- Route scoring by units, items, augments, level, gold, and stage.
- Economy guidance for roll/level/hold.
- Explanation-first recommendations.

## Phase 5 - Premium Personal Features

- Timeline review for each game.
- Personal pattern tracking.
- Combat strength estimate.
- Scenario lab: "what if I roll", "what if I level", "what if I pivot".

