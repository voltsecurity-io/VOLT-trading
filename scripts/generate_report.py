#!/usr/bin/env python3
"""
VOLT Trading Report Generator
Saves trading results and errors for later analysis
"""

import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

LOG_FILE = Path(__file__).parent.parent / "logs" / "volt_trading.log"
REPORT_DIR = Path(__file__).parent.parent / "reports"


def parse_log():
    """Parse trading log and extract key metrics"""
    trades = []
    errors = []
    signals = []
    portfolio_values = []

    with open(LOG_FILE) as f:
        for line in f:
            # Extract trades
            if "BUY executed:" in line or "SELL executed:" in line:
                trades.append(line.strip())

            # Extract errors
            if "ERROR" in line:
                errors.append(line.strip())

            # Extract signals
            if "Signal rejected:" in line:
                signals.append(line.strip())

            # Extract portfolio
            if "Portfolio:" in line and "$" in line:
                portfolio_values.append(line.strip())

    return trades, errors, signals, portfolio_values


def generate_report():
    """Generate daily report"""
    trades, errors, signals, portfolio = parse_log()

    # Get last portfolio value
    last_portfolio = portfolio[-1] if portfolio else "Unknown"

    # Count trade outcomes
    buys = len([t for t in trades if "BUY" in t])
    sells = len([t for t in trades if "SELL" in t])

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_buys": buys,
            "total_sells": sells,
            "total_trades": buys + sells,
            "errors_count": len(errors),
            "rejected_signals": len(signals),
            "last_portfolio": last_portfolio,
        },
        "trades": trades,
        "errors": errors,
        "signals_rejected": signals,
        "portfolio_history": portfolio[-50:],  # Last 50 entries
    }

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORT_DIR / f"daily_report_{timestamp}.json"
    REPORT_DIR.mkdir(exist_ok=True)

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    # Also save latest as JSON for easy access
    with open(REPORT_DIR / "latest_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"📊 Report saved to: {report_file}")
    print(f"   Buys: {buys}, Sells: {sells}")
    print(f"   Errors: {len(errors)}, Rejected: {len(signals)}")

    return report


if __name__ == "__main__":
    generate_report()
