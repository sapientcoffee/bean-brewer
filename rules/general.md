# ☕ Bean-Brewer: Implementation & Delivery Rules

Welcome to **Bean-Brewer**, the high-pressure implementation forge for the Antigravity CLI (`agy`).

## 1. Core Engineering Discipline (No Spec, No Code)
* **Zero Improvisation:** Never write code without an approved `02_PRD.md`, `04_SPEC.md`, and `05_PLAN.md`.
* **Contract-Driven:** Establish physical schemas in `contracts/` before implementing business logic.
* **TDD Loops:** Write failing unit tests first. Implement the minimum code to pass. Refactor cleanly.
* **Stage Outputs Coexistence:** Markdown files (`03_EXTRACTION.md`, `04_SPEC.md`, `05_PLAN.md`, `07_VERIFICATION.md`, `08_WALKTHROUGH.md`) are the definitive source of truth.
* **Velocity Chess Clock:** Log active compute seconds versus human wait durations via `skills/cycle-telemetry` into `07_VERIFICATION.md`.
* **Reaper Anti-Bypass Guardrail:** Before Stage 9 PR delivery, `@execution-verifier` must adversarially confirm exit code 0, zero test bypasses (`.skip`, `xit`), and coverage truth.
* **Harness Self-Healing:** Trigger `skills/harness-immunizer` on >2 failed Stage 7 implementation retries to persist gotcha rules in `rules/gotchas/`.
* **Opportunistic Telemetry:** If `bean-cup` is installed, update the visual dashboard via `scripts/sync_dashboard_if_available.py`. If absent, proceed seamlessly.

