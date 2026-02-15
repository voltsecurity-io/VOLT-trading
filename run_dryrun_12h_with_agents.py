#!/usr/bin/env python3
"""
12-Hour Dry Run Test with Phase 0+1 (VIX + Agents)
"""
import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config_manager import ConfigManager
from src.core.trading_engine import TradingEngine


async def run_test(hours: int, capital: float):
    """Run dry-run test for specified hours"""
    
    # Setup logging to stdout (systemd captures it)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    print("="*70)
    print("🚀 VOLT TRADING - 12H DRY-RUN TEST (Phase 0+1)")
    print("="*70)
    print(f"📊 Test Duration: {hours} hours")
    print(f"💰 Starting Capital: ${capital:,.2f}")
    print(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Force DryRun exchange
    config_manager = ConfigManager("config/trading.json")
    config_manager.config["exchange"]["name"] = "binance_dryrun"
    config_manager.config["trading"]["initial_capital"] = capital
    
    # Verify agents enabled
    agents_enabled = config_manager.config["trading"].get("use_ollama_agents", False)
    print(f"🤖 Ollama Agents: {'✅ ENABLED' if agents_enabled else '⚠️ DISABLED (will use pure TA)'}")
    
    print("\n🔧 Initializing trading engine...")
    
    # Initialize engine
    engine = TradingEngine(config_manager)
    await engine.initialize()
    
    print("✅ Engine initialized")
    print(f"📈 Trading pairs: {config_manager.config['trading']['pairs']}")
    print(f"⏱️  Timeframe: {config_manager.config['trading']['timeframe']}")
    
    # Verify agents actually loaded
    if hasattr(engine.strategy, 'agent_network') and engine.strategy.agent_network:
        print(f"✅ Agent Network loaded with {len(engine.strategy.agent_network.agents)} agents")
    else:
        print("⚠️  WARNING: Agent Network not loaded!")
    
    print("\n🏁 Starting test...\n")
    
    # Start engine
    await engine.start()
    
    # Run for specified duration
    end_time = datetime.now() + timedelta(hours=hours)
    
    try:
        while datetime.now() < end_time and engine.running:
            remaining = end_time - datetime.now()
            hours_left = remaining.total_seconds() / 3600
            
            # Log every hour
            if int(hours_left * 2) % 2 == 0:
                print(f"⏳ Time remaining: {hours_left:.1f}h | Positions: {len(engine.positions)}")
            
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    
    # Stop engine
    print("\n🛑 Stopping engine...")
    await engine.stop()
    
    # Generate report
    print("\n📊 Generating report...")
    await generate_report(engine, hours)
    
    print("\n✅ Test complete!")
    print(f"📁 Report: reports/dryrun_12h_report.json")
    print(f"📈 Trades: reports/dryrun_trades.json")
    print(f"📝 Logs: logs/volt_trading.log")


async def generate_report(engine, hours):
    """Generate test report"""
    report = {
        "test_duration_hours": hours,
        "start_time": (datetime.now() - timedelta(hours=hours)).isoformat(),
        "end_time": datetime.now().isoformat(),
        "initial_capital": engine.config.get("initial_capital", 20000),
        "agents_used": engine.strategy.use_agents if hasattr(engine.strategy, 'use_agents') else False,
        "vix_regime": engine.strategy.vix_regime if hasattr(engine.strategy, 'vix_regime') else "UNKNOWN",
        "current_vix": engine.strategy.current_vix if hasattr(engine.strategy, 'current_vix') else 0.0,
        "total_positions": len(engine.positions),
    }
    
    Path("reports").mkdir(exist_ok=True)
    with open("reports/dryrun_12h_report.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOLT Trading 12h Dry Run Test")
    parser.add_argument("--hours", type=int, default=12, help="Test duration in hours")
    parser.add_argument("--capital", type=float, default=20000, help="Starting capital")
    
    args = parser.parse_args()
    
    asyncio.run(run_test(args.hours, args.capital))
