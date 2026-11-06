#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
☕ Git Worktree & Branch Lifecycle Manager for Parallel Agent Workspaces.
This script automates the creation, merging, and pruning of Git Worktrees
and short-lived isolate branches to ensure complete isolation for parallel subagents.
Supports `--epic-branch <branch>` integration branches and deterministic
`allocate_worker_slot(task_id)` port/slot assignment (slots 1..3, ports 3100..3300).
"""

import argparse
from datetime import datetime, timezone
import json
import os
import re
import subprocess
import sys
import zlib
from typing import Dict, Optional

# Regex for strict input validation to mitigate Shell Injection (Threat Model Sec Control)
ID_SLUG_REGEX = re.compile(r"^[a-zA-Z0-9\-_]+$")
BRANCH_REGEX = re.compile(r"^[a-zA-Z0-9\-_/\.]+$")

# Paths and Config
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKTREES_DIR = os.path.join(WORKSPACE_ROOT, ".worktrees")
LOG_PATH = os.path.join(WORKSPACE_ROOT, "plans/feature/20260618-parallel-worktree-agents/worktree_telemetry.log")

MAX_WORKER_SLOTS = 3
BASE_PORT = 3000
PORT_STEP = 100


def sanitize_input(value: Optional[str], name: str) -> Optional[str]:
    """Ensure arguments are strictly alphanumeric with hyphens/underscores."""
    if not value:
        return value
    if not ID_SLUG_REGEX.match(value):
        print(f"[-] Security Validation Error: Invalid characters in {name}: '{value}'")
        sys.exit(1)
    return value


def sanitize_branch(value: Optional[str], name: str = "epic-branch") -> Optional[str]:
    """Ensure branch names contain only safe ref characters (alphanumeric, -, _, /, .) without '..'."""
    if not value:
        return value
    if ".." in value or value.startswith("-") or not BRANCH_REGEX.match(value):
        print(f"[-] Security Validation Error: Invalid characters in {name}: '{value}'")
        sys.exit(1)
    return value


def allocate_worker_slot(task_id: str, max_slots: int = MAX_WORKER_SLOTS) -> Dict[str, int | str]:
    """
    Deterministically allocates a worker slot (1..3) and port offset (3000 + slot * 100)
    for a given task_id so parallel worktrees never collide on local ports.
    """
    cleaned = str(task_id or "1").strip()
    nums = re.findall(r"\d+", cleaned)
    if nums:
        slot = ((int(nums[-1]) - 1) % max_slots) + 1
    else:
        slot = (zlib.crc32(cleaned.encode("utf-8")) % max_slots) + 1

    port_offset = BASE_PORT + (slot * PORT_STEP)
    return {
        "BEAN_WORKER_SLOT": slot,
        "BEAN_WORKER_PORT": port_offset,
        "PORT": str(port_offset),
        "slot": slot,
        "port_offset": port_offset,
    }


def log_telemetry(task_id, action, branch, worktree_path, status, duration_ms, error=None, extra=None):
    """Write structured JSON logs to telemetry file (Audibility Requirement)."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "task_id": task_id,
        "action": action,
        "branch": branch,
        "worktree_path": worktree_path,
        "status": status,
        "duration_ms": int(duration_ms),
        "error": error,
    }
    if extra:
        log_entry.update(extra)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[-] Warning: Failed to write telemetry log: {e}", file=sys.stderr)


def run_git_cmd(args, cwd=WORKSPACE_ROOT, check=True):
    """Execute a git command and return stdout."""
    try:
        res = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[-] Git command failed: {' '.join(args)}", file=sys.stderr)
        print(f"[-] Git Error output: {e.stderr.strip()}", file=sys.stderr)
        raise


def run_bootstrap_restore(worktree_path):
    """Run lightweight dependency restore inside worktree based on project language."""
    print(f"[*] Bootstrapping worktree dependencies inside: {worktree_path}")

    has_dotnet = False
    for root, _, files in os.walk(worktree_path):
        if any(f.endswith(".csproj") for f in files):
            has_dotnet = True
            break

    if has_dotnet:
        print("[*] .NET project detected. Running dotnet restore...")
        try:
            subprocess.run(["dotnet", "restore"], cwd=worktree_path, check=True)
            print("[+] dotnet restore succeeded!")
        except Exception as e:
            print(f"[-] Warning: dotnet restore failed: {e}", file=sys.stderr)

    if os.path.exists(os.path.join(worktree_path, "package.json")):
        print("[*] Node project detected. Running npm install...")
        try:
            subprocess.run(["npm", "install", "--prefer-offline", "--no-audit"], cwd=worktree_path, check=True)
            print("[+] npm install succeeded!")
        except Exception as e:
            print(f"[-] Warning: npm install failed: {e}", file=sys.stderr)


def action_create(task_id: str, slug: str, epic_branch: Optional[str] = None):
    """Create Git branch (optionally from epic_branch) and mount worktree."""
    start_time = datetime.now(timezone.utc)
    branch_name = f"task/{task_id}-{slug}"
    worktree_path = os.path.join(WORKTREES_DIR, f"task-{task_id}")
    worker_env = allocate_worker_slot(task_id)

    print(f"[*] Creating Isolate Branch: {branch_name}")
    print(f"[*] Mounting Git Worktree at: {worktree_path}")
    print(f"[*] Allocated Worker Slot: BEAN_WORKER_SLOT={worker_env['BEAN_WORKER_SLOT']} (Port {worker_env['port_offset']})")

    try:
        os.makedirs(WORKTREES_DIR, exist_ok=True)

        if os.path.exists(worktree_path):
            print(f"[-] Error: Worktree mount point '{worktree_path}' already exists.")
            sys.exit(1)

        cmd = ["git", "worktree", "add", "-B", branch_name, worktree_path]
        if epic_branch:
            cmd.append(epic_branch)
        run_git_cmd(cmd)

        run_bootstrap_restore(worktree_path)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(
            task_id,
            "create",
            branch_name,
            worktree_path,
            "success",
            duration,
            extra={"epic_branch": epic_branch, "worker_slot": worker_env},
        )
        print(f"[+] Successfully provisioned worktree and branch for task {task_id}!")
        return worker_env

    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(task_id, "create", branch_name, worktree_path, "failure", duration, str(e))
        print(f"[-] Failed to create worktree: {e}", file=sys.stderr)
        sys.exit(1)


def action_merge(task_id: str, epic_branch: Optional[str] = None):
    """Commit changes inside worktree, switch to root (or epic_branch), merge, and prune worktree."""
    start_time = datetime.now(timezone.utc)
    worktree_path = os.path.join(WORKTREES_DIR, f"task-{task_id}")

    print(f"[*] Merging changes from worktree: {worktree_path}")

    if not os.path.exists(worktree_path):
        print(f"[-] Error: Worktree path '{worktree_path}' does not exist.")
        sys.exit(1)

    try:
        branch_name = run_git_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)

        print("[*] Committing uncommitted modifications in worktree...")
        status = run_git_cmd(["git", "status", "--porcelain"], cwd=worktree_path)
        if status:
            run_git_cmd(["git", "add", "-A"], cwd=worktree_path)
            run_git_cmd(
                ["git", "commit", "-m", f"feat(slice-{task_id}): automated implementation & TDD verification"],
                cwd=worktree_path,
            )
            print("[+] Committed modifications successfully.")
        else:
            print("[*] No changes to commit in worktree.")

        lock_file = os.path.join(WORKSPACE_ROOT, ".worktree_merge.lock")
        print("[*] Acquiring merge queue lock...")
        try:
            with open(lock_file, "x") as f:
                f.write(f"{os.getpid()}")
        except FileExistsError:
            print("[*] Waiting for merge queue lock...")
            import time
            attempts = 0
            while os.path.exists(lock_file) and attempts < 10:
                time.sleep(1)
                attempts += 1
            with open(lock_file, "w") as f:
                f.write(f"{os.getpid()}")

        try:
            if epic_branch:
                print(f"[*] Checking out epic integration branch '{epic_branch}'...")
                run_git_cmd(["git", "checkout", epic_branch])
                merge_target = epic_branch
            else:
                merge_target = "main workspace"

            print(f"[*] Merging branch '{branch_name}' into {merge_target}...")
            run_git_cmd(["git", "merge", branch_name, "--no-ff", "-m", f"merge: integrate slice {task_id}"])
            print("[+] Branch merged successfully.")

            print("[*] Removing worktree...")
            run_git_cmd(["git", "worktree", "remove", "--force", worktree_path])
            run_git_cmd(["git", "worktree", "prune"])

            print("[*] Deleting local isolate branch...")
            run_git_cmd(["git", "branch", "-D", branch_name])
            print("[+] Isolate branch deleted.")

        finally:
            if os.path.exists(lock_file):
                os.remove(lock_file)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(
            task_id,
            "merge",
            branch_name,
            worktree_path,
            "success",
            duration,
            extra={"epic_branch": epic_branch},
        )
        print(f"[+] Successfully integrated task {task_id} and cleaned up workspace!")

    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(task_id, "merge", "unknown", worktree_path, "failure", duration, str(e))
        print(f"[-] Failed to merge and clean up worktree: {e}", file=sys.stderr)
        sys.exit(1)


def action_clean():
    """Scan and prune any orphaned or dangling worktrees."""
    start_time = datetime.now(timezone.utc)
    print("[*] Performing Git Worktree prune and directory reconciliation...")
    try:
        run_git_cmd(["git", "worktree", "prune"])

        cleaned_count = 0
        if os.path.exists(WORKTREES_DIR):
            worktree_list = run_git_cmd(["git", "worktree", "list"])
            for item in os.listdir(WORKTREES_DIR):
                item_path = os.path.join(WORKTREES_DIR, item)
                if os.path.isdir(item_path):
                    if item_path not in worktree_list:
                        print(f"[*] Found orphaned worktree folder: {item_path}. Force removing...")
                        import shutil
                        shutil.rmtree(item_path, ignore_errors=True)
                        cleaned_count += 1

        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry("reconciliation", "clean", "none", WORKTREES_DIR, "success", duration)
        print(f"[+] Clean complete. Pruned {cleaned_count} orphaned worktree directories.")

    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry("reconciliation", "clean", "none", WORKTREES_DIR, "failure", duration, str(e))
        print(f"[-] Clean operation failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Git Worktree Lifecycle Manager for parallel subagents.")
    parser.add_argument("--action", choices=["create", "merge", "clean"], required=True, help="Action to perform.")
    parser.add_argument("--task", help="Task ID (e.g., slice-04).")
    parser.add_argument("--slug", help="Feature/slice short slug.")
    parser.add_argument("--epic-branch", dest="epic_branch", help="Epic integration branch (e.g., epic/42-auth).")

    args = parser.parse_args()

    task_id = sanitize_input(args.task, "task")
    slug = sanitize_input(args.slug, "slug")
    epic_branch = sanitize_branch(args.epic_branch, "epic-branch")

    if args.action == "create":
        if not task_id or not slug:
            parser.error("--task and --slug are required for create action.")
        action_create(task_id, slug, epic_branch=epic_branch)
    elif args.action == "merge":
        if not task_id:
            parser.error("--task is required for merge action.")
        action_merge(task_id, epic_branch=epic_branch)
    elif args.action == "clean":
        action_clean()


if __name__ == "__main__":
    main()
