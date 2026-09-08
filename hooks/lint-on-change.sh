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

# Read the input from Gemini CLI via stdin
input=$(cat)

# Extract the file path using jq
# Use // empty to avoid "null" string
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# If file_path is empty, try 'path' (some tools use that)
if [ -z "$file_path" ] || [ "$file_path" == "null" ]; then
    file_path=$(echo "$input" | jq -r '.tool_input.path // empty')
fi

# Log the received path for debugging (to stderr)
echo "Hook received file_path: $file_path" >&2

# If the path is absolute, make it relative to GEMINI_PROJECT_DIR if possible
if [[ "$file_path" == /* ]] && [[ -n "$GEMINI_PROJECT_DIR" ]]; then
    file_path="${file_path#$GEMINI_PROJECT_DIR/}"
fi

# Also handle cases where file_path might start with ./
file_path="${file_path#./}"

# Check for specific files to run relevant commands
# If a config file changes, we might want to run a full lint across all packages
if [[ "$file_path" == "eslint.config.js" || "$file_path" == ".prettierrc" || "$file_path" == "package.json" ]]; then
    echo "Configuration file changed ($file_path). Running full lint..." >&2
    npx turbo lint -- --fix >&2
else
    # Determine the project from the file path and run the respective lint command
    case "$file_path" in
        apps/web/*)
            echo "File changed in web app ($file_path). Running ESLint with fix..." >&2
            npx turbo lint --filter=web -- --fix >&2
            ;;
        apps/workstations-api/*)
            echo "File changed in workstations-api ($file_path). Running ESLint with fix..." >&2
            npx turbo lint --filter=workstations-api -- --fix >&2
            ;;
        skills/*|scripts/*|tests/*)
            echo "Plugin skill/script/test file changed ($file_path). Running fast validation suite..." >&2
            python3 scripts/run_plugin_tests.py --fast >&2
            ;;
        scripts/*)
            echo "Shared script changed ($file_path). Running full lint..." >&2
            npx turbo lint -- --fix >&2
            ;;
        *)
            echo "File $file_path does not belong to a known workspace or has no lint setup." >&2
            ;;
    esac
fi

# Return a valid JSON object to stdout as required by the hook interface
echo '{"decision": "allow"}'
exit 0
