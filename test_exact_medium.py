import subprocess
import json
import time

prompt = "Review BTC/USDT BUY trade. Portfolio: $10k. Safe? JSON: {\"approved\": bool, \"reasoning\": str}"

payload = {
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "system", "content": "Risk expert. JSON only."},
        {"role": "user", "content": prompt}
    ],
    "stream": False
}

print(f"Payload size: {len(json.dumps(payload))} bytes")
print(f"Prompt: {prompt}")
print("\nCalling Ollama...")

start = time.time()
proc = subprocess.run(
    ["curl", "-s", "-v", "-X", "POST", "http://localhost:11434/api/chat",
     "-H", "Content-Type: application/json",
     "-d", json.dumps(payload),
     "--max-time", "15"],
    capture_output=True, text=True, timeout=20
)

elapsed = time.time() - start
print(f"\nElapsed: {elapsed:.1f}s")
print(f"Return code: {proc.returncode}")
print(f"Stdout length: {len(proc.stdout)}")
print(f"Stderr: {proc.stderr[-500:]}")

if proc.returncode == 0 and proc.stdout:
    try:
        response = json.loads(proc.stdout)
        print(f"\n✅ SUCCESS: {response['message']['content']}")
    except Exception as e:
        print(f"\n❌ Parse error: {e}")
        print(f"Raw: {proc.stdout[:200]}")
else:
    print(f"\n❌ FAILED")
