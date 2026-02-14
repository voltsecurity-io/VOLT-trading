#!/usr/bin/env python3
"""
Quick test of the Streamlit dashboard
Generates sample data for testing without running full trading system
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Ensure reports directory exists
Path("reports").mkdir(exist_ok=True)

# Generate sample metrics
sample_metrics = {
    "last_updated": datetime.now().isoformat(),
    "uptime_seconds": 3600,  # 1 hour
    "positions": {
        "BTC/USDT": {
            "entry_price": 50000.0,
            "amount": 0.1,
            "entry_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "last_update": datetime.now().isoformat(),
        },
        "ETH/USDT": {
            "entry_price": 3000.0,
            "amount": 1.0,
            "entry_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "last_update": datetime.now().isoformat(),
        },
    },
    "total_trades": 5,
    "winning_trades": 3,
    "losing_trades": 2,
    "total_pnl": 250.50,
    "initial_portfolio_value": 10000.0,
    "portfolio_history_count": 12,
    "trade_history": [
        {
            "symbol": "BTC/USDT",
            "entry_price": 49000.0,
            "exit_price": 50000.0,
            "amount": 0.1,
            "pnl": 100.0,
            "entry_time": (datetime.now() - timedelta(days=1)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=12)).isoformat(),
        },
        {
            "symbol": "ETH/USDT",
            "entry_price": 3100.0,
            "exit_price": 3000.0,
            "amount": 1.0,
            "pnl": -100.0,
            "entry_time": (datetime.now() - timedelta(days=1)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=10)).isoformat(),
        },
        {
            "symbol": "SOL/USDT",
            "entry_price": 100.0,
            "exit_price": 110.0,
            "amount": 10.0,
            "pnl": 100.0,
            "entry_time": (datetime.now() - timedelta(days=2)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=8)).isoformat(),
        },
        {
            "symbol": "BNB/USDT",
            "entry_price": 400.0,
            "exit_price": 410.0,
            "amount": 2.0,
            "pnl": 20.0,
            "entry_time": (datetime.now() - timedelta(days=2)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=6)).isoformat(),
        },
        {
            "symbol": "BTC/USDT",
            "entry_price": 51000.0,
            "exit_price": 50500.0,
            "amount": 0.1,
            "pnl": -50.0,
            "entry_time": (datetime.now() - timedelta(hours=5)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=3)).isoformat(),
        },
    ],
}

# Save to file
metrics_file = "reports/monitoring_metrics.json"
with open(metrics_file, "w") as f:
    json.dump(sample_metrics, f, indent=2)

print("✅ Sample metrics generated!")
print(f"📊 File: {metrics_file}")
print("\nSample data includes:")
print(f"  - Initial portfolio: ${sample_metrics['initial_portfolio_value']:,.2f}")
print(f"  - Total P&L: ${sample_metrics['total_pnl']:,.2f}")
print(f"  - Win rate: {sample_metrics['winning_trades']/sample_metrics['total_trades']*100:.1f}%")
print(f"  - Open positions: {len(sample_metrics['positions'])}")
print(f"  - Trade history: {len(sample_metrics['trade_history'])} trades")
print("\n🚀 Now run the dashboard:")
print("   streamlit run dashboard/app.py")
print("   or")
print("   ./launch_dashboard.sh")
