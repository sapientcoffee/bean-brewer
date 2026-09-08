#!/usr/bin/env bash
# Copyright 2026 Google LLC
# Apache-2.0
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.gemini/config/plugins/bean-brewer"

echo "☕ Installing bean-brewer plugin..."
mkdir -p "${TARGET_DIR}"
cp -r "${SCRIPT_DIR}/plugin.json" "${TARGET_DIR}/"
cp -r "${SCRIPT_DIR}/gemini-extension.json" "${TARGET_DIR}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/bean-brewer.md" "${TARGET_DIR}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/skills" "${TARGET_DIR}/"
cp -r "${SCRIPT_DIR}/agents" "${TARGET_DIR}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/rules" "${TARGET_DIR}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/hooks" "${TARGET_DIR}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/hooks.json" "${TARGET_DIR}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/scripts" "${TARGET_DIR}/" 2>/dev/null || true

echo "✅ bean-brewer installed successfully to ${TARGET_DIR}."
