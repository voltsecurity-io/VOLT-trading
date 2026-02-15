"""
VOLT Trading Engine
Core trading logic and execution engine
"""

import asyncio
import json
import logging
from pathlib import Path
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

        # Stability tracking
        self._consecutive_errors = 0
        self._max_consecutive_errors = 10
        self._loop_count = 0
        self._last_heartbeat = None
        self._state_file = Path("reports/engine_state.json")

    async def initialize(self):
        """Initialize trading engine components"""
        self.logger.info("Initializing Trading Engine...")

        # Initialize exchange connection
        exchange_config = self.config_manager.get_exchange_config()
        # Pass initial_capital to exchange config for DryRun
        exchange_config["initial_capital"] = self.config.get("initial_capital", 10000)
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

        # Load persisted state
        self._load_state()

        self.logger.info("Trading Engine initialized successfully")

    async def start(self):
        """Start the trading engine"""
        if self.running:
            self.logger.warning("Trading engine is already running")
            return

        self.running = True
        self.logger.info("Starting Trading Engine...")

        # Start trading loop as background task
        self._trading_task = asyncio.create_task(self._trading_loop())
        self.logger.info("✅ Trading loop started as background task")

    async def stop(self):
        """Stop the trading engine"""
        self.running = False
        self.logger.info("Stopping Trading Engine...")

        # Cancel trading task
        if hasattr(self, "_trading_task") and not self._trading_task.done():
            self._trading_task.cancel()
            try:
                await self._trading_task
            except asyncio.CancelledError:
                pass

        # Save state before stopping
        self._save_state()

        # Always close exchange connection
        if self.exchange and hasattr(self.exchange, "close"):
            try:
                await self.exchange.close()
            except Exception as e:
                self.logger.error(f"Error closing exchange: {e}")

        self.logger.info("Trading Engine stopped")

    async def _trading_loop(self):
        """Main trading loop with reconnection and error resilience"""
        self.logger.info("Starting main trading loop...")

        while self.running:
            try:
                self._last_heartbeat = datetime.now()
                self._loop_count += 1

                self.logger.info(f"🔄 Trading loop #{self._loop_count} started")

                # Get market data
                market_data = await self._get_market_data()

                if market_data is not None:
                    # Generate trading signals
                    signals = await self.strategy.generate_signals(
                        market_data, self.positions
                    )

                    self.logger.info(f"📊 Generated {len(signals)} signals")

                    # Risk assessment
                    for signal in signals:
                        risk_assessment = await self.risk_manager.assess_risk(
                            signal, self.positions
                        )

                        if risk_assessment["approved"]:
                            await self._execute_signal(signal, risk_assessment)
                        else:
                            self.logger.info(
                                f"Signal rejected: {signal['symbol']} {signal['action']} "
                                f"- {risk_assessment['reason']}"
                            )

                # Update positions and monitor
                await self._update_positions()
                await self._monitor_performance()

                # Phase 0: Update VIX data every 10 loops (~50 minutes)
                if self._loop_count % 10 == 0:
                    self.logger.info("📊 Updating VIX data...")
                    await self.strategy.update_vix_data()

                # Reset error counter on success
                self._consecutive_errors = 0

                # Periodic state save (every 10 loops)
                if self._loop_count % 10 == 0:
                    self._save_state()

                # Log heartbeat every 12 loops (~1h on 5m timeframe)
                if self._loop_count % 12 == 0:
                    self.logger.info(
                        f"💓 Heartbeat: loop #{self._loop_count}, "
                        f"positions: {len(self.positions)}, "
                        f"errors: {self._consecutive_errors}"
                    )

                # Sleep before next iteration
                sleep_time = self._get_sleep_interval()
                self.logger.debug(f"😴 Sleeping {sleep_time}s until next loop...")
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                raise  # Let cancellation propagate
            except Exception as e:
                self._consecutive_errors += 1
                self.logger.error(
                    f"Trading loop error ({self._consecutive_errors}/{self._max_consecutive_errors}): {e}"
                )

                if self._consecutive_errors >= self._max_consecutive_errors:
                    self.logger.error(
                        "Too many consecutive errors - attempting exchange reconnection"
                    )
                    await self._attempt_reconnection()
                    self._consecutive_errors = 0

                # Exponential backoff: 5s, 10s, 20s, 40s... max 300s
                backoff = min(5 * (2 ** (self._consecutive_errors - 1)), 300)
                await asyncio.sleep(backoff)

    async def _attempt_reconnection(self):
        """Attempt to reconnect to exchange after persistent errors"""
        self.logger.info("Attempting exchange reconnection...")
        try:
            if self.exchange and hasattr(self.exchange, "close"):
                try:
                    await self.exchange.close()
                except Exception:
                    pass

            exchange_config = self.config_manager.get_exchange_config()
            exchange_config["initial_capital"] = self.config.get(
                "initial_capital", 10000
            )
            self.exchange = ExchangeFactory.create_exchange(
                exchange_config["name"], exchange_config
            )
            await self.exchange.initialize()
            self.logger.info("Exchange reconnection successful")
        except Exception as e:
            self.logger.error(f"Exchange reconnection failed: {e}")

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
            self.logger.error(f"Error getting market data: {e}")
            return None

    async def _execute_signal(
        self, signal: Dict[str, Any], risk_assessment: Dict[str, Any]
    ):
        """Execute trading signal"""
        try:
            symbol = signal["symbol"]
            action = signal["action"]  # 'buy' or 'sell'

            # position_size from risk manager is a fraction of capital (e.g. 0.05 = 5%)
            position_size_fraction = risk_assessment["position_size"]

            # Get current price
            price = signal.get("entry_price", 0)
            if not price or price <= 0:
                ticker = await self.exchange.get_ticker(symbol)
                # Handle both dict and float returns
                if isinstance(ticker, dict):
                    price = ticker.get("last", 0) or ticker.get("bid", 0) or 0
                else:
                    price = ticker or 0

            if not price or price <= 0:
                self.logger.error(f"Cannot get price for {symbol}")
                return

            # Convert fraction to base currency amount
            # For SELL: use existing position, for BUY: use capital
            try:
                balance = await self.exchange.get_balance()
                available_capital = float(balance.get("USDT", 0))
            except Exception:
                available_capital = 0
            if available_capital <= 0:
                available_capital = self.config.get("initial_capital", 10000)

            if action == "sell":
                # For sell: get existing position and sell a fraction of it
                positions = await self.exchange.get_positions()
                existing_position = positions.get(symbol, {})
                current_qty = float(existing_position.get("quantity", 0) or 0)
                if current_qty > 0:
                    position_size = current_qty * position_size_fraction
                    dollar_amount = position_size * price
                else:
                    self.logger.warning(f"No position to sell for {symbol}")
                    return
            else:
                # For buy: calculate based on available capital
                dollar_amount = available_capital * position_size_fraction
                position_size = dollar_amount / price

            self.logger.info(
                f"Executing {action} signal for {symbol} - "
                f"Fraction: {position_size_fraction:.3f}, "
                f"Amount: {position_size:.6f} ({dollar_amount:.2f} USD), "
                f"Strength: {signal.get('strength', 0):.2f}"
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
                self.logger.info(
                    f"Order executed: {order.get('side')} {order.get('filled')} "
                    f"{order.get('symbol')} @ {order.get('price')}"
                )
                await self._update_positions_after_order(order)
            else:
                self.logger.error(f"Failed to execute order for {symbol}")

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")

    async def _update_positions(self):
        """Update current positions"""
        try:
            current_positions = await self.exchange.get_positions()
            self.positions = current_positions
            self.last_update = datetime.now()
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")

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

        order_qty = float(order.get("filled", 0))
        if order.get("side") == "buy":
            self.positions[symbol]["quantity"] += order_qty
        else:
            self.positions[symbol]["quantity"] -= order_qty

    async def _monitor_performance(self):
        """Monitor trading performance"""
        try:
            total_value = 0.0
            total_pnl = 0.0

            for symbol, position in self.positions.items():
                if position["quantity"] != 0:
                    ticker = await self.exchange.get_ticker(symbol)
                    # Handle both dict and float returns
                    if isinstance(ticker, dict):
                        current_price = (
                            ticker.get("last", 0) or ticker.get("bid", 0) or 0
                        )
                    else:
                        current_price = ticker or 0

                    if current_price:
                        market_value = position["quantity"] * current_price
                        total_value += market_value

                        if position["quantity"] > 0:
                            pnl = (current_price - position["entry_price"]) * position[
                                "quantity"
                            ]
                            total_pnl += pnl
                            position["unrealized_pnl"] = pnl

            if self.last_update:
                active = len([p for p in self.positions.values() if p["quantity"] != 0])
                self.logger.info(
                    f"Portfolio: ${total_value:.2f} | P&L: ${total_pnl:.2f} | "
                    f"Positions: {active}"
                )

        except Exception as e:
            self.logger.error(f"Error monitoring performance: {e}")

    def _save_state(self):
        """Persist engine state for crash recovery"""
        try:
            Path("reports").mkdir(exist_ok=True)
            state = {
                "positions": self.positions,
                "loop_count": self._loop_count,
                "last_heartbeat": self._last_heartbeat.isoformat()
                if self._last_heartbeat
                else None,
                "last_update": self.last_update.isoformat()
                if self.last_update
                else None,
                "saved_at": datetime.now().isoformat(),
            }
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save engine state: {e}")

    def _load_state(self):
        """Load persisted engine state"""
        try:
            if self._state_file.exists():
                with open(self._state_file, "r") as f:
                    state = json.load(f)
                self.positions = state.get("positions", {})
                self._loop_count = state.get("loop_count", 0)
                self.logger.info(f"Loaded engine state from {state.get('saved_at')}")
        except Exception as e:
            self.logger.warning(f"Could not load engine state: {e}")

    def _get_sleep_interval(self) -> int:
        """Get sleep interval between trading loop iterations"""
        timeframe = self.config.get("timeframe", "5m")

        if timeframe.endswith("m"):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]) * 3600
        else:
            return 300  # Default 5 minutes
