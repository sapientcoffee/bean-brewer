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
plan_lint.py: Zero-token deterministic pre-linter for 05_PLAN.md.
Validates TDD harness pairing, dependency DAG acyclicity, PRD traceability,
and physical contract references before invoking LLM council reviewers.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict, deque


class Task:
    def __init__(self, label, name, is_done=False, line_num=0):
        self.label = label.upper().strip()
        self.name = name.strip()
        self.is_done = is_done
        self.line_num = line_num
        self.target_file = ""
        self.verification = ""
        self.depends_on = []
        self.instructions = ""

    def to_dict(self):
        return {
            "label": self.label,
            "name": self.name,
            "is_done": self.is_done,
            "line_num": self.line_num,
            "target_file": self.target_file,
            "verification": self.verification,
            "depends_on": self.depends_on,
        }


def clean_markdown_inline(text):
    text = text.strip()
    for wrapper in ('***', '**', '*', '`'):
        if text.startswith(wrapper) and text.endswith(wrapper):
            return text[len(wrapper):-len(wrapper)].strip()
    return text


def parse_plan(plan_path):
    if not os.path.exists(plan_path):
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    with open(plan_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    tasks_by_label = {}
    tasks_order = []

    checklist_pattern = re.compile(
        r'^\s*[\-\*]\s+\[([ xX])\]\s*(?:\*\*)?\s*((?:Step|Task)\s+[\w\.\-]+)(?:\s+\[[^\]]+\])?(?:\*\*)?[:\-]\s*(?:\*\*)?\s*(.*)$',
        re.IGNORECASE
    )

    step_header_pattern = re.compile(
        r'^#{2,4}\s*(?:\*\*)?\s*((?:Step|Task)\s+[\w\.\-]+)(?:\*\*)?\s*(.*)$',
        re.IGNORECASE
    )

    # First Pass: discover tasks and collect inline checklist details
    current_inline_task = None
    inline_details = []

    for idx, line in enumerate(lines, 1):
        match = checklist_pattern.match(line)
        if match:
            if current_inline_task and inline_details:
                _parse_task_details(current_inline_task, inline_details)
                inline_details = []
            is_done = match.group(1).lower() == 'x'
            step_label = match.group(2).strip().upper()
            step_name = match.group(3).strip().rstrip("*").strip()
            task = Task(step_label, step_name, is_done, line_num=idx)
            tasks_by_label[step_label] = task
            tasks_order.append(step_label)
            current_inline_task = task
            continue

        if current_inline_task:
            if line.startswith('#'):
                _parse_task_details(current_inline_task, inline_details)
                current_inline_task = None
                inline_details = []
            else:
                inline_details.append(line)

    if current_inline_task and inline_details:
        _parse_task_details(current_inline_task, inline_details)

    # Second Pass: collect details under headers (if present)
    current_header_task = None
    detail_lines = []

    for line in lines:
        header_match = step_header_pattern.match(line)
        if header_match:
            if current_header_task and detail_lines:
                _parse_task_details(current_header_task, detail_lines)
            step_label = header_match.group(1).strip().upper()
            current_header_task = tasks_by_label.get(step_label)
            detail_lines = []
            continue

        if current_header_task:
            if line.startswith('# ') or line.startswith('## '):
                _parse_task_details(current_header_task, detail_lines)
                current_header_task = None
                detail_lines = []
            else:
                detail_lines.append(line)

    if current_header_task and detail_lines:
        _parse_task_details(current_header_task, detail_lines)

    return [tasks_by_label[lbl] for lbl in tasks_order if lbl in tasks_by_label], lines


def _parse_task_details(task, lines):
    target_pattern = re.compile(r'^\s*[*\-\s]*target file[*:\s]+\s*(.+)$', re.IGNORECASE)
    verify_pattern = re.compile(r'^\s*[*\-\s]*verification[*:\s]+\s*(.+)$', re.IGNORECASE)
    depends_pattern = re.compile(r'^\s*[*\-\s]*depends on[*:\s]+\s*(.+)$', re.IGNORECASE)

    instructions = []
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        t_match = target_pattern.match(clean)
        v_match = verify_pattern.match(clean)
        d_match = depends_pattern.match(clean)

        if t_match:
            task.target_file = clean_markdown_inline(t_match.group(1))
        elif v_match:
            task.verification = clean_markdown_inline(v_match.group(1))
        elif d_match:
            deps = d_match.group(1).split(",")
            task.depends_on = [clean_markdown_inline(d).upper() for d in deps if d.strip()]
        else:
            instructions.append(line)

    task.instructions = "\n".join(instructions)


def check_tdd_pairing(tasks):
    errors = []
    warnings = []
    for task in tasks:
        # Check if task is an implementation task (targets a non-test file or implementation name)
        is_test_task = any(kw in task.name.lower() or kw in task.target_file.lower() 
                           for kw in ["test", "harness", "spec", "fixture", "mock"])
        is_doc_task = any(kw in task.name.lower() or kw in task.target_file.lower() 
                          for kw in [".md", "doc", "readme", "diagram"])

        if not is_test_task and not is_doc_task:
            has_verification = bool(task.verification and len(task.verification.strip()) > 3)
            if not has_verification:
                errors.append({
                    "task": task.label,
                    "line": task.line_num,
                    "code": "TDD_MISSING_VERIFICATION",
                    "message": f"{task.label} ('{task.name}') has no declared *Verification:* criteria or test command."
                })
    return errors, warnings


def check_dependencies(tasks):
    errors = []
    warnings = []
    task_map = {t.label: t for t in tasks}
    adj = defaultdict(list)
    in_degree = defaultdict(int)

    for t in tasks:
        in_degree[t.label] = 0

    for t in tasks:
        for dep in t.depends_on:
            if dep not in task_map:
                errors.append({
                    "task": t.label,
                    "line": t.line_num,
                    "code": "MISSING_DEPENDENCY",
                    "message": f"{t.label} declares dependency on non-existent task '{dep}'."
                })
            else:
                adj[dep].append(t.label)
                in_degree[t.label] += 1

    # Kahn's algorithm for cycle detection
    queue = deque([lbl for lbl, deg in in_degree.items() if deg == 0])
    visited_count = 0

    while queue:
        curr = queue.popleft()
        visited_count += 1
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(tasks):
        unresolved = [lbl for lbl, deg in in_degree.items() if deg > 0]
        errors.append({
            "task": "PLAN_DAG",
            "line": 1,
            "code": "CIRCULAR_DEPENDENCY",
            "message": f"Circular dependency detected in execution plan involving: {', '.join(unresolved)}"
        })

    return errors, warnings


def check_prd_traceability(tasks, prd_path, plan_content):
    errors = []
    warnings = []
    if not prd_path or not os.path.exists(prd_path):
        return errors, warnings

    with open(prd_path, "r", encoding="utf-8") as f:
        prd_content = f.read()

    # Extract user story or requirement IDs like US-1, REQ-1, Story 1, Epic 1
    story_pattern = re.compile(r'\b(US-\d+|REQ-\d+|Story\s+\d+|User\s+Story\s+\d+)\b', re.IGNORECASE)
    prd_stories = set(story_pattern.findall(prd_content))

    if prd_stories:
        unmapped_stories = []
        for story in prd_stories:
            if not re.search(re.escape(story), plan_content, re.IGNORECASE):
                unmapped_stories.append(story)
        if unmapped_stories:
            warnings.append({
                "task": "PRD_TRACEABILITY",
                "line": 1,
                "code": "UNMAPPED_PRD_REQUIREMENT",
                "message": f"PRD user stories/requirements not explicitly referenced in 05_PLAN.md: {', '.join(unmapped_stories)}"
            })

    return errors, warnings


def check_contract_integrity(tasks, contracts_dir, plan_content):
    errors = []
    warnings = []
    if not contracts_dir or not os.path.exists(contracts_dir):
        return errors, warnings

    contract_files = []
    for root, _, files in os.walk(contracts_dir):
        for file in files:
            if not file.startswith("."):
                contract_files.append(file)

    for c_file in contract_files:
        if c_file not in plan_content:
            warnings.append({
                "task": "CONTRACT_INTEGRITY",
                "line": 1,
                "code": "UNREFERENCED_CONTRACT_FILE",
                "message": f"Contract file '{c_file}' in contracts/ is not referenced by any task in 05_PLAN.md."
            })

    return errors, warnings


def evaluate_risk_tier(tasks, contracts_dir, full_text):
    """
    Evaluates whether the plan requires a Light, Standard, or Full council review.
    - Light: <= 3 tasks, no contract files
    - Standard: <= 10 tasks or new contracts
    - Full: Auth/security boundary, database migrations, or > 10 tasks
    """
    num_tasks = len(tasks)
    has_contracts = bool(contracts_dir and os.path.exists(contracts_dir) and os.listdir(contracts_dir))
    
    high_risk_keywords = [
        "auth", "authentication", "authorization", "rbac", "migration", 
        "security", "iam", "crypto", "encryption", "jwt", "session"
    ]
    has_high_risk_keywords = any(
        re.search(r'\b' + re.escape(kw) + r'\b', full_text, re.IGNORECASE)
        for kw in high_risk_keywords
    )

    if num_tasks > 10 or has_high_risk_keywords:
        return "Full", "Plan has >10 tasks or affects auth, migrations, or security boundaries."
    elif num_tasks > 3 or has_contracts:
        return "Standard", "Plan has 4-10 tasks or defines physical schema contracts."
    else:
        return "Light", "Plan is small (<= 3 tasks) with zero contract changes."


def lint_plan(plan_path, prd_path=None, contracts_dir=None):
    tasks, lines = parse_plan(plan_path)
    plan_content = "".join(lines)

    all_errors = []
    all_warnings = []

    if not tasks:
        all_errors.append({
            "task": "PLAN_EMPTY",
            "line": 1,
            "code": "NO_TASKS_FOUND",
            "message": "No actionable checklist items found matching format '- [ ] Step X: ...'"
        })
        return {
            "valid": False,
            "task_count": 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "recommended_tier": "Light",
            "tier_reason": "No tasks present."
        }

    # Run check passes
    tdd_errs, tdd_warns = check_tdd_pairing(tasks)
    dep_errs, dep_warns = check_dependencies(tasks)
    prd_errs, prd_warns = check_prd_traceability(tasks, prd_path, plan_content)
    cnt_errs, cnt_warns = check_contract_integrity(tasks, contracts_dir, plan_content)

    all_errors.extend(tdd_errs + dep_errs + prd_errs + cnt_errs)
    all_warnings.extend(tdd_warns + dep_warns + prd_warns + cnt_warns)

    tier, tier_reason = evaluate_risk_tier(tasks, contracts_dir, plan_content)

    return {
        "valid": len(all_errors) == 0,
        "task_count": len(tasks),
        "errors": all_errors,
        "warnings": all_warnings,
        "recommended_tier": tier,
        "tier_reason": tier_reason,
        "tasks": [t.to_dict() for t in tasks]
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic pre-linter for 05_PLAN.md")
    parser.add_argument("--plan", required=True, help="Path to 05_PLAN.md")
    parser.add_argument("--prd", help="Path to 02_PRD.md")
    parser.add_argument("--contracts", help="Path to contracts/ directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    plan_path = os.path.abspath(args.plan)
    plan_dir = os.path.dirname(plan_path)

    prd_path = args.prd
    if not prd_path:
        candidate_prd = os.path.join(plan_dir, "02_PRD.md")
        if os.path.exists(candidate_prd):
            prd_path = candidate_prd

    contracts_dir = args.contracts
    if not contracts_dir:
        candidate_contracts = os.path.join(plan_dir, "contracts")
        if os.path.exists(candidate_contracts):
            contracts_dir = candidate_contracts

    try:
        report = lint_plan(plan_path, prd_path, contracts_dir)
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to lint plan: {e}\n")
        sys.exit(2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print("🔍 05_PLAN.md Deterministic Pre-Linter")
        print("=" * 60)
        print(f"Plan File:       {plan_path}")
        print(f"Total Tasks:     {report['task_count']}")
        print(f"Council Tier:    {report['recommended_tier']} ({report['tier_reason']})")
        print("-" * 60)

        if report['errors']:
            print(f"❌ Found {len(report['errors'])} Error(s):")
            for err in report['errors']:
                print(f"  • [Line {err['line']}] [{err['code']}] {err['message']}")
            print()

        if report['warnings']:
            print(f"⚠️  Found {len(report['warnings'])} Warning(s):")
            for warn in report['warnings']:
                print(f"  • [Line {warn['line']}] [{warn['code']}] {warn['message']}")
            print()

        if report['valid']:
            print("✅ Plan passed all deterministic structural and TDD checks.")
            print(f"👉 Ready to dispatch Stage 6A Council ({report['recommended_tier']} Tier).")
        else:
            print("🛑 Plan linting failed. Please fix structural errors before council dispatch.")

    sys.exit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
