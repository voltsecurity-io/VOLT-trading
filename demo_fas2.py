#!/usr/bin/env python3
"""
Demo for Fas 2: Enhanced Monitoring & Sentiment Analysis
Shows new P&L tracking, position management, and sentiment features
"""

import asyncio
from src.core.config_manager import ConfigManager
from src.exchanges.exchange_factory import ExchangeFactory
from src.agents.simple_agents import MonitoringAgent, SentimentAnalysisAgent


async def demo():
    print("=" * 60)
    print("VOLT Trading - Fas 2 Implementation Demo")
    print("Enhanced Monitoring & Sentiment Analysis")
    print("=" * 60)

    # Initialize config
    config_manager = ConfigManager()
    exchange_config = config_manager.get_exchange_config()

    # Create exchange
    exchange = ExchangeFactory.create_exchange(exchange_config["name"], exchange_config)
    await exchange.initialize()

    print("\n" + "=" * 60)
    print("1. Enhanced MonitoringAgent - Portfolio Tracking")
    print("=" * 60)

    monitoring_agent = MonitoringAgent(config_manager, exchange)
    monitoring_agent.metrics_file = "reports/demo_metrics.json"
    await monitoring_agent.initialize()
    await monitoring_agent.start()

    # Simulate some trading activity
    print("\n📊 Simulating trading activity...")

    # Trade 1: Winning BTC trade
    print("\n📈 Trade 1: BUY 0.1 BTC @ $50,000")
    await monitoring_agent.track_position("BTC/USDT", 50000.0, 0.1, "buy")
    
    print("📉 Trade 1: SELL 0.1 BTC @ $51,000 (Profit!)")
    await monitoring_agent.track_position("BTC/USDT", 51000.0, 0.1, "sell")
    print(f"   Realized P&L: +${monitoring_agent.total_pnl:.2f}")

    # Trade 2: Losing ETH trade
    print("\n📈 Trade 2: BUY 1.0 ETH @ $3,000")
    await monitoring_agent.track_position("ETH/USDT", 3000.0, 1.0, "buy")
    
    print("📉 Trade 2: SELL 1.0 ETH @ $2,900 (Loss)")
    await monitoring_agent.track_position("ETH/USDT", 2900.0, 1.0, "sell")
    print(f"   Realized P&L: ${monitoring_agent.total_pnl:.2f}")

    # Trade 3: Open SOL position
    print("\n📈 Trade 3: BUY 10 SOL @ $100 (Keeping open)")
    await monitoring_agent.track_position("SOL/USDT", 100.0, 10.0, "buy")

    # Get comprehensive P&L
    print("\n" + "-" * 60)
    print("💰 Portfolio Summary")
    print("-" * 60)

    pnl = await monitoring_agent.get_portfolio_pnl()
    
    print(f"Initial Portfolio Value: ${pnl.get('initial_value', 0):,.2f}")
    print(f"Current Portfolio Value: ${pnl.get('current_value', 0):,.2f}")
    print(f"Total P&L: ${pnl.get('total_pnl', 0):,.2f} ({pnl.get('pnl_percentage', 0):.2f}%)")
    print(f"\nRealized P&L: ${pnl.get('realized_pnl', 0):,.2f}")
    print(f"Unrealized P&L: ${pnl.get('unrealized_pnl', 0):,.2f}")
    print(f"\nTotal Trades: {pnl.get('total_trades', 0)}")
    print(f"Winning Trades: {pnl.get('winning_trades', 0)}")
    print(f"Losing Trades: {pnl.get('losing_trades', 0)}")
    print(f"Win Rate: {pnl.get('win_rate', 0):.1f}%")

    # Show open positions
    print("\n" + "-" * 60)
    print("📋 Open Positions")
    print("-" * 60)
    
    if monitoring_agent.positions:
        for symbol, position in monitoring_agent.positions.items():
            print(f"\n{symbol}:")
            print(f"   Amount: {position['amount']}")
            print(f"   Entry Price: ${position['entry_price']:,.2f}")
            print(f"   Entry Time: {position['entry_time']}")
    else:
        print("No open positions")

    # System health
    print("\n" + "=" * 60)
    print("2. System Health Metrics")
    print("=" * 60)

    health = await monitoring_agent.get_health()
    
    print(f"\n🏥 System Status: {health.get('system_status', 'unknown').upper()}")
    print(f"⏱️  Uptime: {health.get('uptime_seconds', 0):.1f} seconds")
    
    if "cpu_usage" in health:
        print(f"💻 CPU Usage: {health['cpu_usage']:.1f}%")
    if "memory_usage" in health:
        print(f"🧠 Memory Usage: {health['memory_usage']:.1f}%")
    if "process_memory_mb" in health:
        print(f"📊 Process Memory: {health['process_memory_mb']:.1f} MB")
    
    print(f"\n📈 Open Positions: {health.get('open_positions', 0)}")
    print(f"📊 Total Trades: {health.get('total_trades', 0)}")
    print(f"🎯 Win Rate: {health.get('win_rate', 0):.1f}%")

    # Save metrics
    print("\n💾 Saving metrics to file...")
    monitoring_agent._save_metrics()
    print(f"✅ Metrics saved to {monitoring_agent.metrics_file}")

    await monitoring_agent.stop()

    print("\n" + "=" * 60)
    print("3. Sentiment Analysis Agent")
    print("=" * 60)

    sentiment_agent = SentimentAnalysisAgent(config_manager)
    await sentiment_agent.initialize()
    await sentiment_agent.start()

    sentiment = await sentiment_agent.get_sentiment()
    
    print(f"\n💭 Sentiment Score: {sentiment.get('sentiment_score', 0):.3f}")
    print(f"   (Range: -1.0 = Very Bearish, 0.0 = Neutral, 1.0 = Very Bullish)")
    print(f"📊 Confidence: {sentiment.get('confidence', 0):.2f}")
    print(f"📰 Sources: {', '.join(sentiment.get('sources', []))}")

    if sentiment_agent.use_api:
        print("\n✅ CryptoPanic API enabled")
        print("   Sentiment will update every hour with real news data")
        if sentiment.get('total_posts'):
            print(f"   Latest update: {sentiment['total_posts']} posts analyzed")
            print(f"   Positive votes: {sentiment.get('positive_votes', 0)}")
            print(f"   Negative votes: {sentiment.get('negative_votes', 0)}")
    else:
        print("\n⚠️  Using neutral sentiment (no API configured)")
        print("   To enable: Set 'sentiment.cryptopanic_api_key' in config")
        print("   Get free API key at: https://cryptopanic.com/developers/api/")

    await sentiment_agent.stop()

    # Cleanup
    if hasattr(exchange, "close"):
        await exchange.close()

    print("\n" + "=" * 60)
    print("✅ Fas 2 Demo Complete!")
    print("=" * 60)
    print("\n🎉 New Features Implemented:")
    print("   ✅ Portfolio P&L tracking (realized + unrealized)")
    print("   ✅ Position management (open, partial close, full close)")
    print("   ✅ Win/Loss statistics & Win Rate calculation")
    print("   ✅ Metrics persistence (saves to JSON)")
    print("   ✅ System health monitoring (CPU, memory, process)")
    print("   ✅ Sentiment analysis (optional CryptoPanic integration)")
    print("\n📊 Metrics file: reports/demo_metrics.json")
    print("\nNext steps:")
    print("   - Fas 3: Build Streamlit dashboard to visualize all this data")
    print("   - Or test full system with 'python main.py'")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
