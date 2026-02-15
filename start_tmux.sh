#!/bin/bash
# VOLT Trading System - tmux Startup Script
# Creates a professional multi-pane trading environment

SESSION_NAME="volt"
VOLT_DIR="/home/omarchy/VOLT-trading"

# Check if session already exists
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Session '$SESSION_NAME' already exists. Attaching..."
    tmux attach-session -t $SESSION_NAME
    exit 0
fi

echo "Creating VOLT Trading session..."

# Create new session with detached mode
tmux new-session -d -s $SESSION_NAME -c $VOLT_DIR

# Window 1: Main Trading
tmux rename-window -t $SESSION_NAME:1 "Trading"
tmux send-keys -t $SESSION_NAME:1 "cd $VOLT_DIR && python main.py" C-m

# Window 2: Webhook Server (for TradingView)
tmux new-window -t $SESSION_NAME -n "Webhook"
tmux send-keys -t $SESSION_NAME:2 "cd $VOLT_DIR && python start_webhook_server.py" C-m

# Window 3: Monitoring/Dashboard
tmux new-window -t $SESSION_NAME -n "Monitor"
tmux send-keys -t $SESSION_NAME:3 "cd $VOLT_DIR && watch -n 5 'curl -s http://localhost:8080/status | python -m json.tool'" C-m

# Window 4: Ollama/LLM
tmux new-window -t $SESSION_NAME -n "LLM"
tmux send-keys -t $SESSION_NAME:4 "watch -n 10 'ollama list'" C-m

# Window 5: Logs
tmux new-window -t $SESSION_NAME -n "Logs"
tmux send-keys -t $SESSION_NAME:5 "tail -f $VOLT_DIR/logs/volt.log" C-m

# Go back to first window
tmux select-window -t $SESSION_NAME:1

# Attach to session
echo "Starting tmux session..."
tmux attach-session -t $SESSION_NAME
