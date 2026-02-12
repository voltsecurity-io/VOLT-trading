"""
VOLT Trading Engine
Core trading logic and execution engine
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.exchanges.exchange_factory import ExchangeFactory
from src.strategies.volt_strategy import VOLTStrategy
from src.risk.risk_manager import RiskManager


class TradingEngine:
    """Core trading engine for VOLT Trading"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.config = config_manager.get_trading_config()

        # Components
        self.exchange = None
        self.strategy = None
        self.risk_manager = None

        # State
        self.running = False
        self.positions = {}
        self.last_update = None

    async def initialize(self):
        """Initialize trading engine components"""
        self.logger.info("🔧 Initializing Trading Engine...")

        # Initialize exchange connection
        exchange_config = self.config_manager.get_exchange_config()
        self.exchange = ExchangeFactory.create_exchange(
            exchange_config["name"], exchange_config
        )
        await self.exchange.initialize()

        # Initialize trading strategy
        self.strategy = VOLTStrategy(self.config_manager)
        await self.strategy.initialize()

        # Initialize risk manager
        self.risk_manager = RiskManager(self.config_manager)
        await self.risk_manager.initialize()

        self.logger.info("✅ Trading Engine initialized successfully")

    async def start(self):
        """Start the trading engine"""
        if self.running:
            self.logger.warning("⚠️ Trading engine is already running")
            return

        self.running = True
        self.logger.info("🚀 Starting Trading Engine...")

        try:
            # Start main trading loop
            await self._trading_loop()

        except Exception as e:
            self.logger.error(f"❌ Trading engine error: {e}")
            self.running = False

    async def stop(self):
        """Stop the trading engine"""
        if not self.running:
            return

        self.running = False
        self.logger.info("🛑 Stopping Trading Engine...")

        # Close positions if needed
        await self._emergency_shutdown()

        # Release exchange connection
        if self.exchange and hasattr(self.exchange, "close"):
            await self.exchange.close()

        self.logger.info("👋 Trading Engine stopped")

    async def _trading_loop(self):
        """Main trading loop"""
        self.logger.info("📊 Starting main trading loop...")

        while self.running:
            try:
                # Get market data
                market_data = await self._get_market_data()

                if market_data is not None:
                    # Generate trading signals
                    signals = await self.strategy.generate_signals(market_data)

                    # Risk assessment
                    for signal in signals:
                        risk_assessment = await self.risk_manager.assess_risk(
                            signal, self.positions
                        )

                        if risk_assessment["approved"]:
                            await self._execute_signal(signal, risk_assessment)
                        else:
                            self.logger.warning(
                                f"⚠️ Signal rejected by risk manager: {risk_assessment['reason']}"
                            )

                # Update positions and monitor
                await self._update_positions()
                await self._monitor_performance()

                # Sleep before next iteration
                await asyncio.sleep(self._get_sleep_interval())

            except Exception as e:
                self.logger.error(f"💥 Trading loop error: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _get_market_data(self) -> Optional[pd.DataFrame]:
        """Get current market data"""
        try:
            symbols = self.config.get("pairs", [])
            timeframe = self.config.get("timeframe", "5m")

            # Get OHLCV data for all symbols
            all_data = {}
            for symbol in symbols:
                data = await self.exchange.get_ohlcv(symbol, timeframe, limit=100)
                if data:
                    all_data[symbol] = pd.DataFrame(
                        data,
                        columns=["timestamp", "open", "high", "low", "close", "volume"],
                    )
                    all_data[symbol]["timestamp"] = pd.to_datetime(
                        all_data[symbol]["timestamp"], unit="ms"
                    )

            return all_data if all_data else None

        except Exception as e:
            self.logger.error(f"❌ Error getting market data: {e}")
            return None

    async def _execute_signal(
        self, signal: Dict[str, Any], risk_assessment: Dict[str, Any]
    ):
        """Execute trading signal"""
        try:
            symbol = signal["symbol"]
            action = signal["action"]  # 'buy' or 'sell'

            # Calculate position size based on risk assessment
            position_size = risk_assessment["position_size"]

            self.logger.info(
                f"🎯 Executing {action} signal for {symbol} - Size: {position_size}"
            )

            if action == "buy":
                order = await self.exchange.create_market_buy_order(
                    symbol, position_size
                )
            else:
                order = await self.exchange.create_market_sell_order(
                    symbol, position_size
                )

            if order:
                self.logger.info(f"✅ Order executed: {order}")
                await self._update_positions_after_order(order)
            else:
                self.logger.error(f"❌ Failed to execute order for {symbol}")

        except Exception as e:
            self.logger.error(f"💥 Error executing signal: {e}")

    async def _update_positions(self):
        """Update current positions"""
        try:
            # Get current positions from exchange
            current_positions = await self.exchange.get_positions()
            self.positions = current_positions

            self.last_update = datetime.now()

        except Exception as e:
            self.logger.error(f"❌ Error updating positions: {e}")

    async def _update_positions_after_order(self, order: Dict[str, Any]):
        """Update positions after order execution"""
        symbol = order.get("symbol")

        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "quantity": 0.0,
                "entry_price": 0.0,
                "unrealized_pnl": 0.0,
                "side": "long",
            }

        # Update position based on order
        order_qty = float(order.get("filled", 0))
        if order.get("side") == "buy":
            self.positions[symbol]["quantity"] += order_qty
        else:
            self.positions[symbol]["quantity"] -= order_qty

    async def _monitor_performance(self):
        """Monitor trading performance"""
        try:
            # Calculate portfolio metrics
            total_value = 0.0
            total_pnl = 0.0

            for symbol, position in self.positions.items():
                if position["quantity"] != 0:
                    current_price = await self.exchange.get_ticker(symbol)
                    if current_price:
                        market_value = position["quantity"] * current_price
                        total_value += market_value

                        # Calculate PnL
                        if position["quantity"] > 0:
                            pnl = (current_price - position["entry_price"]) * position[
                                "quantity"
                            ]
                            total_pnl += pnl
                            position["unrealized_pnl"] = pnl

            # Log performance metrics
            if self.last_update:
                self.logger.info(
                    f"📊 Portfolio Value: ${total_value:.2f} | "
                    f"P&L: ${total_pnl:.2f} | "
                    f"Positions: {len([p for p in self.positions.values() if p['quantity'] != 0])}"
                )

        except Exception as e:
            self.logger.error(f"❌ Error monitoring performance: {e}")

    async def _emergency_shutdown(self):
        """Emergency shutdown - close all positions"""
        self.logger.warning("🚨 Emergency shutdown initiated...")

        for symbol, position in self.positions.items():
            if position["quantity"] != 0:
                try:
                    if position["quantity"] > 0:
                        await self.exchange.create_market_sell_order(
                            symbol, abs(position["quantity"])
                        )
                    else:
                        await self.exchange.create_market_buy_order(
                            symbol, abs(position["quantity"])
                        )
                    self.logger.info(f"✅ Closed position in {symbol}")
                except Exception as e:
                    self.logger.error(f"❌ Error closing {symbol}: {e}")

    def _get_sleep_interval(self) -> int:
        """Get sleep interval between trading loop iterations"""
        timeframe = self.config.get("timeframe", "5m")

        # Convert timeframe to seconds
        if timeframe.endswith("m"):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]) * 3600
        else:
            return 300  # Default 5 minutes
