#!/usr/bin/env python3
"""
Debug script to isolate agent timeout issue
"""
import asyncio
import sys
import logging

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, '.')

from src.ollama_agents.specialized_agents import RiskAgent

async def test_agent_in_context():
    """Test agent in similar context to TradingEngine"""
    print("="*70)
    print("🔍 DEBUGGING AGENT TIMEOUT ISSUE")
    print("="*70)
    
    print("\n1. Creating RiskAgent...")
    agent = RiskAgent()
    print(f"   ✅ Agent created: {agent.agent_id}")
    
    print("\n2. Preparing context (minimal)...")
    context = {
        "proposal": {
            "decision": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.7,
            "reasoning": "Test proposal"
        },
        "portfolio": {
            "positions": [],
            "total_value": 10000,
            "available_capital": 10000,
            "exposure": 0.0
        },
        "correlation": 0.3,
        "max_position_size": 0.10
    }
    
    print("\n3. Calling agent.analyze() with 15s timeout...")
    try:
        # Add timeout to see exactly where it hangs
        result = await asyncio.wait_for(
            agent.analyze(context),
            timeout=15.0
        )
        print(f"   ✅ SUCCESS: {result.get('approved', 'N/A')}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')[:100]}")
        return True
    except asyncio.TimeoutError:
        print(f"   ❌ TIMEOUT after 15s")
        print(f"   Last known state: Agent waiting for Ollama response")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_ollama():
    """Test Ollama directly"""
    import aiohttp
    
    print("\n4. Testing direct Ollama call for comparison...")
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "qwen2.5-coder:7b",
        "messages": [
            {"role": "system", "content": "You are a risk expert."},
            {"role": "user", "content": "Respond with JSON: {\"approved\": true, \"reasoning\": \"test\"}"}
        ],
        "stream": False,
        "options": {"temperature": 0.3}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                print(f"   ✅ Direct Ollama works: {data.get('message', {}).get('content', '')[:80]}")
    except Exception as e:
        print(f"   ❌ Direct Ollama failed: {e}")

async def main():
    # Test direct Ollama first
    await test_direct_ollama()
    
    # Then test agent
    success = await test_agent_in_context()
    
    if success:
        print("\n✅ AGENT WORKS - Issue might be in TradingEngine context")
    else:
        print("\n❌ AGENT FAILS - Issue is in agent implementation")

if __name__ == "__main__":
    asyncio.run(main())
