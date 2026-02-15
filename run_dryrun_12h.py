#!/usr/bin/env python3
"""
VOLT Trading - 12 Hour Dry Run Test
====================================
Launches the trading system in paper-trading mode with real market data.
After the test period, generates a comprehensive analysis report.

Usage:
    python run_dryrun_12h.py [--hours 12] [--capital 10000]
"""

import asyncio
import argparse
import json
import logging
import signal
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Ensure we run from project root
os.chdir(Path(__file__).parent)

from src.core.config_manager import ConfigManager
from src.core.trading_engine import TradingEngine
from src.agents.agent_orchestrator import AgentOrchestrator
from src.utils.logger import setup_logging


class DryRunTest:
    """Manages a timed dry-run trading test"""

    def __init__(self, hours: float = 12.0, initial_capital: float = 10000.0):
        self.hours = hours
        self.initial_capital = initial_capital
        self.start_time = None
        self.end_time = None
        self.running = False
        self._tasks = []

        # Configure for dry run
        self.config_manager = ConfigManager()
        self.config_manager.set("exchange.name", "binance_dryrun")
        self.config_manager.set("exchange.sandbox", False)  # Use real Binance for market data
        self.config_manager.set("exchange.api_key", "")
        self.config_manager.set("exchange.api_secret", "")
        self.config_manager.set("trading.initial_capital", initial_capital)
        self.config_manager.set("monitoring.log_level", "INFO")

        # Components
        self.trading_engine = None
        self.agent_orchestrator = None

        # Test metadata
        self.metadata = {
            "test_type": "dry_run_12h",
            "target_hours": hours,
            "initial_capital": initial_capital,
            "start_time": None,
            "end_time": None,
            "status": "pending",
            "errors": [],
            "exchange": "binance_dryrun",
        }

    async def initialize(self):
        """Initialize all components"""
        # Clear previous test state for a fresh start
        for state_file in [
            Path("reports/dryrun_state.json"),
            Path("reports/dryrun_trades.json"),
            Path("reports/engine_state.json"),
        ]:
            if state_file.exists():
                state_file.unlink()

        setup_logging(self.config_manager.get_logging_config())
        self.logger = logging.getLogger("DryRunTest")

        self.logger.info("=" * 60)
        self.logger.info("VOLT Trading - 12 Hour Dry Run Test")
        self.logger.info("=" * 60)
        self.logger.info(f"Duration: {self.hours} hours")
        self.logger.info(f"Initial capital: ${self.initial_capital:,.2f}")
        self.logger.info(f"Exchange: DryRun (real Binance market data)")
        self.logger.info(f"Pairs: {self.config_manager.get('trading.pairs')}")
        self.logger.info(f"Timeframe: {self.config_manager.get('trading.timeframe')}")
        self.logger.info("=" * 60)

        # Initialize trading engine
        self.trading_engine = TradingEngine(self.config_manager)
        await self.trading_engine.initialize()

        # Initialize agent orchestrator
        self.agent_orchestrator = AgentOrchestrator(
            self.config_manager,
            exchange=self.trading_engine.exchange,
            strategy=self.trading_engine.strategy,
        )
        await self.agent_orchestrator.initialize()

        self.logger.info("All components initialized for dry run test")

    async def run(self):
        """Run the dry-run test for specified duration"""
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=self.hours)
        self.running = True

        self.metadata["start_time"] = self.start_time.isoformat()
        self.metadata["status"] = "running"
        self._save_metadata()

        self.logger.info(f"Test started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Test ends at:    {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Start trading engine (creates background trading loop, returns immediately)
            await self.trading_engine.start()

            # Start orchestrator and timer as concurrent tasks
            orchestrator_task = asyncio.create_task(self.agent_orchestrator.start())
            timer_task = asyncio.create_task(self._timer_loop())
            self._tasks = [orchestrator_task, timer_task]

            # Wait for timer to complete (or error in orchestrator)
            done, pending = await asyncio.wait(
                self._tasks, return_when=asyncio.FIRST_COMPLETED
            )

            # If timer finished, cancel the orchestrator
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

        except asyncio.CancelledError:
            self.logger.info("Test cancelled")
            self.metadata["status"] = "cancelled"
        except Exception as e:
            self.logger.error(f"Test error: {e}")
            self.metadata["status"] = "error"
            self.metadata["errors"].append(str(e))
        finally:
            self.running = False
            await self._shutdown()
            self._generate_report()

    async def _timer_loop(self):
        """Monitor test duration and provide periodic status updates"""
        status_interval = 1800  # Status update every 30 minutes
        next_status = status_interval

        while self.running and datetime.now() < self.end_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            remaining = (self.end_time - datetime.now()).total_seconds()

            # Periodic status update
            if elapsed >= next_status:
                hours_elapsed = elapsed / 3600
                hours_remaining = remaining / 3600
                self.logger.info(
                    f"[STATUS] {hours_elapsed:.1f}h elapsed, "
                    f"{hours_remaining:.1f}h remaining, "
                    f"loops: {self.trading_engine._loop_count}, "
                    f"errors: {self.trading_engine._consecutive_errors}"
                )
                self._save_metadata()
                next_status += status_interval

            await asyncio.sleep(60)  # Check every minute

        if datetime.now() >= self.end_time:
            self.logger.info("Test duration reached - completing test")
            self.metadata["status"] = "completed"

    async def _shutdown(self):
        """Graceful shutdown of all components"""
        self.logger.info("Shutting down test components...")

        if self.trading_engine:
            await self.trading_engine.stop()

        if self.agent_orchestrator:
            await self.agent_orchestrator.stop()

        self.metadata["end_time"] = datetime.now().isoformat()
        self._save_metadata()

    def _generate_report(self):
        """Generate comprehensive analysis report after test"""
        self.logger.info("=" * 60)
        self.logger.info("GENERATING TEST REPORT")
        self.logger.info("=" * 60)

        report = {
            "report_generated": datetime.now().isoformat(),
            "test_metadata": self.metadata,
            "duration": {},
            "trading_performance": {},
            "system_health": {},
            "recommendations": [],
        }

        # Duration stats
        if self.start_time:
            actual_duration = (datetime.now() - self.start_time).total_seconds()
            report["duration"] = {
                "target_hours": self.hours,
                "actual_hours": actual_duration / 3600,
                "actual_seconds": actual_duration,
                "completed_fully": self.metadata["status"] == "completed",
            }

        # Trading performance
        report["trading_performance"] = {
            "total_loops": self.trading_engine._loop_count if self.trading_engine else 0,
            "positions_at_end": len(self.trading_engine.positions) if self.trading_engine else 0,
            "consecutive_errors_at_end": (
                self.trading_engine._consecutive_errors if self.trading_engine else 0
            ),
        }

        # Load trade log if available
        trade_log_file = Path("reports/dryrun_trades.json")
        if trade_log_file.exists():
            try:
                with open(trade_log_file) as f:
                    trades = json.load(f)
                report["trading_performance"]["total_trades"] = len(trades)

                if trades:
                    buys = [t for t in trades if t["side"] == "buy"]
                    sells = [t for t in trades if t["side"] == "sell"]
                    total_bought = sum(t.get("cost", 0) for t in buys)
                    total_sold = sum(t.get("cost", 0) for t in sells)

                    report["trading_performance"]["buy_orders"] = len(buys)
                    report["trading_performance"]["sell_orders"] = len(sells)
                    report["trading_performance"]["total_bought_usd"] = total_bought
                    report["trading_performance"]["total_sold_usd"] = total_sold

                    # Symbols traded
                    symbols_traded = set(t["symbol"] for t in trades)
                    report["trading_performance"]["symbols_traded"] = list(symbols_traded)
            except Exception as e:
                report["trading_performance"]["trade_log_error"] = str(e)

        # Load dryrun state
        state_file = Path("reports/dryrun_state.json")
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                report["trading_performance"]["final_balance"] = state.get("balance", {})
                report["trading_performance"]["total_orders"] = state.get("total_orders", 0)
                report["trading_performance"]["failed_orders"] = state.get("failed_orders", 0)

                # Calculate P&L
                final_usdt = state.get("balance", {}).get("USDT", 0)
                # Note: non-USDT assets need current price for accurate P&L
                report["trading_performance"]["final_usdt"] = final_usdt
                report["trading_performance"]["usdt_pnl"] = final_usdt - self.initial_capital
            except Exception as e:
                report["trading_performance"]["state_error"] = str(e)

        # System health
        report["system_health"] = {
            "total_errors": len(self.metadata.get("errors", [])),
            "status": self.metadata["status"],
        }

        # Recommendations
        if self.metadata["status"] == "completed":
            report["recommendations"].append("Test completed successfully - system is stable")
        if report["trading_performance"].get("total_trades", 0) == 0:
            report["recommendations"].append(
                "No trades executed - strategy conditions may be too strict, "
                "consider adjusting RSI/MACD thresholds"
            )
        if report["system_health"]["total_errors"] > 0:
            report["recommendations"].append(
                f"{report['system_health']['total_errors']} errors occurred - "
                "review logs for patterns"
            )

        # Save report
        report_file = Path("reports/dryrun_12h_report.json")
        Path("reports").mkdir(exist_ok=True)
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("TEST REPORT SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Status: {self.metadata['status']}")
        self.logger.info(f"Duration: {report['duration'].get('actual_hours', 0):.2f} hours")
        self.logger.info(f"Trading loops: {report['trading_performance'].get('total_loops', 0)}")
        self.logger.info(f"Total trades: {report['trading_performance'].get('total_trades', 0)}")
        self.logger.info(f"Total errors: {report['system_health']['total_errors']}")

        if "final_balance" in report["trading_performance"]:
            balance = report["trading_performance"]["final_balance"]
            self.logger.info(f"Final balance: {json.dumps(balance)}")

        self.logger.info(f"Full report saved to: {report_file}")
        self.logger.info("=" * 60)

        for rec in report["recommendations"]:
            self.logger.info(f"  -> {rec}")

    def _save_metadata(self):
        """Save test metadata"""
        try:
            Path("reports").mkdir(exist_ok=True)
            with open("reports/dryrun_metadata.json", "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception:
            pass


async def main():
    parser = argparse.ArgumentParser(description="VOLT Trading 12h Dry Run Test")
    parser.add_argument("--hours", type=float, default=12.0, help="Test duration in hours")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital (USD)")
    args = parser.parse_args()

    test = DryRunTest(hours=args.hours, initial_capital=args.capital)

    # Signal handling
    loop = asyncio.get_running_loop()

    def _stop_test():
        logging.getLogger("DryRunTest").info("Received stop signal - finishing test")
        test.running = False
        test.metadata["status"] = "stopped_by_user"
        for task in test._tasks:
            if not task.done():
                task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _stop_test)

    try:
        await test.initialize()
        await test.run()
    except Exception as e:
        logging.error(f"Fatal test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
