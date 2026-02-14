"""
VOLT Trading Agent Orchestrator
Manages multiple AI trading agents
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.agents.market_data_agent import MarketDataAgent
from src.agents.technical_agent import TechnicalAnalysisAgent
from src.agents.simple_agents import (
    SentimentAnalysisAgent,
    ExecutionAgent,
    MonitoringAgent,
)
from src.exchanges.exchange_factory import BaseExchange
from src.strategies.volt_strategy import VOLTStrategy


class AgentOrchestrator:
    """Orchestrates all trading agents"""

    def __init__(
        self,
        config_manager: ConfigManager,
        exchange: Optional[BaseExchange] = None,
        strategy: Optional[VOLTStrategy] = None,
    ):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.exchange = exchange
        self.strategy = strategy

        # Agents
        self.agents = {}
        self.running = False

    async def initialize(self):
        """Initialize all agents"""
        self.logger.info("🤖 Initializing Agent Orchestrator...")

        # Initialize individual agents with dependencies
        self.agents = {
            "market_data": MarketDataAgent(self.config_manager, self.exchange),
            "technical": TechnicalAnalysisAgent(
                self.config_manager, self.strategy
            ),
            "sentiment": SentimentAnalysisAgent(self.config_manager),
            "execution": ExecutionAgent(self.config_manager, self.exchange),
            "monitoring": MonitoringAgent(self.config_manager, self.exchange),
        }

        # Initialize each agent
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                self.logger.info(f"✅ {name.title()} Agent initialized")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize {name} Agent: {e}")

        self.logger.info("✅ Agent Orchestrator initialized")

    async def start(self):
        """Start all agents"""
        if self.running:
            self.logger.warning("⚠️ Agent Orchestrator is already running")
            return

        self.running = True
        self.logger.info("🚀 Starting Agent Orchestrator...")

        try:
            # Start all agents
            tasks = []
            for name, agent in self.agents.items():
                task = asyncio.create_task(agent.start())
                tasks.append(task)

            # Wait for all agents to start
            await asyncio.gather(*tasks, return_exceptions=True)

            self.logger.info("📈 All agents started successfully")

        except Exception as e:
            self.logger.error(f"❌ Error starting agents: {e}")
            self.running = False

    async def stop(self):
        """Stop all agents"""
        if not self.running:
            return

        self.running = False
        self.logger.info("🛑 Stopping Agent Orchestrator...")

        # Stop all agents
        for name, agent in self.agents.items():
            try:
                await agent.stop()
                self.logger.info(f"👋 {name.title()} Agent stopped")
            except Exception as e:
                self.logger.error(f"❌ Error stopping {name} Agent: {e}")

        self.logger.info("🔄 Agent Orchestrator stopped")

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}

        for name, agent in self.agents.items():
            try:
                agent_status = await agent.get_status()
                status[name] = agent_status
            except Exception as e:
                status[name] = {"error": str(e)}

        return status

    async def coordinate_agents(self) -> Dict[str, Any]:
        """Coordinate between agents for trading decisions"""
        coordination_data = {}

        try:
            # Get data from each agent
            market_data = await self.agents["market_data"].get_latest_data()
            technical_signals = await self.agents["technical"].get_signals()
            sentiment_data = await self.agents["sentiment"].get_sentiment()

            coordination_data = {
                "timestamp": datetime.now().isoformat(),
                "market_data": market_data,
                "technical_signals": technical_signals,
                "sentiment": sentiment_data,
                "coordination_score": self._calculate_coordination_score(
                    market_data, technical_signals, sentiment_data
                ),
            }

        except Exception as e:
            self.logger.error(f"❌ Error coordinating agents: {e}")
            coordination_data["error"] = str(e)

        return coordination_data

    async def sync_market_data_to_technical(self, market_data: Dict):
        """Sync market data from trading engine to technical agent"""
        try:
            if "technical" in self.agents and market_data:
                self.agents["technical"].set_market_data(market_data)
        except Exception as e:
            self.logger.error(f"❌ Error syncing market data to technical agent: {e}")

    def _calculate_coordination_score(
        self, market_data: Dict, technical_signals: Dict, sentiment: Dict
    ) -> float:
        """Calculate how well agents are coordinated"""
        score = 0.0

        # Simple coordination scoring
        if market_data.get("quality", 0) > 0.7:
            score += 0.3

        if technical_signals.get("confidence", 0) > 0.6:
            score += 0.4

        if sentiment.get("sentiment_score", 0) != 0:
            score += 0.3

        return min(score, 1.0)


if __name__ == "__main__":
    # Test agent orchestrator
    config_manager = ConfigManager()
    orchestrator = AgentOrchestrator(config_manager)
    print("✅ Agent Orchestrator test completed")
