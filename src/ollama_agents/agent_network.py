"""
Agent Network - Coordinates Multi-Agent Trading Decisions
Implements weighted voting and consensus building
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.ollama_agents.specialized_agents import (
    StrategyAgent,
    RiskAgent,
    MarketAgent,
    ExecutionAgent,
    AuditorAgent
)
from src.utils.logger import get_logger


class AgentNetwork:
    """
    Coordinates communication between multiple trading agents
    Implements weighted voting for consensus decisions
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Initialize all agents
        self.agents = {}
        self._initialize_agents()
        
        # Decision history
        self.decision_history = []
        
        self.logger.info("🤖 Agent Network initialized with 5 agents")
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        self.agents = {
            "strategy": StrategyAgent(),
            "risk": RiskAgent(),
            "market": MarketAgent(),
            "execution": ExecutionAgent(),
            "auditor": AuditorAgent()
        }
    
    async def propose_trade(
        self, 
        market_data: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full multi-agent trading decision process
        
        Flow:
        1. Strategy agent proposes trade
        2. Market agent provides context
        3. Risk agent reviews
        4. Execution agent optimizes
        5. Auditor checks for issues
        6. Weighted consensus calculated
        
        Args:
            market_data: Current market conditions
            portfolio: Current portfolio state
            
        Returns:
            {
                "decision": "BUY"|"SELL"|"HOLD",
                "confidence": 0.0-1.0,
                "agent_votes": {...},
                "reasoning": "...",
                "consensus_type": "STRONG_BUY"|"BUY"|"HOLD"|...
            }
        """
        self.logger.info(f"🤖 Starting multi-agent analysis for {market_data.get('symbol', 'N/A')}")
        
        try:
            # Step 1: Strategy agent proposes
            strategy_result = await self.agents["strategy"].analyze(market_data)
            self.logger.info(
                f"   Strategy: {strategy_result['decision']} "
                f"(confidence: {strategy_result['confidence']:.0%})"
            )
            
            # Step 2: Market agent provides context
            market_result = await self.agents["market"].analyze(market_data)
            self.logger.info(
                f"   Market: {market_result.get('sentiment', 'NEUTRAL')}"
            )
            
            # Step 3: Risk agent reviews proposal
            risk_context = {
                "proposal": strategy_result,
                "portfolio": portfolio,
                "correlation": market_data.get("correlation", 0.0),
                "max_position_size": market_data.get("max_position_size", 0.10)
            }
            risk_result = await self.agents["risk"].analyze(risk_context)
            
            approved = risk_result.get("approved", False)
            self.logger.info(
                f"   Risk: {'APPROVED' if approved else 'REJECTED'}"
            )
            
            # If risk rejects, override to HOLD
            if not approved:
                return {
                    "decision": "HOLD",
                    "confidence": 0.0,
                    "agent_votes": {
                        "strategy": strategy_result,
                        "market": market_result,
                        "risk": risk_result
                    },
                    "reasoning": f"Risk rejected: {risk_result.get('reasoning', 'Unknown')}",
                    "consensus_type": "REJECTED_BY_RISK"
                }
            
            # Step 4: Execution optimization
            exec_result = await self.agents["execution"].analyze({
                "recommended_size": market_data.get("position_size", 0.05)
            })
            
            # Step 5: Auditor check
            audit_result = await self.agents["auditor"].analyze({
                "agent_decisions": [strategy_result, market_result, risk_result]
            })
            
            # Step 6: Calculate weighted consensus
            consensus = self._calculate_weighted_consensus({
                "strategy": strategy_result,
                "market": market_result,
                "risk": risk_result,
                "execution": exec_result,
                "auditor": audit_result
            })
            
            self.logger.info(
                f"   Consensus: {consensus['consensus_type']} "
                f"(confidence: {consensus['confidence']:.0%})"
            )
            
            # Store decision
            self.decision_history.append({
                "timestamp": datetime.now(),
                "symbol": market_data.get("symbol"),
                "consensus": consensus
            })
            
            return consensus
            
        except Exception as e:
            self.logger.error(f"❌ Agent network error: {e}")
            return {
                "decision": "HOLD",
                "confidence": 0.0,
                "agent_votes": {},
                "reasoning": f"Error: {e}",
                "consensus_type": "ERROR"
            }
    
    def _calculate_weighted_consensus(
        self, 
        agent_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Calculate consensus using weighted voting
        
        Weights:
        - Strategy: 0.25
        - Risk: 0.30 (highest - risk is critical)
        - Market: 0.20
        - Execution: 0.15
        - Auditor: 0.10
        """
        # Get agent weights
        weights = {
            "strategy": self.agents["strategy"].weight,
            "risk": self.agents["risk"].weight,
            "market": self.agents["market"].weight,
            "execution": self.agents["execution"].weight,
            "auditor": self.agents["auditor"].weight
        }
        
        # Calculate weighted scores for each decision
        buy_score = 0.0
        sell_score = 0.0
        hold_score = 0.0
        
        # Strategy vote
        strategy_decision = agent_results["strategy"].get("decision", "HOLD")
        strategy_confidence = agent_results["strategy"].get("confidence", 0.5)
        strategy_weight = weights["strategy"]
        
        if strategy_decision == "BUY":
            buy_score += strategy_weight * strategy_confidence
        elif strategy_decision == "SELL":
            sell_score += strategy_weight * strategy_confidence
        else:
            hold_score += strategy_weight * strategy_confidence
        
        # Market sentiment influence
        market_sentiment = agent_results["market"].get("sentiment", "NEUTRAL")
        market_confidence = agent_results["market"].get("confidence", 0.5)
        market_weight = weights["market"]
        
        if market_sentiment == "BULLISH":
            buy_score += market_weight * market_confidence
        elif market_sentiment == "BEARISH":
            sell_score += market_weight * market_confidence
        else:
            hold_score += market_weight * market_confidence
        
        # Risk approval (binary - either 0 or full weight)
        risk_approved = agent_results["risk"].get("approved", False)
        risk_weight = weights["risk"]
        
        if risk_approved:
            # Risk approves = boost the strategy decision
            if strategy_decision == "BUY":
                buy_score += risk_weight
            elif strategy_decision == "SELL":
                sell_score += risk_weight
        else:
            # Risk rejects = boost HOLD
            hold_score += risk_weight
        
        # Normalize scores
        total_score = buy_score + sell_score + hold_score
        if total_score > 0:
            buy_pct = buy_score / total_score
            sell_pct = sell_score / total_score
            hold_pct = hold_score / total_score
        else:
            buy_pct = sell_pct = hold_pct = 0.33
        
        # Determine final decision
        if buy_pct > sell_pct and buy_pct > hold_pct:
            final_decision = "BUY"
            final_confidence = buy_pct
        elif sell_pct > buy_pct and sell_pct > hold_pct:
            final_decision = "SELL"
            final_confidence = sell_pct
        else:
            final_decision = "HOLD"
            final_confidence = hold_pct
        
        # Classify consensus type
        if final_confidence > 0.70:
            consensus_type = f"STRONG_{final_decision}"
        elif final_confidence > 0.55:
            consensus_type = final_decision
        else:
            consensus_type = f"WEAK_{final_decision}"
        
        # Build reasoning
        reasoning_parts = []
        
        if strategy_decision != "HOLD":
            reasoning_parts.append(
                f"Strategy: {strategy_decision} ({strategy_confidence:.0%})"
            )
        
        if market_sentiment != "NEUTRAL":
            reasoning_parts.append(
                f"Market: {market_sentiment}"
            )
        
        if risk_approved:
            reasoning_parts.append("Risk: Approved")
        else:
            reasoning_parts.append(f"Risk: {agent_results['risk'].get('reasoning', 'Rejected')}")
        
        reasoning = " | ".join(reasoning_parts)
        
        return {
            "decision": final_decision,
            "confidence": final_confidence,
            "consensus_type": consensus_type,
            "reasoning": reasoning,
            "agent_votes": {
                "buy_score": buy_pct,
                "sell_score": sell_pct,
                "hold_score": hold_pct
            },
            "individual_results": agent_results
        }
    
    def update_agent_weights(self, performance_data: Dict[str, Dict]):
        """
        Adjust agent weights based on performance
        
        Args:
            performance_data: {
                "strategy_agent": {"win_rate": 0.65, ...},
                "risk_agent": {"correct_rejections": 10, ...}
            }
        """
        for agent_id, metrics in performance_data.items():
            if agent_id in self.agents:
                win_rate = metrics.get("win_rate", 0.50)
                
                # Agents with >60% win rate get boosted
                if win_rate > 0.65:
                    self.agents[agent_id].weight *= 1.05
                elif win_rate < 0.45:
                    self.agents[agent_id].weight *= 0.95
                
                # Clamp weights
                self.agents[agent_id].weight = max(0.05, min(0.40, self.agents[agent_id].weight))
        
        # Normalize so sum = 1.0
        total_weight = sum(agent.weight for agent in self.agents.values())
        for agent in self.agents.values():
            agent.weight /= total_weight
        
        self.logger.info("🎯 Agent weights rebalanced")
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "total_agents": len(self.agents),
            "agents": {
                agent_id: agent.get_performance_summary()
                for agent_id, agent in self.agents.items()
            },
            "decisions_made": len(self.decision_history)
        }
