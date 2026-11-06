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
Hooks, Scripts, and JSON Configuration Validation Test Suite.
Validates JSON configuration files, shell script syntax, Python bytecode compilation,
and canonical script placement.
"""

import json
import os
import py_compile
import subprocess
import sys
import unittest


def find_repo_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, ".."))


class TestHooksAndScripts(unittest.TestCase):

    def setUp(self):
        self.repo_root = find_repo_root()

    def test_json_configuration_files_are_valid(self):
        json_files = ["plugin.json", "hooks.json", "gemini-extension.json"]
        for j_file in json_files:
            file_path = os.path.join(self.repo_root, j_file)
            if os.path.exists(file_path):
                with self.subTest(file=j_file):
                    with open(file_path, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                            self.assertIsNotNone(data, f"{j_file} parsed as None")
                        except Exception as e:
                            self.fail(f"Invalid JSON syntax in {j_file}: {e}")

    def test_shell_scripts_syntax(self):
        shell_scripts = []
        for search_dir in ["hooks", "scripts"]:
            d_path = os.path.join(self.repo_root, search_dir)
            if os.path.exists(d_path):
                for root, _, files in os.walk(d_path):
                    for file in files:
                        if file.endswith(".sh"):
                            shell_scripts.append(os.path.join(root, file))

        self.assertGreater(len(shell_scripts), 0, "No shell scripts found for syntax validation")

        for sh_script in shell_scripts:
            rel_path = os.path.relpath(sh_script, self.repo_root)
            with self.subTest(script=rel_path):
                res = subprocess.run(["bash", "-n", sh_script], capture_output=True, text=True)
                self.assertEqual(
                    res.returncode, 0,
                    f"Syntax error in shell script {rel_path}: {res.stderr}"
                )

    def test_python_scripts_compilation(self):
        python_scripts = []
        for search_dir in ["scripts", "skills", "tests"]:
            d_path = os.path.join(self.repo_root, search_dir)
            if os.path.exists(d_path):
                for root, _, files in os.walk(d_path):
                    for file in files:
                        if file.endswith(".py"):
                            python_scripts.append(os.path.join(root, file))

        self.assertGreater(len(python_scripts), 0, "No Python scripts found for compilation test")

        for py_script in python_scripts:
            rel_path = os.path.relpath(py_script, self.repo_root)
            with self.subTest(script=rel_path):
                try:
                    py_compile.compile(py_script, doraise=True)
                except Exception as e:
                    self.fail(f"Python compilation failed for {rel_path}: {e}")

    def test_canonical_scripts_exist_and_duplicates_removed(self):
        canonical_paths = [
            os.path.join("scripts", "promote.py"),
            os.path.join("scripts", "gh_resolve_reviews.py"),
            os.path.join("scripts", "plan_lint.py"),
            os.path.join("scripts", "worktree_manager.py"),
            os.path.join("scripts", "okf.py"),
            os.path.join("skills", "plan-council", "scripts", "council_loop.py"),
            os.path.join("skills", "cycle-telemetry", "scripts", "measure_cycle_time.py"),
        ]
        for rel in canonical_paths:
            full = os.path.join(self.repo_root, rel)
            self.assertTrue(os.path.exists(full), f"Canonical script missing at {rel}")

        obsolete_duplicates = [
            os.path.join("scripts", "council_loop.py"),
            os.path.join("scripts", "measure_cycle_time.py"),
            os.path.join("scripts", "immunize_harness.py"),
            os.path.join("scripts", "sync.py"),
            os.path.join("scripts", "sync_dashboard_if_available.py"),
        ]
        for rel in obsolete_duplicates:
            full = os.path.join(self.repo_root, rel)
            self.assertFalse(os.path.exists(full), f"Obsolete duplicate script should be removed: {rel}")


if __name__ == "__main__":
    unittest.main()
