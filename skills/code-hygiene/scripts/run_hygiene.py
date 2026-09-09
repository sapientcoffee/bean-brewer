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
Deterministic Non-LLM Code Hygiene Runner.
Runs local linters, type checkers, and security scanners (eslint, ruff,
cargo check, gitleaks, mypy) and emits concise exit-code summaries.
"""

import argparse
import os
import shutil
import subprocess
import sys

TOOLS = [
    {
        "name": "ruff",
        "cmd": ["ruff", "check", "."],
        "indicator": lambda cwd: any(os.path.exists(os.path.join(cwd, f)) for f in ["pyproject.toml", "ruff.toml", ".ruff.toml"]) or any(f.endswith(".py") for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))),
    },
    {
        "name": "mypy",
        "cmd": ["mypy", "."],
        "indicator": lambda cwd: any(os.path.exists(os.path.join(cwd, f)) for f in ["mypy.ini", "setup.cfg", "pyproject.toml"]),
    },
    {
        "name": "eslint",
        "cmd": ["npx", "eslint", "."],
        "indicator": lambda cwd: any(os.path.exists(os.path.join(cwd, f)) for f in ["eslint.config.js", ".eslintrc.json", ".eslintrc.js", "package.json"]),
    },
    {
        "name": "cargo check",
        "cmd": ["cargo", "check"],
        "indicator": lambda cwd: os.path.exists(os.path.join(cwd, "Cargo.toml")),
    },
    {
        "name": "gitleaks",
        "cmd": ["gitleaks", "detect", "--no-banner", "--redact"],
        "indicator": lambda cwd: os.path.exists(os.path.join(cwd, ".git")),
    },
]


def run_tool(tool_info: dict, cwd: str) -> dict:
    name = tool_info["name"]
    cmd = tool_info["cmd"]

    # Check if primary executable exists
    exe = cmd[0]
    if not shutil.which(exe):
        return {"name": name, "status": "SKIPPED", "exit_code": None, "detail": f"Executable '{exe}' not found in PATH"}

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        status = "PASSED" if proc.returncode == 0 else "FAILED"
        first_line = (proc.stderr or proc.stdout).strip().splitlines()
        detail = first_line[0] if first_line else "Clean"
        return {"name": name, "status": status, "exit_code": proc.returncode, "detail": detail[:80]}
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "TIMED_OUT", "exit_code": -1, "detail": "Execution exceeded 120s"}
    except Exception as e:
        return {"name": name, "status": "ERROR", "exit_code": -1, "detail": str(e)[:80]}


def main():
    parser = argparse.ArgumentParser(description="Deterministic Code Hygiene Runner")
    parser.add_argument("--cwd", default=".", help="Target working directory")
    parser.add_argument("--all", action="store_true", help="Run all available tools regardless of indicator")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)
    results = []
    any_failed = False

    print(f"[code-hygiene] Scanning directory: {cwd}\n")
    print(f"{'Tool':<15} | {'Status':<10} | {'Exit Code':<10} | {'Detail'}")
    print("-" * 65)

    for tool in TOOLS:
        if args.all or tool["indicator"](cwd):
            res = run_tool(tool, cwd)
            results.append(res)
            code_str = str(res["exit_code"]) if res["exit_code"] is not None else "-"
            print(f"{res['name']:<15} | {res['status']:<10} | {code_str:<10} | {res['detail']}")
            if res["status"] in ("FAILED", "ERROR", "TIMED_OUT"):
                any_failed = True

    print("-" * 65)
    if not results:
        print("[code-hygiene] No matching linters/scanners detected for this project.")
        sys.exit(0)

    if any_failed:
        print("[code-hygiene] ❌ One or more hygiene checks failed.")
        sys.exit(1)
    else:
        print("[code-hygiene] ✅ All active hygiene checks passed cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
