---
id: epic-3-implement-recipe-calculator
type: ticket
name: '[AFK] STEP 3: Implement Recipe Calculator'
description: 'Slice 3 (AFK): Implement Recipe Calculator'
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
slice_id: epic-3
execution_mode: AFK
depends_on:
- STEP 2
covers:
- AC3
---

# [AFK] STEP 3: Implement Recipe Calculator

<!-- bean-slice-id: epic-3 -->
Parent Epic: #epic

## Slice Metadata
* **Slice ID:** `epic-3`
* **Execution Mode:** `[AFK]`
* **Target File:** `app/calculator.js`
* **Verification Command:** `python3 tests/test_coffee_mood_app.py`
* **Depends On:** STEP 2

## Acceptance Criteria Covered (`03_PRD.md`)
- AC3: Changing serving size (1 cup / 2 cups) dynamically recalculates required coffee dosage (grams) and water volume (ml) based on the recipe's ratio.

## Implementation Instructions
Follow TDD Red-Green-Refactor workflow per 05_PLAN.md.
