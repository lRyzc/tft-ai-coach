# TFT AI Coach

Personal TFT companion prototype for screen-based coaching, patch-aware data, and local overlays.

## What Exists Now

- Desktop app shell with a coach panel and overlay window.
- Data Dragon updater for current TFT champions, items, traits, augments, and icons.
- Window capture module for Windows desktop/game windows.
- First-pass shop recognition from screen crops using Data Dragon champion portraits.
- OCR-assisted champion name reading for the shop, using Tesseract when installed.
- Live Coach mode that keeps reading the selected game window and updates a compact overlay automatically.
- Minimal, draggable in-game overlay focused on comp, shop, economy, augments, and early/mid/late plan.
- Click-through decision aura that highlights the recommended augment/divinity/reward card in-place.
- Local overlay settings saved under `data/runtime`.
- Dark meta-comps dashboard with tier, difficulty, tempo, carry units, and champion icons.
- Early HUD OCR for stage, level, gold, and augment-choice screens.
- First-pass special choice detection for Divinity and augment screens.
- Debug crop export for shop, board, bench, augments, stage, and gold regions.
- Early recommendation engine that scores comp routes from board, bench, shop, items, gold, level, and stage.
- Research notes on open-source TFT projects worth mining for ideas.

## Quick Start

```powershell
.\scripts\install_deps.ps1
.\scripts\update_data.ps1
.\scripts\run.ps1
```

The first run downloads dependencies into `work/pydeps` and official TFT data into `data/ddragon`.

## Project Shape

```text
src/tft_ai_coach/
  advisor/       decision and recommendation engine
  capture/       Windows screen/window capture
  data/          patch and meta data loading
  ui/            desktop app and overlay
  vision/        screen layout and image recognition pipeline
docs/            research, roadmap, architecture notes
data/meta/       editable comp definitions
```

## Notes

This repo intentionally starts without game memory access, process injection, or click automation. The first goal is to build the local "eye" and "brain": capture the screen, understand the TFT state, and explain decisions.
