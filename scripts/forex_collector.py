#!/usr/bin/env python3
"""
Forex Data Collector
Monitors currency pairs and stores data for analysis
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

FOREX_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "EUR/USDT",
    "GBP/USDT",
    "AUD/USDT",
    "USDC/USDT",
]

DATA_FILE = Path(__file__).parent.parent / "data" / "forex_data.json"


async def fetch_forex_prices(exchange):
    """Fetch current prices for all Forex pairs"""
    prices = {}
    for pair in FOREX_PAIRS:
        try:
            ticker = await exchange.get_ticker(pair)
            prices[pair] = {
                "bid": ticker.get("bid", 0),
                "ask": ticker.get("ask", 0),
                "last": ticker.get("last", 0),
                "volume": ticker.get("volume", 0),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching {pair}: {e}")
    return prices


def save_forex_data(data: dict):
    """Save Forex data to file"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            existing = json.load(f)

    existing.update(data)

    with open(DATA_FILE, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"📊 Saved Forex data for {len(data)} pairs")


async def analyze_forex_opportunities(data: dict):
    """Analyze Forex pairs for investment opportunities"""
    opportunities = []

    for pair, info in data.items():
        if not info.get("last"):
            continue

        spread = (info["ask"] - info["bid"]) / info["last"] * 100
        volume = info.get("volume", 0)

        opportunities.append(
            {
                "pair": pair,
                "price": info["last"],
                "spread_pct": spread,
                "volume_24h": volume,
                "timestamp": info["timestamp"],
            }
        )

    opportunities.sort(key=lambda x: x["volume_24h"], reverse=True)

    print("\n🌍 FOREX ANALYSIS")
    print("=" * 50)
    for opp in opportunities[:5]:
        print(f"  {opp['pair']:10} ${opp['price']:.5f}  Vol: {opp['volume_24h']:,.0f}")
    print("=" * 50)

    return opportunities


async def main():
    """Main Forex monitoring loop"""
    from src.exchanges.exchange_factory import ExchangeFactory

    print("🌍 Starting Forex Data Collector...")

    config = {"exchange": {"name": "binance", "sandbox": True}}
    exchange = ExchangeFactory.create_exchange("bybit_testnet", config)
    await exchange.initialize()

    while True:
        try:
            prices = await fetch_forex_prices(exchange)
            save_forex_data(prices)
            await analyze_forex_opportunities(prices)
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
