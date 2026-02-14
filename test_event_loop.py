import asyncio
import sys
sys.path.insert(0, '.')

from src.ollama_agents.specialized_agents import RiskAgent

async def test_agent():
    print(f"Event loop: {asyncio.get_running_loop()}")
    print(f"Event loop ID: {id(asyncio.get_running_loop())}")
    
    agent = RiskAgent()
    print(f"Agent created in loop: {id(asyncio.get_running_loop())}")
    
    context = {
        "proposal": {"decision": "BUY", "symbol": "BTC/USDT", "confidence": 0.7, "reasoning": "Test"},
        "portfolio": {"positions": [], "total_value": 10000, "available_capital": 10000, "exposure": 0.0},
        "correlation": 0.3,
        "max_position_size": 0.10
    }
    
    print("Calling agent.analyze()...")
    result = await asyncio.wait_for(agent.analyze(context), timeout=10)
    print(f"✅ Result: {result.get('approved')}")

asyncio.run(test_agent())
