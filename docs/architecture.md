# Architecture

```mermaid
flowchart LR
  A["TFT window"] --> B["Window capture"]
  B --> C["Vision pipeline"]
  C --> D["Structured game state"]
  E["Data Dragon updater"] --> F["Local patch database"]
  G["Meta comp database"] --> H["Recommendation engine"]
  F --> H
  D --> H
  H --> I["Desktop coach"]
  H --> J["Overlay"]
  D --> K["Snapshots and review"]
```

## Modules

- `capture`: finds and captures windows.
- `vision`: maps screen regions and turns screenshots into a `GameState`.
- `data`: downloads official static data and loads editable meta files.
- `advisor`: ranks routes and explains decisions.
- `ui`: desktop control center and overlay.

