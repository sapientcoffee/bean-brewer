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
Skill, Agent, and Hooks Schema Test Suite.
Validates all SKILL.md files in skills/, all agent markdown files in agents/,
and hooks.json in the repository root.
"""

import json
import os
import unittest
import yaml


FORBIDDEN_SKILL_STRINGS = (
    "thoughts/allison",
    "thoughts/",
    "allison/",
    "TodoWrite",
    "google_web_search",
    "run_shell_command",
    "03_EXTRACTION.md",
    "08_WALKTHROUGH.md",
)

VALID_AGENT_MODELS = {"inherit", "flash", "flash_lite", "pro"}

FORBIDDEN_LEGACY_TOOLS = {
    "run_shell_command",
    "list_directory",
    "grep_search",
    "replace",
    "glob",
    "search_file_content",
    "activate_skill",
}


def find_repo_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, ".."))


def parse_frontmatter(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        raise ValueError(f"{file_path} does not start with YAML frontmatter delimiter '---'")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{file_path} frontmatter delimiter '---' is invalid or not closed")
    data = yaml.safe_load(parts[1])
    return data, content


class TestSkillsSchema(unittest.TestCase):

    def setUp(self):
        self.repo_root = find_repo_root()
        self.skills_dir = os.path.join(self.repo_root, "skills")
        self.agents_dir = os.path.join(self.repo_root, "agents")
        self.hooks_path = os.path.join(self.repo_root, "hooks.json")

    def test_skills_directory_exists(self):
        self.assertTrue(os.path.exists(self.skills_dir), f"Skills directory not found at {self.skills_dir}")

    def test_all_skills_have_skill_md_and_valid_frontmatter(self):
        skill_folders = [
            d for d in os.listdir(self.skills_dir)
            if os.path.isdir(os.path.join(self.skills_dir, d)) and not d.startswith(".")
        ]
        self.assertGreater(len(skill_folders), 0, "No skill directories found under skills/")

        for skill_name in sorted(skill_folders):
            skill_folder_path = os.path.join(self.skills_dir, skill_name)
            skill_md_path = os.path.join(skill_folder_path, "SKILL.md")

            with self.subTest(skill=skill_name):
                self.assertTrue(
                    os.path.exists(skill_md_path),
                    f"Missing SKILL.md in skill directory: {skill_folder_path}"
                )

                data, content = parse_frontmatter(skill_md_path)
                self.assertIsInstance(
                    data, dict,
                    f"Frontmatter in {skill_md_path} must be a dictionary"
                )
                self.assertIn(
                    "name", data,
                    f"Frontmatter in {skill_md_path} missing required 'name' field"
                )
                self.assertIn(
                    "description", data,
                    f"Frontmatter in {skill_md_path} missing required 'description' field"
                )
                self.assertTrue(
                    data["name"],
                    f"'name' field in {skill_md_path} cannot be empty"
                )
                self.assertTrue(
                    data["description"],
                    f"'description' field in {skill_md_path} cannot be empty"
                )

                for forbidden in FORBIDDEN_SKILL_STRINGS:
                    self.assertNotIn(
                        forbidden,
                        content,
                        f"Forbidden legacy string '{forbidden}' found in {skill_md_path}"
                    )

    def test_all_agents_have_valid_frontmatter_and_tools(self):
        self.assertTrue(os.path.exists(self.agents_dir), f"Agents directory not found at {self.agents_dir}")
        agent_files = [
            f for f in os.listdir(self.agents_dir)
            if f.endswith(".md") and not f.startswith(".")
        ]
        self.assertEqual(len(agent_files), 9, f"Expected 9 agents in agents/, found {len(agent_files)}: {agent_files}")

        for agent_file in sorted(agent_files):
            agent_path = os.path.join(self.agents_dir, agent_file)
            with self.subTest(agent=agent_file):
                data, content = parse_frontmatter(agent_path)
                self.assertIsInstance(data, dict)
                self.assertEqual(data.get("kind"), "local", f"{agent_file} must have kind: local")
                self.assertIs(data.get("subagent"), True, f"{agent_file} must have subagent: true")
                self.assertIs(data.get("mainAgent"), False, f"{agent_file} must have mainAgent: false")
                self.assertIn(
                    data.get("model"),
                    VALID_AGENT_MODELS,
                    f"{agent_file} model '{data.get('model')}' not in {VALID_AGENT_MODELS}"
                )
                tools = data.get("tools", [])
                self.assertIsInstance(tools, list, f"{agent_file} tools must be a list")
                self.assertGreater(len(tools), 0, f"{agent_file} tools list cannot be empty")
                for tool in tools:
                    self.assertNotIn(
                        tool,
                        FORBIDDEN_LEGACY_TOOLS,
                        f"{agent_file} uses forbidden legacy tool '{tool}'"
                    )
                self.assertNotIn("gemini-3.1-pro-preview", content)

    def test_hooks_json_schema(self):
        self.assertTrue(os.path.exists(self.hooks_path), f"hooks.json not found at {self.hooks_path}")
        with open(self.hooks_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.assertIn("hooks", payload)
        hooks = payload["hooks"]
        self.assertIsInstance(hooks, dict)

        for flat_event in ("SessionStart", "Stop"):
            if flat_event in hooks:
                event_list = hooks[flat_event]
                self.assertIsInstance(event_list, list, f"{flat_event} must be a list")
                for entry in event_list:
                    self.assertIsInstance(entry, dict)
                    self.assertNotIn(
                        "matcher",
                        entry,
                        f"{flat_event} entries must be flat hook objects, not matcher wrappers"
                    )
                    self.assertEqual(entry.get("type"), "command")
                    self.assertTrue(entry.get("command"))
                    if "timeout" in entry:
                        self.assertLessEqual(entry["timeout"], 60, f"{flat_event} timeout must be in seconds (<= 60)")

        for matcher_event in ("PreToolUse", "PostToolUse"):
            if matcher_event in hooks:
                event_list = hooks[matcher_event]
                self.assertIsInstance(event_list, list, f"{matcher_event} must be a list")
                for group in event_list:
                    self.assertIsInstance(group, dict)
                    self.assertIn("matcher", group, f"{matcher_event} entry must have 'matcher'")
                    self.assertIn("hooks", group, f"{matcher_event} entry must have 'hooks' list")
                    for h in group["hooks"]:
                        self.assertEqual(h.get("type"), "command")
                        self.assertTrue(h.get("command"))
                        if "timeout" in h:
                            self.assertLessEqual(h["timeout"], 60, f"{matcher_event} timeout must be in seconds (<= 60)")


if __name__ == "__main__":
    unittest.main()
