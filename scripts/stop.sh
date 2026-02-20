#!/bin/bash
# VOLT Trading System - Stop Script

SESSION_NAME="volt"

echo "🛑 Stopping VOLT Trading System..."

# Kill TMUX session
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "📺 Killing TMUX session: $SESSION_NAME"
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null
fi

# Kill any remaining Python processes
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*webhook" 2>/dev/null || true
pkill -f "python.*start_webhook" 2>/dev/null || true

echo "✅ VOLT Trading System stopped!"
