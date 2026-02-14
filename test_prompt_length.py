import subprocess
import json

prompts = {
    "short": "Approve BTC trade. JSON: {\"approved\": true}",
    "medium": "Review BTC/USDT BUY trade. Portfolio: $10k. Safe? JSON: {\"approved\": bool, \"reasoning\": str}",
    "long": """Review this trade:
Action: BUY BTC/USDT
Confidence: 70%
Portfolio: $10,000
Exposure: 0%
Correlation: 0.30

Respond in JSON with: approved (bool), concerns (list), reasoning (str)"""
}

for name, prompt_text in prompts.items():
    print(f"\n{name.upper()} ({len(prompt_text)} chars):")
    payload = {
        "model": "qwen2.5-coder:7b",
        "messages": [
            {"role": "system", "content": "Risk expert. JSON only."},
            {"role": "user", "content": prompt_text}
        ],
        "stream": False
    }
    
    try:
        proc = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload),
             "--max-time", "10"],
            capture_output=True, text=True, timeout=15
        )
        
        if proc.returncode == 0 and proc.stdout:
            response = json.loads(proc.stdout)
            print(f"   ✅ SUCCESS: {response['message']['content'][:60]}")
        else:
            print(f"   ❌ FAILED: returncode={proc.returncode}, stderr={proc.stderr[:80]}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
