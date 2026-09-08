---
name: sync
description: Parse 05_PLAN.md and synchronize tasks to GitHub issues
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

# Brew Sync Skill

This skill parses the active execution plan (`05_PLAN.md`), extracts implementation steps and checklists, and synchronizes them with GitHub Issues using the GitHub CLI (`gh`).

## 1. Objective
To automate the traceability of technical decisions and ensure that every item on the execution plan's checklist is mapped to an actionable, tracked issue on GitHub. This integrates Phase 5 (Execution Planning) with Stage 6/7 tracking.

## 2. Workflow Steps

1. **Locate Plan and Epic Context**:
   - Determine the plan file path. If not provided, search for the first `05_PLAN.md` under `plans/feature/*`.
   - Identify the parent Epic Issue ID. If not explicitly provided, look up `02_PRD.md` or parse active git branches and logs.

2. **Parse Implementation Plan**:
   - Run the python-based markdown parser to parse checkbox states, headers, dependencies, and verification criteria for each task inside the `05_PLAN.md`.

3. **Check Idempotency & Sorting**:
   - Perform a topological sort of extracted tasks based on declared dependencies (`*Depends On:*` metadata).
   - Query existing issues in the GitHub repository using `gh issue list` to prevent creating duplicate issues for already provisioned tasks.

4. **Provision Issues on GitHub**:
   - For any missing tasks, call `gh issue create` to initialize new tracked issues, attaching appropriate metadata, labels, and descriptions.
   - Link each new issue back to the parent Epic Issue.

5. **Post hand-shake Coordination Comment**:
   - Post a final coordination status comment to the parent Epic Issue notifying developers and peer agents that tasks are synchronized and ready for human review.

## 3. Parameters and Flags

The underlying synchronization engine (`scripts/sync.py`) accepts the following flags:
*   `--plan <path>`: Optional path to the target plan markdown file.
*   `--epic <id>`: Optional target GitHub Epic Issue number.
*   `--dry-run`: Dry-run mode to parse and print sequenced tasks without writing changes to GitHub.

## 4. Execution Example

### Standalone Dry Run:
```bash
python3 scripts/sync.py --plan plans/feature/20260618-sync-automation/05_PLAN.md --dry-run
```

### Full Synchronization:
```bash
agy sync --plan plans/feature/20260618-sync-automation/05_PLAN.md --epic 123
```
