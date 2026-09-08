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

# --- Coffee Tip of the Day ---
tips=(
  "For the best flavor, use fresh beans roasted within the last 2 weeks."
  "The ideal water temperature for brewing is between 195°F and 205°F (90.5°C to 96°C)."
  "Store your coffee in an airtight, opaque container in a cool, dark place."
  "The grind size matters: coarse for French Press, fine for Espresso."
  "Always rinse your paper filters with hot water to remove any 'papery' taste."
)

# Pick a random tip
random_tip=${tips[$RANDOM % ${#tips[@]}]}

echo "## ☕ Coffee Tip of the Day"
echo "> $random_tip"
echo ""

# --- Git History ---
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "## 📜 Last 3 Commits"
    if git rev-parse HEAD > /dev/null 2>&1; then
        git log -n 3 --format="- %s"
    else
        echo "- (No commits yet)"
    fi
else
    echo "## 📜 Last 3 Commits"
    echo "- (Not a git repository)"
fi
echo "---"
