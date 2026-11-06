# ☕ Bean-Brewer: Implementation & Delivery Rules

Welcome to **Bean-Brewer**, the high-pressure implementation forge for Google Antigravity (`agy`).

## 1. Triage First (Ristretto / Cortado / Carafe)
* **Ristretto (`XS/S`)**: $\le 2$ files, no schema changes. Bypass `.scratch/<id>/` ceremony and execute direct Red-Green-Refactor TDD with a single atomic Conventional Commit.
* **Cortado (`M`)**: 3–6 files, localized contract changes. Run compact `.scratch/<id>/` spec & slice planning with Light Council review (`@code-inspection`).
* **Carafe (`L/XL`)**: Multi-component architecture or $>6$ files. Execute the full pipeline from Blind Cupping (`01_QUESTIONS.md` -> `02_EXTRACTION.md`) through Spec PR promotion (`skills/promote`) and parallel Group Head execution.

## 2. Core Engineering Discipline (No Spec, No Code)
* **Blind Cupping Barrier**: Stage 2 (`skills/research`) reads *only* `.scratch/<id>/01_QUESTIONS.md` and ignores `.scratch/` specs and `Status: Proposed` ADRs.
* **Zero Brittle File Paths in Specs**: `.scratch/<id>/04_SPEC.md` (`skills/to-spec`) defines durable module boundaries, physical schemas in `contracts/`, and `SEAM-01..N` test seams — never hardcoded source file paths.
* **Tracer-Bullet Vertical Slices**: `.scratch/<id>/05_PLAN.md` (`skills/to-tickets`) decomposes work into vertical slices tagged `[AFK]` or `[HITL]` with `*Depends On:*` and `Covers: AC1, AC2` references.
* **OKF Frontmatter Stamping**: Stamp all `.scratch/<id>/` artifacts deterministically via `python3 scripts/okf.py stamp`.
* **Stage 6 Review & Promotion**: Validate plans with `scripts/plan_lint.py` and `skills/plan-council` (`.scratch/<id>/06_COUNCIL.md`), resolve PR review threads via `skills/resolve-reviews`, and promote slices via `skills/promote` (`--clean-scratch`) before squash-merging the Spec PR.
* **Isolated Group Head TDD**: Each `@code-implementation` Group Head works inside `.worktrees/task-<id>-<slug>/` off **The Pass** (`--epic-branch epic/<id>-<slug>`) with `BEAN_WORKER_SLOT` isolation and produces **one atomic Conventional Commit per ticket**.
* **Velocity Chess Clock**: Log active compute seconds versus human wait durations via `skills/cycle-telemetry/scripts/measure_cycle_time.py` into `07_VERIFICATION.md`.
* **Reaper Anti-Bypass & Spec-Axis Guardrail**: Before Stage 9 PR delivery, `@execution-verifier` must confirm exit code `0`, zero test bypasses (`.skip`, `xit`), 100% `AC1..ACN` to passing test function mapping in the diff, and flip shipped ADRs from `Status: Proposed` to `Status: Accepted`.
* **Walkthrough Asset Paths**: Store walkthrough recordings/screenshots in the plan directory and reference them in `06_WALKTHROUGH.md` using repository-root-relative paths without a leading slash.
