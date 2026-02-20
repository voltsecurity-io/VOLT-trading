#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p "$REPO_ROOT/logs"

LOCKFILE="$REPO_ROOT/.auto_report.lock"
if command -v flock &>/dev/null; then
    exec 9>"$LOCKFILE"
    flock -n 9 || exit 0
fi

PYTHON="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

"$PYTHON" scripts/generate_report.py >> "$REPO_ROOT/logs/auto_report.log" 2>&1

minute="$(date +%M)"
if [[ "$minute" == "00" ]]; then
    git add reports/ 2>/dev/null || true
    if ! git diff --cached --quiet; then
        git commit -m "Auto-save: $(date -Is)" 2>/dev/null || true
        git push origin master 2>/dev/null || true
        git push gitlab master 2>/dev/null || true
    fi
fi
