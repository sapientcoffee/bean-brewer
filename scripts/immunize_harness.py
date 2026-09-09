#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Harness Immunizer Tool (Velocity Harness Patch).
Extracts root causes from repeated Stage 7 implementation/test failures (>2 retries)
and generates permanent architectural gotcha rules under rules/gotchas/<slug>.md.
"""

import argparse
import datetime
import os
import re
import sys


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)


def generate_rule_content(title: str, slug: str, root_cause: str, remediation: str) -> str:
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"""<!--
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

# 🛡️ Architectural Gotcha: {title}

**Rule Identifier:** `{slug}`  
**Captured Date:** `{now_iso}`  
**Origin:** Stage 7 Execution Loop Self-Healing Trigger (>2 Retries)

---

## 💥 Problem & Root Cause
{root_cause.strip()}

---

## 🔒 Architectural Constraint & Remediation
{remediation.strip()}

---

## 📋 Directives for Agents & Engineers
1. **Pre-Implementation Check:** Before implementing or modifying related modules, review this gotcha.
2. **Mandatory Test Guardrail:** Include a regression test verifying this specific failure mode cannot occur.
3. **Zero Improvisation:** Never bypass this rule without an approved ADR update.
"""


def main():
    parser = argparse.ArgumentParser(description="Harness Immunizer: Velocity Harness Patch")
    parser.add_argument("--issue-title", required=True, help="Human-readable title of the gotcha/bug")
    parser.add_argument("--root-cause", required=True, help="Detailed explanation of the failure root cause")
    parser.add_argument("--remediation", default="Enforce proper lifecycle management, resource cleanup, and verification assertions.", help="Mandatory architectural constraint or fix pattern")
    parser.add_argument("--rule-slug", default=None, help="Optional slug for filename (derived from title if omitted)")
    parser.add_argument("--repo-root", default=".", help="Root directory of the repository")

    args = parser.parse_args()

    slug = args.rule_slug or slugify(args.issue_title)
    if not slug.endswith(".md"):
        filename = f"{slug}.md"
    else:
        filename = slug
        slug = slug[:-3]

    repo_root = os.path.abspath(args.repo_root)
    gotchas_dir = os.path.join(repo_root, "rules", "gotchas")
    os.makedirs(gotchas_dir, exist_ok=True)

    target_path = os.path.join(gotchas_dir, filename)
    content = generate_rule_content(args.issue_title, slug, args.root_cause, args.remediation)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[harness-immunizer] ✅ Successfully created harness immunity rule: {target_path}")


if __name__ == "__main__":
    main()
