#!/bin/bash
# Check 12-hour test status

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo "════════════════════════════════════════════════════════════"
echo "📊 VOLT-Trading 12-Hour Test Status"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Checked at: $(date +'%Y-%m-%d %H:%M:%S')"
echo ""

# Check if test is running
if [ ! -f /tmp/volt_trading.pid ]; then
    echo -e "${RED}❌ Test is NOT running${NC}"
    echo ""
    echo "Start test with:"
    echo "  ./run_12h_test.sh"
    exit 1
fi

TRADING_PID=$(cat /tmp/volt_trading.pid 2>/dev/null)
DASHBOARD_PID=$(cat /tmp/volt_dashboard.pid 2>/dev/null)
END_TIMESTAMP=$(cat /tmp/volt_test_end.timestamp 2>/dev/null)

# Check processes
echo "════════════════════════════════════════════════════════════"
echo "🔧 SYSTEM STATUS"
echo "════════════════════════════════════════════════════════════"
echo ""

if ps -p $TRADING_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Trading Engine:${NC} Running (PID: $TRADING_PID)"
    
    # CPU and Memory usage
    CPU=$(ps -p $TRADING_PID -o %cpu= | tr -d ' ')
    MEM=$(ps -p $TRADING_PID -o %mem= | tr -d ' ')
    echo "  CPU: ${CPU}%"
    echo "  Memory: ${MEM}%"
else
    echo -e "${RED}✗ Trading Engine:${NC} NOT RUNNING"
fi

echo ""

if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Dashboard:${NC} Running (PID: $DASHBOARD_PID)"
    echo "  URL: http://localhost:8501"
else
    echo -e "${RED}✗ Dashboard:${NC} NOT RUNNING"
fi

echo ""

# Time remaining
if [ -n "$END_TIMESTAMP" ]; then
    NOW=$(date +%s)
    REMAINING=$((END_TIMESTAMP - NOW))
    
    if [ $REMAINING -gt 0 ]; then
        HOURS=$((REMAINING / 3600))
        MINUTES=$(( (REMAINING % 3600) / 60 ))
        
        echo "════════════════════════════════════════════════════════════"
        echo "⏱️  TIME REMAINING"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        echo -e "${BLUE}${HOURS}h ${MINUTES}m${NC} remaining"
        echo "Test ends at: $(date -d @$END_TIMESTAMP +'%Y-%m-%d %H:%M:%S')"
        echo ""
        
        # Progress bar
        TOTAL_SECONDS=$((12 * 3600))
        ELAPSED=$((TOTAL_SECONDS - REMAINING))
        PERCENT=$((ELAPSED * 100 / TOTAL_SECONDS))
        
        echo "Progress: ${PERCENT}%"
        printf "["
        for i in {1..50}; do
            if [ $i -le $((PERCENT / 2)) ]; then
                printf "="
            else
                printf " "
            fi
        done
        printf "]\n"
    else
        echo -e "${GREEN}⏱️  Test duration completed!${NC}"
    fi
fi

echo ""

# Trading metrics
if [ -f "reports/monitoring_metrics.json" ]; then
    echo "════════════════════════════════════════════════════════════"
    echo "📈 TRADING METRICS"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    
    python -c "
import json
import sys

try:
    with open('reports/monitoring_metrics.json', 'r') as f:
        data = json.load(f)
    
    total_pnl = data.get('total_pnl', 0)
    realized_pnl = data.get('realized_pnl', 0)
    unrealized_pnl = data.get('unrealized_pnl', 0)
    
    trades = data.get('trades', [])
    total_trades = len(trades)
    
    wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
    losses = sum(1 for t in trades if t.get('pnl', 0) < 0)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    positions = data.get('positions', {})
    open_positions = len(positions)
    
    print(f'Total P&L:        {total_pnl:>10.2f} SEK')
    print(f'  Realized:       {realized_pnl:>10.2f} SEK')
    print(f'  Unrealized:     {unrealized_pnl:>10.2f} SEK')
    print()
    print(f'Total Trades:     {total_trades:>10}')
    print(f'  Wins:           {wins:>10}')
    print(f'  Losses:         {losses:>10}')
    print(f'  Win Rate:       {win_rate:>9.1f}%')
    print()
    print(f'Open Positions:   {open_positions:>10}')
    
except Exception as e:
    print(f'Error reading metrics: {e}')
    sys.exit(1)
" 2>/dev/null || echo "No metrics available yet"
fi

echo ""

# System health
echo "════════════════════════════════════════════════════════════"
echo "🖥️  SYSTEM HEALTH"
echo "════════════════════════════════════════════════════════════"
echo ""

# Battery status
if [ -f /sys/class/power_supply/BAT0/capacity ]; then
    BATTERY=$(cat /sys/class/power_supply/BAT0/capacity)
    STATUS=$(cat /sys/class/power_supply/BAT0/status)
    echo "Battery: ${BATTERY}% (${STATUS})"
else
    echo "Battery: N/A"
fi

# CPU temperature
if command -v sensors &> /dev/null; then
    TEMP=$(sensors | grep -i 'Package id 0' | awk '{print $4}' | head -1)
    if [ -n "$TEMP" ]; then
        echo "CPU Temp: $TEMP"
    fi
fi

# Load average
LOAD=$(uptime | awk -F'load average:' '{print $2}')
echo "Load Average:$LOAD"

# Disk space
DISK=$(df -h . | tail -1 | awk '{print $5 " used (" $4 " free)"}')
echo "Disk: $DISK"

echo ""

# Sleep inhibitor
if pgrep -f "systemd-inhibit.*VOLT-Trading" > /dev/null; then
    echo -e "${GREEN}✓ Sleep prevention: ACTIVE${NC}"
else
    echo -e "${YELLOW}⚠ Sleep prevention: INACTIVE${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 QUICK ACTIONS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "View live logs:          tail -f logs/trading.log"
echo "View dashboard:          http://localhost:8501"
echo "View detailed metrics:   cat reports/monitoring_metrics.json | python -m json.tool"
echo "Stop test:               ./stop_test.sh"
echo ""
echo "════════════════════════════════════════════════════════════"
