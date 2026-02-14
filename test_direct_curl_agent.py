import subprocess
import json

context = {
    "proposal": {"decision": "BUY", "symbol": "BTC/USDT", "confidence": 0.7, "reasoning": "Test"},
    "portfolio": {"positions": [], "total_value": 10000, "available_capital": 10000, "exposure": 0.0},
    "correlation": 0.3,
    "max_position_size": 0.10
}

prompt = f"""
Analyze this trade proposal from a risk management perspective:

PROPOSAL:
{json.dumps(context.get('proposal', {}), indent=2)}

CURRENT PORTFOLIO:
{json.dumps(context.get('portfolio', {}), indent=2)}

RISK PARAMETERS:
- Asset correlation: {context.get('correlation', 0.5):.2f}
- Max position size: {context.get('max_position_size', 0.10):.1%}

RESPOND ONLY WITH JSON:
{{
  "approved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Your analysis",
  "suggested_size": 0.05,
  "risk_score": 0.0-1.0,
  "concerns": ["list", "of", "concerns"]
}}
"""

messages = [
    {"role": "system", "content": "You are a risk expert. Respond in JSON."},
    {"role": "user", "content": prompt}
]

payload = {
    "model": "qwen2.5-coder:7b",
    "messages": messages,
    "stream": False,
    "options": {"temperature": 0.3}
}

print("Testing direct curl with RiskAgent's exact prompt...")
proc = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
     "-H", "Content-Type: application/json",
     "-d", json.dumps(payload),
     "--max-time", "10"],
    capture_output=True,
    text=True,
    timeout=15
)

if proc.returncode == 0:
    response = json.loads(proc.stdout)
    print(f"✅ SUCCESS: {response['message']['content'][:200]}")
else:
    print(f"❌ FAILED: {proc.stderr}")
