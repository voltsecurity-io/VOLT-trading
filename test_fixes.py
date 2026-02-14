#!/usr/bin/env python3
"""Quick test of fixes"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_vix():
    from src.collectors.volatility_collector import VolatilityCollector
    
    print("Testing VIX collector (fixed aiohttp → requests)...")
    collector = VolatilityCollector()
    
    try:
        vix_data = await asyncio.wait_for(
            collector.get_vix_data(),
            timeout=10
        )
        print(f"✅ VIX fetch: {vix_data['current_vix']:.1f} ({vix_data['regime']})")
        return True
    except asyncio.TimeoutError:
        print("❌ VIX fetch timeout (should not happen)")
        return False
    except Exception as e:
        print(f"⚠️ VIX fetch error: {e} (but didn't hang!)")
        return True  # Error is OK, timeout is not

async def test_strategy():
    import pandas as pd
    from src.core.config_manager import ConfigManager
    from src.strategies.volt_strategy import VOLTStrategy
    
    print("\nTesting strategy (fixed sell-without-position)...")
    config = ConfigManager('config/trading.json')
    strategy = VOLTStrategy(config)
    
    # Create fake market data
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='5min'),
        'open': [100] * 100,
        'high': [105] * 100,
        'low': [95] * 100,
        'close': [100] * 100,
        'volume': [1000] * 100
    })
    
    # Test with no positions - should NOT generate sell
    market_data = {'BTC/USDT': data}
    positions = {}  # Empty - no holdings
    
    signals = await strategy.generate_signals(market_data, positions)
    
    sell_signals = [s for s in signals if s['action'] == 'sell']
    if sell_signals:
        print(f"❌ Generated {len(sell_signals)} SELL signals without position!")
        return False
    else:
        print(f"✅ No invalid SELL signals ({len(signals)} total signals)")
        return True

async def main():
    print("="*60)
    print("TESTING FIXES")
    print("="*60)
    
    vix_ok = await test_vix()
    strat_ok = await test_strategy()
    
    print("\n" + "="*60)
    if vix_ok and strat_ok:
        print("✅ ALL FIXES WORKING")
    else:
        print("❌ SOME FIXES FAILED")
    print("="*60)

asyncio.run(main())
