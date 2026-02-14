"""
Base Agent Class for Ollama-powered Trading Agents
Foundation for all specialized agents
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import requests

from src.utils.logger import get_logger


class BaseAgent(ABC):
    """
    Abstract base class for all Ollama-powered agents
    
    Each agent has:
    - A specific role in trading decisions
    - Access to Ollama LLM for reasoning
    - Ability to communicate with other agents
    - Performance tracking
    """
    
    def __init__(
        self, 
        agent_id: str,
        role: str,
        model_name: str = "qwen2.5-coder:7b",
        initial_weight: float = 0.20
    ):
        self.agent_id = agent_id
        self.role = role
        self.model_name = model_name if model_name != "qwen2.5-coder:7b" else "gemma3:latest"
        self.weight = initial_weight
        
        self.logger = get_logger(f"Agent.{agent_id}")
        
        # Ollama connection
        self.ollama_url = "http://localhost:11434"
        
        # Performance tracking
        self.metrics = {
            "proposals_made": 0,
            "proposals_approved": 0,
            "correct_predictions": 0,
            "false_positives": 0,
            "win_rate": 0.0,
            "avg_confidence": 0.0,
            "total_pnl": 0.0
        }
        
        # Conversation history (for context)
        self.conversation_history = []
        self.max_history = 10
        
        self.logger.info(
            f"🤖 Agent initialized: {agent_id} "
            f"({role}) using {model_name}"
        )
    
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method - implemented by each specialized agent
        
        Args:
            context: Market data, positions, signals, etc.
            
        Returns:
            {
                "decision": "BUY"|"SELL"|"HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "...",
                "metadata": {...}
            }
        """
        pass
    
    async def think(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Core reasoning using Ollama LLM via requests (sync wrapped in executor)
        
        Args:
            prompt: User prompt for the LLM
            system_prompt: Optional system context
            
        Returns:
            str: LLM response
        """
        try:
            self.logger.debug(f"🧠 think() called for {self.agent_id}")
            
            # Prepare messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add conversation history for context
            messages.extend(self.conversation_history[-self.max_history:])
            
            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            self.logger.debug(f"📝 Prepared {len(messages)} messages")
            
            # Use sync requests in executor (avoids async HTTP issues on Python 3.14)
            def _call_ollama():
                response = requests.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9
                        }
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Ollama API error {response.status_code}: {response.text}")
            
            # Run in thread pool executor
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, _call_ollama)
            
            assistant_message = data['message']['content']
            
            # Store in conversation history
            self._add_to_history("user", prompt)
            self._add_to_history("assistant", assistant_message)
            
            self.logger.debug(f"✅ think() complete for {self.agent_id}")
            return assistant_message
            
        except asyncio.TimeoutError:
            self.logger.error(f"⏱️ Ollama timeout for {self.agent_id}")
            return "ERROR: Timeout"
        except Exception as e:
            self.logger.error(f"❌ Ollama error for {self.agent_id}: {e}")
            return f"ERROR: {str(e)}"
    
    async def communicate(
        self, 
        to_agent_id: str, 
        message_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send message to another agent
        
        Args:
            to_agent_id: Target agent ID
            message_type: Type of message (e.g., "TRADE_PROPOSAL", "RISK_REVIEW")
            payload: Message content
            
        Returns:
            Message dict ready to be sent
        """
        message = {
            "message_id": self._generate_message_id(),
            "timestamp": datetime.now().isoformat(),
            "from": self.agent_id,
            "to": to_agent_id,
            "type": message_type,
            "payload": payload
        }
        
        self.logger.debug(
            f"📨 {self.agent_id} → {to_agent_id}: {message_type}"
        )
        
        return message
    
    async def receive(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming message from another agent
        
        Args:
            message: Message dict
            
        Returns:
            Response dict
        """
        self.logger.debug(
            f"📬 {self.agent_id} received {message['type']} "
            f"from {message['from']}"
        )
        
        # Subclasses can override to handle specific message types
        return {
            "status": "ACKNOWLEDGED",
            "from": self.agent_id,
            "in_reply_to": message.get("message_id")
        }
    
    def update_metrics(self, outcome: str, pnl: float = 0.0):
        """
        Update agent performance metrics
        
        Args:
            outcome: "CORRECT" | "FALSE_POSITIVE" | "STOPPED"
            pnl: Profit/loss from trade
        """
        if outcome == "CORRECT":
            self.metrics["correct_predictions"] += 1
        elif outcome == "FALSE_POSITIVE":
            self.metrics["false_positives"] += 1
        
        self.metrics["total_pnl"] += pnl
        
        # Recalculate win rate
        total = (
            self.metrics["correct_predictions"] + 
            self.metrics["false_positives"]
        )
        
        if total > 0:
            self.metrics["win_rate"] = (
                self.metrics["correct_predictions"] / total
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get agent performance summary"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "weight": self.weight,
            "metrics": self.metrics,
            "model": self.model_name
        }
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # Trim if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"MSG_{self.agent_id}_{timestamp}"
    
    def clear_history(self):
        """Clear conversation history (useful for new analysis)"""
        self.conversation_history = []
        self.logger.debug(f"🗑️ {self.agent_id} conversation history cleared")


class MockOllamaAgent(BaseAgent):
    """
    Mock agent for testing (doesn't require Ollama)
    """
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock analysis"""
        return {
            "decision": "HOLD",
            "confidence": 0.50,
            "reasoning": f"Mock response from {self.agent_id}",
            "metadata": {}
        }
    
    async def think(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Mock thinking"""
        return f"[MOCK] Analyzed: {prompt[:50]}..."
