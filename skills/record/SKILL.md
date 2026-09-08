---
name: record
description: Record terminal interactions and compile them to animated GIFs. Use during walkthroughs or on-demand recording sessions.
---

<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->


# Asciinema Terminal Recording Skill

This skill allows agents to programmatically record terminal sessions, type out scenarios character-by-character, and render them as beautiful, high-quality animated `.gif` and `.cast` files.

## 🔑 Parameters & Flags

When invoking this skill, parse any command flags or arguments requested:
*   `--scenario <path>`: Path to a scenario JSON file for automated playback.
*   `--output <path>`: Optional destination path (without extension) for the recording.
*   `--upload`: Optional flag to upload the session recording to asciinema.org.

Execute the record orchestration script using python3:
```bash
python3 scripts/record.py [flags]
```
(Substitute any parsed flags into the bash execution). Confirm output file generation and display paths of the raw `.cast` file and rendered `.gif` file to the user.

## 1. Automated Playback Scenarios

When you need to record a repeatable walkthrough, construct a JSON scenario file.

### 1.1 Scenario Schema
Save your scenario file (e.g. `walkthrough_scenario.json`) inside the active feature's plan directory. Use the following schema:

```json
{
  "prompt": "agy ☕ ",
  "steps": [
    {
      "type": "comment",
      "text": "# Let's compile and validate the plugin",
      "delay": 1.0,
      "speed": 0.04
    },
    {
      "type": "command",
      "text": "agy plugin validate .",
      "delay": 2.0,
      "speed": 0.04
    }
  ]
}
```

*   `prompt`: (String, Optional) The terminal prompt displayed to the left of commands. Defaults to `agy ☕ `.
*   `steps`: (Array of Objects) The steps to execute sequentially.
    *   `type`: Must be `"comment"` (animated text output with trailing newline) or `"command"` (animated text output followed by sub-process execution).
    *   `text`: The commentary or shell command to run.
    *   `delay`: (Float, Optional) Time in seconds to pause after execution/printing. Defaults to `1.0`.
    *   `speed`: (Float, Optional) Delay in seconds between individual keystrokes during typing animation. Defaults to `0.04`.

---

## 2. Running the Recording

Trigger the terminal recording engine using the `record` CLI command.

### 2.1 Contextual Recording (Stage 8 Walkthrough)
When recording a verification walkthrough for an active Brew:
1.  Save the scenario JSON file to the Brew's plan directory:
    `plans/feature/<brew-timestamp-slug>/walkthrough_scenario.json`.
2.  Execute the CLI command targeting that plan folder:
    ```bash
    agy record --scenario plans/feature/<timestamp-slug>/walkthrough_scenario.json --output plans/feature/<timestamp-slug>/walkthrough
    ```
3.  Once complete, embed the resulting `.gif` asset directly inside your `08_WALKTHROUGH.md` report using a relative path:
    ```markdown
    ![Walkthrough Demo](plans/feature/timestamp/walkthrough.gif)
    ```
4.  Stage all generated files (`.cast`, `.gif`, `.json`) in Git:
    ```bash
    git add plans/feature/<brew-timestamp-slug>/
    ```

### 2.2 Standalone On-Demand Recording
To capture arbitrary interactive terminal sessions:
1.  Run the CLI command without scenario flags:
    ```bash
    agy record --output docs/recordings/my-interactive-demo
    ```
2.  Type your commands inside the spawned shell.
3.  Type `exit` or press `Ctrl-D` to complete recording and auto-compile the `.gif`.
