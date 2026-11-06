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
promote.py: Spec PR Promotion Engine ("Calling the Order") for Bean-Brewer.

Replaces legacy sync.py with:
1. Parsing of 05_PLAN.md (and optional 03_PRD.md for verbatim AC text lookup).
2. Slice metadata support: [AFK] / [HITL] execution mode, Depends On, and Covers: AC1, AC2.
3. Deterministic hidden idempotency marker: <!-- bean-slice-id: <epic_id>-<slice_num> -->
   so re-running promotion matches by marker ID rather than fragile issue title.
4. GitHub Issue body limit guard (MAX_BODY_CHARS = 60000), truncating with a pointer if exceeded.
5. --offline mode: writes OKF-formatted ticket files into <bundle_dir>/tickets/<epic_id>-<num>-<slug>.md
   + <bundle_dir>/tickets/index.md (with OKF frontmatter stamping).
6. --github mode (with --dry-run support): builds GraphQL / gh payloads to create/update sub-issues
   under Parent #<epic_id>, links native blockedBy dependencies, and if --clean-scratch is passed,
   executes `git rm -rf <bundle_dir>` so .scratch/<id> is removed before Spec PR merge.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    from scripts.okf import extract_frontmatter, render_markdown, stamp_file, utc_now_iso
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from scripts.okf import extract_frontmatter, render_markdown, stamp_file, utc_now_iso

MAX_BODY_CHARS = 60000


def slugify(text: str) -> str:
    """Converts a slice/task title into a clean kebab-case filename slug."""
    cleaned = re.sub(r"[^\w\s\-]", "", text.lower()).strip()
    slug = re.sub(r"[\s_]+", "-", cleaned)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "slice"


def extract_slice_num(label: str, fallback_idx: int = 1) -> str:
    """Extracts a deterministic slice number/identifier from a step/slice label."""
    # e.g. "STEP 1" -> "1", "SLICE 02" -> "02", "STEP 1.A" -> "1a"
    m = re.search(r"(?:STEP|TASK|SLICE)\s+([\w\.\-]+)", label, re.IGNORECASE)
    raw = m.group(1) if m else label
    normalized = re.sub(r"[^a-zA-Z0-9]", "", raw).lower()
    return normalized or str(fallback_idx)


def format_idempotency_marker(epic_id: str | int, slice_num: str | int) -> str:
    """Returns the deterministic hidden HTML marker for a slice."""
    return f"<!-- bean-slice-id: {epic_id}-{slice_num} -->"


def extract_idempotency_marker(text: str) -> Optional[str]:
    """Extracts `<epic_id>-<slice_num>` from a ticket/issue body if present."""
    if not text:
        return None
    m = re.search(r"<!--\s*bean-slice-id:\s*([^\s>]+)\s*-->", text)
    return m.group(1).strip() if m else None


class SliceTask:
    def __init__(
        self,
        label: str,
        name: str,
        is_done: bool = False,
        execution_mode: str = "AFK",
        slice_num: str = "1",
    ):
        self.label = label.strip().upper()
        self.name = name.strip()
        self.is_done = is_done
        self.execution_mode = execution_mode.upper() if execution_mode else "AFK"
        self.slice_num = str(slice_num)
        self.target_file = "Not specified"
        self.verification = "Not specified"
        self.depends_on: List[str] = []
        self.covers: List[str] = []
        self.expanded_covers: List[str] = []
        self.instructions = ""
        self.issue_number: Optional[int] = None
        self.ticket_path: Optional[str] = None
        self.sync_status = "Pending"

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def marker_id(self, epic_id: str | int) -> str:
        return f"{epic_id}-{self.slice_num}"

    def marker_comment(self, epic_id: str | int) -> str:
        return format_idempotency_marker(epic_id, self.slice_num)

    def to_dict(self, epic_id: str | int = "epic") -> Dict[str, Any]:
        return {
            "label": self.label,
            "slice_num": self.slice_num,
            "slice_id": self.marker_id(epic_id),
            "marker": self.marker_comment(epic_id),
            "name": self.name,
            "slug": self.slug,
            "execution_mode": self.execution_mode,
            "is_done": self.is_done,
            "target_file": self.target_file,
            "verification": self.verification,
            "depends_on": self.depends_on,
            "covers": self.covers,
            "expanded_covers": self.expanded_covers,
            "instructions": self.instructions.strip(),
            "issue_number": self.issue_number,
            "ticket_path": self.ticket_path,
            "sync_status": self.sync_status,
        }


# Backwards-compatible alias
Task = SliceTask


def clean_markdown_inline(text: str) -> str:
    """Removes wrapping bold, italic, or backticks from inline markdown."""
    text = text.strip()
    for wrapper in ("***", "**", "*", "`"):
        if text.startswith(wrapper) and text.endswith(wrapper) and len(text) > 2 * len(wrapper):
            return text[len(wrapper) : -len(wrapper)].strip()
    return text


def parse_prd_acceptance_criteria(prd_path: Optional[str | Path]) -> Dict[str, str]:
    """Parses 03_PRD.md (or 02_PRD.md) to map AC identifiers (e.g. 'AC1', 'AC-01') to verbatim text."""
    ac_map: Dict[str, str] = {}
    if not prd_path:
        return ac_map
    p = Path(prd_path)
    if not p.is_file():
        return ac_map

    content = p.read_text(encoding="utf-8")
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Match bullet/numbered/heading patterns like:
        # - **AC1**: User can authenticate via OAuth2
        # - **AC1:** User can authenticate via OAuth2
        # - AC-1: User can authenticate
        # ### AC1: User can authenticate
        m = re.match(
            r"^(?:[\-\*\+]|\d+\.|#{1,4})?\s*(?:\*\*|\*)?(AC[\-\_]?\d+)(?:\*\*|\*)?\s*[:\-\—]\s*(?:\*\*|\*)?\s*(.+)$",
            line,
            re.IGNORECASE,
        )
        if m:
            ac_id = m.group(1).upper()
            ac_text = m.group(2).strip()
            ac_map[ac_id] = ac_text
            # Also register normalized form without hyphen (AC-1 <-> AC1)
            norm_id = ac_id.replace("-", "").replace("_", "")
            ac_map[norm_id] = ac_text
            continue

        # Match markdown table row: | AC1 | User can authenticate |
        t_match = re.match(
            r"^\|\s*(?:\*\*|\*)?(AC[\-\_]?\d+)(?:\*\*|\*)?\s*\|\s*([^|]+)\|",
            line,
            re.IGNORECASE,
        )
        if t_match:
            ac_id = t_match.group(1).upper()
            ac_text = t_match.group(2).strip()
            if ac_text and not set(ac_text).issubset({"-", ":", " "}):
                ac_map[ac_id] = ac_text
                norm_id = ac_id.replace("-", "").replace("_", "")
                ac_map[norm_id] = ac_text

    return ac_map


def expand_ac_references(covers: List[str], ac_map: Dict[str, str]) -> List[str]:
    """Expands AC IDs (e.g. ['AC1', 'AC2']) into verbatim descriptions using ac_map."""
    expanded: List[str] = []
    for ac_id in covers:
        key = ac_id.strip().upper()
        norm_key = key.replace("-", "").replace("_", "")
        verbatim = ac_map.get(key) or ac_map.get(norm_key)
        if verbatim:
            expanded.append(f"{key}: {verbatim}")
        else:
            expanded.append(key)
    return expanded


def _parse_task_details(task: SliceTask, lines: List[str], ac_map: Dict[str, str]) -> None:
    """Parses metadata lines and aggregates instruction lists for a SliceTask."""
    target_file_pattern = re.compile(r"^\s*[*\-\s]*target file[s]?[*:\s]+\s*(.+)$", re.IGNORECASE)
    verification_pattern = re.compile(r"^\s*[*\-\s]*verification[*:\s]+\s*(.+)$", re.IGNORECASE)
    depends_on_pattern = re.compile(r"^\s*[*\-\s]*depends on[*:\s]+\s*(.+)$", re.IGNORECASE)
    covers_pattern = re.compile(r"^\s*[*\-\s]*covers[*:\s]+\s*(.+)$", re.IGNORECASE)
    mode_pattern = re.compile(r"^\s*[*\-\s]*(?:execution\s+)?mode[*:\s]+\s*(AFK|HITL)\b", re.IGNORECASE)

    instructions: List[str] = []
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        target_match = target_file_pattern.match(clean_line)
        verify_match = verification_pattern.match(clean_line)
        depends_match = depends_on_pattern.match(clean_line)
        covers_match = covers_pattern.match(clean_line)
        mode_match = mode_pattern.match(clean_line)

        if target_match:
            task.target_file = clean_markdown_inline(target_match.group(1))
        elif verify_match:
            task.verification = clean_markdown_inline(verify_match.group(1))
        elif depends_match:
            raw_deps = clean_markdown_inline(depends_match.group(1))
            if raw_deps.lower() in ("none", "n/a", "-"):
                task.depends_on = []
            else:
                deps = [clean_markdown_inline(d).upper() for d in raw_deps.split(",") if d.strip()]
                task.depends_on = [d for d in deps if d.lower() not in ("none", "n/a", "-")]
        elif covers_match:
            raw_covers = clean_markdown_inline(covers_match.group(1))
            cov_items = [clean_markdown_inline(c).upper() for c in raw_covers.split(",") if c.strip()]
            task.covers = [c for c in cov_items if c.lower() not in ("none", "n/a", "-")]
            task.expanded_covers = expand_ac_references(task.covers, ac_map)
        elif mode_match:
            task.execution_mode = mode_match.group(1).upper()
        else:
            instructions.append(line)

    if instructions:
        task.instructions = "\n".join(instructions)


def parse_plan_file(
    plan_path: str | Path,
    prd_path: Optional[str | Path] = None,
) -> List[SliceTask]:
    """Parses 05_PLAN.md into a structured list of SliceTask objects."""
    p = Path(plan_path)
    if not p.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    # Auto-discover 03_PRD.md (or 02_PRD.md) in the same bundle directory if prd_path is not given
    if prd_path is None:
        for candidate_name in ("03_PRD.md", "02_PRD.md"):
            cand = p.parent / candidate_name
            if cand.is_file():
                prd_path = cand
                break

    ac_map = parse_prd_acceptance_criteria(prd_path)
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()

    tasks_by_label: Dict[str, SliceTask] = {}
    tasks_order: List[str] = []

    checklist_pattern = re.compile(
        r"^\s*[\-\*]\s+\[([ xX])\]\s*(?:\*\*)?\s*((?:Step|Task|Slice)\s+([\w\.\-]+))(?:\s+\[([^\]]+)\])?(?:\*\*)?[:\-]\s*(?:\*\*)?\s*(.*)$",
        re.IGNORECASE,
    )
    step_header_pattern = re.compile(
        r"^#{2,4}\s*(?:\*\*)?\s*((?:Step|Task|Slice)\s+([\w\.\-]+))(?:\s+\[([^\]]+)\])?(?:\*\*)?[:\-\s]*(.*)$",
        re.IGNORECASE,
    )

    # First Pass: discover checklist items and inline metadata beneath them
    current_inline_task: Optional[SliceTask] = None
    inline_details: List[str] = []
    seq = 0

    for line in lines:
        match = checklist_pattern.match(line)
        if match:
            if current_inline_task and inline_details:
                _parse_task_details(current_inline_task, inline_details, ac_map)
                inline_details = []
            seq += 1
            is_done = match.group(1).lower() == "x"
            step_label = match.group(2).strip().upper()
            bracket_tag = (match.group(4) or "").strip().upper()
            step_name = match.group(5).strip().rstrip("*").strip()

            # Check if [AFK] or [HITL] appears in bracket_tag or inside step_name
            exec_mode = "AFK"
            if bracket_tag in ("AFK", "HITL"):
                exec_mode = bracket_tag
            else:
                mode_in_name = re.search(r"\[(AFK|HITL)\]", step_name, re.IGNORECASE)
                if mode_in_name:
                    exec_mode = mode_in_name.group(1).upper()
                    step_name = re.sub(r"\s*\[(AFK|HITL)\]\s*", " ", step_name, flags=re.IGNORECASE).strip()

            slice_num = extract_slice_num(step_label, fallback_idx=seq)
            task = SliceTask(
                label=step_label,
                name=step_name,
                is_done=is_done,
                execution_mode=exec_mode,
                slice_num=slice_num,
            )
            tasks_by_label[step_label] = task
            tasks_order.append(step_label)
            current_inline_task = task
            continue

        if current_inline_task:
            if line.startswith("#"):
                _parse_task_details(current_inline_task, inline_details, ac_map)
                current_inline_task = None
                inline_details = []
            else:
                inline_details.append(line)

    if current_inline_task and inline_details:
        _parse_task_details(current_inline_task, inline_details, ac_map)

    # Second Pass: extract detailed instructions/metadata under ## / ### / #### Step headers
    current_header_task: Optional[SliceTask] = None
    detail_lines: List[str] = []

    for line in lines:
        header_match = step_header_pattern.match(line)
        if header_match:
            if current_header_task and detail_lines:
                _parse_task_details(current_header_task, detail_lines, ac_map)

            step_label = header_match.group(1).strip().upper()
            bracket_tag = (header_match.group(3) or "").strip().upper()
            header_rest = (header_match.group(4) or "").strip().rstrip("*").strip()
            current_header_task = tasks_by_label.get(step_label)
            if current_header_task is None:
                seq += 1
                exec_mode = bracket_tag if bracket_tag in ("AFK", "HITL") else "AFK"
                mode_in_rest = re.search(r"\[(AFK|HITL)\]", header_rest, re.IGNORECASE)
                if mode_in_rest:
                    exec_mode = mode_in_rest.group(1).upper()
                    header_rest = re.sub(r"\s*\[(AFK|HITL)\]\s*", " ", header_rest, flags=re.IGNORECASE).strip()
                slice_num = extract_slice_num(step_label, fallback_idx=seq)
                current_header_task = SliceTask(
                    label=step_label,
                    name=header_rest or step_label,
                    is_done=False,
                    execution_mode=exec_mode,
                    slice_num=slice_num,
                )
                tasks_by_label[step_label] = current_header_task
                tasks_order.append(step_label)
            elif bracket_tag in ("AFK", "HITL"):
                current_header_task.execution_mode = bracket_tag

            detail_lines = []
            continue

        if current_header_task:
            if line.startswith("# ") or line.startswith("## "):
                _parse_task_details(current_header_task, detail_lines, ac_map)
                current_header_task = None
                detail_lines = []
            else:
                detail_lines.append(line)

    if current_header_task and detail_lines:
        _parse_task_details(current_header_task, detail_lines, ac_map)

    return [tasks_by_label[label] for label in tasks_order if label in tasks_by_label]


def topological_sort(tasks: List[SliceTask]) -> List[SliceTask]:
    """Schedules tasks based on depends_on constraints using Kahn's algorithm."""
    tasks_by_label = {t.label: t for t in tasks}
    adj: Dict[str, List[str]] = {t.label: [] for t in tasks}
    in_degree: Dict[str, int] = {t.label: 0 for t in tasks}

    for t in tasks:
        for dep in t.depends_on:
            if dep in tasks_by_label:
                adj[dep].append(t.label)
                in_degree[t.label] += 1
            else:
                sys.stderr.write(f"[WARN] Dependency '{dep}' for '{t.label}' is external to this plan.\n")

    queue = [label for label, degree in in_degree.items() if degree == 0]
    heapq.heapify(queue)
    sorted_labels: List[str] = []

    while queue:
        curr = heapq.heappop(queue)
        sorted_labels.append(curr)

        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(queue, neighbor)

    if len(sorted_labels) != len(tasks):
        raise ValueError("Circular dependency detected in execution plan!")

    return [tasks_by_label[label] for label in sorted_labels]


def enforce_body_limit(
    body: str,
    plan_path: str = "05_PLAN.md",
    max_chars: int = MAX_BODY_CHARS,
) -> str:
    """Enforces GitHub's 60,000-character body limit, truncating with a pointer if exceeded."""
    if len(body) <= max_chars:
        return body

    pointer_suffix = (
        f"\n\n...\n\n> **[TRUNCATED]** Body exceeded `MAX_BODY_CHARS` ({max_chars} chars). "
        f"See full slice specification in `{plan_path}`."
    )
    allowed = max(0, max_chars - len(pointer_suffix))
    return body[:allowed] + pointer_suffix


def render_slice_body(
    task: SliceTask,
    epic_id: str | int,
    plan_path: str = "05_PLAN.md",
    max_chars: int = MAX_BODY_CHARS,
) -> str:
    """Renders the canonical Markdown body for a promoted slice (with hidden idempotency marker)."""
    marker = task.marker_comment(epic_id)
    prereqs = ", ".join(task.depends_on) if task.depends_on else "None"

    ac_lines: List[str] = []
    if task.expanded_covers:
        for item in task.expanded_covers:
            ac_lines.append(f"- {item}")
    elif task.covers:
        for item in task.covers:
            ac_lines.append(f"- {item}")
    else:
        ac_lines.append("- None specified")

    ac_section = "\n".join(ac_lines)
    instructions = task.instructions.strip() or "Follow TDD Red-Green-Refactor workflow per 05_PLAN.md."

    body = f"""{marker}
Parent Epic: #{epic_id}

## Slice Metadata
* **Slice ID:** `{task.marker_id(epic_id)}`
* **Execution Mode:** `[{task.execution_mode}]`
* **Target File:** `{task.target_file}`
* **Verification Command:** `{task.verification}`
* **Depends On:** {prereqs}

## Acceptance Criteria Covered (`03_PRD.md`)
{ac_section}

## Implementation Instructions
{instructions}
"""
    return enforce_body_limit(body, plan_path=str(plan_path), max_chars=max_chars)


def find_matching_issue(
    task: SliceTask,
    open_issues: List[Dict[str, Any]],
    epic_id: str | int,
) -> Optional[Dict[str, Any]]:
    """Matches an existing issue primarily via deterministic `<!-- bean-slice-id: ... -->` marker."""
    expected_marker_id = task.marker_id(epic_id)
    # 1. Deterministic marker match inside issue body (survives title renames!)
    for issue in open_issues:
        body = issue.get("body") or ""
        found_marker = extract_idempotency_marker(body)
        if found_marker == expected_marker_id:
            return issue

    # 2. Fallback to legacy title prefix only if issue has no marker
    target_prefix = f"[Task] {task.label}:".upper()
    slice_prefix = f"[{task.execution_mode}] {task.label}:".upper()
    for issue in open_issues:
        body = issue.get("body") or ""
        if extract_idempotency_marker(body) is not None:
            continue
        title = (issue.get("title") or "").strip().upper()
        if title.startswith(target_prefix) or title.startswith(slice_prefix):
            return issue

    return None


def promote_offline(
    tasks: List[SliceTask],
    bundle_dir: str | Path,
    epic_id: str | int = "epic",
    plan_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Writes OKF-formatted ticket files into `<bundle_dir>/tickets/<epic_id>-<num>-<slug>.md` + `tickets/index.md`."""
    b_dir = Path(bundle_dir).resolve()
    tickets_dir = b_dir / "tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True)

    plan_rel = "../05_PLAN.md"
    if plan_path is None and (b_dir / "05_PLAN.md").exists():
        plan_path = b_dir / "05_PLAN.md"

    # Scan existing ticket files in tickets/ by hidden bean-slice-id marker for idempotency
    existing_by_marker: Dict[str, Path] = {}
    for existing_md in tickets_dir.glob("*.md"):
        if existing_md.name == "index.md":
            continue
        try:
            raw_text = existing_md.read_text(encoding="utf-8")
        except Exception:
            continue
        m_id = extract_idempotency_marker(raw_text)
        if m_id:
            existing_by_marker[m_id] = existing_md

    created_count = 0
    updated_count = 0
    ticket_records: List[Dict[str, Any]] = []

    for task in tasks:
        marker_id = task.marker_id(epic_id)
        filename = f"{epic_id}-{task.slice_num}-{task.slug}.md"
        target_ticket_path = tickets_dir / filename

        prev_path = existing_by_marker.get(marker_id)
        if prev_path is not None:
            if prev_path != target_ticket_path and prev_path.exists():
                # Slice title was renamed: remove the old slug file so no duplicate remains
                prev_path.unlink()
            task.sync_status = "Updated"
            updated_count += 1
        else:
            task.sync_status = "Created"
            created_count += 1

        body = render_slice_body(
            task,
            epic_id=epic_id,
            plan_path=str(plan_path or "05_PLAN.md"),
        )
        full_md = f"\n# [{task.execution_mode}] {task.label}: {task.name}\n\n{body}"
        target_ticket_path.write_text(full_md, encoding="utf-8")

        sources_list = [plan_rel] if (b_dir / "05_PLAN.md").exists() else None
        stamp_file(
            file_path=target_ticket_path,
            okf_type="ticket",
            stage="6_promote",
            by="bean-brewer/promote",
            name=f"[{task.execution_mode}] {task.label}: {task.name}",
            description=f"Slice {task.slice_num} ({task.execution_mode}): {task.name}",
            status="stable",
            sources=sources_list,
            bundle_dir=b_dir,
        )

        # Attach slice-specific OKF frontmatter metadata while keeping id == stem
        fm, stamped_body, _ = extract_frontmatter(target_ticket_path)
        fm["slice_id"] = marker_id
        fm["execution_mode"] = task.execution_mode
        fm["depends_on"] = task.depends_on
        fm["covers"] = task.covers
        target_ticket_path.write_text(render_markdown(fm, stamped_body), encoding="utf-8")

        task.ticket_path = str(target_ticket_path)
        ticket_records.append(task.to_dict(epic_id))

    # Write <bundle_dir>/tickets/index.md catalog
    index_path = tickets_dir / "index.md"
    rows = []
    for t in tasks:
        t_fname = f"{epic_id}-{t.slice_num}-{t.slug}.md"
        deps_str = ", ".join(t.depends_on) if t.depends_on else "-"
        covers_str = ", ".join(t.covers) if t.covers else "-"
        rows.append(
            f"| [{t.marker_id(epic_id)}]({t_fname}) | `{t.execution_mode}` | {t.name} | `{deps_str}` | `{covers_str}` | `{t.sync_status}` |"
        )
    table_str = "\n".join(rows) if rows else "| *(empty)* | - | - | - | - | - |"
    index_fm = {
        "id": "tickets",
        "type": "index",
        "name": f"Promoted Tickets Catalog (Epic {epic_id})",
        "description": f"Offline OKF vertical-slice tickets promoted from 05_PLAN.md for Epic {epic_id}.",
        "status": "stable",
        "stage": "6_promote",
        "generated": {"by": "bean-brewer/promote", "at": utc_now_iso()},
    }
    index_body = (
        f"\n# Promoted Tickets Catalog (Epic {epic_id})\n\n"
        "| Slice ID | Mode | Title | Depends On | Covers | Status |\n"
        "| :--- | :---: | :--- | :--- | :--- | :---: |\n"
        f"{table_str}\n"
    )
    index_path.write_text(render_markdown(index_fm, index_body), encoding="utf-8")

    return {
        "mode": "offline",
        "epic_id": str(epic_id),
        "bundle_dir": str(b_dir),
        "tickets_dir": str(tickets_dir),
        "index_path": str(index_path),
        "created": created_count,
        "updated": updated_count,
        "tickets": ticket_records,
    }


def build_github_promotion_payload(
    tasks: List[SliceTask],
    epic_id: str | int,
    open_issues: Optional[List[Dict[str, Any]]] = None,
    plan_path: str = "05_PLAN.md",
    bundle_dir: Optional[str | Path] = None,
    clean_scratch: bool = False,
) -> Dict[str, Any]:
    """Builds the GraphQL / gh CLI promotion plan, sub-issue links, and blockedBy dependency edges."""
    existing_issues = open_issues or []
    operations: List[Dict[str, Any]] = []
    sub_issue_mutations: List[Dict[str, Any]] = []
    dependency_mutations: List[Dict[str, Any]] = []

    for task in tasks:
        title = f"[{task.execution_mode}] {task.label}: {task.name}"
        body = render_slice_body(task, epic_id=epic_id, plan_path=str(plan_path))
        matched = find_matching_issue(task, existing_issues, epic_id=epic_id)

        if matched:
            task.issue_number = matched.get("number")
            task.sync_status = "Updated"
            op_type = "update"
            gh_cmd = [
                "gh", "issue", "edit", str(task.issue_number),
                "--title", title,
                "--body-file", "-",
            ]
        else:
            task.sync_status = "Created"
            op_type = "create"
            gh_cmd = [
                "gh", "issue", "create",
                "--title", title,
                "--body-file", "-",
                "--label", "ready-for-dev",
                "--label", task.execution_mode.lower(),
            ]

        operations.append({
            "action": op_type,
            "slice_id": task.marker_id(epic_id),
            "label": task.label,
            "title": title,
            "execution_mode": task.execution_mode,
            "issue_number": task.issue_number,
            "depends_on": task.depends_on,
            "covers": task.covers,
            "expanded_covers": task.expanded_covers,
            "body": body,
            "gh_command": gh_cmd,
        })

        sub_issue_mutations.append({
            "parent_epic": int(epic_id) if str(epic_id).isdigit() else str(epic_id),
            "slice_id": task.marker_id(epic_id),
            "query": (
                "mutation AddSubIssue($issueId: ID!, $subIssueId: ID!) { "
                "addSubIssue(input: {issueId: $issueId, subIssueId: $subIssueId}) { "
                "issue { id } subIssue { id } } }"
            ),
        })

        for dep_label in task.depends_on:
            dependency_mutations.append({
                "slice_id": task.marker_id(epic_id),
                "blocked_by_label": dep_label,
                "relation": "blockedBy",
                "query": (
                    "mutation AddBlockedBy($issueId: ID!, $blockingIssueId: ID!) { "
                    "addBlockedBy(input: {issueId: $issueId, blockingIssueId: $blockingIssueId}) { "
                    "issue { id } blockingIssue { id } } }"
                ),
            })

    clean_cmd: Optional[List[str]] = None
    if clean_scratch and bundle_dir:
        clean_cmd = ["git", "rm", "-rf", str(bundle_dir)]

    return {
        "mode": "github",
        "epic_id": str(epic_id),
        "operations": operations,
        "sub_issue_mutations": sub_issue_mutations,
        "blocked_by_mutations": dependency_mutations,
        "clean_scratch": clean_scratch,
        "clean_scratch_command": clean_cmd,
        "tasks": [t.to_dict(epic_id) for t in tasks],
    }


def fetch_open_issues() -> List[Dict[str, Any]]:
    """Queries open issues (including body for marker matching) from GitHub using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        return json.loads(result.stdout)
    except Exception as exc:
        sys.stderr.write(f"[WARN] Failed to fetch open issues via gh CLI: {exc}\n")
        return []


def clean_scratch_bundle(bundle_dir: str | Path, dry_run: bool = False) -> List[str]:
    """Executes `git rm -rf <bundle_dir>` to remove `.scratch/<id>` before Spec PR merge."""
    cmd = ["git", "rm", "-rf", str(bundle_dir)]
    if not dry_run:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return cmd


def execute_github_promotion(payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Executes or dry-runs the GitHub promotion payload."""
    if dry_run:
        return payload

    for op in payload.get("operations", []):
        cmd = op["gh_command"]
        body = op["body"]
        res = subprocess.run(
            cmd,
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        if op["action"] == "create":
            m = re.search(r"/issues/(\d+)", res.stdout.strip())
            if m:
                op["issue_number"] = int(m.group(1))

    if payload.get("clean_scratch") and payload.get("clean_scratch_command"):
        cmd = payload["clean_scratch_command"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    return payload


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Promote 05_PLAN.md slices into offline OKF tickets or GitHub sub-issues")
    parser.add_argument("--plan", help="Path to 05_PLAN.md file")
    parser.add_argument("--prd", help="Optional path to 03_PRD.md file for verbatim AC expansion")
    parser.add_argument("--bundle-dir", help="Path to OKF bundle directory (defaults to parent of 05_PLAN.md)")
    parser.add_argument("--epic", default="epic", help="Parent Epic issue number or identifier")
    parser.add_argument("--offline", action="store_true", help="Write OKF ticket files to <bundle_dir>/tickets/")
    parser.add_argument("--github", action="store_true", help="Promote slices to GitHub sub-issues under Parent Epic")
    parser.add_argument("--dry-run", action="store_true", help="Build and print JSON payload without mutating GitHub")
    parser.add_argument("--clean-scratch", action="store_true", help="Run `git rm -rf <bundle_dir>` to clean .scratch/<id>")

    args = parser.parse_args(argv)

    plan_path = args.plan
    if not plan_path and args.bundle_dir:
        candidate = os.path.join(args.bundle_dir, "05_PLAN.md")
        if os.path.exists(candidate):
            plan_path = candidate

    if not plan_path:
        for base_dir in (".scratch", "plans/feature"):
            if os.path.exists(base_dir):
                for subdir in sorted(os.listdir(base_dir), reverse=True):
                    candidate = os.path.join(base_dir, subdir, "05_PLAN.md")
                    if os.path.exists(candidate):
                        plan_path = candidate
                        break
            if plan_path:
                break

    if not plan_path or not os.path.exists(plan_path):
        sys.stderr.write("[ERROR] No active 05_PLAN.md found. Please specify --plan.\n")
        return 1

    bundle_dir = args.bundle_dir or os.path.dirname(os.path.abspath(plan_path))
    tasks = parse_plan_file(plan_path, prd_path=args.prd)
    sorted_tasks = topological_sort(tasks)

    if args.offline or (not args.github and not args.dry_run):
        result = promote_offline(
            tasks=sorted_tasks,
            bundle_dir=bundle_dir,
            epic_id=args.epic,
            plan_path=plan_path,
        )
        print(json.dumps(result, indent=2))
        return 0

    open_issues = [] if args.dry_run else fetch_open_issues()
    payload = build_github_promotion_payload(
        tasks=sorted_tasks,
        epic_id=args.epic,
        open_issues=open_issues,
        plan_path=plan_path,
        bundle_dir=bundle_dir,
        clean_scratch=args.clean_scratch,
    )
    result = execute_github_promotion(payload, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
