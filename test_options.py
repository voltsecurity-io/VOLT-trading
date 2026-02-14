import subprocess
import json

# Test without options
print("Test 1: NO options parameter")
payload1 = {
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Say approved in JSON"}],
    "stream": False
}
proc1 = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
     "-d", json.dumps(payload1), "--max-time", "10"],
    capture_output=True, text=True, timeout=15
)
print(f"   Result: {proc1.returncode}, {len(proc1.stdout)} bytes")
if proc1.returncode == 0:
    print(f"   ✅ {json.loads(proc1.stdout)['message']['content'][:50]}")

# Test WITH options
print("\nTest 2: WITH options (temperature, top_p)")
payload2 = {
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Say approved in JSON"}],
    "stream": False,
    "options": {"temperature": 0.3, "top_p": 0.9}
}
proc2 = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
     "-d", json.dumps(payload2), "--max-time", "10"],
    capture_output=True, text=True, timeout=15
)
print(f"   Result: {proc2.returncode}, {len(proc2.stdout)} bytes")
if proc2.returncode == 0:
    print(f"   ✅ {json.loads(proc2.stdout)['message']['content'][:50]}")
else:
    print(f"   ❌ TIMEOUT")

# Test with ONLY temperature
print("\nTest 3: WITH only temperature")
payload3 = {
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Say approved in JSON"}],
    "stream": False,
    "options": {"temperature": 0.3}
}
proc3 = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
     "-d", json.dumps(payload3), "--max-time", "10"],
    capture_output=True, text=True, timeout=15
)
print(f"   Result: {proc3.returncode}, {len(proc3.stdout)} bytes")
if proc3.returncode == 0:
    print(f"   ✅ {json.loads(proc3.stdout)['message']['content'][:50]}")
else:
    print(f"   ❌ TIMEOUT")
