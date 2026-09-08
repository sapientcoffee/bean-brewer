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

import argparse
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request

def find_binary(name):
    """Finds a binary in system PATH or local cached bin directory."""
    path = shutil.which(name)
    if path:
        return path
    local_path = os.path.join(".agents", "bin", name)
    if os.path.exists(local_path) and os.access(local_path, os.X_OK):
        return os.path.abspath(local_path)
    return None

def download_agg():
    """Programmatically fetches the official pre-compiled AGG binary if missing."""
    bin_dir = os.path.abspath(os.path.join(".agents", "bin"))
    os.makedirs(bin_dir, exist_ok=True)
    agg_path = os.path.join(bin_dir, "agg")

    if os.path.exists(agg_path) and os.access(agg_path, os.X_OK):
        return agg_path

    machine = platform.machine().lower()
    if "x86_64" in machine or "amd64" in machine:
        url = "https://github.com/asciinema/agg/releases/download/v1.4.3/agg-x86_64-unknown-linux-gnu"
    elif "aarch64" in machine or "arm64" in machine:
        url = "https://github.com/asciinema/agg/releases/download/v1.4.3/agg-aarch64-unknown-linux-gnu"
    else:
        print(f"[-] Unsupported architecture for auto-download: {machine}. Skipping AGG auto-download.")
        return None

    print(f"[*] Downloading AGG static compiler from {url}...")
    try:
        # Avoid standard SSL cert check blocks on some environments if needed, but default first
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            with open(agg_path, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
        os.chmod(agg_path, 0o755)
        print(f"[+] AGG static binary successfully saved to {agg_path}")
        return agg_path
    except Exception as e:
        print(f"[-] Failed to download AGG binary: {e}")
        if os.path.exists(agg_path):
            try:
                os.remove(agg_path)
            except Exception:
                pass
        return None

def main():
    parser = argparse.ArgumentParser(description="Brew: Asciinema Terminal Recorder")
    parser.add_argument("--scenario", help="Path to scenario JSON file for automated typing playback")
    parser.add_argument("--output", help="Output file path (without extension; will output .cast and .gif)")
    parser.add_argument("--upload", action="store_true", help="Upload resulting .cast to asciinema.org")
    parser.add_argument("--theme", default="dracula", help="Select GIF color theme (dracula, monokai, solarized-dark, solarized-light, asciinema) [default: dracula]")

    args = parser.parse_args()

    # Validate Asciinema is available
    asciinema_bin = find_binary("asciinema")
    if not asciinema_bin:
        sys.stderr.write("[-] Error: 'asciinema' CLI tool is not installed on this system.\n")
        sys.stderr.write("    Please install it using your package manager (e.g. 'sudo apt install asciinema').\n")
        sys.exit(1)

    # Determine paths
    default_name = f"recording_{int(time.time())}"
    
    if args.output:
        # Standardize so output has directory path resolved
        base_path = os.path.abspath(args.output)
    else:
        base_path = os.path.abspath(os.path.join("docs", "recordings", default_name))

    os.makedirs(os.path.dirname(base_path), exist_ok=True)
    cast_path = f"{base_path}.cast"
    gif_path = f"{base_path}.gif"

    # Resolve dependencies
    tmux_bin = find_binary("tmux")
    agg_bin = find_binary("agg")
    if not agg_bin:
        agg_bin = download_agg()

    # Determine execution strategy
    if args.scenario:
        scenario_abs = os.path.abspath(args.scenario)
        if not os.path.exists(scenario_abs):
            sys.stderr.write(f"[-] Error: Scenario file {scenario_abs} does not exist.\n")
            sys.exit(1)

        playback_script = os.path.abspath(os.path.join("scripts", "playback.py"))

        if tmux_bin:
            print("[*] TMUX detected. Spawning isolated 100x30 containerized recording...")
            
            # Generate a highly descriptive, unique, and sanitized TMUX session name based on the scenario filename
            scenario_base = os.path.splitext(os.path.basename(scenario_abs))[0]
            if scenario_base.endswith("_scenario"):
                scenario_base = scenario_base[:-9]
            clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in scenario_base)
            session_name = f"agy-record-{clean_name}"
            
            # Ensure no stale TMUX session exists with this name before starting
            subprocess.run([tmux_bin, "kill-session", "-t", session_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Safely escape paths for the shell command executed by asciinema's -c flag
            playback_cmd = f"python3 {shlex.quote(playback_script)} {shlex.quote(scenario_abs)}"
            
            # Start detached tmux session with standard 100x30 resolution, setting TERM directly
            tmux_cmd = [
                tmux_bin, "new-session", "-d", "-s", session_name, "-x", "100", "-y", "30",
                "env", "TERM=xterm-256color", asciinema_bin, "rec", "--overwrite", "-c", playback_cmd, cast_path
            ]
            
            subprocess.run(tmux_cmd, check=True)

            # Poll tmux session until complete
            print(f"[*] Recording terminal actions programmatically inside TMUX session '{session_name}'. Please wait...")
            while True:
                poll_cmd = [tmux_bin, "has-session", "-t", session_name]
                res = subprocess.run(poll_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode != 0:
                    break
                time.sleep(0.5)

            print("[+] Recording completed.")
        else:
            print("[!] TMUX not found. Running fallback direct PTY recording (Window sizing will match host)...")
            recording_cmd = [
                asciinema_bin, "rec", "--overwrite", "-c", f"python3 {shlex.quote(playback_script)} {shlex.quote(scenario_abs)}", cast_path
            ]
            subprocess.run(recording_cmd, check=True)
    else:
        # Interactive mode
        print("[*] Entering interactive recording mode.")
        print("    Type 'exit' or hit 'Ctrl-D' to finish recording.")
        
        if tmux_bin:
            session_name = f"agy-record-interactive-{int(time.time()) % 10000:04d}"
            interactive_cmd = [
                asciinema_bin, "rec", "-c", f"{tmux_bin} new-session -A -s {session_name}", cast_path
            ]
        else:
            interactive_cmd = [asciinema_bin, "rec", cast_path]
            
        subprocess.run(interactive_cmd, check=True)
        print("[+] Interactive recording saved.")

    # Verification of cast output
    if not os.path.exists(cast_path) or os.path.getsize(cast_path) == 0:
        sys.stderr.write("[-] Error: Raw .cast file was not generated or is empty.\n")
        sys.exit(1)

    print(f"[+] Raw session saved: {cast_path}")

    # Compile to GIF if AGG compiler is available
    if agg_bin:
        print(f"[*] Compiling .cast to animated GIF using {agg_bin} (Theme: {args.theme})...")
        try:
            compile_cmd = [agg_bin, "--theme", args.theme, cast_path, gif_path]
            subprocess.run(compile_cmd, check=True)
            print(f"[+] Premium visual compiled: {gif_path}")
        except Exception as e:
            sys.stderr.write(f"[-] Failed to compile GIF using AGG: {e}\n")
    else:
        print("[!] AGG compiler is missing. Skipping local GIF rendering.")
        print("    To compile manually, upload your .cast to asciinema.org or run 'agg'.")

    # Handle Upload Flag
    if args.upload:
        print("[*] Uploading session to asciinema.org...")
        try:
            upload_cmd = [asciinema_bin, "upload", cast_path]
            res = subprocess.run(upload_cmd, capture_output=True, text=True, check=True)
            print("[+] Upload successful!")
            print(res.stdout)
        except Exception as e:
            sys.stderr.write(f"[-] Failed to upload cast: {e}\n")

if __name__ == "__main__":
    main()
