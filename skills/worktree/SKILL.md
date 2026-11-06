---
name: worktree
description: Manage Git Worktrees, Epic integration branches (--epic-branch epic/<id>-<slug>), and BEAN_WORKER_SLOT isolation for parallel Group Head execution.
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

# 🌿 Skill: Brew Worktree & The Pass (`worktree`)

This skill orchestrates Git Worktrees, **The Pass** (`--epic-branch epic/<id>-<slug>`), and `BEAN_WORKER_SLOT` environment isolation to provide collision-free concurrent workspaces for parallel **Group Head** (`@code-implementation`) subagents.

---

## 1. Architectural Concepts

### The Pass (`--epic-branch epic/<id>-<slug>`)
Multi-slice Carafe and Cortado builds integrate onto a dedicated epic integration branch (**The Pass**: `epic/<id>-<slug>`) rather than merging incomplete slices directly onto `main`.
- Each parallel **Group Head** branches off `epic/<id>-<slug>` into its own worktree `.worktrees/task-<id>-<slug>/`.
- When a Group Head finishes its TDD cycle and creates its single atomic Conventional Commit, the worktree branch merges cleanly back into `epic/<id>-<slug>`.

### Group Head `Workspace: inherit` & `BEAN_WORKER_SLOT` Isolation
When invoking `@code-implementation` via `invoke_subagent`:
- Set `Workspace: inherit` and instruct the Group Head to work strictly inside `.worktrees/task-<id>-<slug>/`.
- Assign a deterministic `BEAN_WORKER_SLOT` integer (`1..N`) to each concurrent Group Head so test databases, ephemeral ports (`PORT=$((3000 + BEAN_WORKER_SLOT))`), and cache directories never collide across parallel worktrees.

---

## 2. Workflow Steps

1. **Create Worktree (`--action create`)**:
   - Ensure the epic integration branch (**The Pass**: `epic/<id>-<slug>`) exists.
   - Provision an isolated git worktree at `.worktrees/task-<id>-<slug>/` branched from `--epic-branch epic/<id>-<slug>`.
   - Assign and export `BEAN_WORKER_SLOT` for the worker slot.

2. **Merge Slice to The Pass (`--action merge`)**:
   - Fast-forward or cleanly merge the verified single-ticket commit from `.worktrees/task-<id>-<slug>/` into `--epic-branch epic/<id>-<slug>`.

3. **Prune & Clean Worktrees (`--action clean`)**:
   - Prune completed worktree directories under `.worktrees/` and release `BEAN_WORKER_SLOT` allocations.

---

## 3. Parameters and Flags

* `--action <create|merge|clean>` (Required): The worktree lifecycle phase to trigger.
* `--task <id>` (Required for `create` & `merge`): The ticket/slice identifier.
* `--slug <slug>` (Required for `create`): Short directory-safe slug for the task branch.
* `--epic-branch epic/<id>-<slug>` (Optional): Target integration branch (**The Pass**) from which task worktrees branch and into which they merge.
* `--slot <1..N>` (Optional): Explicit `BEAN_WORKER_SLOT` index for port/resource isolation.

---

## 4. Execution Examples

### Spawning an Isolated Group Head Worktree off The Pass:
```bash
python3 scripts/worktree_manager.py --action create --task 456 --slug implement-auth --epic-branch epic/450-oauth --slot 1
```

### Merging a Verified Slice Back into The Pass:
```bash
python3 scripts/worktree_manager.py --action merge --task 456 --epic-branch epic/450-oauth
```

### Cleanup & Reconciliation:
```bash
python3 scripts/worktree_manager.py --action clean
```

---

## 5. Antigravity Enterprise `/teamwork` Wave Mode (Stage 7/8 Carafe Builds)

For large **Carafe** builds with tightly coupled contract seams across parallel vertical slices, `@expo` can launch an **Enterprise `/teamwork` Wave** combining worktree isolation with live peer-to-peer coordination via `send_message`:

- **Wave Roster**:
  - **3x `@code-implementation` Group Heads**: Each bound to its own isolated `.worktrees/task-<id>-<slug>/` directory (`Workspace: inherit`) and dedicated `BEAN_WORKER_SLOT` (`1..3`) branched off **The Pass** (`epic/<id>-<slug>`).
  - **`@contract-auditor`**: Monitors shared schema contracts (`contracts/`) and resolves cross-slice interface questions in real time via `send_message` without breaking worktree isolation.
  - **`@execution-verifier` (Velocity Reaper)**: Continuously verifies merged slices on **The Pass** (`epic/<id>-<slug>`), executes the Spec-Axis Check (`AC1..ACN`), and coordinates with `@walkthrough-recorder` to produce `plans/<id>/06_WALKTHROUGH.md`.
- **Strict Worktree Boundary**: Even in `/teamwork` mode, each `@code-implementation` Group Head modifies files **only** inside its assigned `.worktrees/task-<id>-<slug>/` worktree and produces one atomic Conventional Commit per ticket before merging into `epic/<id>-<slug>`.
