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
import shutil
import tempfile
import unittest

from scripts.plan_lint import lint_plan


class TestPlanLint(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.plan_path = os.path.join(self.test_dir, "05_PLAN.md")
        self.prd_path = os.path.join(self.test_dir, "02_PRD.md")
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

        # Create contract file
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
        # Light plan
        content_light = """# Small Plan
- [ ] Step 1: Tiny update
*Target File:* src/helper.py
*Verification:* pytest tests/test_helper.py
"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(content_light)

        report_light = lint_plan(self.plan_path)
        self.assertEqual(report_light["recommended_tier"], "Light")

        # Full plan triggered by auth keyword
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

        # Create unused contract
        with open(os.path.join(self.contracts_dir, "orphan_schema.json"), "w") as f:
            f.write("{}")

        report = lint_plan(self.plan_path, contracts_dir=self.contracts_dir)
        self.assertTrue(report["valid"])  # warnings do not invalidate the plan
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


if __name__ == "__main__":
    unittest.main()
