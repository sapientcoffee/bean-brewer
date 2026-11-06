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
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for skill_script_dir in (
    os.path.join(REPO_ROOT, "skills", "plan-council", "scripts"),
    os.path.join(REPO_ROOT, "skills", "cycle-telemetry", "scripts"),
):
    if skill_script_dir not in sys.path:
        sys.path.insert(0, skill_script_dir)

from council_loop import (  # noqa: E402
    COUNCIL_PERSONAS,
    JUDGE_MODELS,
    JUDGES_PER_AREA,
    TIER_REVIEWERS,
    aggregate_area_judges,
    compute_consensus_score,
    get_judges_for_tier,
    get_reviewers_for_tier,
    normalize_judge_model,
    parse_reviewer_payload,
    run_council_round,
    validate_evidence,
)
from measure_cycle_time import compute_metrics  # noqa: E402


class TestCouncilLoop(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.plan_path = os.path.join(self.test_dir, "05_PLAN.md")
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write("# Sample Plan\n- [ ] Step 1: Init\n*Target File:* src/app.py\n*Verification:* pytest\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tier_reviewers_uses_code_inspection(self):
        self.assertIn("code-inspection", COUNCIL_PERSONAS)
        self.assertNotIn("auditor", COUNCIL_PERSONAS)
        for tier in ("Light", "Standard", "Full"):
            self.assertIn("@code-inspection", TIER_REVIEWERS[tier])
            self.assertNotIn("@auditor", TIER_REVIEWERS[tier])
            self.assertIn("code-inspection", get_reviewers_for_tier(tier))

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
  "persona": "code-inspection",
  "status": "CHANGES_REQUESTED",
  "findings": [{"id": "AUD-01", "severity": "HIGH", "description": "Missing test"}]
}
```
"""
        parsed = parse_reviewer_payload(raw, "code-inspection")
        self.assertEqual(parsed["persona"], "code-inspection")
        self.assertEqual(len(parsed["findings"]), 1)

    def test_validate_evidence_citations(self):
        f1 = {"quote": "Step 1: Init implementation", "description": "Issue"}
        valid1, _ = validate_evidence(f1)
        self.assertTrue(valid1)

        f2 = {"description": "Task references `src/app.py` directly without test"}
        valid2, _ = validate_evidence(f2)
        self.assertTrue(valid2)

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

        with open(result["report_path"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Stage 6A: Plan Review Council Report", content)
        self.assertIn("Decisions Requiring Human Judgment", content)
        self.assertIn("Arbiter Hardening Proposals for `@architect`", content)
        self.assertIn("Stakeholder Consensus Scorecard", content)
        self.assertIn("@code-inspection", content)

    def test_critical_finding_triggers_revision_and_proposal(self):
        findings_data = {
            "code-inspection": {
                "persona": "code-inspection",
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
        with open(findings_file, "w", encoding="utf-8") as f:
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
        with open(findings_file, "w", encoding="utf-8") as f:
            json.dump(findings_data, f)

        result = run_council_round(
            plan_path=self.plan_path,
            tier="Full",
            round_number=3,
            findings_file=findings_file,
        )
        self.assertEqual(result["verdict"], "CIRCUIT_BREAKER_TRIGGERED")
        with open(result["report_path"], "r", encoding="utf-8") as f:
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

    def test_judge_models_and_tier_panel_sizing(self):
        self.assertEqual(JUDGES_PER_AREA, 3)
        self.assertEqual(
            [m["name"] for m in JUDGE_MODELS],
            ["opus", "argon", "flash-3.8"],
        )
        self.assertEqual(normalize_judge_model("claude-opus"), "opus")
        self.assertEqual(normalize_judge_model("gemini-4-argon"), "argon")
        self.assertEqual(normalize_judge_model("gemini-3.8-flash"), "flash-3.8")
        self.assertEqual(normalize_judge_model("flash 3.8"), "flash-3.8")

        light_judges = get_judges_for_tier("Light")
        std_judges = get_judges_for_tier("Standard")
        full_judges = get_judges_for_tier("Full")
        self.assertEqual(len(light_judges), 6)
        self.assertEqual(len(std_judges), 9)
        self.assertEqual(len(full_judges), 12)
        for j in full_judges:
            self.assertIn("persona", j)
            self.assertIn("judge_id", j)
            self.assertIn("model", j)
            self.assertIn("display_model", j)
            self.assertIn("subagent_model", j)

    def test_aggregate_area_judges_deduplicates_high_and_critical_findings(self):
        judge_payloads = [
            {
                "model": "opus",
                "findings": [
                    {
                        "id": "AUD-CRIT-1",
                        "severity": "CRITICAL",
                        "quote": "Step 1: Init without verification",
                        "target_task": "Step 1",
                        "description": "Missing verification seam on init",
                        "recommendation": "Add SEAM-01 test",
                    }
                ],
            },
            {
                "model": "argon",
                "findings": [
                    {
                        "id": "AUD-CRIT-1",
                        "severity": "HIGH",
                        "quote": "Step 1: Init without verification",
                        "target_task": "Step 1",
                        "description": "Missing verification seam on init",
                        "recommendation": "Add SEAM-01 test",
                    },
                    {
                        "id": "AUD-HIGH-SOLO",
                        "severity": "HIGH",
                        "quote": "Step 2: Unchecked contract",
                        "target_task": "Step 2",
                        "description": "Missing contract validation",
                        "recommendation": "Validate contract schema",
                    },
                ],
            },
            {
                "model": "flash-3.8",
                "findings": [
                    {
                        "id": "AUD-CRIT-1",
                        "severity": "CRITICAL",
                        "quote": "Step 1: Init without verification",
                        "target_task": "Step 1",
                        "description": "Missing verification seam on init",
                        "recommendation": "Add SEAM-01 test",
                    }
                ],
            },
        ]
        agg = aggregate_area_judges("code-inspection", judge_payloads)
        self.assertEqual(len(agg["findings"]), 2)
        by_id = {f["id"]: f for f in agg["findings"]}
        self.assertEqual(by_id["AUD-CRIT-1"]["severity"], "CRITICAL")
        self.assertEqual(by_id["AUD-CRIT-1"]["judge_count"], 3)
        self.assertEqual(by_id["AUD-CRIT-1"]["agreement"], "3/3")
        self.assertEqual(by_id["AUD-CRIT-1"]["judges"], ["argon", "flash-3.8", "opus"])
        self.assertEqual(by_id["AUD-HIGH-SOLO"]["judge_count"], 1)
        self.assertEqual(by_id["AUD-HIGH-SOLO"]["agreement"], "1/3")

    def test_aggregate_area_judges_quorum_filters_single_judge_medium_and_low(self):
        judge_payloads = [
            {
                "model": "opus",
                "findings": [
                    {
                        "id": "MED-QUORUM",
                        "severity": "MEDIUM",
                        "quote": "Step 1: Init",
                        "target_task": "Step 1",
                        "description": "Suboptimal retry backoff in Step 1",
                    },
                    {
                        "id": "LOW-NOISE",
                        "severity": "LOW",
                        "quote": "Target File: src/app.py",
                        "target_task": "Step 1",
                        "description": "Nitpick variable naming",
                    },
                ],
            },
            {
                "model": "argon",
                "findings": [
                    {
                        "id": "MED-QUORUM",
                        "severity": "MEDIUM",
                        "quote": "Step 1: Init",
                        "target_task": "Step 1",
                        "description": "Suboptimal retry backoff in Step 1",
                    }
                ],
            },
            {
                "model": "flash-3.8",
                "findings": [],
            },
        ]
        agg = aggregate_area_judges("code-inspection", judge_payloads)
        self.assertEqual(len(agg["findings"]), 1)
        self.assertEqual(agg["findings"][0]["id"], "MED-QUORUM")
        self.assertEqual(agg["findings"][0]["agreement"], "2/3")
        self.assertEqual(len(agg["filtered_minority_findings"]), 1)
        self.assertEqual(agg["filtered_minority_findings"][0]["id"], "LOW-NOISE")

    def test_run_council_round_with_three_judge_panel_and_colon_keys(self):
        findings_data = {
            "code-inspection": {
                "judges": [
                    {
                        "model": "opus",
                        "findings": [
                            {
                                "id": "CRIT-SHARED",
                                "severity": "CRITICAL",
                                "quote": "Step 1: Init",
                                "target_task": "Step 1",
                                "description": "Critical issue reported by all 3 judges",
                                "recommendation": "Fix Step 1",
                            },
                            {
                                "id": "MED-NOISE",
                                "severity": "MEDIUM",
                                "quote": "Verification: pytest",
                                "target_task": "Step 1",
                                "description": "Single judge medium nit",
                            },
                        ],
                    },
                    {
                        "model": "argon",
                        "findings": [
                            {
                                "id": "CRIT-SHARED",
                                "severity": "CRITICAL",
                                "quote": "Step 1: Init",
                                "target_task": "Step 1",
                                "description": "Critical issue reported by all 3 judges",
                                "recommendation": "Fix Step 1",
                            }
                        ],
                    },
                    {
                        "model": "flash-3.8",
                        "findings": [
                            {
                                "id": "CRIT-SHARED",
                                "severity": "CRITICAL",
                                "quote": "Step 1: Init",
                                "target_task": "Step 1",
                                "description": "Critical issue reported by all 3 judges",
                                "recommendation": "Fix Step 1",
                            }
                        ],
                    },
                ]
            },
            "contract-auditor:opus": {
                "findings": [
                    {
                        "id": "MED-2OF3",
                        "severity": "MEDIUM",
                        "quote": "Target File: src/app.py",
                        "target_task": "Step 1",
                        "description": "Missing schema field",
                    }
                ]
            },
            "contract-auditor:argon": {
                "findings": [
                    {
                        "id": "MED-2OF3",
                        "severity": "MEDIUM",
                        "quote": "Target File: src/app.py",
                        "target_task": "Step 1",
                        "description": "Missing schema field",
                    }
                ]
            },
            "contract-auditor:flash-3.8": {
                "findings": []
            },
        }
        findings_file = os.path.join(self.test_dir, "panel_findings.json")
        with open(findings_file, "w", encoding="utf-8") as f:
            json.dump(findings_data, f)

        result = run_council_round(
            plan_path=self.plan_path,
            tier="Standard",
            round_number=1,
            findings_file=findings_file,
        )
        # 1 CRITICAL (-25) + 1 MEDIUM (-3) = 72.0 (MED-NOISE is filtered out, CRIT-SHARED counted once)
        self.assertEqual(result["consensus_score"], 72.0)
        self.assertEqual(result["matrix"]["judges_per_area"], 3)
        self.assertEqual(result["matrix"]["judge_models"], ["opus", "argon", "flash-3.8"])
        ci_summary = result["matrix"]["reviewer_summary"]["code-inspection"]
        self.assertEqual(ci_summary["critical"], 1)
        self.assertEqual(ci_summary["medium"], 0)
        self.assertEqual(ci_summary["filtered_minority_count"], 1)


if __name__ == "__main__":
    unittest.main()
