---
id: epic-2-implement-recipe-catalog
type: ticket
name: '[AFK] STEP 2: Implement Recipe Catalog'
description: 'Slice 2 (AFK): Implement Recipe Catalog'
status: stable
stage: 6_promote
generated:
  by: bean-brewer/promote
  at: '2026-11-06T16:38:55Z'
sources:
- id: 05_PLAN
  resource: ../05_PLAN.md
  last_modified: '2026-11-06T16:38:35Z'
  sha256: 1bc5f360527c78948bbc229bd6b0aa40985543fcac73916d730822a289ddbb5d
stages_completed:
  6_promote: bean-brewer/promote (2026-11-06T16:38:55Z)
slice_id: epic-2
execution_mode: AFK
depends_on:
- STEP 1
covers:
- AC1
- AC2
---

# [AFK] STEP 2: Implement Recipe Catalog

<!-- bean-slice-id: epic-2 -->
Parent Epic: #epic

## Slice Metadata
* **Slice ID:** `epic-2`
* **Execution Mode:** `[AFK]`
* **Target File:** `app/data/coffee_moods.js`
* **Verification Command:** `python3 tests/test_coffee_mood_app.py`
* **Depends On:** STEP 1

## Acceptance Criteria Covered (`03_PRD.md`)
- AC1: The web application renders a mood grid containing at least 6 distinct moods (`focus`, `sluggish`, `stressed`, `creative`, `social`, `midnight`).
- AC2: Selecting any mood renders a dynamic Coffee Card with origin, roast level, tasting notes, brew method, ratio, grind size, and mood-matching lore.

## Implementation Instructions
Follow TDD Red-Green-Refactor workflow per 05_PLAN.md.
