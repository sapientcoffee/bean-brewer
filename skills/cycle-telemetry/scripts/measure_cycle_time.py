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
Cycle Telemetry ("Chess Clock") Measurement Tool.
Records active agent compute latency vs human waiting time and outputs
structured metrics to JSON and 07_VERIFICATION.md.
"""

import argparse
import datetime
import json
import os
import sys
import time

VALID_EVENTS = {
    "agent_exec_start",
    "agent_exec_end",
    "human_wait_start",
    "human_wait_end",
}


def load_telemetry(telemetry_file: str) -> dict:
    if os.path.exists(telemetry_file):
        try:
            with open(telemetry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "events": [],
        "metrics": {
            "total_agent_compute_seconds": 0.0,
            "total_human_wait_seconds": 0.0,
            "event_count": 0,
        },
    }


def save_telemetry(telemetry_file: str, data: dict):
    os.makedirs(os.path.dirname(os.path.abspath(telemetry_file)), exist_ok=True)
    with open(telemetry_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def compute_metrics(events: list) -> dict:
    agent_compute = 0.0
    human_wait = 0.0
    last_agent_start = None
    last_human_start = None

    for ev in events:
        name = ev.get("event")
        ts = ev.get("timestamp", 0.0)
        if name == "agent_exec_start":
            last_agent_start = ts
        elif name == "agent_exec_end":
            if last_agent_start is not None and ts >= last_agent_start:
                agent_compute += (ts - last_agent_start)
                last_agent_start = None
        elif name == "human_wait_start":
            last_human_start = ts
        elif name == "human_wait_end":
            if last_human_start is not None and ts >= last_human_start:
                human_wait += (ts - last_human_start)
                last_human_start = None

    total = agent_compute + human_wait
    compute_ratio = (agent_compute / total * 100.0) if total > 0 else 0.0

    return {
        "total_agent_compute_seconds": round(agent_compute, 2),
        "total_human_wait_seconds": round(human_wait, 2),
        "total_cycle_seconds": round(total, 2),
        "compute_ratio_pct": round(compute_ratio, 1),
        "event_count": len(events),
    }


def format_markdown_summary(metrics: dict) -> str:
    return (
        "## ⏱️ Cycle Telemetry (Velocity Chess Clock)\n\n"
        "| Metric | Value |\n"
        "| :--- | :--- |\n"
        f"| **Active Agent Compute** | `{metrics['total_agent_compute_seconds']}s` |\n"
        f"| **Human Wait Duration** | `{metrics['total_human_wait_seconds']}s` |\n"
        f"| **Total Cycle Latency** | `{metrics['total_cycle_seconds']}s` |\n"
        f"| **Compute / Total Ratio** | `{metrics['compute_ratio_pct']}%` |\n"
    )


def append_to_verification_file(verif_file: str, markdown_block: str):
    if not os.path.exists(verif_file):
        return
    with open(verif_file, "r", encoding="utf-8") as f:
        content = f.read()

    marker = "## ⏱️ Cycle Telemetry (Velocity Chess Clock)"
    if marker in content:
        parts = content.split(marker)
        remainder = parts[1]
        next_header_pos = remainder.find("\n## ")
        if next_header_pos != -1:
            after = remainder[next_header_pos:]
        else:
            after = ""
        new_content = parts[0].rstrip() + "\n\n" + markdown_block.strip() + "\n" + after.lstrip()
    else:
        new_content = content.rstrip() + "\n\n" + markdown_block

    with open(verif_file, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    parser = argparse.ArgumentParser(description="Velocity Cycle Telemetry measurement CLI")
    subparsers = parser.add_subparsers(dest="command")

    log_parser = subparsers.add_parser("log", help="Log an execution timestamp event")
    log_parser.add_argument("--event", required=True, choices=list(VALID_EVENTS), help="Event name")
    log_parser.add_argument("--plan-dir", default=".", help="Target plan directory")
    log_parser.add_argument("--timestamp", type=float, default=None, help="Explicit epoch timestamp")

    report_parser = subparsers.add_parser("report", help="Generate summary report and sync to 07_VERIFICATION.md")
    report_parser.add_argument("--plan-dir", default=".", help="Target plan directory")
    report_parser.add_argument("--verification-file", default=None, help="Path to 07_VERIFICATION.md")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    plan_dir = os.path.abspath(args.plan_dir)
    telemetry_file = os.path.join(plan_dir, "cycle_telemetry.json")
    data = load_telemetry(telemetry_file)

    if args.command == "log":
        now_ts = args.timestamp if args.timestamp is not None else time.time()
        iso_str = datetime.datetime.fromtimestamp(now_ts, datetime.timezone.utc).isoformat()
        event_entry = {
            "event": args.event,
            "timestamp": now_ts,
            "iso": iso_str,
        }
        data["events"].append(event_entry)
        data["metrics"] = compute_metrics(data["events"])
        save_telemetry(telemetry_file, data)
        print(f"[cycle-telemetry] Logged {args.event} at {iso_str}")

        verif_file = os.path.join(plan_dir, "07_VERIFICATION.md")
        if os.path.exists(verif_file):
            summary = format_markdown_summary(data["metrics"])
            append_to_verification_file(verif_file, summary)

    elif args.command == "report":
        metrics = compute_metrics(data["events"])
        data["metrics"] = metrics
        save_telemetry(telemetry_file, data)
        summary = format_markdown_summary(metrics)
        print(summary)

        verif_file = args.verification_file or os.path.join(plan_dir, "07_VERIFICATION.md")
        if os.path.exists(verif_file):
            append_to_verification_file(verif_file, summary)
            print(f"[cycle-telemetry] Appended metrics to {verif_file}")


if __name__ == "__main__":
    main()
