import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test")

async def test_with_history():
    """Test with conversation history like BaseAgent"""
    conversation_history = []
    max_history = 10
    
    messages = []
    messages.append({"role": "system", "content": "You are a test assistant."})
    messages.extend(conversation_history[-max_history:])  # Empty list
    messages.append({"role": "user", "content": "Say hello in JSON"})
    
    logger.debug(f"Messages: {messages}")
    
    async with aiohttp.ClientSession() as session:
        logger.debug("Session created")
        async with session.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen2.5-coder:7b",
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            logger.debug(f"Got response: {response.status}")
            data = await response.json()
            logger.debug(f"Result: {data['message']['content'][:50]}")
            return True

async def main():
    try:
        await asyncio.wait_for(test_with_history(), timeout=15)
        print("✅ SUCCESS")
    except asyncio.TimeoutError:
        print("❌ TIMEOUT")

asyncio.run(main())
