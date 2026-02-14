import json

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

print(f"Prompt length: {len(prompt)} chars")
print(f"Prompt preview:")
print(prompt[:500])
