# ☕ Bean-Brewer: Implementation & Delivery Rules

Welcome to **Bean-Brewer**, the high-pressure implementation forge for the Antigravity CLI (`agy`).

## 1. Core Engineering Discipline (No Spec, No Code)
* **Zero Improvisation:** Never write code without an approved `02_PRD.md`, `04_SPEC.md`, and `05_PLAN.md`.
* **Contract-Driven:** Establish physical schemas in `contracts/` before implementing business logic.
* **TDD Loops:** Write failing unit tests first. Implement the minimum code to pass. Refactor cleanly.
* **Stage Outputs Coexistence:** Markdown files (`03_EXTRACTION.md`, `04_SPEC.md`, `05_PLAN.md`, `07_VERIFICATION.md`, `08_WALKTHROUGH.md`) are the definitive source of truth.
* **Opportunistic Telemetry:** If `bean-cup` is installed, update the visual dashboard via `scripts/sync_dashboard_if_available.py`. If absent, proceed seamlessly.
