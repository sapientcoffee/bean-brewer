---
name: to-spec
description: Stage 4 Recipe Card Spec generator. Synthesizes .scratch/<id>/04_SPEC.md and physical contracts/ from 02_EXTRACTION.md and 03_PRD.md with zero brittle source file paths, SEAM-01..N test seams, and OKF frontmatter stamping.
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

# 📋 Skill: Stage 4 Recipe Card Spec (`to-spec`)

You are executing the **Recipe Card Spec** (`to-spec`) skill for Stage 4 of the Bean-Brewer pipeline. Your goal is to synthesize `.scratch/<id>/02_EXTRACTION.md` (Blind Cupping factual map) and `.scratch/<id>/03_PRD.md` (Product Requirements & `AC1..ACN`) into `.scratch/<id>/04_SPEC.md` and physical schema contracts in `.scratch/<id>/contracts/`.

---

## ⚡ Operational Protocol

### Step 1: Delegate Specification Synthesis to `@system-design` (`invoke_subagent`)
To keep the Head Barista (`@expo`) inside the Smart Zone ($< 100\text{K}$ tokens), delegate Gate 1 specification synthesis to `@system-design` via `invoke_subagent`:
1. Instruct `@system-design` to read `.scratch/<id>/02_EXTRACTION.md` (existing component boundaries, domain interfaces, and architectural invariants) and `.scratch/<id>/03_PRD.md` (user stories, numbered acceptance criteria `AC1..ACN`, and non-goals).
2. `@system-design` authors `.scratch/<id>/04_SPEC.md` and physical schema contracts in `.scratch/<id>/contracts/`, stamps OKF frontmatter, and returns a concise ($\le 300$ words) summary.

### Step 2: Enforce Zero Brittle Source File Paths
- **CRITICAL**: `@system-design` must **NOT** hardcode brittle implementation file paths or line numbers inside `.scratch/<id>/04_SPEC.md`.
- Describe architecture strictly through **Durable Module Boundaries**, **Public Interfaces**, **Data Contracts**, and **State Transitions**. File path mapping belongs exclusively to `02_EXTRACTION.md` and ephemeral execution slices.

### Step 3: Emit Physical Schema Contracts (`contracts/`)
- Emit machine-verifiable contract definitions into `.scratch/<id>/contracts/` (e.g., `openapi.yaml`, `schema.json`, `types.ts`, `schema.proto`) before finalizing the specification prose.

### Step 4: Define Architectural Test Seams (`SEAM-01..N`)
- Every external boundary, module interface, or state transition in `.scratch/<id>/04_SPEC.md` must declare numbered test seams (`SEAM-01`, `SEAM-02`, ... `SEAM-0N`):
  - **Seam ID**: `SEAM-01`
  - **Boundary / Interface**: Logical module or contract boundary under test.
  - **Fixture / Harness Strategy**: In-memory fake, contract test, or integration harness required.
  - **Mapped ACs**: Traceability back to `AC1..ACN` from `03_PRD.md`.

### Step 5: Stamp OKF Frontmatter & Lint Spec
Stamp deterministic OKF frontmatter on `.scratch/<id>/04_SPEC.md` and verify zero brittle source file paths via `plan_lint.py`:
```bash
python3 scripts/okf.py stamp --file ".scratch/<id>/04_SPEC.md" --doc-type "spec" --status "Draft"
python3 scripts/plan_lint.py --spec ".scratch/<id>/04_SPEC.md"
```

---

## 📄 Output Structure (`.scratch/<id>/04_SPEC.md`)

```markdown
# 04 Technical Specification: <Feature Title>

## 1. Architectural Overview & Module Boundaries
Describe logical components, state ownership, and interaction flows (zero hardcoded source file paths).

## 2. Physical Contracts (`contracts/`)
Summary of schemas emitted in `.scratch/<id>/contracts/`.

## 3. Test Seams (`SEAM-01..N`)
| Seam ID | Module Boundary | Verification Strategy | Covers ACs |
| :--- | :--- | :--- | :--- |
| `SEAM-01` | <Boundary Name> | <Contract / Unit / Integration> | `AC1, AC2` |

## 4. Failure Modes & Invariants
Rate limits, idempotency guarantees, rollback boundaries, and security invariants.
```
