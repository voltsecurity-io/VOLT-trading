#!/usr/bin/env python3
"""
VOLT Trading Report Generator
Saves trading results and errors for later analysis
"""

import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "logs" / "volt_trading.log"
REPORT_DIR = Path(__file__).parent.parent / "reports"


def parse_log():
    """Parse trading log and extract key metrics"""
    trades = []
    errors = []
    signals = []
    portfolio_values = []
    log_file_found = True

    if not LOG_FILE.exists():
        return trades, errors, signals, portfolio_values, False

    with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "BUY executed:" in line or "SELL executed:" in line:
                trades.append(line.strip())

            if "ERROR" in line:
                errors.append(line.strip())

            if "Signal rejected:" in line:
                signals.append(line.strip())

            if "Portfolio:" in line and "$" in line:
                portfolio_values.append(line.strip())

    return trades, errors, signals, portfolio_values, True


def generate_report():
    """Generate daily report"""
    trades, errors, signals, portfolio_values, log_file_found = parse_log()

    last_portfolio = portfolio_values[-1] if portfolio_values else "Unknown"

    buys = len([t for t in trades if "BUY" in t])
    sells = len([t for t in trades if "SELL" in t])

    report = {
        "generated_at": datetime.now().isoformat(),
        "log_file_found": log_file_found,
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
        "portfolio_history": portfolio_values[-50:],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORT_DIR / f"daily_report_{timestamp}.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(REPORT_DIR / "latest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    status = "📊" if log_file_found else "⚠️"
    print(f"{status} Report saved to: {report_file}")
    print(f"   Log found: {log_file_found}")
    print(f"   Buys: {buys}, Sells: {sells}")
    print(f"   Errors: {len(errors)}, Rejected: {len(signals)}")

    return report


if __name__ == "__main__":
    generate_report()
