#!/usr/bin/env python3
"""
Test Phase 0 Implementation
VIX Data Collector & Dynamic Thresholds
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.volatility_collector import VolatilityCollector, get_volatility_signal
from src.core.config_manager import ConfigManager
from src.strategies.volt_strategy import VOLTStrategy


async def test_vix_collector():
    """Test VIX data collection"""
    print("\n" + "="*80)
    print("🧪 TEST 1: VIX Data Collector")
    print("="*80 + "\n")
    
    collector = VolatilityCollector()
    
    # Test 1: Get VIX data
    print("📊 Fetching VIX data...")
    vix_data = await collector.get_vix_data()
    
    print(f"   Current VIX: {vix_data['current_vix']:.2f}")
    print(f"   Regime: {vix_data['regime']}")
    print(f"   Percentile: {vix_data['vix_percentile_1y']:.0%}")
    print(f"   ✅ VIX data collected successfully\n")
    
    # Test 2: Get IV Rank
    print("📊 Calculating IV Rank for BTC/USDT...")
    iv_data = await collector.get_iv_rank("BTC/USDT")
    
    print(f"   Current IV: {iv_data['current_iv']:.1f}")
    print(f"   IV Rank: {iv_data['iv_rank']:.0%}")
    print(f"   Mean Reversion Signal: {iv_data['mean_reversion_signal']}")
    print(f"   ✅ IV Rank calculated\n")
    
    # Test 3: Get Term Structure
    print("📊 Fetching VIX term structure...")
    term_data = await collector.get_volatility_term_structure()
    
    print(f"   Spot VIX: {term_data['spot_vix']:.2f}")
    print(f"   Structure: {term_data['structure']}")
    print(f"   Fear Indicator: {term_data['fear_indicator']}")
    print(f"   ✅ Term structure fetched\n")
    
    # Test 4: Composite Signal
    print("📊 Generating composite volatility signal...")
    signal = await collector.get_composite_volatility_signal("ETH/USDT")
    
    print(f"   Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']:.0%}")
    print(f"   Reasoning: {signal['reasoning']}")
    print(f"   ✅ Composite signal generated\n")
    
    return True


async def test_dynamic_thresholds():
    """Test dynamic threshold system"""
    print("\n" + "="*80)
    print("🧪 TEST 2: Dynamic Thresholds")
    print("="*80 + "\n")
    
    config_manager = ConfigManager()
    strategy = VOLTStrategy(config_manager)
    
    # Test different VIX levels
    test_cases = [
        (10.0, "LOW", 0.40),
        (15.0, "NORMAL", 0.45),
        (25.0, "ELEVATED", 0.55),
        (35.0, "PANIC", 0.70)
    ]
    
    print("📊 Testing adaptive thresholds...\n")
    
    for vix, expected_regime, expected_threshold in test_cases:
        strategy.current_vix = vix
        strategy.vix_regime = ""  # Reset to trigger log
        
        threshold = strategy._get_adaptive_threshold()
        
        status = "✅" if threshold == expected_threshold else "❌"
        print(f"   VIX {vix:5.1f} → {strategy.vix_regime:8s} → threshold {threshold:.2f} {status}")
        
        assert threshold == expected_threshold, f"Expected {expected_threshold}, got {threshold}"
    
    print(f"\n   ✅ All threshold tests passed\n")
    
    return True


async def test_integration():
    """Test full integration"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Integration Test")
    print("="*80 + "\n")
    
    config_manager = ConfigManager()
    strategy = VOLTStrategy(config_manager)
    
    # Update VIX data
    print("📊 Updating VIX data in strategy...")
    await strategy.update_vix_data()
    
    print(f"   Current VIX: {strategy.current_vix:.2f}")
    print(f"   Current Regime: {strategy.vix_regime}")
    
    # Get current threshold
    threshold = strategy._get_adaptive_threshold()
    print(f"   Adaptive Threshold: {threshold:.2f}")
    print(f"   ✅ Integration test passed\n")
    
    return True


async def test_convenience_function():
    """Test convenience function"""
    print("\n" + "="*80)
    print("🧪 TEST 4: Convenience Function")
    print("="*80 + "\n")
    
    print("📊 Getting volatility signal for BTC/USDT...")
    signal = await get_volatility_signal("BTC/USDT")
    
    print(f"   Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']:.0%}")
    print(f"   Components:")
    for key, value in signal['components'].items():
        print(f"      {key}: {value}")
    print(f"   Reasoning: {signal['reasoning']}")
    print(f"   ✅ Convenience function works\n")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "PHASE 0: FOUNDATION TESTS" + " "*33 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("VIX Data Collector", test_vix_collector),
        ("Dynamic Thresholds", test_dynamic_thresholds),
        ("Integration", test_integration),
        ("Convenience Function", test_convenience_function)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, True, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"❌ {test_name} FAILED: {e}\n")
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if error:
            print(f"      Error: {error}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 ALL TESTS PASSED! Phase 0 implementation successful.\n")
        return 0
    else:
        print("\n   ⚠️  SOME TESTS FAILED. Please review errors above.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
