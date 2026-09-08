#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="${HOME}/.gemini/config/plugins/bean-brewer"
echo "🗑️  Removing ${TARGET_DIR}..."
python3 -c "import shutil, os; p = os.path.expanduser('~/.gemini/config/plugins/bean-brewer'); shutil.rmtree(p) if os.path.exists(p) else None"
echo "✅ Uninstalled bean-brewer."
