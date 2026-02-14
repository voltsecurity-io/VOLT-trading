#!/bin/bash
# Simple 12-hour test - Run in tmux/screen for persistence

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════"
echo "🚀 VOLT-Trading 12-Hour Test"
echo "════════════════════════════════════════════════════════════"
echo ""

# Activate venv
source .venv/bin/activate

# Create directories
mkdir -p logs reports

# Test metadata
END_TIME=$(date -d "+12 hours" +"%Y-%m-%d %H:%M:%S")
TEST_LOG="logs/12h_test_$(date +%Y%m%d_%H%M%S).log"

cat > reports/test_run_metadata.json << EOF
{
  "test_id": "12h_test_$(date +%Y%m%d_%H%M%S)",
  "start_time": "$(date +"%Y-%m-%d %H:%M:%S")",
  "end_time": "$END_TIME",
  "duration_hours": 12,
  "initial_capital": 20000,
  "currency": "SEK",
  "trading_mode": "testnet",
  "pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT"],
  "status": "running"
}
EOF

echo "✅ Starting 12-hour test..."
echo "   Log: $TEST_LOG"
echo "   End time: $END_TIME"
echo ""

# Start dashboard if not running
if ! pgrep -f "streamlit run dashboard" > /dev/null; then
    echo "📊 Starting dashboard..."
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run dashboard/app.py \
        --server.headless=true \
        --server.port=8501 \
        > logs/dashboard.log 2>&1 &
    sleep 3
    echo "✅ Dashboard: http://localhost:8501"
fi

echo ""
echo "🤖 Starting trading engine..."
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Run trading with output to both file and screen
python main.py 2>&1 | tee "$TEST_LOG"
