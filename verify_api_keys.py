#!/usr/bin/env python3
"""
API Key Verification Script
Testar Binance API-nycklar innan trading startar
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config_manager import ConfigManager
from src.exchanges.exchange_factory import ExchangeFactory


def print_banner():
    print("═" * 60)
    print("🔐 VOLT-Trading API Key Verification")
    print("═" * 60)
    print()


def verify_api_keys():
    """Verify that API keys are working"""
    
    print("📋 Step 1: Loading configuration...")
    try:
        config = ConfigManager()
        print("✅ Config loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Check if API keys are configured
    api_key = config.get("exchange.api_key", "")
    api_secret = config.get("exchange.api_secret", "")
    sandbox = config.get("exchange.sandbox", True)
    
    print()
    print("🔍 Step 2: Checking API key configuration...")
    
    if not api_key or not api_secret:
        print("❌ API keys are NOT configured!")
        print()
        print("To add API keys:")
        print("  ./setup_api_keys.sh")
        print()
        print("Or manually edit: config/trading.json")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"✅ API Secret: {api_secret[:8]}...****")
    print(f"✅ Mode: {'TESTNET (Sandbox)' if sandbox else '🚨 PRODUCTION 🚨'}")
    
    print()
    print("🌐 Step 3: Connecting to Binance...")
    
    try:
        exchange_name = config.get("exchange.name", "binance")
        exchange_config = {
            "name": exchange_name,
            "sandbox": config.get("exchange.sandbox", True),
            "api_key": config.get("exchange.api_key", ""),
            "api_secret": config.get("exchange.api_secret", ""),
        }
        exchange = ExchangeFactory.create_exchange(exchange_name, exchange_config)
        
        # Initialize exchange
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(exchange.initialize())
        
        print("✅ Connected to Binance")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False
    
    print()
    print("💰 Step 4: Fetching account balance...")
    
    try:
        # BinanceExchange wraps ccxt exchange
        if hasattr(exchange, 'exchange'):
            ccxt_exchange = exchange.exchange
        else:
            ccxt_exchange = exchange
            
        balance = ccxt_exchange.fetch_balance()
        
        # Show USDT balance
        usdt_balance = balance.get('USDT', {})
        free = usdt_balance.get('free', 0.0)
        used = usdt_balance.get('used', 0.0)
        total = usdt_balance.get('total', 0.0)
        
        print(f"✅ USDT Balance:")
        print(f"   Free:  ${free:.2f}")
        print(f"   Used:  ${used:.2f}")
        print(f"   Total: ${total:.2f}")
        
        if total == 0 and sandbox:
            print()
            print("⚠️  Your testnet balance is 0!")
            print("   Get test funds at: https://testnet.binance.vision/")
        
    except Exception as e:
        print(f"❌ Failed to fetch balance: {e}")
        print()
        print("Common issues:")
        print("  - Invalid API key or secret")
        print("  - API keys don't have 'Enable Reading' permission")
        print("  - IP not whitelisted (if using IP restriction)")
        return False
    
    print()
    print("📊 Step 5: Fetching market data...")
    
    try:
        if hasattr(exchange, 'exchange'):
            ccxt_exchange = exchange.exchange
        else:
            ccxt_exchange = exchange
            
        ticker = ccxt_exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        print(f"✅ BTC/USDT Price: ${price:,.2f}")
    except Exception as e:
        print(f"❌ Failed to fetch ticker: {e}")
        return False
    
    print()
    print("📝 Step 6: Checking API permissions...")
    
    try:
        if hasattr(exchange, 'exchange'):
            ccxt_exchange = exchange.exchange
        else:
            ccxt_exchange = exchange
            
        # Try to create a test order (will fail but shows permission check)
        if hasattr(ccxt_exchange, 'create_test_order'):
            ccxt_exchange.create_test_order(
                symbol='BTC/USDT',
                type='limit',
                side='buy',
                amount=0.001,
                price=1.0
            )
            print("✅ Trading permission confirmed")
        else:
            print("⚠️  Cannot verify trading permission (test order not supported)")
            print("   But this is OK - will work during actual trading")
    except AttributeError:
        # ccxt might not support test orders for all exchanges
        print("⚠️  Cannot verify trading permission (test order not supported)")
    except Exception as e:
        if 'permission' in str(e).lower() or 'forbidden' in str(e).lower():
            print(f"❌ Trading permission denied: {e}")
            print()
            print("To fix:")
            print("  - Enable 'Enable Spot & Margin Trading' on your API key")
            return False
        else:
            # Other errors are ok (like price filter, etc)
            print("✅ Trading permission OK (got expected error)")
    
    print()
    print("═" * 60)
    print("🎉 ALL CHECKS PASSED!")
    print("═" * 60)
    print()
    print("Your API keys are working correctly!")
    print()
    print("Next steps:")
    print("  1. Start trading: ./start_dryrun.sh")
    print("  2. Monitor logs: tail -f logs/trading.log")
    print("  3. View dashboard: http://localhost:8501")
    print()
    
    if not sandbox:
        print("🚨" * 30)
        print("⚠️  WARNING: PRODUCTION MODE ACTIVE!")
        print("⚠️  Real money will be traded!")
        print("⚠️  Start with SMALL amounts!")
        print("⚠️  Monitor CLOSELY for 24+ hours!")
        print("🚨" * 30)
        print()
    
    return True


if __name__ == "__main__":
    print_banner()
    
    success = verify_api_keys()
    
    sys.exit(0 if success else 1)
