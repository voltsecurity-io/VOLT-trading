#!/bin/bash
# VOLT-Trading Dry-Run Starter
# Aktiverar sandbox mode och startar trading systemet

cd "$(dirname "$0")"

echo "=================================================="
echo "🚀 VOLT-Trading DRY-RUN MODE"
echo "=================================================="
echo "Mode: Binance Testnet (Sandbox)"
echo "Pairs: BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, AVAX/USDT"
echo "Capital: $20,000 (simulated)"
echo "Timeframe: 5 minutes"
echo "=================================================="
echo ""

# Aktivera virtual environment
if [ -d ".venv" ]; then
    echo "✓ Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ ERROR: .venv not found. Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Verifiera dependencies
echo "✓ Checking dependencies..."
python -c "import ccxt, pandas, numpy, streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -q -r requirements.txt
fi

# Skapa reports directory om den inte finns
mkdir -p reports

echo ""
echo "✓ Starting VOLT-Trading Engine..."
echo "  Press Ctrl+C to stop"
echo ""
echo "=================================================="
echo ""

# Starta trading engine
python main.py
