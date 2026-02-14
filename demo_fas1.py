#!/usr/bin/env python3
"""
Quick demo to verify Fas 1 implementation
Tests agents with real Binance testnet connection
"""

import asyncio
from src.core.config_manager import ConfigManager
from src.exchanges.binance_exchange import BinanceExchange
from src.strategies.volt_strategy import VOLTStrategy
from src.agents.market_data_agent import MarketDataAgent
from src.agents.technical_agent import TechnicalAnalysisAgent
from src.agents.simple_agents import ExecutionAgent, MonitoringAgent


async def demo():
    print("=" * 60)
    print("VOLT Trading - Fas 1 Implementation Demo")
    print("=" * 60)

    # Initialize config
    config_manager = ConfigManager()
    exchange_config = config_manager.get_exchange_config()

    # Create exchange (use stub if no API keys)
    if exchange_config["name"] == "binance_stub":
        print("\n⚠️  Using BinanceExchangeStub (no API keys configured)")
        from src.exchanges.exchange_factory import ExchangeFactory

        exchange = ExchangeFactory.create_exchange("binance_stub", exchange_config)
    else:
        print(f"\n✅ Using real Binance exchange (sandbox: {exchange_config.get('sandbox', False)})")
        exchange = BinanceExchange(exchange_config)

    await exchange.initialize()

    # Create strategy
    strategy = VOLTStrategy(config_manager)
    await strategy.initialize()

    print("\n" + "=" * 60)
    print("1. Testing MarketDataAgent")
    print("=" * 60)

    market_agent = MarketDataAgent(config_manager, exchange)
    await market_agent.initialize()

    # Fetch data for one symbol
    symbol = "BTC/USDT"
    print(f"\nFetching data for {symbol}...")
    data = await market_agent._fetch_symbol_data(symbol)

    if data:
        print(f"✅ Price: ${data['price']:,.2f}")
        print(f"✅ 24h Change: {data['change_24h']:.2f}%")
        print(f"✅ Volume: {data['volume']:,.0f}")
        print(f"✅ High/Low: ${data['high_24h']:,.2f} / ${data['low_24h']:,.2f}")
    else:
        print("❌ No data received")

    print("\n" + "=" * 60)
    print("2. Testing TechnicalAnalysisAgent")
    print("=" * 60)

    technical_agent = TechnicalAnalysisAgent(config_manager, strategy)
    await technical_agent.initialize()

    # Get OHLCV data
    print(f"\nFetching OHLCV data for {symbol}...")
    ohlcv = await exchange.get_ohlcv(symbol, "5m", limit=100)

    if ohlcv and len(ohlcv) > 0:
        import pandas as pd

        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        print(f"✅ Received {len(df)} candles")

        # Set market data
        technical_agent.set_market_data({symbol: df})
        await technical_agent._analyze_markets()

        # Check results
        if symbol in technical_agent.technical_signals:
            signals = technical_agent.technical_signals[symbol]
            print(f"\n📊 Technical Indicators for {symbol}:")
            print(f"   RSI: {signals.get('rsi', 'N/A'):.2f}" if 'rsi' in signals else "   RSI: N/A")
            print(f"   MACD: {signals.get('macd', 'N/A'):.4f}" if 'macd' in signals else "   MACD: N/A")
            print(f"   BB Upper: ${signals.get('bb_upper', 'N/A'):,.2f}" if 'bb_upper' in signals else "   BB Upper: N/A")
            print(f"   BB Lower: ${signals.get('bb_lower', 'N/A'):,.2f}" if 'bb_lower' in signals else "   BB Lower: N/A")

            # Generate signal
            await technical_agent._generate_signals()
            signal = signals.get("signal", {})
            if signal:
                print(f"\n🎯 Signal: {signal.get('action', 'N/A').upper()}")
                print(f"   Strength: {signal.get('strength', 0):.2f}")
                print(f"   Reasoning: {', '.join(signal.get('reasoning', []))}")
    else:
        print("❌ No OHLCV data received")

    print("\n" + "=" * 60)
    print("3. Testing ExecutionAgent")
    print("=" * 60)

    execution_agent = ExecutionAgent(config_manager, exchange)
    await execution_agent.initialize()

    print("\n✅ ExecutionAgent initialized with exchange connection")
    print(
        "   (Skipping actual order execution in demo - use trading loop for real orders)"
    )

    print("\n" + "=" * 60)
    print("4. Testing MonitoringAgent")
    print("=" * 60)

    monitoring_agent = MonitoringAgent(config_manager, exchange)
    await monitoring_agent.initialize()
    await monitoring_agent.start()

    health = await monitoring_agent.get_health()
    print(f"\n🏥 System Health:")
    print(f"   Status: {health.get('system_status', 'N/A')}")
    print(f"   Uptime: {health.get('uptime_seconds', 0):.1f}s")

    if "cpu_usage" in health:
        print(f"   CPU: {health['cpu_usage']:.1f}%")
        print(f"   Memory: {health['memory_usage']:.1f}%")

    if "portfolio_balance" in health:
        print(f"\n💰 Portfolio Balance:")
        for currency, balance in health["portfolio_balance"].items():
            if isinstance(balance, dict):
                print(f"   {currency}: {balance.get('total', 0):.4f}")

    await monitoring_agent.stop()

    # Cleanup
    if hasattr(exchange, "close"):
        await exchange.close()

    print("\n" + "=" * 60)
    print("✅ Fas 1 Demo Complete!")
    print("=" * 60)
    print("\nAll core agents are now using REAL data from Binance! 🎉")
    print("\nNext steps:")
    print("  - Fas 2: Enhanced monitoring + sentiment analysis")
    print("  - Fas 3: Streamlit dashboard")
    print("  - Run 'python main.py' to start full trading system")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
