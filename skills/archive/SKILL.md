---
name: archive
description: Clears away the 'spent grounds' (completed plans) into ./plans/archive and updates .geminiignore.
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

# Brew Archive Skill

This skill clears away "spent grounds" (completed plans, rejection reports, and research findings) into an archive directory to keep the workspace tidy and prevent cluttering active context in subsequent runs.

## 1. Objective
To maintain a high signal-to-noise ratio in the workspace by isolating completed implementation files, research, or rejected designs from active planning directories, and to configure `.geminiignore` so that automated agents bypass the archive.

## 2. Workflow Steps

1. **Read the Master Roadmap**:
   - Access the workspace's master roadmap (typically `./plans/00_MASTER_ROADMAP.md` or equivalent) to determine which campaigns, tasks, or phases are marked as "Completed", "Done", or are otherwise fully resolved.

2. **Identify Archivable Files**:
   - Cross-reference the completed roadmap items with existing documents in `./plans/` (or its subdirectories).
   - Identify corresponding files such as:
     - Executed task files (e.g., `PHASE_X.md`, timestamped sub-folders)
     - Finished research/extraction reports (e.g., `03_EXTRACTION.md`)
     - Finished specifications (e.g., `04_SPEC.md`)
     - Finished validation/verification reports
     - Rejection reports

3. **Archive Files**:
   - Verify if the `./plans/archive` directory exists. If not, create it.
   - Move all identified completed files or directories into `./plans/archive/`.
   - **CRITICAL**: Do NOT move the Master Roadmap itself (`./plans/00_MASTER_ROADMAP.md` or equivalent), and do NOT move any plan files that are currently active or pending.

4. **Update `.geminiignore`**:
   - Read the `.geminiignore` file in the root of the project. If it does not exist, create it.
   - Check if `plans/archive/` is specified in `.geminiignore`.
   - If not present, append the line `plans/archive/` on a new line to ensure that agents ignore archived content in subsequent sweeps.

5. **Summarize**:
   - Output a brief, clean success message listing the specific files and directories that were successfully cleared away.

## 3. Parameters and Flags
This command/skill does not require any mandatory command-line arguments but operates based on files detected under `./plans` and referenced in the Master Roadmap.

## 4. Execution Example
Run the command via `agy` or as a task:
```bash
agy archive
```
