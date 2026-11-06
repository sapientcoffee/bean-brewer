---
id: 06_WALKTHROUGH
type: walkthrough
name: Antigravity Sovereign SDLC Walkthrough
description: Antigravity Sovereign SDLC Walkthrough (8_verify)
status: stable
stage: 8_verify
generated:
  by: bean-brewer/record
  at: '2026-11-06T16:21:25Z'
sources:
- id: 07_VERIFICATION
  resource: 07_VERIFICATION.md
  last_modified: '2026-11-06T16:21:25Z'
  sha256: 13b03acccf59fec241ff445ca629f639b52e0864c3c7e2360450d727bf1dc8f3
- id: 08_RETRO
  resource: 08_RETRO.md
  last_modified: '2026-11-06T16:20:11Z'
  sha256: f2f0934e5e11a4933c78d873f1e639447e8d0e8969151b2f813b910f1a58d6eb
stages_completed:
  0_triage: carafe/brownfield
  7_tdd: 4-parallel-group-heads
  8_verify: bean-brewer/record (2026-11-06T16:21:25Z)
---

# ☕ Feature Walkthrough: Antigravity Sovereign SDLC (`06_WALKTHROUGH`)

## 1. What Was Built & Why

We modernized the Specialty Coffee Swarm into five modular, collision-free Antigravity plugins (**`bean-core`**, **`bean-roaster`**, **`bean-grinder`**, **`bean-brewer`**, and **`bean-descale`**) implementing Dex Horthy's **QRSPI** alignment gates, Matt Pocock's **Spec PR Promotion Gate** and vertical tracer-bullet slicing, and **Google Open Knowledge Format (OKF v0.2)** with deterministic `stages_completed` provenance pairs.

### Key Architectural Highlights
1. **Stateless Expo Orchestrator (`bean-core/agents/expo.md`):**
   - Operates as the Head Barista at the pass (`mainAgent: true`), delegating exploration, implementation, and verification via `invoke_subagent` while never reading or editing application `src/` directly.
   - Rehydrates across phase-bounded conversations via `SessionStart` (`rehydrate.py`) and enforces destructive git blocks via `PreToolUse` (`git_guardrails.py`).
2. **OKF v0.2 + Stage-Provenance Engine (`scripts/okf.py`, `validate_okf.py`, `okf_stamp.py`):**
   - Fixed the upstream `rel_root == Path(".")` bug so root-level bundle files (`01_QUESTIONS.md`..`06_COUNCIL.md`) are validated.
   - Deterministically stamps `id` (matching filename stem), `type`, `status`, `generated: {by, at}`, `verified`, `sources` (with real SHA-256 and mtime), and `stages_completed` audit pairs, while appending chronological entries to `log.md`.
3. **Blind Cupping & Recipe Card (`research`, `to-spec`, `to-tickets`, `plan_lint.py`):**
   - `research` strips legacy harness artifacts and passes *only* `.scratch/<id>/01_QUESTIONS.md` to read-only scouts.
   - `plan_lint.py` enforces Pocock's `/to-spec` rule against brittle source file paths in `04_SPEC.md` and detects upstream SHA-256 staleness across OKF `sources`.
4. **Spec PR Promotion & GraphQL Review Resolver (`promote.py` & `gh_resolve_reviews.py`):**
   - `gh_resolve_reviews.py` filters `reviewThreads` by collaborator trust association, formats the **Four-Verdict Table** (`fix | reject | defer | ask`), and emits `resolveReviewThread` GraphQL mutations.
   - `promote.py` supports both `--offline` (`.scratch/<id>/tickets/`) and `--github` (expanding `Covers: AC1` into verbatim AC text from `03_PRD.md`, embedding `<!-- bean-slice-id -->` markers for rename-safe idempotency, enforcing a 60,000-char body guard, and running `git rm -rf .scratch/<id>` prior to single-approval squash-merge).
5. **Parallel Group Heads, The Pass & Backflush Retro (`worktree_manager.py` & `retro.py`):**
   - `worktree_manager.py` adds `--epic-branch` (`epic/<id>-<slug>`) and deterministic `BEAN_WORKER_SLOT` (`1..3`) port/DB offset isolation.
   - `retro.py` mines `transcript.jsonl` to produce empirical session telemetry in `08_RETRO.md`.

---

## 2. How to Verify Locally

```bash
# 1. Run the full bean-brewer + bean-core unit test suite (42 tests)
python3 -m unittest discover -s /home/robedwards/workspace/bean-brewer/tests -v

# 2. Validate this durable OKF delivery bundle (including --require-stages)
python3 /home/robedwards/workspace/bean-brewer/scripts/okf.py validate \
  /home/robedwards/workspace/bean-brewer/plans/100-sovereign-sdlc --require-stages
```
