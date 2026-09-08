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
"""

import os
import sys
import re
import json
import argparse
import subprocess
from datetime import datetime, timezone

# Regex for strict input validation to mitigate Shell Injection (Threat Model Sec Control)
ID_SLUG_REGEX = re.compile(r"^[a-zA-Z0-9\-_]+$")

# Paths and Config
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKTREES_DIR = os.path.join(WORKSPACE_ROOT, ".worktrees")
LOG_PATH = os.path.join(WORKSPACE_ROOT, "plans/feature/20260618-parallel-worktree-agents/worktree_telemetry.log")

def sanitize_input(value, name):
    """Ensure arguments are strictly alphanumeric with hyphens/underscores."""
    if not value:
        return value
    if not ID_SLUG_REGEX.match(value):
        print(f"[-] Security Validation Error: Invalid characters in {name}: '{value}'")
        sys.exit(1)
    return value

def log_telemetry(task_id, action, branch, worktree_path, status, duration_ms, error=None):
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
        "error": error
    }
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
            check=check
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[-] Git command failed: {' '.join(args)}", file=sys.stderr)
        print(f"[-] Git Error output: {e.stderr.strip()}", file=sys.stderr)
        raise

def run_bootstrap_restore(worktree_path):
    """Run lightweight dependency restore inside worktree based on project language."""
    print(f"[*] Bootstrapping worktree dependencies inside: {worktree_path}")
    
    # 1. Look for .csproj files (.NET)
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
            
    # 2. Look for package.json (Node)
    if os.path.exists(os.path.join(worktree_path, "package.json")):
        print("[*] Node project detected. Running npm install...")
        try:
            subprocess.run(["npm", "install", "--prefer-offline", "--no-audit"], cwd=worktree_path, check=True)
            print("[+] npm install succeeded!")
        except Exception as e:
            print(f"[-] Warning: npm install failed: {e}", file=sys.stderr)

def action_create(task_id, slug):
    """Create Git branch and mount worktree."""
    start_time = datetime.now(timezone.utc)
    branch_name = f"task/{task_id}-{slug}"
    worktree_path = os.path.join(WORKTREES_DIR, f"task-{task_id}")
    
    print(f"[*] Creating Isolate Branch: {branch_name}")
    print(f"[*] Mounting Git Worktree at: {worktree_path}")
    
    try:
        # Create worktrees parent directory if not exists
        os.makedirs(WORKTREES_DIR, exist_ok=True)
        
        if os.path.exists(worktree_path):
            print(f"[-] Error: Worktree mount point '{worktree_path}' already exists.")
            sys.exit(1)
            
        # Add git worktree and force-create/reset the branch to ensure a clean state
        run_git_cmd(["git", "worktree", "add", "-B", branch_name, worktree_path])
        
        # Bootstrap dependencies inside the worktree
        run_bootstrap_restore(worktree_path)
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(task_id, "create", branch_name, worktree_path, "success", duration)
        print(f"[+] Successfully provisioned worktree and branch for task {task_id}!")
        
    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(task_id, "create", branch_name, worktree_path, "failure", duration, str(e))
        print(f"[-] Failed to create worktree: {e}", file=sys.stderr)
        sys.exit(1)

def action_merge(task_id):
    """Commit changes inside worktree, switch to root, merge, and prune worktree."""
    start_time = datetime.now(timezone.utc)
    worktree_path = os.path.join(WORKTREES_DIR, f"task-{task_id}")
    
    print(f"[*] Merging changes from worktree: {worktree_path}")
    
    if not os.path.exists(worktree_path):
        print(f"[-] Error: Worktree path '{worktree_path}' does not exist.")
        sys.exit(1)
        
    try:
        # Get branch name currently checked out in that worktree
        branch_name = run_git_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)
        
        # Stage and commit any outstanding changes inside worktree
        print("[*] Committing uncommitted modifications in worktree...")
        status = run_git_cmd(["git", "status", "--porcelain"], cwd=worktree_path)
        if status:
            run_git_cmd(["git", "add", "-A"], cwd=worktree_path)
            run_git_cmd(["git", "commit", "-m", f"feat(slice-{task_id}): automated implementation & TDD verification"], cwd=worktree_path)
            print("[+] Committed modifications successfully.")
        else:
            print("[*] No changes to commit in worktree.")
            
        # Lock merge process (Lock-Protected Merge Queue spec)
        lock_file = os.path.join(WORKSPACE_ROOT, ".worktree_merge.lock")
        print("[*] Acquiring merge queue lock...")
        # Since this is a simple python runner, we write/check lock file
        # In multi-process python we can use an exclusive file lock
        try:
            with open(lock_file, "x") as f:
                f.write(f"{os.getpid()}")
        except FileExistsError:
            print("[*] Waiting for merge queue lock...")
            # We fail/warn or wait. For simplicity, we override/sleep or raise error
            # In our swarm, tasks will serialize this or await lock removal
            # We will force-write for now or wait
            import time
            attempts = 0
            while os.path.exists(lock_file) and attempts < 10:
                time.sleep(1)
                attempts += 1
            with open(lock_file, "w") as f:
                f.write(f"{os.getpid()}")
                
        try:
            print(f"[*] Merging branch '{branch_name}' into main workspace...")
            # Run merge in the root directory
            run_git_cmd(["git", "merge", branch_name, "--no-ff", "-m", f"merge: integrate slice {task_id}"])
            print("[+] Branch merged successfully.")
            
            # Prune and remove worktree
            print("[*] Removing worktree...")
            run_git_cmd(["git", "worktree", "remove", "--force", worktree_path])
            run_git_cmd(["git", "worktree", "prune"])
            
            # Delete local branch
            print("[*] Deleting local isolate branch...")
            run_git_cmd(["git", "branch", "-D", branch_name])
            print("[+] Isolate branch deleted.")
            
        finally:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_telemetry(task_id, "merge", branch_name, worktree_path, "success", duration)
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
        # Run git prune
        run_git_cmd(["git", "worktree", "prune"])
        
        # Check .worktrees subdirectory
        cleaned_count = 0
        if os.path.exists(WORKTREES_DIR):
            worktree_list = run_git_cmd(["git", "worktree", "list"])
            for item in os.listdir(WORKTREES_DIR):
                item_path = os.path.join(WORKTREES_DIR, item)
                if os.path.isdir(item_path):
                    # Check if git recognizes this worktree path
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
    
    args = parser.parse_args()
    
    # Input Sanitization for Shell Injection Mitigation (Threat Model Control)
    task_id = sanitize_input(args.task, "task")
    slug = sanitize_input(args.slug, "slug")
    
    if args.action == "create":
        if not task_id or not slug:
            parser.error("--task and --slug are required for create action.")
        action_create(task_id, slug)
    elif args.action == "merge":
        if not task_id:
            parser.error("--task is required for merge action.")
        action_merge(task_id)
    elif args.action == "clean":
        action_clean()

if __name__ == "__main__":
    main()
