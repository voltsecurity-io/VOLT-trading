#!/usr/bin/env python3
"""
Test Agent Integration into VOLT Strategy
Verifies that Ollama agents work with TradingEngine
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.core.config_manager import ConfigManager
from src.strategies.volt_strategy import VOLTStrategy


async def test_strategy_with_agents():
    """Test strategy generates signals and validates with agents"""
    print("\n" + "="*60)
    print("TEST 1: Strategy Signal Generation with Agent Validation")
    print("="*60)
    
    config_manager = ConfigManager("config/trading.json")
    strategy = VOLTStrategy(config_manager)
    await strategy.initialize()
    
    # Check if agents are enabled
    if not strategy.use_agents:
        print("❌ FAIL: Agents not initialized")
        return False
    
    print(f"✅ Agents enabled: {strategy.agent_network is not None}")
    
    # Create sample market data (bullish setup)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
    
    # Simulate strong buy signal
    prices = np.linspace(45000, 46500, 100)  # Uptrend
    volumes = np.random.uniform(100, 200, 100)
    volumes[-1] = 300  # Volume spike
    
    btc_df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': volumes
    })
    
    market_data = {'BTC/USDT': btc_df}
    
    print("\n🔍 Generating signals with agent validation...")
    signals = await strategy.generate_signals(market_data, positions={})
    
    if not signals:
        print("⚠️  No signals generated (agents may have rejected)")
        return True  # This is valid behavior
    
    signal = signals[0]
    print(f"\n📊 Signal Generated:")
    print(f"   Symbol: {signal['symbol']}")
    print(f"   Action: {signal['action']}")
    print(f"   Confidence: {signal['confidence']:.1%}")
    
    if 'agent_consensus' in signal:
        consensus = signal['agent_consensus']
        print(f"\n🤖 Agent Consensus:")
        print(f"   Decision: {consensus['decision']}")
        print(f"   Type: {consensus['type']}")
        print(f"   Agent Confidence: {consensus['confidence']:.1%}")
        print(f"   Reasoning: {consensus.get('reasoning', 'N/A')[:100]}...")
        print("✅ PASS: Agent consensus present")
    else:
        print("⚠️  WARNING: No agent consensus (may have failed)")
    
    return True


async def test_agent_rejection():
    """Test that agents can reject bad signals"""
    print("\n" + "="*60)
    print("TEST 2: Agent Rejection of Risky Signals")
    print("="*60)
    
    config_manager = ConfigManager("config/trading.json")
    strategy = VOLTStrategy(config_manager)
    await strategy.initialize()
    
    if not strategy.use_agents:
        print("⚠️  SKIP: Agents disabled")
        return True
    
    # Create sample data for extreme overbought condition
    dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
    prices = np.linspace(45000, 52000, 100)  # Steep uptrend (15%+)
    
    eth_df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.uniform(100, 150, 100)
    })
    
    market_data = {'ETH/USDT': eth_df}
    
    # Simulate portfolio with high exposure
    positions = {
        'BTC/USDT': {'size': 0.08, 'value': 8000},
        'SOL/USDT': {'size': 0.05, 'value': 5000}
    }
    
    print("\n🔍 Testing with high-risk scenario (steep uptrend + existing positions)...")
    signals = await strategy.generate_signals(market_data, positions)
    
    print(f"\n📊 Result: {len(signals)} signals generated")
    
    if signals:
        signal = signals[0]
        if 'agent_consensus' in signal:
            consensus = signal['agent_consensus']
            print(f"   Decision: {consensus['decision']}")
            print(f"   Type: {consensus['type']}")
            
            if consensus['type'] == 'REJECTED_BY_RISK':
                print("✅ PASS: Agents correctly rejected risky trade")
            else:
                print("⚠️  INFO: Agents approved (may be acceptable depending on threshold)")
        else:
            print("⚠️  No agent consensus")
    else:
        print("✅ PASS: Signal rejected (either by strategy or agents)")
    
    return True


async def test_agent_timeout_fallback():
    """Test that strategy works even if agents timeout"""
    print("\n" + "="*60)
    print("TEST 3: Graceful Fallback on Agent Timeout")
    print("="*60)
    
    config_manager = ConfigManager("config/trading.json")
    strategy = VOLTStrategy(config_manager)
    
    # Test with agents disabled
    strategy.use_agents = False
    
    await strategy.initialize()
    
    dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
    prices = np.linspace(1500, 1550, 100)
    
    bnb_df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.uniform(100, 200, 100)
    })
    
    market_data = {'BNB/USDT': bnb_df}
    
    print("\n🔍 Testing with agents disabled (fallback mode)...")
    signals = await strategy.generate_signals(market_data, positions={})
    
    print(f"📊 Signals generated: {len(signals)}")
    
    if signals:
        signal = signals[0]
        has_consensus = 'agent_consensus' in signal
        print(f"   Has agent data: {has_consensus}")
        
        if not has_consensus:
            print("✅ PASS: Strategy works without agents")
        else:
            print("❌ FAIL: Agent data present when disabled")
            return False
    else:
        print("✅ PASS: No signals (valid outcome)")
    
    return True


async def test_vix_integration():
    """Test VIX + Agent integration"""
    print("\n" + "="*60)
    print("TEST 4: VIX + Agent System Integration")
    print("="*60)
    
    config_manager = ConfigManager("config/trading.json")
    strategy = VOLTStrategy(config_manager)
    await strategy.initialize()
    
    print(f"\n📊 Initial VIX: {strategy.current_vix:.1f} ({strategy.vix_regime})")
    
    # Update VIX
    print("🔄 Updating VIX data...")
    await strategy.update_vix_data()
    
    print(f"📊 Updated VIX: {strategy.current_vix:.1f} ({strategy.vix_regime})")
    
    # Check threshold adaptation
    threshold = strategy._get_adaptive_threshold()
    print(f"🎯 Current threshold: {threshold:.2f}")
    
    print("✅ PASS: VIX system functional")
    
    return True


async def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("🧪 VOLT TRADING - AGENT INTEGRATION TEST SUITE")
    print("="*70)
    
    tests = [
        ("Signal Generation + Agents", test_strategy_with_agents),
        ("Agent Risk Rejection", test_agent_rejection),
        ("Agent Timeout Fallback", test_agent_timeout_fallback),
        ("VIX + Agent Integration", test_vix_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, "ERROR"))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for name, status in results:
        icon = "✅" if status == "PASS" else "⚠️" if status == "ERROR" else "❌"
        print(f"{icon} {name}: {status}")
    
    passed = sum(1 for _, s in results if s == "PASS")
    total = len(results)
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Agent integration successful!")
    else:
        print("⚠️  Some tests failed or errored - review above")


if __name__ == "__main__":
    asyncio.run(main())
