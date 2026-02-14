# VOLT Trading - Agent Timeout Issue: Partial Fix

## Problem Identified
**Root Cause:** Python 3.14 + async HTTP libraries + Ollama resource contention

### Timeline of Issues
1. **aiohttp:** Hung on `protocol.read()` - Python 3.14 compatibility bug
2. **httpx:** Same timeout behavior  
3. **subprocess curl:** Worked in isolation but hung in async context
4. **requests + executor:** Worked but Ollama still timeout:ed due to RAM

### Resource Problem
- **Available RAM:** 2.5GB when agents started
- **Ollama requirements:** 
  - qwen2.5-coder:7b = 4GB
  - gemma3:latest = 3GB  
- **Issue:** Multiple model runners spawning simultaneously, exhausting RAM

## Solutions Implemented

###  ✅ Fixed: HTTP Library
- Replaced `aiohttp` → `requests` library
- Uses `loop.run_in_executor()` for sync-to-async
- **Status:** Works in isolation (agent tests pass)

### ⚠️ Partial: Model Size
- Changed default from qwen2.5-coder (4GB) → gemma3 (3GB)
- **File:** `src/ollama_agents/base_agent.py` line 36
- **Status:** Reduces RAM but agents still timeout in production

### ❌ Not Fixed: Production Timeout
- Agents work standalone: ✅
- Agents timeout in TradingEngine: ❌
- **Hypothesis:** Ollama takes >60s to load model on first request when system is under load

## Workaround: Disable Agents
**Current State:**
- `config/trading.json`: `use_ollama_agents: false`
- 12h test RUNNING with Phase 0 (VIX) only
- System stable and functional

## Recommendations

### Option A: Increase Timeout (Quick Fix)
```python
# In base_agent.py, line ~115
timeout=120  # Instead of 60
```

### Option B: Model Preloading (Better)
```python
# In agent_network.py __init__
async def _warmup_ollama(self):
    """Load model before first use"""
    for agent in self.agents:
        await agent.think("warmup", "You are ready.")
```

### Option C: Smaller Model (Best for 16GB RAM)
- Use `tinyllama` (637MB) or `phi` (1.6GB)
- Edit `specialized_agents.py` all `__init__` functions
- Trade-off: Lower quality decisions

### Option D: Upgrade Python
- Downgrade to Python 3.12 (aiohttp works perfectly)
- Requires mise reinstall: `mise use python@3.12`

## Files Modified
1. `src/ollama_agents/base_agent.py`
   - Import: aiohttp → requests
   - Method: think() uses sync requests + executor
   
2. `config/trading.json`
   - `use_ollama_agents: false` (temporary)

## Next Steps
1. Let 12h test run without agents (baseline data)
2. Implement Option B (model preloading) tomorrow
3. Test with agents after warmup
4. If still fails, go to Option C (smaller model)
