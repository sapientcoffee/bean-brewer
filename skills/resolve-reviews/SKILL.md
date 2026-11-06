---
name: resolve-reviews
description: Stage 6B Spec PR Review Resolver. Runs scripts/gh_resolve_reviews.py to fetch unresolved GraphQL reviewThreads, presents the Four-Verdict Table (fix | reject | defer | ask) via ask_question, applies approved fixes in one delta commit, and resolves threads.
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

# 🔍 Skill: Stage 6B Spec PR Review Resolver (`resolve-reviews`)

You are executing the **Spec PR Review Resolver** (`resolve-reviews`) skill. During Stage 6B (Spec PR human & automated review), this skill fetches all unresolved GitHub Pull Request review threads via GraphQL, categorizes them using the **Four-Verdict Table**, confirms actions with the human via `ask_question`, applies all `fix` items in a single delta commit, and resolves threads via GraphQL.

---

## ⚡ Operational Protocol

### Step 1: Fetch Unresolved Review Threads
Execute the GraphQL review fetcher to retrieve all unresolved `reviewThreads` for the active Spec PR:
```bash
python3 scripts/gh_resolve_reviews.py fetch --pr <pr-number>
```

### Step 2: Triage into the Four-Verdict Table (`fix | reject | defer | ask`)
Evaluate each unresolved thread against `.scratch/<id>/03_PRD.md`, `.scratch/<id>/04_SPEC.md`, and `.scratch/<id>/05_PLAN.md`, assigning one of four recommended verdicts:
- **`fix`**: Valid defect, missing edge case, or contract mismatch. Will be patched in the current delta commit.
- **`reject`**: Contradicts approved PRD scope, violates architectural invariants, or is factually incorrect. Will reply with technical rationale and resolve.
- **`defer`**: Out-of-scope enhancement suitable for a follow-up ticket/issue. Will log follow-up reference and resolve.
- **`ask`**: Ambiguous product trade-off requiring explicit human judgment before action.

Present the **Four-Verdict Table** (`Thread ID | File:Line | Reviewer Comment | Recommended Verdict (fix | reject | defer | ask) | Proposed Action`) and confirm decisions with the user via the `ask_question` tool.

### Step 3: Apply Approved `fix` Changes in One Delta Commit
1. Edit the target files in `.scratch/<id>/` or `contracts/` for all confirmed `fix` threads.
2. Re-stamp modified OKF documents via `python3 scripts/okf.py stamp` and re-verify `python3 scripts/plan_lint.py`.
3. Stage and create **one atomic delta commit** covering the review fixes:
   ```bash
   git commit -m "docs(spec): address PR #<pr-number> review feedback"
   git push
   ```

### Step 4: Reply and Resolve Review Threads via GraphQL
Run `scripts/gh_resolve_reviews.py` to post rationale replies and mark resolved threads in batch:
```bash
python3 scripts/gh_resolve_reviews.py resolve --pr <pr-number> --resolutions "<resolutions-json>"
```
