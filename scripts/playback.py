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

import json
import os
import pty
import subprocess
import sys
import time

def simulate_typing(text, speed=0.04):
    """Animates typing character-by-character to standard output."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Add slight variation to make typing feel organic
        time.sleep(speed)

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python3 playback.py <scenario_json>\n")
        sys.exit(1)

    scenario_path = sys.argv[1]
    if not os.path.exists(scenario_path):
        sys.stderr.write(f"Error: Scenario file {scenario_path} not found.\n")
        sys.exit(1)

    with open(scenario_path, "r", encoding="utf-8") as f:
        try:
            scenario = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Error parsing JSON: {e}\n")
            sys.exit(1)

    prompt = scenario.get("prompt", "agy ☕ ")
    steps = scenario.get("steps", [])

    # Print the initial prompt
    sys.stdout.write(prompt)
    sys.stdout.flush()

    for step in steps:
        step_type = step.get("type")
        delay = float(step.get("delay", 1.0))
        speed = float(step.get("speed", 0.04))

        if step_type == "comment":
            # For comments, type out the commentary line
            comment_text = step.get("text", "")
            simulate_typing(comment_text, speed)
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(delay)
            # Re-print prompt after a comment
            sys.stdout.write(prompt)
            sys.stdout.flush()

        elif step_type == "command":
            # Type out the command line
            command_text = step.get("text", "")
            simulate_typing(command_text, speed)
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(0.5) # Quick pause before hitting Enter execution

            # Execute the command inside a pseudo-terminal (PTY) to preserve colors and formatting
            master, slave = pty.openpty()
            process = subprocess.Popen(
                command_text,
                shell=True,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                close_fds=True,
                env=os.environ
            )
            os.close(slave)

            # Set master to non-blocking mode
            import fcntl
            fl = fcntl.fcntl(master, fcntl.F_GETFL)
            fcntl.fcntl(master, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            inputs = step.get("inputs", [])
            start_time = time.time()
            input_idx = 0
            last_input_time = start_time
            inputs_finished_time = None

            while True:
                # Check if process has terminated
                if process.poll() is not None:
                    # Read any remaining output
                    while True:
                        try:
                            data = os.read(master, 1024)
                            if not data:
                                break
                            sys.stdout.buffer.write(data)
                            sys.stdout.buffer.flush()
                        except OSError:
                            break
                    break

                # Try to read from master (non-blocking)
                try:
                    data = os.read(master, 1024)
                    if data:
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                except OSError:
                    pass

                # Check if we have input to send
                if input_idx < len(inputs):
                    current_input = inputs[input_idx]
                    delay_before = float(current_input.get("delay_before", 1.0))
                    text_to_send = current_input.get("text", "")
                    speed = float(current_input.get("speed", 0.04))

                    if time.time() - last_input_time >= delay_before:
                        # Simulate typing this input directly into the PTY master!
                        for char in text_to_send:
                            os.write(master, char.encode('utf-8'))
                            # Read any echoed back or output characters to display them immediately
                            try:
                                data = os.read(master, 1024)
                                if data:
                                    sys.stdout.buffer.write(data)
                                    sys.stdout.buffer.flush()
                            except OSError:
                                pass
                            time.sleep(speed)

                        input_idx += 1
                        last_input_time = time.time()
                        if input_idx >= len(inputs):
                            inputs_finished_time = time.time()

                # If all inputs are finished, wait and terminate process
                if inputs_finished_time is not None:
                    wait_after_last = float(step.get("delay", 5.0))
                    if time.time() - inputs_finished_time >= wait_after_last:
                        process.terminate()

                time.sleep(0.01) # Sleep a tiny bit to prevent 100% CPU spinning

            process.wait()
            os.close(master)
            time.sleep(delay)
            # Print prompt for the next step (or trailing empty line)
            sys.stdout.write(prompt)
            sys.stdout.flush()

    # Clear trailing line gracefully
    sys.stdout.write("\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
