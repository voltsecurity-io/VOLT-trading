#!/bin/bash
# VOLT Trading System - Startup Script
# Usage: ./scripts/start.sh [options]
# Options: --dryrun (default), --live

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

MODE="${1:-dryrun}"

echo "========================================"
echo "  VOLT Trading System - Starting"
echo "========================================"
echo "Project: $PROJECT_DIR"
echo "Mode: $MODE"
echo "Time: $(date)"
echo "========================================"

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️ .env file not found, copying from .env.example"
    cp .env.example .env
    echo "⚠️ Please configure .env with your API keys!"
fi

# Check required environment variables
if [ -z "$OLLAMA_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ Warning: No LLM API key configured (OLLAMA_API_KEY or OPENAI_API_KEY)"
fi

# Kill any existing trading processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*webhook" 2>/dev/null || true

# Start TMUX session
SESSION_NAME="volt"

# Check if session exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "📺 Attaching to existing TMUX session: $SESSION_NAME"
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
fi

echo "📺 Creating new TMUX session..."
tmux new-session -d -s "$SESSION_NAME"

# Window 1: Main Trading Engine
tmux rename-window -t "$SESSION_NAME:1" "Trading"
tmux send-keys -t "$SESSION_NAME:1" "cd $PROJECT_DIR && source .env 2>/dev/null && python main.py" C-m

sleep 2

# Window 2: Webhook Server (for external triggers)
tmux rename-window -t "$SESSION_NAME:2" "Webhook"
tmux send-keys -t "$SESSION_NAME:2" "cd $PROJECT_DIR && source .env 2>/dev/null && python start_webhook_server.py" C-m

sleep 1

# Window 3: Monitoring Dashboard
tmux rename-window -t "$SESSION_NAME:3" "Monitor"
tmux send-keys -t "$SESSION_NAME:3" "watch -n 5 'curl -s http://localhost:8080/status | python -m json.tool'" C-m

sleep 1

# Window 4: Logs
tmux rename-window -t "$SESSION_NAME:4" "Logs"
tmux send-keys -t "$SESSION_NAME:4" "tail -f logs/volt_trading.log" C-m

sleep 1

echo ""
echo "✅ VOLT Trading System started!"
echo "========================================"
echo "TMUX Session: $SESSION_NAME"
echo ""
echo "Windows:"
echo "  1: Trading     - Main trading engine"
echo "  2: Webhook     - Webhook server (port 8080)"
echo "  3: Monitor     - Live status monitoring"
echo "  4: Logs        - Real-time logs"
echo ""
echo "Commands:"
echo "  tmux attach -t $SESSION_NAME    # Attach to session"
echo "  ./scripts/stop.sh              # Stop system"
echo "  ./scripts/status.sh            # Check status"
echo "========================================"
