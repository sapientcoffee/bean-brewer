# ☕ Bean-Brewer: Agent Orchestration & Triage Constitution (`AGENTS.md`)

Welcome to **Bean-Brewer**, the multi-agent specification, decomposition, and implementation forge for Google Antigravity (`agy`).

---

## 1. Brew Size Triage Rule (Ristretto / Cortado / Carafe)

Before generating planning artifacts or dispatching subagents, triage every incoming request into one of three deterministic brew sizes:

| Brew Size | Scope & Triggers | Pipeline Path |
| :--- | :--- | :--- |
| **Ristretto** (`XS/S`) | $\le 2$ files, typo/bugfix, config tweak, zero new schemas or public contracts | **Fast-Track TDD**: Skip `.scratch/<id>/` ceremony. Write failing test -> fix -> `skills/code-hygiene` -> single atomic Conventional Commit. |
| **Cortado** (`M`) | 3–6 files, single-component feature or endpoint, localized contract update | **Compact Recipe**: Emit `.scratch/<id>/03_PRD.md`, `04_SPEC.md`, and `05_PLAN.md` ($\le 3$ slices) -> Light Council (`@code-inspection`) -> Group Head TDD on **The Pass** (`epic/<id>-<slug>`). |
| **Carafe** (`L/XL`) | Cross-cutting architecture, $>6$ files, new schemas/auth boundaries, multi-agent parallelism | **Full 9-Stage Barista Pipeline**: `01_QUESTIONS.md` -> Stage 2 Blind Cupping (`02_EXTRACTION.md`) -> `03_PRD.md` -> `04_SPEC.md` (`to-spec`) -> `05_PLAN.md` (`to-tickets`) -> Stage 6A Council (`06_COUNCIL.md`) -> Stage 6B Spec PR & `promote` -> Stage 7 Parallel Group Heads (`worktree`) -> Stage 8 Reaper (`@execution-verifier` & `06_WALKTHROUGH.md`) -> Stage 9 PR Delivery. |

---

## 2. Information Barriers & Context Hygiene

1. **Stage 2 Blind Cupping (`skills/research`)**:
   - Read-only scouts (`research`, `@context-mapping`, `@codebase-analysis`, `@pattern-recognition`) read **only** `.scratch/<id>/01_QUESTIONS.md`, and `@extraction-synthesizer` compiles their factual findings into `.scratch/<id>/02_EXTRACTION.md` with OKF stamping.
   - Never pass feature prompts, `.scratch/` specs, or `Status: Proposed` ADRs into Blind Cupping, and **never** use `/teamwork` during Stage 2 Blind Cupping.
2. **Stage 4 Durable Specifications (`skills/to-spec`)**:
   - Delegate to `@system-design` via `invoke_subagent`. `.scratch/<id>/04_SPEC.md` must contain **zero brittle source file paths**. Define architecture via module boundaries, physical `contracts/`, and numbered test seams (`SEAM-01..N`).
3. **Stage 5 Tracer-Bullet Slices (`skills/to-tickets`)**:
   - Delegate to `@system-design` via `invoke_subagent`. `.scratch/<id>/05_PLAN.md` decomposes work into end-to-end vertical slices (`[AFK]` or `[HITL]`), referencing PRD acceptance criteria strictly by ID (`Covers: AC1, AC2`).
4. **Stage 6B Promotion (`skills/promote`)**:
   - `scripts/promote.py --github --clean-scratch` provisions native GitHub Sub-Issues with verbatim ACs and `<!-- bean-slice-id -->` markers, then removes `.scratch/<id>/` before the Spec PR is squash-merged.

---

## 3. Group Head Execution, Reaper Verification, & Enterprise `/teamwork`

- **Worktree & Slot Isolation (`skills/worktree`)**: Every parallel `@code-implementation` **Group Head** runs inside `.worktrees/task-<id>-<slug>/` branched off **The Pass** (`--epic-branch epic/<id>-<slug>`) with a dedicated `BEAN_WORKER_SLOT`.
- **One Atomic Commit per Ticket**: Each Group Head executes Red-Green-Refactor and creates **one atomic Conventional Commit** for its assigned slice before merging back into **The Pass**.
- **Velocity Reaper (`@execution-verifier`) & Walkthrough Recorder (`@walkthrough-recorder`)**: `@execution-verifier` adversarially verifies exit code `0`, performs the **Spec-Axis Check** (every `AC1..ACN` maps to at least one passing test function in the diff), checks for test bypasses (`.skip`, `xit`), and flips shipped ADRs from `Status: Proposed` to `Status: Accepted`. `@walkthrough-recorder` authors `walkthrough_scenario.json`, runs `scripts/record.py`, and compiles `plans/<id>/06_WALKTHROUGH.md` with repo-root-relative asset paths without a leading slash.
- **Enterprise `/teamwork` Council & Wave Options (`Carafe`)**:
  - **Stage 6A `/teamwork` Council**: For high-blast-radius Carafe specs, convene `@system-design` (Plan Owner), `@contract-auditor`, `@code-inspection`, `@threat-modeler`, `@reviewer-product`, and `@review-arbiter` (Chair) via `/teamwork` (`send_message`) for live cross-examination before running `council_loop.py`.
  - **Stage 7/8 `/teamwork` Wave**: Combine 3x `@code-implementation` Group Heads (in isolated `.worktrees/task-<id>-<slug>/` slots) with `@contract-auditor` and `@execution-verifier` to collaborate across contract seams on **The Pass**.
