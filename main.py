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

    async def initialize(self):
        """Initialize all components"""
        # Setup logging
        setup_logging(self.config_manager.get_logging_config())
        self.logger = logging.getLogger(__name__)

        self.logger.info("🚀 Initializing VOLT Trading System...")

        # Initialize trading engine
        self.trading_engine = TradingEngine(self.config_manager)
        await self.trading_engine.initialize()

        # Initialize agent orchestrator
        self.agent_orchestrator = AgentOrchestrator(self.config_manager)
        await self.agent_orchestrator.initialize()

        self.logger.info("✅ VOLT Trading System initialized successfully")

    async def start(self):
        """Start the trading system"""
        if self.running:
            self.logger.warning("⚠️ Trading system is already running")
            return

        self.running = True
        self.logger.info("🎯 Starting VOLT Trading Engine...")

        try:
            # Start trading engine and agent orchestrator concurrently
            engine_task = asyncio.create_task(self.trading_engine.start())
            orchestrator_task = asyncio.create_task(self.agent_orchestrator.start())

            self.logger.info("📈 VOLT Trading is now running")

            # Wait for both (engine runs indefinitely, orchestrator starts agents)
            await asyncio.gather(engine_task, orchestrator_task)

        except KeyboardInterrupt:
            self.logger.info("🛑 Received shutdown signal")
            await self.shutdown()
        except Exception as e:
            self.logger.error(f"❌ Critical error: {e}")
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the system"""
        if not self.running:
            return

        self.running = False
        self.logger.info("🔄 Shutting down VOLT Trading System...")

        # Shutdown components
        if self.trading_engine:
            await self.trading_engine.stop()

        if self.agent_orchestrator:
            await self.agent_orchestrator.stop()

        self.logger.info("👋 VOLT Trading System shutdown complete")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🚨 Received signal {signum}")
        asyncio.create_task(self.shutdown())


async def main():
    """Main entry point"""
    volt = VOLTTrading()

    # Setup signal handlers
    signal.signal(signal.SIGINT, volt.signal_handler)
    signal.signal(signal.SIGTERM, volt.signal_handler)

    try:
        await volt.initialize()
        await volt.start()
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
