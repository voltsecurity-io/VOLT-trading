"""
Ollama-based AI Agents for VOLT Trading
Multi-agent system with weighted consensus
"""

from src.ollama_agents.base_agent import BaseAgent
from src.ollama_agents.agent_network import AgentNetwork

__all__ = ['BaseAgent', 'AgentNetwork']
