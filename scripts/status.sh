#!/bin/bash
# VOLT Trading System - Status Script

SESSION_NAME="volt"

echo "========================================"
echo "  VOLT Trading System - Status"
echo "========================================"
echo "Time: $(date)"
echo ""

# Check TMUX session
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "📺 TMUX Session: ✅ Running"
    echo ""
    echo "Windows:"
    tmux list-windows -t "$SESSION_NAME" 2>/dev/null | while read line; do
        echo "  $line"
    done
else
    echo "📺 TMUX Session: ❌ Not running"
fi

echo ""

# Check processes
if pgrep -f "python.*main.py" > /dev/null; then
    echo "🤖 Trading Engine: ✅ Running"
else
    echo "🤖 Trading Engine: ❌ Not running"
fi

if pgrep -f "python.*webhook" > /dev/null; then
    echo "🌐 Webhook Server: ✅ Running"
else
    echo "🌐 Webhook Server: ❌ Not running"
fi

echo ""

# Check API status
echo "📡 API Status:"
if curl -s --max-time 2 http://localhost:8080/status > /dev/null 2>&1; then
    echo "  HTTP Server: ✅ Responding"
    curl -s --max-time 2 http://localhost:8080/status 2>/dev/null | python -m json.tool 2>/dev/null | head -10 || true
else
    echo "  HTTP Server: ❌ Not responding"
fi

echo ""
echo "========================================"
