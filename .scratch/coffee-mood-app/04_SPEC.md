---
id: 04_SPEC
type: specification
name: 04_SPEC
description: System Architecture Specification for Coffee Mood App
status: draft
stage: 4_spec
generated:
  by: bean-brewer/to-spec
  at: '2026-11-06T16:37:43Z'
sources:
- id: 03_PRD
  resource: 03_PRD.md
stages_completed:
  4_spec: bean-brewer/to-spec (2026-11-06T16:37:43Z)
---

# ☕ System Architecture Specification: Coffee Mood Selection Web App (`04_SPEC`)

## 1. Architectural Topology & Module Boundaries
The web application is structured across decoupled module boundaries:
- **Module `MoodCatalog`**: Encapsulates the immutable catalog of mood profiles, recipes, and tasting descriptors validated against schema `contracts/coffee-mood-schema.json`.
- **Module `RecipeCalculator`**: Calculates dry coffee dosage (g), water volume (ml), and temperature based on serving size scale factor and brew method ratio.
- **Module `BrewTimerState`**: Manages the tick interval, countdown timer duration, pause/resume state machine, and phase announcements.
- **Module `ViewRenderer`**: Renders DOM elements, accessibility tags, active mood highlight states, and recipe details.

## 2. Formal Schema Contract
All recipe models adhere to the JSON Schema contract defined in `contracts/coffee-mood-schema.json`.

## 3. Physical Test Seams
- **`SEAM-01` (Catalog & Lookup Seam)**: Given a valid mood key (`focus`, `sluggish`, `stressed`, `creative`, `social`, `midnight`), the lookup returns a complete recipe matching the contract schema. Invalid mood keys fall back safely to `focus`.
- **`SEAM-02` (Dosage Scaling Seam)**: Given base water volume 250ml and brew ratio 1:16, returns 15.6g of coffee. When scaling to 2 servings (500ml), returns 31.2g.
- **`SEAM-03` (Timer State Seam)**: Supports transitions `idle -> running -> paused -> running -> completed`. Emits accurate remaining seconds on every tick.
- **`SEAM-04` (DOM & Accessibility Seam)**: All interactive buttons possess accessible names, color contrast conforms to WCAG AA, and tab indexing is sequential.
