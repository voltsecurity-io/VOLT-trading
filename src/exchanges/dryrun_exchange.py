"""
VOLT Trading - Dry Run Exchange
Uses real market data from Binance but simulates all trades locally.
Perfect for testing strategies without risking real funds.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.exchanges.exchange_factory import BaseExchange
from src.exchanges.binance_exchange import BinanceExchange
from src.utils.logger import get_logger


class DryRunExchange(BaseExchange):
    """Paper trading exchange that reads real data but simulates trades locally.

    - Market data (OHLCV, tickers) comes from real Binance API
    - Orders are simulated locally with realistic fills
    - Portfolio is tracked in memory and persisted to disk
    - All trades are logged for post-analysis
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger("DryRunExchange")

        # Real exchange for market data only (public endpoints, no auth needed)
        self._market_data_config = {
            "sandbox": config.get("sandbox", False),
            "api_key": "",
            "api_secret": "",
        }
        self._real_exchange: Optional[BinanceExchange] = None

        # Paper portfolio
        initial_capital = config.get("initial_capital", 10000.0)
        self._balance: Dict[str, float] = {"USDT": float(initial_capital)}
        self._order_counter = 0

        # Trade log
        self._trade_log = []
        self._state_file = Path("reports/dryrun_state.json")
        self._trade_log_file = Path("reports/dryrun_trades.json")

        # Stats
        self._start_time = None
        self._total_orders = 0
        self._failed_orders = 0

    async def initialize(self):
        """Initialize real exchange connection for market data"""
        self.logger.info("Initializing DryRun Exchange (paper trading)...")

        # Create real exchange for public market data
        self._real_exchange = BinanceExchange(self._market_data_config)
        await self._real_exchange.initialize()

        self._start_time = datetime.now()

        # Load saved state if exists
        self._load_state()

        self.logger.info(
            f"DryRun Exchange ready - Starting balance: "
            f"{json.dumps({k: v for k, v in self._balance.items() if v > 0})}"
        )

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list:
        """Fetch real OHLCV data from Binance"""
        if not self._real_exchange:
            return []
        return await self._real_exchange.get_ohlcv(symbol, timeframe, limit)

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch real ticker price from Binance"""
        if not self._real_exchange:
            return {"last": 0, "bid": 0, "ask": 0, "volume": 0, "percentage": 0}
        return await self._real_exchange.get_ticker(symbol)

    async def create_market_buy_order(
        self, symbol: str, amount: float
    ) -> Dict[str, Any]:
        """Simulate a market buy order"""
        self._total_orders += 1

        try:
            # Get real current price
            ticker = await self.get_ticker(symbol)
            price = ticker.get("last", 0) if isinstance(ticker, dict) else ticker
            if not price or price <= 0:
                self._failed_orders += 1
                self.logger.error(f"DryRun: Cannot get price for {symbol}")
                return {}

            # Parse symbol (e.g., "BTC/USDT" -> base="BTC", quote="USDT")
            base, quote = symbol.split("/")
            cost = price * amount

            # Check if we have enough quote currency
            available = self._balance.get(quote, 0.0)
            if available < cost:
                self._failed_orders += 1
                self.logger.warning(
                    f"DryRun: Insufficient {quote} for buy {amount} {symbol} "
                    f"(need {cost:.2f}, have {available:.2f})"
                )
                return {}

            # Execute paper trade
            self._balance[quote] = available - cost
            self._balance[base] = self._balance.get(base, 0.0) + amount

            self._order_counter += 1
            order = {
                "id": f"dryrun_buy_{self._order_counter}",
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "price": price,
                "cost": cost,
                "filled": amount,
                "status": "closed",
                "timestamp": datetime.now().isoformat(),
            }

            self._log_trade(order)
            self._save_state()

            self.logger.info(
                f"DryRun BUY: {amount:.6f} {base} @ ${price:,.2f} "
                f"(cost: ${cost:.2f}) | USDT remaining: ${self._balance.get('USDT', 0):.2f}"
            )

            return order

        except Exception as e:
            self._failed_orders += 1
            self.logger.error(f"DryRun buy error: {e}")
            return {}

    async def create_market_sell_order(
        self, symbol: str, amount: float
    ) -> Dict[str, Any]:
        """Simulate a market sell order"""
        self._total_orders += 1

        try:
            ticker = await self.get_ticker(symbol)
            price = ticker.get("last", 0) if isinstance(ticker, dict) else ticker
            if not price or price <= 0:
                self._failed_orders += 1
                self.logger.error(f"DryRun: Cannot get price for {symbol}")
                return {}

            base, quote = symbol.split("/")
            proceeds = price * amount

            # Check if we have enough base currency
            available = self._balance.get(base, 0.0)
            if available < amount:
                self._failed_orders += 1
                self.logger.warning(
                    f"DryRun: Insufficient {base} for sell {amount} {symbol} "
                    f"(have {available:.6f})"
                )
                return {}

            # Execute paper trade
            self._balance[base] = available - amount
            self._balance[quote] = self._balance.get(quote, 0.0) + proceeds

            self._order_counter += 1
            order = {
                "id": f"dryrun_sell_{self._order_counter}",
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "price": price,
                "cost": proceeds,
                "filled": amount,
                "status": "closed",
                "timestamp": datetime.now().isoformat(),
            }

            self._log_trade(order)
            self._save_state()

            self.logger.info(
                f"DryRun SELL: {amount:.6f} {base} @ ${price:,.2f} "
                f"(proceeds: ${proceeds:.2f}) | USDT total: ${self._balance.get('USDT', 0):.2f}"
            )

            return order

        except Exception as e:
            self._failed_orders += 1
            self.logger.error(f"DryRun sell error: {e}")
            return {}

    async def get_positions(self) -> Dict[str, Any]:
        """Get simulated positions from paper portfolio"""
        positions = {}

        for currency, amount in self._balance.items():
            if amount <= 0 or currency == "USDT":
                continue

            symbol = f"{currency}/USDT"
            try:
                ticker = await self.get_ticker(symbol)
                current_price = (
                    ticker.get("last", 0) if isinstance(ticker, dict) else ticker
                )
                if current_price and current_price > 0:
                    positions[symbol] = {
                        "symbol": symbol,
                        "quantity": amount,
                        "entry_price": current_price,
                        "unrealized_pnl": 0.0,
                        "side": "long",
                    }
            except Exception:
                pass

        return positions

    async def get_balance(self) -> Dict[str, Any]:
        """Get paper portfolio balance"""
        return {k: v for k, v in self._balance.items() if v > 0}

    async def close(self):
        """Close real exchange connection and save final state"""
        self._save_state()
        self._save_trade_log()

        if self._real_exchange:
            await self._real_exchange.close()

        self.logger.info(
            f"DryRun Exchange closed. Total orders: {self._total_orders}, "
            f"Failed: {self._failed_orders}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get dry run statistics"""
        uptime = 0
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()

        return {
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": uptime,
            "total_orders": self._total_orders,
            "failed_orders": self._failed_orders,
            "success_rate": (
                (self._total_orders - self._failed_orders) / self._total_orders * 100
                if self._total_orders > 0
                else 100.0
            ),
            "balance": {k: v for k, v in self._balance.items() if v > 0},
            "trade_count": len(self._trade_log),
        }

    def _log_trade(self, order: Dict[str, Any]):
        """Log trade for analysis"""
        self._trade_log.append(order)
        # Keep log bounded
        if len(self._trade_log) > 10000:
            self._trade_log = self._trade_log[-10000:]

    def _save_state(self):
        """Persist portfolio state to disk"""
        try:
            Path("reports").mkdir(exist_ok=True)
            state = {
                "balance": self._balance,
                "order_counter": self._order_counter,
                "total_orders": self._total_orders,
                "failed_orders": self._failed_orders,
                "last_saved": datetime.now().isoformat(),
            }
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save dryrun state: {e}")

    def _load_state(self):
        """Load persisted portfolio state"""
        try:
            if self._state_file.exists():
                with open(self._state_file, "r") as f:
                    state = json.load(f)
                self._balance = state.get("balance", self._balance)
                self._order_counter = state.get("order_counter", 0)
                self.logger.info(
                    f"Loaded previous dryrun state: {state.get('last_saved')}"
                )
        except Exception as e:
            self.logger.warning(f"Could not load dryrun state: {e}")

    def _save_trade_log(self):
        """Save complete trade log for analysis"""
        try:
            Path("reports").mkdir(exist_ok=True)
            with open(self._trade_log_file, "w") as f:
                json.dump(self._trade_log, f, indent=2)
            self.logger.info(f"Trade log saved: {len(self._trade_log)} trades")
        except Exception as e:
            self.logger.error(f"Failed to save trade log: {e}")
