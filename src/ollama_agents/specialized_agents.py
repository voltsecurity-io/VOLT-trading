"""
Specialized Trading Agents
Each agent has a specific role in the trading decision process
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.ollama_agents.base_agent import BaseAgent
from src.utils.logger import get_logger


class StrategyAgent(BaseAgent):
    """
    Generates trading signals based on technical analysis
    Role: Propose BUY/SELL/HOLD decisions
    """

    def __init__(self, model_name: str = "qwen2.5-coder:7b"):
        super().__init__(
            agent_id="strategy_agent",
            role="Trading Strategy & Signal Generation",
            model_name=model_name,
            initial_weight=0.25,
        )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signal

        Context includes:
        - symbol: Trading pair
        - price: Current price
        - rsi: RSI value
        - macd: MACD value
        - volume: Volume data
        - volatility: VIX/IV data
        """
        symbol = context.get("symbol", "UNKNOWN")

        # Build analysis prompt
        prompt = self._build_analysis_prompt(context)

        # Get LLM reasoning
        system_prompt = """You are an expert crypto trading strategist.
        Analyze technical indicators and provide a clear BUY/SELL/HOLD decision.
        Be concise and focus on actionable insights.
        Format your response as JSON with keys: decision, confidence, reasoning."""

        response = await self.think(prompt, system_prompt)

        # Parse response
        try:
            result = self._parse_llm_response(response)
            result["agent_id"] = self.agent_id
            result["symbol"] = symbol

            self.metrics["proposals_made"] += 1
            self.metrics["avg_confidence"] = (
                self.metrics["avg_confidence"] * (self.metrics["proposals_made"] - 1)
                + result["confidence"]
            ) / self.metrics["proposals_made"]

            return result

        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            return {
                "decision": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Parse error: {e}",
                "agent_id": self.agent_id,
                "symbol": symbol,
            }

    def _build_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt from market context"""
        return f"""
        Analyze this trading opportunity:
        
        Symbol: {context.get("symbol", "N/A")}
        Price: ${context.get("price", 0):.2f}
        
        Technical Indicators:
        - RSI: {context.get("rsi", 50):.1f}
        - MACD: {context.get("macd", 0):.2f}
        - MACD Signal: {context.get("macd_signal", 0):.2f}
        - Bollinger Position: {context.get("bb_position", "middle")}
        - Volume Ratio: {context.get("volume_ratio", 1.0):.2f}
        
        Volatility Context:
        - VIX Level: {context.get("vix", 20):.1f}
        - IV Rank: {context.get("iv_rank", 0.5):.0%}
        
        Should we BUY, SELL, or HOLD?
        Respond in JSON format with: decision, confidence (0-1), reasoning.
        """

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        # Try to extract JSON
        try:
            # Look for JSON block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")

            data = json.loads(json_str)

            # Validate required fields
            decision = data.get("decision", "HOLD").upper()
            if decision not in ["BUY", "SELL", "HOLD"]:
                decision = "HOLD"

            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            reasoning = data.get("reasoning", "No reasoning provided")

            return {
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning,
            }

        except Exception as e:
            # Fallback: extract from text
            response_lower = response.lower()

            if "buy" in response_lower and "sell" not in response_lower:
                decision = "BUY"
            elif "sell" in response_lower:
                decision = "SELL"
            else:
                decision = "HOLD"

            return {
                "decision": decision,
                "confidence": 0.50,
                "reasoning": response[:200],
            }


class RiskAgent(BaseAgent):
    """
    Assesses risk and reviews trade proposals
    Role: Approve/reject trades based on risk metrics
    """

    def __init__(self, model_name: str = "qwen2.5-coder:7b"):
        super().__init__(
            agent_id="risk_agent",
            role="Risk Management & Position Sizing",
            model_name=model_name,
            initial_weight=0.30,
        )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review trade proposal for risk

        Context includes:
        - proposal: Trade proposal from strategy agent
        - portfolio: Current positions
        - correlation: Asset correlations
        """
        proposal = context.get("proposal", {})

        prompt = self._build_risk_prompt(context)

        # MORE AGGRESSIVE RISK MANAGEMENT
        system_prompt = """You are a risk management expert for trading.
        Your goal is to APPROVE trades that have reasonable risk, not to reject them.
        Only reject if there are CLEAR, SIGNIFICANT risks.
        A trade with 30%+ confidence should typically be APPROVED.
        Respond in JSON with: approved (bool), concerns (list), modifications (dict), reasoning."""

        response = await self.think(prompt, system_prompt)

        try:
            result = self._parse_risk_response(response)
            result["agent_id"] = self.agent_id

            if result["approved"]:
                self.metrics["proposals_approved"] += 1

            return result

        except Exception as e:
            self.logger.error(f"Risk parsing error: {e}")
            return {
                "approved": False,
                "concerns": [f"Parse error: {e}"],
                "modifications": {},
                "reasoning": "Error in risk assessment",
                "agent_id": self.agent_id,
            }

    def _build_risk_prompt(self, context: Dict[str, Any]) -> str:
        """Build risk assessment prompt"""
        proposal = context.get("proposal", {})
        portfolio = context.get("portfolio", {})

        return f"""
        Review this trade proposal:
        
        Proposed Action: {proposal.get("decision", "UNKNOWN")}
        Symbol: {proposal.get("symbol", "N/A")}
        Confidence: {proposal.get("confidence", 0):.0%}
        Reasoning: {proposal.get("reasoning", "N/A")}
        
        Current Portfolio:
        - Total Positions: {len(portfolio.get("positions", []))}
        - Total Value: ${portfolio.get("total_value", 0):.2f}
        - Available Capital: ${portfolio.get("available_capital", 0):.2f}
        
        Risk Metrics:
        - Portfolio Correlation: {context.get("correlation", 0):.2f}
        - Max Position Size: {context.get("max_position_size", 0.10):.0%}
        - Current Exposure: {portfolio.get("exposure", 0):.0%}
        
        Is this trade safe to execute?
        Respond in JSON: approved, concerns, modifications, reasoning.
        """

    def _parse_risk_response(self, response: str) -> Dict[str, Any]:
        """Parse risk assessment response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                json_str = response

            data = json.loads(json_str)

            return {
                "approved": bool(data.get("approved", False)),
                "concerns": data.get("concerns", []),
                "modifications": data.get("modifications", {}),
                "reasoning": data.get("reasoning", ""),
            }

        except:
            # Fallback: look for keywords
            approved = (
                "approved" in response.lower()
                and "not approved" not in response.lower()
            )

            return {
                "approved": approved,
                "concerns": ["Unable to parse full response"],
                "modifications": {},
                "reasoning": response[:200],
            }


class MarketAgent(BaseAgent):
    """
    Analyzes overall market conditions and trends
    Role: Provide market context for decisions
    """

    def __init__(self, model_name: str = "gemma3:latest"):
        super().__init__(
            agent_id="market_agent",
            role="Market Analysis & Trend Detection",
            model_name=model_name,
            initial_weight=0.20,
        )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market conditions

        Returns overall market assessment
        """
        prompt = f"""
        Analyze current market conditions:
        
        VIX Level: {context.get("vix", 20):.1f}
        Market Regime: {context.get("vix_regime", "NORMAL")}
        Overall Trend: {context.get("trend", "NEUTRAL")}
        
        Volume: {context.get("volume_trend", "stable")}
        Volatility: {context.get("volatility_trend", "stable")}
        
        What is the overall market sentiment?
        Respond JSON: sentiment (BULLISH/BEARISH/NEUTRAL), confidence, reasoning.
        """

        system_prompt = (
            "You are a market analyst. Provide clear market sentiment analysis."
        )

        response = await self.think(prompt, system_prompt)

        # Simple parsing
        try:
            if "bullish" in response.lower():
                sentiment = "BULLISH"
            elif "bearish" in response.lower():
                sentiment = "BEARISH"
            else:
                sentiment = "NEUTRAL"

            return {
                "sentiment": sentiment,
                "confidence": 0.60,
                "reasoning": response[:200],
                "agent_id": self.agent_id,
            }
        except:
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.50,
                "reasoning": "Analysis inconclusive",
                "agent_id": self.agent_id,
            }


class ExecutionAgent(BaseAgent):
    """
    Optimizes trade execution and timing
    Role: Determine best execution strategy
    """

    def __init__(self, model_name: str = "qwen2.5-coder:7b"):
        super().__init__(
            agent_id="execution_agent",
            role="Trade Execution & Timing",
            model_name=model_name,
            initial_weight=0.15,
        )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize execution strategy"""
        return {
            "execution_type": "MARKET",  # or LIMIT
            "urgency": "NORMAL",
            "position_size": context.get("recommended_size", 0.05),
            "reasoning": "Standard execution recommended",
            "agent_id": self.agent_id,
        }


class AuditorAgent(BaseAgent):
    """
    Oversees other agents and detects errors
    Role: Quality control and error correction
    """

    def __init__(self, model_name: str = "qwen2.5-coder:7b"):
        super().__init__(
            agent_id="auditor_agent",
            role="Oversight & Error Detection",
            model_name=model_name,
            initial_weight=0.10,
        )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Audit agent decisions for inconsistencies"""

        decisions = context.get("agent_decisions", [])

        # Check for conflicts
        buy_votes = sum(1 for d in decisions if d.get("decision") == "BUY")
        sell_votes = sum(1 for d in decisions if d.get("decision") == "SELL")

        if buy_votes > 0 and sell_votes > 0:
            conflict = True
            reasoning = f"Conflict detected: {buy_votes} BUY vs {sell_votes} SELL votes"
        else:
            conflict = False
            reasoning = "No conflicts detected"

        return {
            "conflict_detected": conflict,
            "issues": [],
            "reasoning": reasoning,
            "agent_id": self.agent_id,
        }
