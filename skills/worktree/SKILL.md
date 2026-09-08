---
name: worktree
description: Manage Git Worktrees and Isolate Branches for parallel agent execution.
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

# Brew Worktree Skill

This skill orchestrates Git Worktrees and Isolate Branches to provide robust, concurrent workspace isolation for parallel developer agents within the barista swarm.

## 1. Objective
To prevent file collision and state leakage during parallel agent runs by creating dedicated git worktrees for separate tasks, then cleanly merging and pruning them upon completion or cleaning them up during startup reconciliation.

## 2. Workflow Steps

1. **Parse Input Parameters**:
   - Verify that `--action` is provided (`create`, `merge`, or `clean`).
   - For `create` or `merge` actions, verify that `--task <id>` is provided.
   - For `create` action, verify that `--slug <slug>` is provided.

2. **Execute Lifecycle Action**:
   - **`create` Action**:
     - Check out a new isolated git branch for the specified task.
     - Add a git worktree mapping to `.worktrees/task-<id>-<slug>/` inside the workspace.
     - Prepare files and ensure `.worktrees/` is ignored (e.g. registered in workspace `.gitignore`).
   - **`merge` Action**:
     - Pull/merge the task branch's finalized commits back into the main development branch.
     - Handle clean merging, staging, and conflict resolution gracefully.
   - **`clean` Action**:
     - Prune the corresponding worktree paths from git list.
     - Remove any orphaned/completed worktree directories to preserve storage and restore clean state.

3. **Log & Report Telemetry**:
   - Record actions and status inside JSON logs in `plans/feature/<active-feature>/worktree_telemetry.log`.
   - Output exact details on branch created/merged, mounted path, and execution times.

## 3. Parameters and Flags

The worktree lifecycle manager accepts the following parameters:
*   `--action <create|merge|clean>` (Required): The worktree lifecycle phase to trigger.
*   `--task <id>` (Required for `create` & `merge`): The identifier of the specific task or ticket.
*   `--slug <slug>` (Required for `create`): A short URL/directory-safe string description for the task branch.

## 4. Execution Examples

### Spawning a new Isolated Worktree:
```bash
agy worktree --action create --task 456 --slug implement-auth-validation
```

### Merging and Finalizing work:
```bash
agy worktree --action merge --task 456
```

### Startup Reconciliation and Cleanup:
```bash
agy worktree --action clean
```
