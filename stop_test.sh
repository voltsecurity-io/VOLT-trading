#!/bin/bash
# Stop 12-hour test run

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════"
echo "🛑 Stopping VOLT-Trading Test"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ ! -f /tmp/volt_trading.pid ]; then
    echo "❌ No test is running"
    exit 1
fi

TRADING_PID=$(cat /tmp/volt_trading.pid 2>/dev/null)
DASHBOARD_PID=$(cat /tmp/volt_dashboard.pid 2>/dev/null)

echo "Stopping trading engine (PID: $TRADING_PID)..."
kill $TRADING_PID 2>/dev/null || true
sleep 2

echo "Stopping dashboard (PID: $DASHBOARD_PID)..."
kill $DASHBOARD_PID 2>/dev/null || true
sleep 1

# Force kill if still running
if ps -p $TRADING_PID > /dev/null 2>&1; then
    echo "Force stopping trading engine..."
    kill -9 $TRADING_PID 2>/dev/null || true
fi

if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    echo "Force stopping dashboard..."
    kill -9 $DASHBOARD_PID 2>/dev/null || true
fi

# Update test metadata
if [ -f "reports/test_run_metadata.json" ]; then
    python -c "
import json
with open('reports/test_run_metadata.json', 'r') as f:
    data = json.load(f)
data['status'] = 'stopped_manually'
data['actual_end_time'] = '$(date +"%Y-%m-%d %H:%M:%S")'
with open('reports/test_run_metadata.json', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || true
fi

# Cleanup
rm -f /tmp/volt_trading.pid
rm -f /tmp/volt_dashboard.pid
rm -f /tmp/volt_test_end.timestamp

echo ""
echo "✅ Test stopped successfully"
echo ""
echo "Results saved in:"
echo "  - reports/monitoring_metrics.json"
echo "  - reports/test_run_metadata.json"
echo ""
