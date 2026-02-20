#!/bin/bash
# Auto-report loop for tmux
# Run this in a separate tmux pane: ./scripts/auto_report_loop.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔄 Starting auto-report loop (every 15 min)..."
echo "   Log: $REPO_ROOT/logs/auto_report_loop.log"
echo "   Press Ctrl+C to stop"
echo ""

while true; do
    echo "--- $(date) ---"
    ./scripts/auto_report.sh >> "$REPO_ROOT/logs/auto_report_loop.log" 2>&1
    echo "   Next run in 15 minutes..."
    sleep 900
done
