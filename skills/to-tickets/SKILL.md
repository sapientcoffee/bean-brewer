---
name: to-tickets
description: "Stage 5 Recipe Card Slices decomposer. Decomposes .scratch/<id>/04_SPEC.md into tracer-bullet vertical slices in .scratch/<id>/05_PLAN.md with AC ID references (Covers: AC1, AC2), [AFK]/[HITL] execution modes, DAG dependencies (*Depends On:*), and OKF frontmatter stamping."
---

<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# 🎟️ Skill: Stage 5 Recipe Card Slices (`to-tickets`)

You are executing the **Recipe Card Slices** (`to-tickets`) skill for Stage 5 of the Bean-Brewer pipeline. Your goal is to decompose `.scratch/<id>/04_SPEC.md` and `.scratch/<id>/03_PRD.md` into self-contained, end-to-end **tracer-bullet vertical slices** in `.scratch/<id>/05_PLAN.md`.

---

## ⚡ Operational Protocol

### Step 1: Delegate Vertical-Slice Decomposition to `@system-design` (`invoke_subagent`)
- Delegate Gate 2 vertical-slice planning to `@system-design` via `invoke_subagent` so `@expo` remains in the Smart Zone ($< 100\text{K}$ tokens).
- Avoid horizontal layer-cake tasks (e.g., "create all DB tables", then "create all API routes").
- Each ticket (`SLICE-01`, `SLICE-02`, ...) must cut vertically through contract, logic, and verification harness (`SEAM-01..N`) so it compiles, passes tests, and delivers verifiable behavior independently.

### Step 2: Reference Acceptance Criteria by ID (`Covers: AC1, AC2`)
- Never duplicate or paraphrase acceptance criteria prose inside `.scratch/<id>/05_PLAN.md`.
- Every slice MUST declare `Covers: AC1, AC2` referencing exact AC IDs defined in `.scratch/<id>/03_PRD.md`.
- Every `AC1..ACN` in `03_PRD.md` must be covered by at least one slice.

### Step 3: Declare Execution Mode (`[AFK]` or `[HITL]`) & DAG Dependencies
- Prefix each slice title with its autonomy classification:
  - `[AFK]`: Autonomous execution suitable for a parallel **Group Head** (`@code-implementation`) inside an isolated worktree.
  - `[HITL]`: Requires human-in-the-loop review, external credentials, or interactive design verification.
- Declare explicit DAG dependencies using `*Depends On:* None` or `*Depends On:* SLICE-01, SLICE-02`.

### Step 4: Stamp OKF Frontmatter & Lint Plan
1. Stamp OKF metadata onto `.scratch/<id>/05_PLAN.md`:
   ```bash
   python3 scripts/okf.py stamp --file ".scratch/<id>/05_PLAN.md" --doc-type "plan" --status "Draft"
   ```
2. Validate DAG acyclicity, TDD verification pairing, and AC traceability:
   ```bash
   python3 scripts/plan_lint.py --plan ".scratch/<id>/05_PLAN.md"
   ```

---

## 📄 Output Structure (`.scratch/<id>/05_PLAN.md`)

```markdown
# 05 Execution Plan: <Feature Title>

## Vertical Slices

### [ ] SLICE-01: [AFK] <Vertical Slice Title>
- *Depends On:* None
- Covers: AC1, AC2
- *Test Seam:* `SEAM-01`
- *Verification:* `pytest tests/test_slice_01.py`

### [ ] SLICE-02: [HITL] <Vertical Slice Title>
- *Depends On:* SLICE-01
- Covers: AC3
- *Test Seam:* `SEAM-02`
- *Verification:* `pytest tests/test_slice_02.py`
```
