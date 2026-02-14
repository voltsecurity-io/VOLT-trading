#!/bin/bash
# VOLT-Trading 12-Hour Test Run
# Prevents laptop sleep and runs full trading test

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "🚀 VOLT-Trading 12-Hour Test Run"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}System: Lenovo ThinkPad X1 Nano Gen 1${NC}"
echo -e "${BLUE}Capital: 20,000 SEK (testnet)${NC}"
echo -e "${BLUE}Duration: 12 hours${NC}"
echo -e "${BLUE}Dashboard: http://localhost:8501${NC}"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if already running
if pgrep -f "python.*main.py" > /dev/null; then
    echo -e "${RED}❌ Trading system is already running!${NC}"
    echo ""
    echo "Stop it first with:"
    echo "  python control.py stop"
    exit 1
fi

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    exit 1
fi

source .venv/bin/activate

# Create necessary directories
mkdir -p logs reports

# Check dependencies
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
python -c "import ccxt, pandas, numpy, streamlit, psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install -q -r requirements.txt
fi
echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Verify API keys
echo -e "${YELLOW}🔐 Verifying API keys...${NC}"
source .venv/bin/activate
python verify_api_keys.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API key verification failed!${NC}"
    echo ""
    echo "Run API key verification:"
    echo "  source .venv/bin/activate && python verify_api_keys.py"
    echo ""
    echo "Or setup keys:"
    echo "  ./setup_api_keys.sh"
    exit 1
fi
echo -e "${GREEN}✓ API keys verified${NC}"
echo ""

# Calculate end time (12 hours from now)
END_TIME=$(date -d "+12 hours" +"%Y-%m-%d %H:%M:%S")
END_TIMESTAMP=$(date -d "+12 hours" +%s)

# Create test run metadata
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

echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Pre-flight checks complete!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}Test will run until: $END_TIME${NC}"
echo ""
echo "Starting in 5 seconds..."
echo "  - Trading Engine"
echo "  - Dashboard"
echo "  - Sleep Prevention"
echo "  - System Monitor"
echo ""
sleep 5

# Create log file for this test run
TEST_LOG="logs/12h_test_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$TEST_LOG") 2>&1

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 STARTING 12-HOUR TEST RUN"
echo "════════════════════════════════════════════════════════════"
echo ""

# Start dashboard in background (detached)
echo -e "${YELLOW}📊 Starting dashboard...${NC}"
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run dashboard/app.py \
    --server.headless=true \
    --server.port=8501 \
    > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
sleep 3

# Verify dashboard started
if ! pgrep -f "streamlit run" > /dev/null; then
    echo -e "${RED}❌ Dashboard failed to start!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dashboard running (PID: $DASHBOARD_PID)${NC}"
echo -e "${GREEN}  → http://localhost:8501${NC}"
echo ""

# Prevent laptop sleep using systemd-inhibit (works on Arch Linux)
echo -e "${YELLOW}⚡ Preventing system sleep...${NC}"

# Start trading engine with systemd-inhibit to prevent sleep
systemd-inhibit \
    --what=sleep:idle:handle-lid-switch \
    --who="VOLT-Trading" \
    --why="Running 12-hour trading test" \
    --mode=block \
    python main.py &

TRADING_PID=$!
sleep 3

# Verify trading started
if ! pgrep -f "python.*main.py" > /dev/null; then
    echo -e "${RED}❌ Trading engine failed to start!${NC}"
    kill $DASHBOARD_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ Trading engine running (PID: $TRADING_PID)${NC}"
echo -e "${GREEN}✓ System sleep DISABLED${NC}"
echo ""

# Store PIDs for monitoring
echo "$TRADING_PID" > /tmp/volt_trading.pid
echo "$DASHBOARD_PID" > /tmp/volt_dashboard.pid
echo "$END_TIMESTAMP" > /tmp/volt_test_end.timestamp

echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ 12-HOUR TEST RUN ACTIVE!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}Dashboard:${NC}  http://localhost:8501"
echo -e "${BLUE}Test Log:${NC}   $TEST_LOG"
echo -e "${BLUE}End Time:${NC}   $END_TIME"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 MONITORING"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "View live metrics:"
echo "  watch -n 10 'cat reports/monitoring_metrics.json | python -m json.tool'"
echo ""
echo "View logs:"
echo "  tail -f $TEST_LOG"
echo ""
echo "View system stats:"
echo "  htop -p $TRADING_PID"
echo ""
echo "Check status:"
echo "  ./check_test_status.sh"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🛑 TO STOP TEST EARLY"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  ./stop_test.sh"
echo ""
echo "Or manually:"
echo "  kill $TRADING_PID $DASHBOARD_PID"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Test is now running. Check dashboard at http://localhost:8501${NC}"
echo ""
echo "This terminal will continue to show the trading engine output."
echo "Press Ctrl+C to stop the test."
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Monitor and wait
wait $TRADING_PID

# Cleanup when done
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🏁 TEST RUN COMPLETED"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Stopping dashboard..."
kill $DASHBOARD_PID 2>/dev/null || true

# Update metadata
python -c "
import json
with open('reports/test_run_metadata.json', 'r') as f:
    data = json.load(f)
data['status'] = 'completed'
data['actual_end_time'] = '$(date +"%Y-%m-%d %H:%M:%S")'
with open('reports/test_run_metadata.json', 'w') as f:
    json.dump(data, f, indent=2)
"

echo -e "${GREEN}✓ Test completed successfully!${NC}"
echo ""
echo "Results saved in:"
echo "  - reports/monitoring_metrics.json"
echo "  - reports/test_run_metadata.json"
echo "  - $TEST_LOG"
echo ""
