---
name: research
description: Stage 2 Blind Cupping factual codebase extraction. Reads only .scratch/<id>/01_QUESTIONS.md, dispatches parallel read-only subagents via invoke_subagent, writes .scratch/<id>/02_EXTRACTION.md, and stamps OKF metadata.
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

# ☕ Skill: Stage 2 Blind Cupping (`research`)

You are executing Stage 2 **Blind Cupping** (`research`). Your sole mission is to document the codebase **as it exists today** with surgical `file:line` precision, completely isolated from feature design bias.

---

## 🛡️ Horthy's Blind Research Rule (Strict Information Barrier)

1. **Read ONLY `.scratch/<id>/01_QUESTIONS.md`**:
   - Ingest solely the neutral architectural questions emitted in `.scratch/<id>/01_QUESTIONS.md`.
   - **NEVER** pass raw user feature prompts, solution hypotheses, or proposed designs to research subagents.
2. **Ignore Unshipped Specs & Proposed ADRs**:
   - Ignore all draft specifications or plans in `.scratch/` and ignore any `docs/adr/*.md` files with `Status: Proposed`.
   - Only inspect live production code, tests, and `docs/adr/*.md` files with `Status: Accepted`.
3. **Documentarians, Not Critics**:
   - Do **NOT** suggest improvements, critiques, root-cause analyses, or architectural changes.
   - Describe **only** what exists, where it lives (`path/to/file.py:123`), how data flows, and what patterns are currently implemented.

---

## ⚡ Operational Protocol

### Step 1: Ingest Neutral Research Questions
Read `.scratch/<id>/01_QUESTIONS.md` using `read_file` to extract the decomposed investigation topics.

### Step 2: Fan Out Read-Only Subagents (`invoke_subagent`)
Spawn parallel read-only subagents via `invoke_subagent` to investigate distinct questions concurrently:
- **`research`**: Built-in read-only research subagent for broad codebase exploration.
- **`@context-mapping`**: Fast scout (`model: flash`) to locate files, directories, entry points, and test suites.
- **`@codebase-analysis`**: Deep execution-path tracer to document control flow, state transitions, and function signatures with `file:line` references.
- **`@pattern-recognition`**: Pattern cataloger to extract concrete usage idioms and testing conventions from the live repository.

### Step 3: Synthesize `.scratch/<id>/02_EXTRACTION.md`
Wait for all subagents to complete and synthesize their factual findings into `.scratch/<id>/02_EXTRACTION.md`:

```markdown
# 02 Blind Cupping Extraction: <Topic>

## 1. Research Questions Answered
Summary mapping each question from `01_QUESTIONS.md` to verified codebase facts.

## 2. Component & File Map
- `path/to/module.py:10-45` — Factual description of module responsibilities.

## 3. Data Flow & Execution Paths
Step-by-step trace of live function invocations, state mutations, and error handling.

## 4. Established Codebase Patterns & Test Seams
Existing structural conventions, dependency injection points, and test harness patterns.

## 5. Accepted Historical Context (`docs/adr/`)
References to `Status: Accepted` ADRs governing the inspected subsystems.
```

### Step 4: Stamp OKF Metadata
Run `scripts/okf.py stamp` via `run_command` to attach deterministic OKF frontmatter:
```bash
python3 scripts/okf.py stamp --file ".scratch/<id>/02_EXTRACTION.md" --doc-type "extraction" --status "Complete"
```
