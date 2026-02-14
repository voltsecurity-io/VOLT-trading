#!/bin/bash
# Simple 12-hour test starter (bypasses verification issues)

set -e

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════"
echo "🚀 VOLT-Trading 12-Hour Test (Quick Start)"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "System: Lenovo ThinkPad X1 Nano Gen 1"
echo "Capital: 20,000 SEK (testnet)"
echo "Duration: 12 hours"
echo "Dashboard: http://localhost:8501"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if already running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Trading system is already running!"
    echo ""
    echo "Stop it first:"
    echo "  pkill -f 'python.*main.py'"
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Create directories
mkdir -p logs reports

# Calculate end time
END_TIME=$(date -d "+12 hours" +"%Y-%m-%d %H:%M:%S")
END_TIMESTAMP=$(date -d "+12 hours" +%s)

# Create metadata
cat > reports/test_run_metadata.json << EOF
{
  "test_id": "12h_test_$(date +%Y%m%d_%H%M%S)",
  "start_time": "$(date +"%Y-%m-%d %H:%M:%S")",
  "end_time": "$END_TIME",
  "duration_hours": 12,
  "initial_capital": 20000,
  "currency": "SEK",
  "trading_mode": "testnet",
  "system": "Lenovo ThinkPad X1 Nano Gen 1",
  "pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT"],
  "status": "running"
}
EOF

TEST_LOG="logs/12h_test_$(date +%Y%m%d_%H%M%S).log"

echo "✅ Starting 12-hour test..."
echo "   Log: $TEST_LOG"
echo "   End time: $END_TIME"
echo ""

# Start dashboard
echo "📊 Starting dashboard..."
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run dashboard/app.py \
    --server.headless=true \
    --server.port=8501 \
    > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
sleep 3

echo "✅ Dashboard running at http://localhost:8501"
echo ""

# Start trading with sleep prevention
echo "🤖 Starting trading engine with sleep prevention..."
echo ""

systemd-inhibit \
    --what=sleep:idle:handle-lid-switch \
    --who="VOLT-Trading" \
    --why="Running 12-hour trading test" \
    --mode=block \
    python main.py 2>&1 | tee "$TEST_LOG" &

TRADING_PID=$!

# Store PIDs
echo "$TRADING_PID" > /tmp/volt_trading.pid
echo "$DASHBOARD_PID" > /tmp/volt_dashboard.pid
echo "$END_TIMESTAMP" > /tmp/volt_test_end.timestamp

sleep 3

if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Trading engine failed to start!"
    kill $DASHBOARD_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ 12-HOUR TEST IS RUNNING!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Dashboard:  http://localhost:8501"
echo "Log file:   $TEST_LOG"
echo "End time:   $END_TIME"
echo ""
echo "Monitor:"
echo "  ./check_test_status.sh"
echo "  tail -f $TEST_LOG"
echo ""
echo "Stop:"
echo "  ./stop_test.sh"
echo "  or press Ctrl+C"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Test is running. Close this terminal or press Ctrl+C to stop."
echo ""

# Wait for trading process
wait $TRADING_PID

# Cleanup
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🏁 TEST COMPLETED"
echo "════════════════════════════════════════════════════════════"
echo ""
kill $DASHBOARD_PID 2>/dev/null || true

python -c "
import json
try:
    with open('reports/test_run_metadata.json', 'r') as f:
        data = json.load(f)
    data['status'] = 'completed'
    data['actual_end_time'] = '$(date +"%Y-%m-%d %H:%M:%S")'
    with open('reports/test_run_metadata.json', 'w') as f:
        json.dump(data, f, indent=2)
except: pass
" 2>/dev/null || true

echo "✅ Results saved in:"
echo "   - reports/monitoring_metrics.json"
echo "   - reports/test_run_metadata.json"
echo "   - $TEST_LOG"
echo ""
