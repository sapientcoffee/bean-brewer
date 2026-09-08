#!/usr/bin/env python3
# Copyright 2026 Google LLC
# Apache-2.0
"""
Opportunistic Dashboard Sync Helper.
Attempts to find manage_dashboard.py from bean-cup. If present, runs it.
If not present, silently exits 0 so this repository remains 100% self-contained.
"""
import os
import sys
import subprocess

CANDIDATES = [
    os.path.expanduser("~/.gemini/config/plugins/bean-cup/skills/visual-dashboard/scripts/manage_dashboard.py"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "bean-cup", "skills", "visual-dashboard", "scripts", "manage_dashboard.py")),
    os.path.expanduser("~/.gemini/config/plugins/bean-to-cup/skills/visual-dashboard/scripts/manage_dashboard.py"),
]

def main():
    dashboard_script = None
    for cand in CANDIDATES:
        if os.path.exists(cand):
            dashboard_script = cand
            break

    if dashboard_script:
        args = sys.argv[1:]
        if args and args[0].startswith("--"):
            args = ["auto-sync"] + args
        cmd = [sys.executable, dashboard_script] + args
        try:
            res = subprocess.run(cmd)
            sys.exit(res.returncode)
        except Exception as e:
            print(f"Notice: Dashboard sync skipped ({e})")
            sys.exit(0)
    else:
        # bean-cup is not installed, exit 0 cleanly
        sys.exit(0)

if __name__ == "__main__":
    main()
