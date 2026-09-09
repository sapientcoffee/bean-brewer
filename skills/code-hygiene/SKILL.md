---
name: code-hygiene
description: Deterministic local code hygiene runner. Executes non-LLM static linters, typecheckers, and security tools (eslint, ruff, cargo check, gitleaks, mypy) emitting brief exit-code summaries.
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

# 🧹 Skill: Deterministic Code Hygiene

You are executing the **Code Hygiene** skill. This skill runs fast, deterministic, non-LLM local quality tooling to verify code formatting, type safety, and secret exposure before engaging heavier reasoning agents.

## Decoupled Stage 7 Verification Architecture
Stage 7 verification is split into two independent operations:
1. **Deterministic Code Hygiene (`code-hygiene` skill)**: Non-LLM execution of local linters and analyzers. Emits binary exit codes without wasting LLM token context.
2. **Architectural Contract Audit (`@contract-auditor` subagent)**: Isolated subagent checking generated API routes, JSON schemas, and data structures against `04_SPEC.md` and `contracts/`.

## CLI Usage
Execute the helper script from the repository root:
```bash
python3 skills/code-hygiene/scripts/run_hygiene.py [--cwd <target-dir>] [--all]
```

## Evaluated Tools
- **`ruff`**: Python linting and code formatting checks.
- **`mypy`**: Python static type validation.
- **`eslint`**: JavaScript / TypeScript linting.
- **`cargo check`**: Rust compilation and type verification.
- **`gitleaks`**: Local secret leakage scanning.

## Output Summary
Emits an exit code summary table:
```
Tool            | Status     | Exit Code  | Detail
-----------------------------------------------------------------
ruff            | PASSED     | 0          | All checks passed
gitleaks        | PASSED     | 0          | No leaks detected
-----------------------------------------------------------------
```
