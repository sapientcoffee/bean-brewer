#!/bin/bash
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

# Hook to inject git status into the context
# This script runs before every prompt in the `gemini-cli-examples` context

# Reconcile and prune any dangling/orphaned git worktrees
python3 $(dirname "$0")/../scripts/worktree_manager.py --action clean >/dev/null 2>&1

echo "## Git Context"
echo "- **Branch:** $(git branch --show-current 2>/dev/null || echo 'Not a git repo')"
echo "- **Status:** $(git status --porcelain 2>/dev/null | wc -l) modified files"
echo "---"

