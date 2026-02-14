"""
VOLT Trading Main Application
Evolved from X1Nano-Superior with enhanced features
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

from src.core.trading_engine import TradingEngine
from src.core.config_manager import ConfigManager
from src.utils.logger import setup_logging
from src.agents.agent_orchestrator import AgentOrchestrator


class VOLTTrading:
    """Main VOLT Trading Application"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.trading_engine = None
        self.agent_orchestrator = None
        self.running = False
        self._tasks = []

    async def initialize(self):
        """Initialize all components"""
        # Setup logging
        setup_logging(self.config_manager.get_logging_config())
        self.logger = logging.getLogger(__name__)

        self.logger.info("Initializing VOLT Trading System...")

        # Initialize trading engine
        self.trading_engine = TradingEngine(self.config_manager)
        await self.trading_engine.initialize()

        # Initialize agent orchestrator with dependencies
        self.agent_orchestrator = AgentOrchestrator(
            self.config_manager,
            exchange=self.trading_engine.exchange,
            strategy=self.trading_engine.strategy,
        )
        await self.agent_orchestrator.initialize()

        self.logger.info("VOLT Trading System initialized successfully")

    async def start(self):
        """Start the trading system"""
        if self.running:
            self.logger.warning("Trading system is already running")
            return

        self.running = True
        self.logger.info("Starting VOLT Trading Engine...")

        try:
            # Start trading engine and agent orchestrator concurrently
            engine_task = asyncio.create_task(self.trading_engine.start())
            orchestrator_task = asyncio.create_task(self.agent_orchestrator.start())
            self._tasks = [engine_task, orchestrator_task]

            self.logger.info("VOLT Trading is now running")

            # Wait for both (engine runs indefinitely, orchestrator starts agents)
            await asyncio.gather(*self._tasks)

        except asyncio.CancelledError:
            self.logger.info("Tasks cancelled - shutting down")
        except Exception as e:
            self.logger.error(f"Critical error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the system"""
        if not self.running:
            return

        self.running = False
        self.logger.info("Shutting down VOLT Trading System...")

        # Cancel running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for task cancellation with timeout
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Shutdown components
        if self.trading_engine:
            await self.trading_engine.stop()

        if self.agent_orchestrator:
            await self.agent_orchestrator.stop()

        self.logger.info("VOLT Trading System shutdown complete")


async def main():
    """Main entry point"""
    volt = VOLTTrading()

    # Setup signal handlers using asyncio loop (proper async signal handling)
    loop = asyncio.get_running_loop()

    def _signal_handler():
        if volt.running:
            logging.getLogger(__name__).info("Received shutdown signal")
            asyncio.ensure_future(volt.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    try:
        await volt.initialize()
        await volt.start()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        await volt.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
