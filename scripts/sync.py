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

import argparse
import json
import os
import re
import subprocess
import sys

class Task:
    def __init__(self, label, name, is_done):
        self.label = label.strip().upper()  # e.g., "STEP 1.A"
        self.name = name.strip()
        self.is_done = is_done
        self.target_file = "Not specified"
        self.verification = "Not specified"
        self.depends_on = []
        self.instructions = ""
        self.issue_number = None
        self.sync_status = "Pending"

    def to_dict(self):
        return {
            "label": self.label,
            "name": self.name,
            "is_done": self.is_done,
            "target_file": self.target_file,
            "verification": self.verification,
            "depends_on": self.depends_on,
            "instructions": self.instructions.strip(),
            "issue_number": self.issue_number,
            "sync_status": self.sync_status
        }

def clean_markdown_inline(text):
    """Removes wrapping bold, italic, or backticks from inline markdown if they wrap the entire text."""
    text = text.strip()
    for wrapper in ('***', '**', '*', '`'):
        if text.startswith(wrapper) and text.endswith(wrapper):
            return text[len(wrapper):-len(wrapper)].strip()
    return text

def parse_plan_file(plan_path):
    """Parses 05_PLAN.md into a structured list of Task objects."""
    if not os.path.exists(plan_path):
        sys.stderr.write(f"[ERROR] Plan file not found: {plan_path}\n")
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    tasks_by_label = {}
    tasks_order = []

    # First Pass: Find all checklist items
    checklist_pattern = re.compile(r'^\s*[\-\*]\s+\[([ xX])\]\s*(?:\*\*)?\s*((?:Step|Task)\s+([\w\.]+))(?:\s+\[[^\]]+\])?(?:\*\*)?[:\-]\s*(?:\*\*)?\s*(.*)$', re.IGNORECASE)
    
    for line in lines:
        match = checklist_pattern.match(line)
        if match:
            is_done = match.group(1).lower() == 'x'
            step_label = match.group(2).strip().upper()
            step_name = match.group(4).strip().rstrip("*").strip()
            
            task = Task(step_label, step_name, is_done)
            tasks_by_label[step_label] = task
            tasks_order.append(step_label)

    # Second Pass: Extract detailed instructions and metadata under #### headers
    step_header_pattern = re.compile(r'^####\s*(?:\*\*)?\s*((?:Step|Task)\s+([\w\.]+))(?:\*\*)?\s*(.*)$', re.IGNORECASE)
    
    current_task = None
    detail_lines = []

    for line in lines:
        header_match = step_header_pattern.match(line)
        if header_match:
            # Save the accumulated details for the previous task
            if current_task and detail_lines:
                parse_details(current_task, detail_lines)
            
            step_label = header_match.group(1).strip().upper()
            current_task = tasks_by_label.get(step_label)
            detail_lines = []
            continue

        if current_task:
            # Stop accumulating if we reach another major markdown heading section
            if line.startswith('## ') or line.startswith('# '):
                parse_details(current_task, detail_lines)
                current_task = None
                detail_lines = []
            else:
                detail_lines.append(line)

    # Clean up the final task
    if current_task and detail_lines:
        parse_details(current_task, detail_lines)

    return [tasks_by_label[label] for label in tasks_order if label in tasks_by_label]

def parse_details(task, lines):
    """Parses metadata lines and aggregates instruction lists."""
    target_file_pattern = re.compile(r'^\s*[*\-\s]*target file[*:\s]+\s*(.+)$', re.IGNORECASE)
    verification_pattern = re.compile(r'^\s*[*\-\s]*verification[*:\s]+\s*(.+)$', re.IGNORECASE)
    depends_on_pattern = re.compile(r'^\s*[*\-\s]*depends on[*:\s]+\s*(.+)$', re.IGNORECASE)

    instructions = []
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        target_match = target_file_pattern.match(clean_line)
        verify_match = verification_pattern.match(clean_line)
        depends_match = depends_on_pattern.match(clean_line)

        if target_match:
            task.target_file = clean_markdown_inline(target_match.group(1))
        elif verify_match:
            task.verification = clean_markdown_inline(verify_match.group(1))
        elif depends_match:
            # Parse dependency list, e.g. Step 1.A, Step 1.B
            deps = depends_match.group(1).split(",")
            task.depends_on = [clean_markdown_inline(d).upper() for d in deps if d.strip()]
        else:
            instructions.append(line)

    task.instructions = "\n".join(instructions)

def topological_sort(tasks):
    """Schedules tasks based on depends_on constraints using Kahn's algorithm."""
    tasks_by_label = {t.label: t for t in tasks}
    adj = {t.label: [] for t in tasks}
    in_degree = {t.label: 0 for t in tasks}

    for t in tasks:
        for dep in t.depends_on:
            if dep in tasks_by_label:
                adj[dep].append(t.label)
                in_degree[t.label] += 1
            else:
                sys.stderr.write(f"[WARN] Dependency '{dep}' for '{t.label}' is external to this plan.\n")

    import heapq
    queue = [label for label, degree in in_degree.items() if degree == 0]
    heapq.heapify(queue)
    sorted_labels = []

    while queue:
        curr = heapq.heappop(queue)
        sorted_labels.append(curr)

        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(queue, neighbor)

    if len(sorted_labels) != len(tasks):
        sys.stderr.write("[ERROR] Circular dependency detected in execution plan!\n")
        sys.exit(1)

    return [tasks_by_label[label] for label in sorted_labels]

def fetch_open_issues():
    """Queries open issues from the remote repository using the gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--json", "number,title"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[ERROR] Failed to fetch open issues from GitHub: {e.stderr.strip()}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to execute gh CLI command: {e}\n")
        return []

def find_matching_issue(task, open_issues):
    """Looks for an existing issue starting with [Task] <Step_Label>:"""
    target_prefix = f"[Task] {task.label}:".upper()
    for issue in open_issues:
        title = issue.get("title", "").strip().upper()
        if title.startswith(target_prefix):
            return issue
    return None

def create_task_issue(task, epic_number):
    """Creates a sub-task issue on GitHub and returns the issue number."""
    title = f"[Task] {task.label}: {task.name}"
    
    body = f"""Parent Epic: #{epic_number}

## Metadata
* **Target File:** `{task.target_file}`
* **Verification Command:** `{task.verification}`
* **Prerequisites:** {', '.join(task.depends_on) if task.depends_on else 'None'}

## Swarm Action Instructions
{task.instructions}
"""
    try:
        result = subprocess.run(
            [
                "gh", "issue", "create",
                "--title", title,
                "--body-file", "-",
                "--label", "ready-for-dev"
            ],
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        # Parse issue URL to extract number, e.g. "https://github.com/.../issues/145"
        output_url = result.stdout.strip()
        match = re.search(r'/issues/(\d+)', output_url)
        if match:
            return int(match.group(1))
        return output_url
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[ERROR] Failed to create GitHub issue for {task.label}: {e.stderr.strip()}\n")
        return None

def post_epic_comment(epic_number, tasks, plan_path):
    """Comments on the parent Epic on GitHub summarizing the synced tasks."""
    plan_basename = os.path.basename(plan_path)
    
    table_rows = []
    for t in tasks:
        issue_ref = f"#{t.issue_number}" if t.issue_number else "N/A"
        status_label = f"Skipped ({issue_ref})" if t.sync_status == "Skipped" else f"Created ({issue_ref})"
        table_rows.append(
            f"| {t.label} | {t.name} | `{t.target_file}` | `{t.verification}` | {status_label} |"
        )
    
    body = f"""### ☕ Swarm Synchronization Complete

The task execution graph has been successfully compiled from [{plan_basename}](file://{os.path.abspath(plan_path)}) and synchronized to GitHub issues:

| Task | Title | Target File | Verification | Status |
| :--- | :--- | :--- | :--- | :--- |
{chr(10).join(table_rows)}

@maintainer The technical specification and task breakdown are ready. Please review the local markdown files and apply the 'approved' label or click "Proceed" to continue execution (Phase 6 Human Gate).
"""
    try:
        subprocess.run(
            ["gh", "issue", "comment", str(epic_number), "--body-file", "-"],
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        print(f"[INFO] Successfully posted synchronization comment to Epic #{epic_number}")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[ERROR] Failed to comment on Epic #{epic_number}: {e.stderr.strip()}\n")

def main():
    parser = argparse.ArgumentParser(description="Synchronize 05_PLAN.md with GitHub issues")
    parser.add_argument("--plan", help="Path to 05_PLAN.md file")
    parser.add_argument("--epic", type=int, help="Epic Issue Number")
    parser.add_argument("--dry-run", action="store_true", help="Parse plan and print JSON output without syncing")

    args = parser.parse_args()

    # Default plan discovery
    plan_path = args.plan
    if not plan_path:
        feature_dir = "plans/feature"
        if os.path.exists(feature_dir):
            subdirs = sorted(os.listdir(feature_dir), reverse=True)
            for subdir in subdirs:
                candidate = os.path.join(feature_dir, subdir, "05_PLAN.md")
                if os.path.exists(candidate):
                    plan_path = candidate
                    break

    if not plan_path:
        sys.stderr.write("[ERROR] No active 05_PLAN.md found. Please specify --plan.\n")
        sys.exit(1)

    print(f"[INFO] Parsing plan: {plan_path}")
    tasks = parse_plan_file(plan_path)

    print("[INFO] Constructing topological sorted DAG...")
    sorted_tasks = topological_sort(tasks)

    if args.dry_run:
        print("[INFO] Dry-run parsing completed successfully.")
        print(json.dumps([t.to_dict() for t in sorted_tasks], indent=2))
        sys.exit(0)

    # Remote Sync Execution
    epic_number = args.epic
    if not epic_number:
        # Prompt or look for epic_id in the git/workspace context
        sys.stderr.write("[ERROR] No Epic issue number provided. Please specify --epic <id>.\n")
        sys.exit(1)

    print(f"[INFO] Fetching active open issues from GitHub...")
    open_issues = fetch_open_issues()

    newly_created = 0
    skipped_count = 0

    print(f"[INFO] Synchronizing tasks under Parent Epic #{epic_number}...")
    for task in sorted_tasks:
        existing = find_matching_issue(task, open_issues)
        if existing:
            task.issue_number = existing.get("number")
            task.sync_status = "Skipped"
            skipped_count += 1
            print(f"[SKIP] {task.label} already exists as Issue #{task.issue_number}")
        else:
            print(f"[SYNC] Creating issue for {task.label}: {task.name}...")
            issue_num = create_task_issue(task, epic_number)
            if issue_num:
                task.issue_number = issue_num
                task.sync_status = "Created"
                newly_created += 1
                print(f"[INFO] Successfully created Issue #{task.issue_number} for {task.label}")
            else:
                sys.stderr.write(f"[ERROR] Failed to synchronize task {task.label}\n")
                sys.exit(1)

    print(f"[INFO] Sync complete. Created {newly_created} new tasks, skipped {skipped_count} duplicates.")

    # Comment on Parent Epic
    print(f"[INFO] Posting handshake comment to Parent Epic #{epic_number}...")
    post_epic_comment(epic_number, sorted_tasks, plan_path)

if __name__ == "__main__":
    main()
