#!/usr/bin/env python3
"""
TradingView Webhook Server for VOLT Trading System
Starts a webhook listener to receive TradingView alerts and execute trades on Bybit Testnet
"""

import asyncio
import json
from aiohttp import web

from src.exchanges.bybit_exchange import BybitTestnetExchange, TradingViewWebhookHandler
from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger


async def create_app(config_manager: ConfigManager):
    """Create the webhook application"""

    exchange_config = {
        "initial_balance": config_manager.get("bybit.initial_balance", 100000),
        "bybit_api_key": config_manager.get("bybit.api_key", ""),
        "bybit_api_secret": config_manager.get("bybit.secret", ""),
    }

    exchange = BybitTestnetExchange(exchange_config)
    await exchange.initialize()

    webhook_handler = TradingViewWebhookHandler(exchange)

    app = web.Application()

    async def handle_webhook(request):
        payload = await request.json()
        result = await webhook_handler.handle_webhook(payload)
        return web.json_response(result)

    async def handle_status(request):
        balance = await exchange.get_balance()
        positions = await exchange.get_positions()
        orders = await exchange.get_order_history()

        return web.json_response(
            {
                "status": "running",
                "exchange": "bybit_testnet",
                "balance": balance,
                "positions": positions,
                "recent_orders": orders[-10:] if orders else [],
            }
        )

    async def handle_test(request):
        test_order = await exchange.create_market_buy_order("BTC/USDT", 0.001)
        return web.json_response(
            {"message": "Test order executed", "order": test_order}
        )

    app.router.add_post("/webhook/tradingview", handle_webhook)
    app.router.add_get("/status", handle_status)
    app.router.add_post("/test", handle_test)

    app["exchange"] = exchange
    app["webhook_handler"] = webhook_handler

    return app


async def main():
    """Start the webhook server"""
    logger = get_logger(__name__)

    logger.info("=" * 50)
    logger.info("🚀 VOLT TradingView Webhook Server")
    logger.info("=" * 50)

    config_manager = ConfigManager()

    app = await create_app(config_manager)

    host = "0.0.0.0"
    port = 8080

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"✅ Webhook server started on http://{host}:{port}")
    logger.info("")
    logger.info("📝 TradingView Alert Configuration:")
    logger.info(f"   Webhook URL: http://YOUR_IP:8080/webhook/tradingview")
    logger.info("")
    logger.info("📋 JSON format for alerts:")
    logger.info('   {"action": "buy", "symbol": "BTC/USDT", "amount": 0.01}')
    logger.info('   {"action": "sell", "symbol": "ETH/USDT", "amount": 0.1}')
    logger.info("")
    logger.info("🔗 Endpoints:")
    logger.info(f"   POST /webhook/tradingview - Execute trade")
    logger.info(f"   GET  /status              - Check balance & positions")
    logger.info(f"   POST /test                - Execute test order")
    logger.info("")
    logger.info("🛑 Press Ctrl+C to stop")
    logger.info("=" * 50)

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
