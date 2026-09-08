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

# Test suite for hooks/lint-on-change.sh

# Mocking npx to capture calls
MOCK_NPX_LOG=$(mktemp)
export MOCK_NPX_LOG

npx() {
    echo "npx $*" >> "$MOCK_NPX_LOG"
}
export -f npx

# Assertion helpers
assert_npx_called() {
    local expected=$1
    if ! grep -qxF "$expected" "$MOCK_NPX_LOG"; then
        echo "FAIL: npx command not found"
        echo "  Expected: $expected"
        echo "  Actual log content:"
        cat "$MOCK_NPX_LOG"
        exit 1
    fi
}

assert_npx_NOT_called() {
    local log_content
    log_content=$(cat "$MOCK_NPX_LOG")
    if [[ -s "$MOCK_NPX_LOG" ]]; then
        echo "FAIL: npx command was called but should not have been"
        echo "  Actual log content:"
        echo "$log_content"
        exit 1
    fi
}

clear_mock_log() {
    > "$MOCK_NPX_LOG"
}

# Test runner
run_test() {
    local name=$1
    local input=$2
    local project_dir=${3:-""}

    echo "Running test: $name..."
    clear_mock_log

    export GEMINI_PROJECT_DIR="$project_dir"
    local output
    output=$(printf '%s\n' "$input" | bash hooks/lint-on-change.sh)
    local exit_code=$?

    if [[ $exit_code -ne 0 ]]; then
        echo "FAIL: Script exited with code $exit_code"
        exit 1
    fi

    if [[ "$output" != '{"decision": "allow"}' ]]; then
        echo "FAIL: Unexpected output: $output"
        exit 1
    fi

    echo "  DONE"
}

# Cleanup on exit
trap 'rm -f "$MOCK_NPX_LOG"' EXIT

# --- Tests ---

# Configuration files
run_test "eslint.config.js change" '{"tool_input": {"file_path": "eslint.config.js"}}'
assert_npx_called "npx turbo lint -- --fix"

run_test ".prettierrc change" '{"tool_input": {"file_path": ".prettierrc"}}'
assert_npx_called "npx turbo lint -- --fix"

run_test "package.json change" '{"tool_input": {"file_path": "package.json"}}'
assert_npx_called "npx turbo lint -- --fix"

# Shared scripts
run_test "shared script change" '{"tool_input": {"file_path": "scripts/deploy.sh"}}'
assert_npx_called "npx turbo lint -- --fix"

# Workspace paths
run_test "web app change" '{"tool_input": {"file_path": "apps/web/src/index.ts"}}'
assert_npx_called "npx turbo lint --filter=web -- --fix"

run_test "workstations-api change" '{"tool_input": {"file_path": "apps/workstations-api/src/main.ts"}}'
assert_npx_called "npx turbo lint --filter=workstations-api -- --fix"

# JSON input variations
run_test "using 'path' instead of 'file_path'" '{"tool_input": {"path": "apps/web/src/App.tsx"}}'
assert_npx_called "npx turbo lint --filter=web -- --fix"

# Absolute path and GEMINI_PROJECT_DIR
run_test "absolute path with GEMINI_PROJECT_DIR" '{"tool_input": {"file_path": "/home/user/project/apps/web/src/index.ts"}}' "/home/user/project"
assert_npx_called "npx turbo lint --filter=web -- --fix"

run_test "path starting with ./" '{"tool_input": {"file_path": "./apps/web/src/index.ts"}}'
assert_npx_called "npx turbo lint --filter=web -- --fix"

# Unmatched file
run_test "unmatched file" '{"tool_input": {"file_path": "random/file.txt"}}'
assert_npx_NOT_called

echo "All tests passed!"
