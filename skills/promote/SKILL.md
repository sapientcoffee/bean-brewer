---
name: promote
description: Stage 6B Calling the Order promotion skill. Runs scripts/promote.py in --offline or --github --clean-scratch mode to publish native GitHub Sub-Issues with verbatim ACs and <!-- bean-slice-id --> markers, removing .scratch/<id>/ prior to Spec PR squash-merge.
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

# 📣 Skill: Stage 6B Calling the Order (`promote`)

You are executing the **Calling the Order** (`promote`) skill. After the Plan Review Council (`skills/plan-council`) converges and all Spec PR review threads are resolved (`skills/resolve-reviews`), this skill promotes ephemeral `.scratch/<id>/` planning artifacts into durable repository artifacts (`docs/adr/`, `plans/<id>/`) and native GitHub Sub-Issues, then cleans `.scratch/<id>/` so zero scratch bloat ever lands on `main`.

---

## ⚡ Operational Protocol

### Mode A: Offline / Local Promotion (`--offline`)
When working in an air-gapped or local-only workspace without GitHub synchronization:
```bash
python3 scripts/promote.py --scratch-dir ".scratch/<id>" --offline
```
- Validates OKF frontmatter across `.scratch/<id>/`.
- Expands `Covers: AC1, AC2` references from `.scratch/<id>/05_PLAN.md` using verbatim AC blocks from `.scratch/<id>/03_PRD.md`.
- Promotes architecture decisions to `docs/adr/` (`Status: Proposed`) and durable execution manifests to `plans/<id>/`.

### Mode B: GitHub Native Sub-Issue Promotion & Scratch Cleanup (`--github --clean-scratch`)
Prior to final Spec PR approval and squash-merge:
```bash
python3 scripts/promote.py --scratch-dir ".scratch/<id>" --github --parent-issue <issue-number> --clean-scratch
```
1. **Idempotent Sub-Issue Provisioning**:
   - Publishes or updates native GitHub Sub-Issues linked to `--parent-issue`.
   - Injects verbatim Acceptance Criteria (`AC1..ACN`) from `03_PRD.md` into each sub-issue body so parallel **Group Heads** have self-contained requirements.
   - Embeds `<!-- bean-slice-id: SLICE-XX -->` HTML markers for deterministic idempotency across re-runs.
2. **Ephemeral Scratch Removal (`--clean-scratch`)**:
   - Removes `.scratch/<id>/` from the branch and stages the deletion (`git rm -rf .scratch/<id>`) alongside promoted `docs/adr/` and `plans/<id>/` artifacts in a single pre-merge commit.
3. **Final Spec PR Squash-Merge**:
   - Once `.scratch/<id>/` is removed and CI checks pass, the Spec PR is ready for final human approval and squash-merge.
