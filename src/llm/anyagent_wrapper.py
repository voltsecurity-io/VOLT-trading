"""
VOLT Agent using Mozilla's any-agent framework
Provides multi-framework support and standardized tracing
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from any_agent import AgentConfig, AnyAgent
    from any_agent.tools import search_web, visit_webpage

    ANY_AGENT_AVAILABLE = True
except ImportError:
    ANY_AGENT_AVAILABLE = False
    logger.warning(
        "any-agent not installed. Install with: pip install 'any-agent[agno,openai]'"
    )


@dataclass
class VOLTAgentConfig:
    name: str
    description: str
    model_id: str = "openai:gpt-4o-mini"
    framework: str = "agno"  # agno, openai, langchain, etc.


class AnyAgentWrapper:
    """
    Wrapper around any-agent for VOLT trading agents
    Provides:
    - Multi-framework support
    - Built-in tracing
    - MCP tool integration
    - Easy provider switching
    """

    def __init__(
        self,
        config: VOLTAgentConfig,
        tools: Optional[List[Any]] = None,
        instructions: Optional[str] = None,
    ):
        self.config = config
        self.tools = tools or []
        self.instructions = instructions or ""
        self.agent = None
        self.framework = config.framework

    async def initialize(self):
        """Initialize any-agent with configuration"""
        if not ANY_AGENT_AVAILABLE:
            raise ImportError("any-agent not installed")

        # Set up API key from environment
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        if not api_key:
            logger.warning("No LLM API key found in environment")

        # Create agent config
        agent_config = AgentConfig(
            name=self.config.name,
            model_id=self.config.model_id,
            instructions=self._build_instructions(),
            description=self.config.description,
            tools=self.tools,
        )

        # Create agent based on framework
        self.agent = await AnyAgent.create_async(self.framework, agent_config)

        logger.info(f"✅ {self.config.name} agent initialized ({self.framework})")

    def _build_instructions(self) -> str:
        """Build agent instructions"""
        base = f"""You are a {self.config.name} for a cryptocurrency trading system.
        
{self.instructions}

You must respond with structured JSON for trading decisions.
Always prioritize risk management and capital preservation."""
        return base

    async def think(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate thought using any-agent"""
        if not self.agent:
            await self.initialize()

        # Build full prompt with context
        full_prompt = prompt
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_prompt = f"Context:\n{context_str}\n\nQuestion:\n{prompt}"

        try:
            response = await self.agent.run_async(full_prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Error in any-agent: {e}")
            return f"ERROR: {str(e)}"

    async def analyze_market(self, symbol: str, market_data: Dict) -> Dict:
        """Analyze market for a symbol"""
        prompt = f"""Analyze {symbol} based on this market data:
{market_data}

Respond with:
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "reason": "brief explanation",
    "entry_price": estimated,
    "stop_loss": estimated,
    "take_profit": estimated
}}"""

        result = await self.think(prompt, {"symbol": symbol})

        # Parse JSON response
        try:
            import json

            return json.loads(result)
        except:
            return {"action": "HOLD", "confidence": 0, "reason": "parse_error"}

    async def evaluate_risk(self, trade_proposal: Dict) -> Dict:
        """Evaluate risk of a trade proposal"""
        prompt = f"""Evaluate the risk of this trade:
{trade_proposal}

Consider:
- Position size relative to portfolio
- Correlation with existing positions
- Current market volatility
- Stop loss distance

Respond with:
{{
    "approved": true/false,
    "risk_score": 0.0-1.0,
    "reasons": ["reason1", "reason2"]
}}"""

        result = await self.think(prompt)

        try:
            import json

            return json.loads(result)
        except:
            return {"approved": False, "risk_score": 1.0, "reasons": ["parse_error"]}


# Predefined agent configurations for VOLT
AGENT_CONFIGS = {
    "strategy": VOLTAgentConfig(
        name="Strategy Agent",
        description="Generates trading signals based on technical analysis",
        model_id="openai:gpt-4o-mini",
        instructions="Analyze price charts, indicators, and patterns to generate buy/sell signals.",
    ),
    "risk": VOLTAgentConfig(
        name="Risk Agent",
        description="Evaluates risk and approves/rejects trades",
        model_id="openai:gpt-4o-mini",
        instructions="Evaluate trading proposals for risk. Approve only when risk/reward is favorable.",
    ),
    "market": VOLTAgentConfig(
        name="Market Agent",
        description="Analyzes overall market conditions",
        model_id="openai:gpt-4o-mini",
        instructions="Analyze market trends, sentiment, and macro conditions.",
    ),
    "execution": VOLTAgentConfig(
        name="Execution Agent",
        description="Optimizes trade execution",
        model_id="openai:gpt-4o-mini",
        instructions="Determine best execution strategy: market vs limit orders, timing, etc.",
    ),
}


async def create_voltagent(agent_type: str, framework: str = "agno") -> AnyAgentWrapper:
    """Factory function to create VOLT agents"""

    if agent_type not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent type: {agent_type}")

    config = AGENT_CONFIGS[agent_type]
    config.framework = framework

    agent = AnyAgentWrapper(config)
    await agent.initialize()

    return agent
