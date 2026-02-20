#!/usr/bin/env python3
"""
VOLT Trading System - Monitoring Script
Checks system health and sends alerts
"""

import json
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
STATUS_URL = "http://localhost:8080/status"
LOG_FILE = PROJECT_DIR / "logs" / "monitor.log"


def log(message: str):
    """Log message to file and stdout"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def check_http_server() -> dict:
    """Check if HTTP server is responding"""
    try:
        resp = requests.get(STATUS_URL, timeout=5)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_process(name: str) -> bool:
    """Check if process is running"""
    import subprocess

    result = subprocess.run(["pgrep", "-f", f"python.*{name}"], capture_output=True)
    return result.returncode == 0


def main():
    log("=" * 50)
    log("VOLT System Health Check")

    issues = []

    # Check HTTP server
    log("Checking HTTP server...")
    server = check_http_server()
    if server["ok"]:
        data = server["data"]
        log(
            f"  ✅ Server OK - Equity: ${data.get('portfolio', {}).get('equity', 0):.2f}"
        )
        log(f"  📊 Trades today: {data.get('trading', {}).get('trades_today', 0)}")
        log(f"  💰 Cash: ${data.get('portfolio', {}).get('cash', 0):.2f}")
    else:
        log(f"  ❌ Server error: {server['error']}")
        issues.append("HTTP server not responding")

    # Check processes
    if not check_process("main.py"):
        issues.append("Trading engine not running")
        log("  ❌ Trading engine not running")
    else:
        log("  ✅ Trading engine running")

    if not check_process("webhook"):
        issues.append("Webhook server not running")
        log("  ❌ Webhook server not running")
    else:
        log("  ✅ Webhook server running")

    # Report
    log("=" * 50)
    if issues:
        log("⚠️ ISSUES DETECTED:")
        for issue in issues:
            log(f"  - {issue}")
        sys.exit(1)
    else:
        log("✅ All systems operational")
        sys.exit(0)


if __name__ == "__main__":
    main()
