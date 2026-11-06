---
name: archive
description: Clears away 'spent grounds' (completed .scratch/<id>/ and plans/<id>/ bundles) into ./plans/archive and updates .geminiignore.
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

# 🧹 Skill: Brew Archive (`archive`)

This skill clears away "spent grounds" (completed `.scratch/<id>/` and `plans/<id>/` bundles, rejection reports, and extraction findings) into `./plans/archive/` to keep the workspace tidy and prevent cluttering active context in subsequent runs.

## 1. Objective
To maintain a high signal-to-noise ratio in the workspace by isolating completed `.scratch/<id>/` and `plans/<id>/` bundles from active directories, and configuring `.geminiignore` so automated agents bypass archived artifacts.

## 2. Workflow Steps

1. **Identify Completed Bundles**:
   - Inspect `./plans/` (including `plans/<id>/` bundles and `./plans/00_MASTER_ROADMAP.md` if present) and `.scratch/<id>/` to determine which features, epics, or phases are marked `Completed`, `Shipped`, or `Done`.

2. **Identify Archivable Files**:
   - Locate completed `.scratch/<id>/` and `plans/<id>/` bundles containing:
     - Research questions (`01_QUESTIONS.md`) and Blind Cupping extraction reports (`02_EXTRACTION.md`)
     - Product requirements (`03_PRD.md`) and technical specifications (`04_SPEC.md`)
     - Execution plans (`05_PLAN.md`), council reviews (`06_COUNCIL.md`), verification reports (`07_VERIFICATION.md`), and walkthroughs (`06_WALKTHROUGH.md`)

3. **Archive Bundles**:
   - Ensure `./plans/archive/` exists.
   - Move completed `plans/<id>/` bundles (and any leftover local `.scratch/<id>/` bundles that were not already removed by `promote --clean-scratch`) into `./plans/archive/<id>/`.
   - **CRITICAL**: Do NOT move `./plans/00_MASTER_ROADMAP.md` or any active/in-progress plan bundles.

4. **Update `.geminiignore`**:
   - Read `.geminiignore` in the repository root (create it if absent).
   - Ensure `plans/archive/` and `.scratch/` are listed so search and context indexing ignore spent grounds.

5. **Summarize**:
   - Output a concise summary of archived `.scratch/<id>/` and `plans/<id>/` directories.
