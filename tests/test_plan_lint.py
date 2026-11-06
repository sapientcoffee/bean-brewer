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

"""Unit tests for scripts/plan_lint.py."""

import os
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.okf import stamp_file
from scripts.plan_lint import (
    check_sources_staleness,
    lint_plan,
    lint_plan_content,
    lint_spec_content,
    lint_spec_file,
)


class TestPlanLint(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.plan_path = os.path.join(self.test_dir, "05_PLAN.md")
        self.prd_path = os.path.join(self.test_dir, "02_PRD.md")
        self.spec_path = os.path.join(self.test_dir, "04_SPEC.md")
        self.contracts_dir = os.path.join(self.test_dir, "contracts")
        os.makedirs(self.contracts_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_plan_passes(self):
        content = """# Feature Plan
- [ ] Step 1: Define API Contract
*Target File:* contracts/api.json
*Verification:* pytest tests/test_contracts.py

- [ ] Step 2: Implement Handler
*Target File:* src/handler.py
*Depends On:* Step 1
*Verification:* pytest tests/test_handler.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        with open(os.path.join(self.contracts_dir, "api.json"), "w") as f:
            f.write("{}")

        report = lint_plan(self.plan_path, contracts_dir=self.contracts_dir)
        self.assertTrue(report["valid"])
        self.assertEqual(len(report["errors"]), 0)
        self.assertEqual(report["task_count"], 2)
        self.assertEqual(report["recommended_tier"], "Standard")

    def test_missing_tdd_verification_triggers_error(self):
        content = """# Plan Without TDD
- [ ] Step 1: Implement Business Logic
*Target File:* src/service.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        report = lint_plan(self.plan_path)
        self.assertFalse(report["valid"])
        error_codes = [e["code"] for e in report["errors"]]
        self.assertIn("TDD_MISSING_VERIFICATION", error_codes)

    def test_circular_dependency_triggers_error(self):
        content = """# Circular Plan
- [ ] Step 1: Task One
*Target File:* src/a.py
*Verification:* pytest tests/test_a.py
*Depends On:* Step 2

- [ ] Step 2: Task Two
*Target File:* src/b.py
*Verification:* pytest tests/test_b.py
*Depends On:* Step 1
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        report = lint_plan(self.plan_path)
        self.assertFalse(report["valid"])
        error_codes = [e["code"] for e in report["errors"]]
        self.assertIn("CIRCULAR_DEPENDENCY", error_codes)

    def test_missing_dependency_triggers_error(self):
        content = """# Missing Dep Plan
- [ ] Step 1: Task One
*Target File:* src/a.py
*Verification:* pytest tests/test_a.py
*Depends On:* Step 99
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        report = lint_plan(self.plan_path)
        self.assertFalse(report["valid"])
        error_codes = [e["code"] for e in report["errors"]]
        self.assertIn("MISSING_DEPENDENCY", error_codes)

    def test_risk_tier_evaluation_light_vs_full(self):
        content_light = """# Small Plan
- [ ] Step 1: Tiny update
*Target File:* src/helper.py
*Verification:* pytest tests/test_helper.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content_light)

        report_light = lint_plan(self.plan_path)
        self.assertEqual(report_light["recommended_tier"], "Light")

        content_full = """# Auth Migration Plan
- [ ] Step 1: Update Auth Provider and Session Token
*Target File:* src/auth.py
*Verification:* pytest tests/test_auth.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content_full)

        report_full = lint_plan(self.plan_path)
        self.assertEqual(report_full["recommended_tier"], "Full")

    def test_unreferenced_contract_warning(self):
        content = """# Feature Plan
- [ ] Step 1: Implement Service
*Target File:* src/service.py
*Verification:* pytest tests/test_service.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        with open(os.path.join(self.contracts_dir, "orphan_schema.json"), "w") as f:
            f.write("{}")

        report = lint_plan(self.plan_path, contracts_dir=self.contracts_dir)
        self.assertTrue(report["valid"])
        warn_codes = [w["code"] for w in report["warnings"]]
        self.assertIn("UNREFERENCED_CONTRACT_FILE", warn_codes)

    def test_unmapped_prd_story_warning(self):
        content = """# Plan
- [ ] Step 1: Implement Service
*Target File:* src/service.py
*Verification:* pytest tests/test_service.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        with open(self.prd_path, "w", encoding="utf-8") as f:
            f.write("# PRD\n\n### User Story US-101: User Login\nMust allow login.")

        report = lint_plan(self.plan_path, prd_path=self.prd_path)
        self.assertTrue(report["valid"])
        warn_codes = [w["code"] for w in report["warnings"]]
        self.assertIn("UNMAPPED_PRD_REQUIREMENT", warn_codes)

    def test_empty_plan_fails(self):
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write("# Empty Plan\nNo tasks here.")

        report = lint_plan(self.plan_path)
        self.assertFalse(report["valid"])
        err_codes = [e["code"] for e in report["errors"]]
        self.assertIn("NO_TASKS_FOUND", err_codes)

    def test_lint_spec_content_flags_brittle_file_paths(self):
        clean_spec = """# 04_SPEC.md: Authentication Architecture
We expose the `TokenVerifier` interface and validate JWT claims against `contracts/auth.json`.
"""
        clean_res = lint_spec_content(clean_spec)
        self.assertTrue(clean_res["valid"])
        self.assertEqual(clean_res["flagged_paths"], [])

        brittle_spec = """# 04_SPEC.md: Authentication Architecture
Modify `src/auth/token_service.ts` and `app/models/user.py` to add column checks.
"""
        brittle_res = lint_spec_content(brittle_spec)
        self.assertFalse(brittle_res["valid"])
        self.assertIn("src/auth/token_service.ts", brittle_res["flagged_paths"])
        self.assertIn("app/models/user.py", brittle_res["flagged_paths"])
        codes = [e["code"] for e in brittle_res["errors"]]
        self.assertIn("SPEC_BRITTLE_FILE_PATH", codes)

    def test_check_sources_staleness_detects_upstream_modification(self):
        prd_p = Path(self.test_dir) / "03_PRD.md"
        prd_p.write_text("# PRD v1\n- **AC1**: Initial requirement\n", encoding="utf-8")

        spec_p = Path(self.spec_path)
        spec_p.write_text("# Spec v1\nArchitecture overview.\n", encoding="utf-8")
        stamp_file(
            file_path=spec_p,
            okf_type="spec",
            stage="4_spec",
            by="bean-brewer/to-spec",
            sources=["03_PRD.md"],
            bundle_dir=Path(self.test_dir),
        )

        # Freshly stamped -> valid, not stale
        fresh = check_sources_staleness(spec_p)
        self.assertTrue(fresh["valid"])
        self.assertFalse(fresh["stale"])

        # Mutate upstream 03_PRD.md after 04_SPEC.md was stamped
        prd_p.write_text("# PRD v2 (mutated)\n- **AC1**: Changed requirement\n", encoding="utf-8")
        stale = check_sources_staleness(spec_p)
        self.assertFalse(stale["valid"])
        self.assertTrue(stale["stale"])
        self.assertIn("03_PRD.md", stale["stale_sources"])
        self.assertEqual(stale["errors"][0]["code"], "STALE_SOURCE_SHA256")


if __name__ == "__main__":
    unittest.main()
