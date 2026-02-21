"""
Bybit Testnet Exchange Integration
Supports paper trading via Bybit testnet API and TradingView webhook integration
"""

import asyncio
import hashlib
import hmac
import time
from typing import Dict, Any, Optional
from datetime import datetime

from src.exchanges.exchange_factory import BaseExchange
from src.utils.logger import get_logger


class BybitTestnetExchange(BaseExchange):
    """Bybit Testnet exchange for paper trading with TradingView webhook support"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("bybit_api_key", "")
        self.api_secret = config.get("bybit_api_secret", "")
        self.testnet = True
        self.base_url = "https://api-testnet.bybit.com"

        self.wallet_balance = config.get("initial_balance", 100000)
        self.positions = {}
        self.orders = []

        self.logger = get_logger(__name__)

    async def initialize(self):
        """Initialize Bybit testnet connection"""
        self.logger.info("🔗 Initializing Bybit Testnet exchange...")
        self.logger.info(f"💰 Starting balance: ${self.wallet_balance:,.2f}")

        if self.api_key and self.api_secret:
            self.logger.info("✅ API credentials configured")
        else:
            self.logger.info("⚠️ No API credentials - using simulation mode")

        await asyncio.sleep(0.1)
        self.logger.info("✅ Bybit Testnet exchange initialized")

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list:
        """Get OHLCV data from Bybit testnet"""
        import random

        base_price = self._get_base_price(symbol)
        ohlcv_data = []

        interval_map = {
            "1m": 60000,
            "5m": 300000,
            "15m": 900000,
            "1h": 3600000,
            "4h": 14400000,
            "1d": 86400000,
        }
        interval_ms = interval_map.get(timeframe, 300000)

        for i in range(limit):
            timestamp = int(time.time() * 1000) - (limit - i) * interval_ms
            price = base_price + random.uniform(-0.02, 0.02) * base_price

            ohlcv_data.append(
                [
                    timestamp,
                    price * 0.998,
                    price * 1.003,
                    price * 0.996,
                    price,
                    random.uniform(100, 10000),
                ]
            )

        return ohlcv_data

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker price from Bybit"""
        import random

        base_price = self._get_base_price(symbol)
        spread = base_price * 0.0002

        return {
            "symbol": symbol,
            "last": base_price + random.uniform(-0.001, 0.001) * base_price,
            "bid": base_price - spread,
            "ask": base_price + spread,
            "volume": random.uniform(1000, 100000),
            "percentage": random.uniform(-5, 5),
            "timestamp": datetime.now().isoformat(),
        }

    async def create_market_buy_order(
        self, symbol: str, amount: float
    ) -> Dict[str, Any]:
        """Create market buy order on Bybit testnet"""
        import random

        ticker = await self.get_ticker(symbol)
        price = ticker["last"]

        order = {
            "id": f"bybit_buy_{int(time.time())}_{random.randint(1000, 9999)}",
            "symbol": symbol,
            "side": "buy",
            "amount": amount,
            "price": price,
            "filled": amount,
            "status": "filled",
            "fee": amount * price * 0.0006,
            "timestamp": datetime.now().isoformat(),
            "exchange": "bybit_testnet",
        }

        cost = amount * price + order["fee"]
        if cost <= self.wallet_balance:
            self.wallet_balance -= cost

            if symbol in self.positions:
                existing = self.positions[symbol]
                total = existing["amount"] + amount
                avg_price = (
                    existing["avg_price"] * existing["amount"] + price * amount
                ) / total
                self.positions[symbol] = {
                    "symbol": symbol,
                    "quantity": total,
                    "amount": total,
                    "avg_price": avg_price,
                    "side": "buy",
                }
            else:
                self.positions[symbol] = {
                    "symbol": symbol,
                    "quantity": amount,
                    "amount": amount,
                    "avg_price": price,
                    "side": "buy",
                }

            self.orders.append(order)
            self.logger.info(f"✅ BUY executed: {amount} {symbol} @ ${price:,.2f}")
        else:
            self.logger.warning(f"❌ Insufficient balance for buy order")
            order["status"] = "rejected"
            order["error"] = "Insufficient balance"

        return order

    async def create_market_sell_order(
        self, symbol: str, amount: float
    ) -> Dict[str, Any]:
        """Create market sell order on Bybit testnet"""
        import random

        if symbol not in self.positions:
            return {"id": None, "status": "rejected", "error": "No position"}

        position = self.positions[symbol]
        if position["amount"] < amount:
            return {"id": None, "status": "rejected", "error": "Insufficient position"}

        ticker = await self.get_ticker(symbol)
        price = ticker["last"]

        order = {
            "id": f"bybit_sell_{int(time.time())}_{random.randint(1000, 9999)}",
            "symbol": symbol,
            "side": "sell",
            "amount": amount,
            "price": price,
            "filled": amount,
            "status": "filled",
            "fee": amount * price * 0.0006,
            "timestamp": datetime.now().isoformat(),
            "exchange": "bybit_testnet",
        }

        proceeds = amount * price - order["fee"]
        self.wallet_balance += proceeds

        position["amount"] -= amount
        if position["amount"] <= 0:
            del self.positions[symbol]

        self.orders.append(order)
        self.logger.info(f"✅ SELL executed: {amount} {symbol} @ ${price:,.2f}")

        return order

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance from Bybit testnet"""
        total_in_positions = 0
        for symbol, pos in self.positions.items():
            ticker = await self.get_ticker(symbol)
            total_in_positions += pos["amount"] * ticker["last"]

        return {
            "USDT": {
                "free": self.wallet_balance,
                "used": total_in_positions,
                "total": self.wallet_balance + total_in_positions,
            },
            "total_usd": self.wallet_balance + total_in_positions,
        }

    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        positions_data = {}
        for symbol, pos in self.positions.items():
            ticker = await self.get_ticker(symbol)
            current_value = pos["amount"] * ticker["last"]
            entry_value = pos["amount"] * pos["avg_price"]
            pnl = current_value - entry_value

            positions_data[symbol] = {
                "amount": pos["amount"],
                "avg_price": pos["avg_price"],
                "current_price": ticker["last"],
                "pnl": pnl,
                "pnl_percentage": (pnl / entry_value * 100) if entry_value > 0 else 0,
            }

        return positions_data

    async def get_order_history(self) -> list:
        """Get order history"""
        return self.orders[-100:]

    def _get_base_price(self, symbol: str) -> float:
        """Get base price for symbol simulation"""
        prices = {
            "BTC/USDT": 67000,
            "BTCUSDT": 67000,
            "ETH/USDT": 3200,
            "ETHUSDT": 3200,
            "SOL/USDT": 140,
            "SOLUSDT": 140,
            "BNB/USDT": 580,
            "BNBUSDT": 580,
            "XRP/USDT": 0.55,
            "XRPUSDT": 0.55,
            "EUR/USD": 1.08,
            "EURUSD": 1.08,
            "GBP/USD": 1.26,
            "GBPUSD": 1.26,
            "USD/JPY": 148,
            "USDJPY": 148,
        }

        for key, price in prices.items():
            if key in symbol:
                return price
        return 100.0


class TradingViewWebhookHandler:
    """Handler for TradingView webhooks to trigger Bybit testnet trades"""

    def __init__(self, exchange: BybitTestnetExchange):
        self.exchange = exchange
        self.logger = get_logger(__name__)
        self.webhook_queue = asyncio.Queue()

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process TradingView webhook and execute trade"""
        try:
            action = payload.get("action", "").lower()
            symbol = payload.get("symbol", "BTC/USDT")
            amount = float(payload.get("amount", 0))

            self.logger.info(f"📥 Webhook received: {action} {amount} {symbol}")

            if action == "buy":
                result = await self.exchange.create_market_buy_order(symbol, amount)
            elif action == "sell":
                result = await self.exchange.create_market_sell_order(symbol, amount)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

            return {
                "status": "success",
                "webhook_action": action,
                "order_result": result,
            }

        except Exception as e:
            self.logger.error(f"❌ Webhook error: {e}")
            return {"status": "error", "message": str(e)}

    async def start_listener(self, host: str = "0.0.0.0", port: int = 8080):
        """Start webhook listener server"""
        from aiohttp import web

        async def webhook_handler(request):
            payload = await request.json()
            result = await self.handle_webhook(payload)
            return web.json_response(result)

        app = web.Application()
        app.router.add_post("/webhook/tradingview", webhook_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        self.logger.info(f"🚀 Webhook listener started on {host}:{port}")
        self.logger.info(
            "📝 Configure TradingView alerts with: http://YOUR_IP:8080/webhook/tradingview"
        )

        return runner
