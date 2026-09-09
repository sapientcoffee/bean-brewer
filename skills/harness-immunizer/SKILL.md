---
name: harness-immunizer
description: Velocity Harness Patch self-healing mechanism. Extracts failure root causes upon repeated Stage 7 retries (>2) and permanently writes architectural gotcha rules into rules/gotchas/.
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

# 🛡️ Skill: Harness Immunizer (Velocity Harness Patch)

You are executing the **Harness Immunizer** skill. This skill forms the swarm's self-healing immune system. When an implementation failure loop repeats (>2 failed retries between code generation and verification), this skill isolates the underlying root cause and generates a permanent architectural constraint in `rules/gotchas/<slug>.md`.

## When to Trigger
- Any Stage 7 task where code implementation and verification fail more than twice in succession.
- Recurring systemic errors (e.g., async database teardown hangs, mock leakages, missing environment variable fallbacks).

## CLI Usage
Execute the script to record a new gotcha rule:
```bash
python3 scripts/immunize_harness.py \
  --issue-title "Async DB Cleanup" \
  --root-cause "Database connection pools remained open across test boundaries, hanging async event loop teardown." \
  --remediation "Always implement explicit async teardown fixtures with pool termination and timeout guards." \
  --rule-slug "async-db-cleanup"
```

## Systemic Effect
Subsequent runs by any agent across the repository will ingest `rules/gotchas/` during context initialization, preventing recurrent architectural failure loops.
