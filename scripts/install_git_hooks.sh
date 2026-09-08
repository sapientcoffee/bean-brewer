#!/usr/bin/env bash
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

# Opt-in Git Pre-Commit Hook Installer for Bean-to-Cup Plugin

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_HOOKS_DIR="${REPO_ROOT}/.git/hooks"
PRE_COMMIT_HOOK="${GIT_HOOKS_DIR}/pre-commit"

if [ ! -d "${GIT_HOOKS_DIR}" ]; then
    echo "Error: .git/hooks directory not found at ${GIT_HOOKS_DIR}"
    exit 1
fi

echo "Installing opt-in git pre-commit hook..."

cat << 'EOF' > "${PRE_COMMIT_HOOK}"
#!/usr/bin/env bash
# Bean-to-Cup Pre-Commit Verification Hook
echo "☕ Running Bean-to-Cup pre-commit schema & unit tests..."
python3 scripts/run_plugin_tests.py --fast
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit test verification failed! Commit aborted."
    exit 1
fi
echo "🟢 Pre-commit tests passed."
EOF

chmod +x "${PRE_COMMIT_HOOK}"

echo "✅ Git pre-commit hook successfully installed at ${PRE_COMMIT_HOOK}"
