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

"""Unit tests for Stage 6A Plan Council loop and arbitration."""

import json
import os
import shutil
import tempfile
import unittest

from scripts.measure_cycle_time import compute_metrics
from scripts.council_loop import (
    compute_consensus_score,
    parse_reviewer_payload,
    run_council_round,
    validate_evidence,
)


class TestCouncilLoop(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.plan_path = os.path.join(self.test_dir, "05_PLAN.md")
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write("# Sample Plan\n- [ ] Step 1: Init\n*Target File:* src/app.py\n*Verification:* pytest\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_consensus_score_formula(self):
        self.assertEqual(compute_consensus_score(0, 0, 0, 0), 100.0)
        self.assertEqual(compute_consensus_score(1, 0, 0, 0), 75.0)
        self.assertEqual(compute_consensus_score(0, 1, 0, 0), 90.0)
        self.assertEqual(compute_consensus_score(1, 1, 1, 1), 61.0)
        self.assertEqual(compute_consensus_score(5, 5, 0, 0), 0.0)

    def test_parse_reviewer_payload_json_block(self):
        raw = """Here are findings:
```json
{
  "persona": "auditor",
  "status": "CHANGES_REQUESTED",
  "findings": [{"id": "AUD-01", "severity": "HIGH", "description": "Missing test"}]
}
```
"""
        parsed = parse_reviewer_payload(raw, "auditor")
        self.assertEqual(parsed["persona"], "auditor")
        self.assertEqual(len(parsed["findings"]), 1)

    def test_validate_evidence_citations(self):
        # Explicit quote
        f1 = {"quote": "Step 1: Init implementation", "description": "Issue"}
        valid1, _ = validate_evidence(f1)
        self.assertTrue(valid1)

        # Backticked quote in description
        f2 = {"description": "Task references `src/app.py` directly without test"}
        valid2, _ = validate_evidence(f2)
        self.assertTrue(valid2)

        # No evidence
        f3 = {"description": "I feel this might be wrong"}
        valid3, _ = validate_evidence(f3)
        self.assertFalse(valid3)

    def test_clean_round_converges(self):
        result = run_council_round(
            plan_path=self.plan_path,
            tier="Standard",
            round_number=1,
            simulate=True,
        )
        self.assertEqual(result["verdict"], "CONVERGED_ROBUST")
        self.assertEqual(result["consensus_score"], 100.0)
        self.assertTrue(os.path.exists(result["report_path"]))
        self.assertTrue(os.path.exists(result["matrix_path"]))

        # Verify content contains required sections
        with open(result["report_path"], "r") as f:
            content = f.read()
        self.assertIn("Stage 6A: Plan Review Council Report", content)
        self.assertIn("Decisions Requiring Human Judgment", content)
        self.assertIn("Arbiter Hardening Proposals for `@architect`", content)
        self.assertIn("Stakeholder Consensus Scorecard", content)

    def test_critical_finding_triggers_revision_and_proposal(self):
        findings_data = {
            "auditor": {
                "persona": "auditor",
                "status": "CHANGES_REQUESTED",
                "findings": [
                    {
                        "id": "AUD-CRIT-1",
                        "severity": "CRITICAL",
                        "quote": "Step 1: Init without verification",
                        "target_task": "Step 1",
                        "description": "Critical regression risk on app initialization",
                        "recommendation": "Add integration test fixture before proceeding",
                    }
                ],
            }
        }
        findings_file = os.path.join(self.test_dir, "findings.json")
        with open(findings_file, "w") as f:
            json.dump(findings_data, f)

        result = run_council_round(
            plan_path=self.plan_path,
            tier="Full",
            round_number=1,
            findings_file=findings_file,
        )
        self.assertEqual(result["verdict"], "NEEDS_REVISION")
        self.assertEqual(result["consensus_score"], 75.0)
        self.assertEqual(len(result["matrix"]["proposals"]), 1)
        self.assertEqual(result["matrix"]["proposals"][0]["architect_disposition"], "PENDING")

    def test_round_three_trips_circuit_breaker(self):
        findings_data = {
            "threat-modeler": {
                "persona": "threat-modeler",
                "status": "CHANGES_REQUESTED",
                "findings": [
                    {
                        "id": "SEC-01",
                        "severity": "HIGH",
                        "quote": "Step 1: Unauthenticated endpoint",
                        "description": "Missing auth boundary check",
                    }
                ],
            }
        }
        findings_file = os.path.join(self.test_dir, "findings.json")
        with open(findings_file, "w") as f:
            json.dump(findings_data, f)

        result = run_council_round(
            plan_path=self.plan_path,
            tier="Full",
            round_number=3,
            findings_file=findings_file,
        )
        self.assertEqual(result["verdict"], "CIRCUIT_BREAKER_TRIGGERED")
        with open(result["report_path"], "r") as f:
            content = f.read()
        self.assertIn("Circuit Breaker Tripped", content)

    def test_cycle_telemetry_includes_council_seconds(self):
        events = [
            {"event": "council_exec_start", "timestamp": 100.0},
            {"event": "council_exec_end", "timestamp": 125.0},
            {"event": "agent_exec_start", "timestamp": 200.0},
            {"event": "agent_exec_end", "timestamp": 250.0},
            {"event": "human_wait_start", "timestamp": 300.0},
            {"event": "human_wait_end", "timestamp": 320.0},
        ]
        metrics = compute_metrics(events)
        self.assertEqual(metrics["total_council_review_seconds"], 25.0)
        self.assertEqual(metrics["total_agent_compute_seconds"], 50.0)
        self.assertEqual(metrics["total_human_wait_seconds"], 20.0)
        self.assertEqual(metrics["total_cycle_seconds"], 95.0)


if __name__ == "__main__":
    unittest.main()
