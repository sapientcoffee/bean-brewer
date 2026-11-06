---
name: cycle-telemetry
description: Velocity Chess Clock telemetry tracker. Deterministically measures active agent compute time versus human waiting time and syncs metrics into 07_VERIFICATION.md.
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

# ⏱️ Skill: Cycle Telemetry (Velocity Chess Clock)

You are executing the **Cycle Telemetry** skill. This skill tracks development velocity by recording active agent compute time versus human waiting time (the "Velocity Chess Clock") deterministically without LLM token consumption.

## Objectives
- Deterministically log transitions between autonomous agent computation and human review.
- Persist structured timestamps and latency deltas in `<plan-dir>/cycle_telemetry.json`.
- Automatically render an up-to-date execution summary block in `07_VERIFICATION.md`.

## Integration Points
1. **Stage 6A (Plan Council Review):**
   - When the council review loop starts:
     ```bash
     python3 scripts/measure_cycle_time.py log --event council_exec_start --plan-dir "plans/<feature>/<timestamp>"
     ```
   - When council arbitration concludes:
     ```bash
     python3 scripts/measure_cycle_time.py log --event council_exec_end --plan-dir "plans/<feature>/<timestamp>"
     ```
2. **Stage 6B (Human Review Gate):**
   - When presenting the plan to the human:
     ```bash
     python3 scripts/measure_cycle_time.py log --event human_wait_start --plan-dir "plans/<feature>/<timestamp>"
     ```
   - When the human approves and execution resumes:
     ```bash
     python3 scripts/measure_cycle_time.py log --event human_wait_end --plan-dir "plans/<feature>/<timestamp>"
     ```
3. **Stage 7 (Implementation & Verification Loop):**
   - When subagents or tools start implementation:
     ```bash
     python3 scripts/measure_cycle_time.py log --event agent_exec_start --plan-dir "plans/<feature>/<timestamp>"
     ```
   - When implementation and local verifications complete:
     ```bash
     python3 scripts/measure_cycle_time.py log --event agent_exec_end --plan-dir "plans/<feature>/<timestamp>"
     ```
3. **Stage 8 / 9 (Walkthrough & PR Delivery):**
   - Generate final summary report:
     ```bash
     python3 scripts/measure_cycle_time.py report --plan-dir "plans/<feature>/<timestamp>"
     ```

## Output Format in `07_VERIFICATION.md`
```markdown
## ⏱️ Cycle Telemetry (Velocity Chess Clock)

| Metric | Value |
| :--- | :--- |
| **Active Agent Compute** | `142.30s` |
| **Human Wait Duration** | `65.10s` |
| **Total Cycle Latency** | `207.40s` |
| **Compute / Total Ratio** | `68.6%` |
```
