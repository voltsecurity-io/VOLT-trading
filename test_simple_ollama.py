import subprocess
import json
import time

# Test 1: Simple prompt
print("Test 1: Simple prompt...")
start = time.time()
payload1 = {
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Say hello in JSON: {\"msg\": \"...\"}"}],
    "stream": False
}
proc1 = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
     "-d", json.dumps(payload1)],
    capture_output=True, text=True, timeout=10
)
print(f"   ✅ {time.time()-start:.1f}s: {json.loads(proc1.stdout)['message']['content'][:50]}")

# Test 2: With system prompt (like agents use)
print("\nTest 2: With system prompt...")
start = time.time()
payload2 = {
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "system", "content": "You are a risk expert."},
        {"role": "user", "content": "Approve this trade in JSON: {\"approved\": true}"}
    ],
    "stream": False,
    "options": {"temperature": 0.3}
}
proc2 = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
     "-d", json.dumps(payload2)],
    capture_output=True, text=True, timeout=10
)
print(f"   ✅ {time.time()-start:.1f}s: {json.loads(proc2.stdout)['message']['content'][:50]}")

# Test 3: Long prompt (like RiskAgent)
print("\nTest 3: Long multi-line prompt...")
start = time.time()
long_prompt = """
Review this trade proposal:

Proposed Action: BUY
Symbol: BTC/USDT
Confidence: 70%
Reasoning: Test proposal

Current Portfolio:
- Total Positions: 0
- Total Value: $10000.00
- Available Capital: $10000.00

Risk Metrics:
- Portfolio Correlation: 0.30
- Max Position Size: 10%
- Current Exposure: 0%

Is this trade safe to execute?
Respond in JSON: approved, concerns, modifications, reasoning.
"""
payload3 = {
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "system", "content": "You are a risk expert. Respond in JSON."},
        {"role": "user", "content": long_prompt}
    ],
    "stream": False,
    "options": {"temperature": 0.3, "top_p": 0.9}
}
try:
    proc3 = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
         "-d", json.dumps(payload3),
         "--max-time", "15"],
        capture_output=True, text=True, timeout=20
    )
    if proc3.returncode == 0:
        print(f"   ✅ {time.time()-start:.1f}s: {json.loads(proc3.stdout)['message']['content'][:80]}")
    else:
        print(f"   ❌ curl error: {proc3.stderr[:100]}")
except subprocess.TimeoutExpired:
    print(f"   ❌ TIMEOUT after {time.time()-start:.1f}s - THIS IS THE PROBLEM!")
