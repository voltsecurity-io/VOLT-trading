"""
Simple agent implementations for missing agents
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.exchanges.exchange_factory import BaseExchange


class SentimentAnalysisAgent:
    """Agent for sentiment analysis with optional CryptoPanic API integration"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.running = False
        self.sentiment_data = {}
        self.sentiment_cache = {}
        self.cache_timeout = 3600  # 1 hour cache

        # CryptoPanic API (optional)
        self.api_key = config_manager.get("sentiment.cryptopanic_api_key", None)
        self.use_api = self.api_key is not None

    async def initialize(self):
        self.logger.info("💭 Initializing Sentiment Analysis Agent...")

        if self.use_api:
            self.logger.info(
                "✅ CryptoPanic API configured - will fetch real sentiment"
            )
        else:
            self.logger.info(
                "⚠️ No sentiment API configured - using neutral sentiment (0.0)"
            )
            self.logger.info(
                "   To enable: Add 'sentiment.cryptopanic_api_key' to config"
            )

    async def start(self):
        self.running = True
        self.logger.info("🚀 Sentiment Analysis Agent started")

        if self.use_api:
            # Start background sentiment fetching
            asyncio.create_task(self._sentiment_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Sentiment Analysis Agent stopped")

    async def _sentiment_loop(self):
        """Background loop to fetch sentiment periodically"""
        while self.running:
            try:
                # Fetch sentiment every hour
                await self._fetch_sentiment()
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                self.logger.error(f"Error in sentiment loop: {e}")
                await asyncio.sleep(600)  # Retry in 10 minutes on error

    async def _fetch_sentiment(self):
        """Fetch sentiment from CryptoPanic API"""
        if not self.use_api:
            return

        try:
            import aiohttp

            # Get crypto news from CryptoPanic
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": self.api_key,
                "currencies": "BTC,ETH,BNB,SOL",  # Major cryptos
                "filter": "hot",  # Hot news
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._process_sentiment_data(data)
                    else:
                        self.logger.warning(f"CryptoPanic API error: {response.status}")
        except ImportError:
            self.logger.warning(
                "aiohttp not installed - cannot fetch sentiment. Install with: pip install aiohttp"
            )
            self.use_api = False
        except Exception as e:
            self.logger.error(f"Error fetching sentiment: {e}")

    def _process_sentiment_data(self, data: Dict):
        """Process CryptoPanic API response and calculate sentiment"""
        try:
            posts = data.get("results", [])
            if not posts:
                return

            # Simple sentiment scoring based on votes
            total_positive = 0
            total_negative = 0
            total_important = 0

            for post in posts:
                votes = post.get("votes", {})
                positive = votes.get("positive", 0)
                negative = votes.get("negative", 0)
                important = votes.get("important", 0)

                total_positive += positive
                total_negative += negative
                total_important += important

            # Calculate sentiment score (-1 to 1)
            total_votes = total_positive + total_negative
            if total_votes > 0:
                sentiment_score = (total_positive - total_negative) / total_votes
            else:
                sentiment_score = 0.0

            # Weight by importance
            importance_factor = min(total_important / 10, 1.0)  # Max 1.0
            weighted_sentiment = sentiment_score * (0.7 + 0.3 * importance_factor)

            # Update cache
            self.sentiment_cache = {
                "sentiment_score": weighted_sentiment,
                "confidence": min(
                    total_votes / 100, 1.0
                ),  # More votes = higher confidence
                "sources": ["cryptopanic"],
                "total_posts": len(posts),
                "positive_votes": total_positive,
                "negative_votes": total_negative,
                "important_votes": total_important,
                "last_update": datetime.now().isoformat(),
            }

            self.logger.info(
                f"📰 Sentiment updated: {weighted_sentiment:.3f} ({len(posts)} posts, {total_votes} votes)"
            )

        except Exception as e:
            self.logger.error(f"Error processing sentiment data: {e}")

    async def get_sentiment(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get latest sentiment (with caching)"""
        # Check cache age
        if self.sentiment_cache:
            last_update = datetime.fromisoformat(
                self.sentiment_cache.get("last_update", datetime.now().isoformat())
            )
            age_seconds = (datetime.now() - last_update).total_seconds()

            if age_seconds < self.cache_timeout:
                return self.sentiment_cache

        # If using API and cache is stale, try to fetch
        if self.use_api and not self.sentiment_cache:
            await self._fetch_sentiment()
            if self.sentiment_cache:
                return self.sentiment_cache

        # Fallback to neutral sentiment
        return {
            "sentiment_score": 0.0,  # Neutral
            "confidence": 0.5,
            "sources": ["none"],
            "last_update": datetime.now().isoformat(),
            "note": "Using neutral sentiment - configure CryptoPanic API for real data",
        }

    async def get_sentiment_for_symbol(self, symbol: str) -> float:
        """Get sentiment score for specific symbol (-1 to 1)"""
        sentiment = await self.get_sentiment(symbol)
        return sentiment.get("sentiment_score", 0.0)

    async def get_status(self) -> Dict[str, Any]:
        has_sentiment = bool(self.sentiment_cache)
        return {
            "running": self.running,
            "status": "active" if self.running else "stopped",
            "api_enabled": self.use_api,
            "has_recent_sentiment": has_sentiment,
            "last_update": (
                self.sentiment_cache.get("last_update")
                if self.sentiment_cache
                else None
            ),
        }


class ExecutionAgent:
    """Agent for trade execution"""

    def __init__(
        self, config_manager: ConfigManager, exchange: Optional[BaseExchange] = None
    ):
        self.config_manager = config_manager
        self.exchange = exchange
        self.logger = get_logger(__name__)
        self.running = False
        self.execution_history = []

    async def initialize(self):
        self.logger.info("⚡ Initializing Execution Agent...")

        if not self.exchange:
            self.logger.warning(
                "⚠️ No exchange provided - ExecutionAgent will not be able to execute orders"
            )
        else:
            self.logger.info("✅ Exchange connection available for order execution")

    async def start(self):
        self.running = True
        self.logger.info("🚀 Execution Agent started")

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Execution Agent stopped")

    async def execute_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trading order via exchange"""
        if not self.exchange:
            self.logger.error("❌ Cannot execute order - no exchange available")
            return {
                "order_id": None,
                "status": "failed",
                "error": "No exchange connection",
                "order": order,
            }

        try:
            symbol = order.get("symbol")
            side = order.get("side")  # 'buy' or 'sell'
            amount = order.get("amount")

            # Validate order parameters
            if not symbol or not side or not amount:
                raise ValueError("Missing required order parameters")

            # Execute via exchange
            if side.lower() == "buy":
                result = await self.exchange.create_market_buy_order(symbol, amount)
            elif side.lower() == "sell":
                result = await self.exchange.create_market_sell_order(symbol, amount)
            else:
                raise ValueError(f"Invalid order side: {side}")

            # Track execution
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "order": order,
                "result": result,
                "status": "filled" if result else "failed",
            }
            self.execution_history.append(execution_record)

            self.logger.info(
                f"✅ Order executed: {side.upper()} {amount} {symbol} - Order ID: {result.get('id', 'N/A')}"
            )

            return {
                "order_id": result.get("id"),
                "status": "filled" if result else "failed",
                "filled_price": result.get("price"),
                "filled_amount": result.get("filled"),
                "fee": result.get("fee"),
                "order": order,
                "exchange_response": result,
            }

        except Exception as e:
            self.logger.error(f"❌ Order execution failed: {e}")
            return {
                "order_id": None,
                "status": "failed",
                "error": str(e),
                "order": order,
            }

    async def get_execution_history(self) -> list:
        """Get history of executed orders"""
        return self.execution_history

    async def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "total_executions": len(self.execution_history),
            "status": "active" if self.running else "stopped",
        }


class MonitoringAgent:
    """Agent for system monitoring with portfolio tracking and P&L calculation"""

    def __init__(
        self, config_manager: ConfigManager, exchange: Optional[BaseExchange] = None
    ):
        self.config_manager = config_manager
        self.exchange = exchange
        self.logger = get_logger(__name__)
        self.running = False
        self.system_health = {}
        self.start_time = None

        # Portfolio tracking
        self.positions = {}  # {symbol: {entry_price, amount, entry_time}}
        self.initial_portfolio_value = 0.0
        self.portfolio_history = []  # Historical snapshots
        self.trade_history = []  # Track all trades for performance metrics

        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

        # Metrics persistence
        self.metrics_file = "reports/monitoring_metrics.json"

    async def initialize(self):
        self.logger.info("🔍 Initializing Monitoring Agent...")
        self.start_time = datetime.now()

        if not self.exchange:
            self.logger.warning(
                "⚠️ No exchange provided - portfolio monitoring will be limited"
            )
        else:
            # Get initial portfolio value
            try:
                balance = await self.exchange.get_balance()
                if balance:
                    self.initial_portfolio_value = self._calculate_portfolio_value(
                        balance
                    )
                    self.logger.info(
                        f"💰 Initial portfolio value: ${self.initial_portfolio_value:,.2f}"
                    )
            except Exception as e:
                self.logger.warning(f"Could not fetch initial balance: {e}")

        # Load historical metrics if exists (disable for fresh start)
        # Uncomment the line below to load previous metrics:
        # self._load_metrics()

    async def start(self):
        self.running = True
        self.logger.info("🚀 Monitoring Agent started")

        # Start background monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Monitoring Agent stopped")

        # Save metrics before stopping
        self._save_metrics()

    async def _monitoring_loop(self):
        """Background loop to periodically capture metrics"""
        while self.running:
            try:
                # Capture snapshot every 5 minutes
                await asyncio.sleep(300)
                await self._capture_portfolio_snapshot()
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Brief pause on error

    async def _capture_portfolio_snapshot(self):
        """Capture current portfolio state"""
        if not self.exchange:
            return

        try:
            balance = await self.exchange.get_balance()
            if balance:
                snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "portfolio_value": self._calculate_portfolio_value(balance),
                    "balance": balance,
                    "positions": self.positions.copy(),
                }
                self.portfolio_history.append(snapshot)

                # Keep only last 1000 snapshots
                if len(self.portfolio_history) > 1000:
                    self.portfolio_history = self.portfolio_history[-1000:]

                self.logger.debug(
                    f"📸 Portfolio snapshot: ${snapshot['portfolio_value']:,.2f}"
                )

                # Save metrics to disk
                self._save_metrics()
        except Exception as e:
            self.logger.error(f"Error capturing portfolio snapshot: {e}")

    async def track_position(
        self, symbol: str, entry_price: float, amount: float, side: str
    ):
        """Track a new or updated position"""
        if side.lower() == "buy":
            # Opening or adding to position
            if symbol in self.positions:
                # Average down/up
                existing = self.positions[symbol]
                total_amount = existing["amount"] + amount
                avg_price = (
                    existing["entry_price"] * existing["amount"] + entry_price * amount
                ) / total_amount
                self.positions[symbol] = {
                    "entry_price": avg_price,
                    "amount": total_amount,
                    "entry_time": existing["entry_time"],
                    "last_update": datetime.now().isoformat(),
                }
            else:
                # New position
                self.positions[symbol] = {
                    "entry_price": entry_price,
                    "amount": amount,
                    "entry_time": datetime.now().isoformat(),
                    "last_update": datetime.now().isoformat(),
                }
            self.logger.info(
                f"📈 Position opened/added: {amount} {symbol} @ ${entry_price:,.2f}"
            )

            # Save metrics after position update
            self._save_metrics()
        else:
            # Closing position
            if symbol in self.positions:
                position = self.positions[symbol]
                pnl = (entry_price - position["entry_price"]) * amount
                self.total_pnl += pnl

                # Track trade
                self.total_trades += 1
                if pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

                self.trade_history.append(
                    {
                        "symbol": symbol,
                        "entry_price": position["entry_price"],
                        "exit_price": entry_price,
                        "amount": amount,
                        "pnl": pnl,
                        "entry_time": position["entry_time"],
                        "exit_time": datetime.now().isoformat(),
                    }
                )

                # Update or remove position
                if position["amount"] <= amount:
                    del self.positions[symbol]
                    self.logger.info(f"📉 Position closed: {symbol}, P&L: ${pnl:,.2f}")
                else:
                    self.positions[symbol]["amount"] -= amount
                    self.logger.info(
                        f"📉 Partial close: {amount} {symbol}, P&L: ${pnl:,.2f}"
                    )

                # Save metrics after trade
                self._save_metrics()

    async def get_portfolio_pnl(self) -> Dict[str, Any]:
        """Calculate current portfolio P&L"""
        if not self.exchange:
            return {"error": "No exchange connection"}

        try:
            current_balance = await self.exchange.get_balance()
            if not current_balance:
                return {"error": "Could not fetch balance"}

            current_value = self._calculate_portfolio_value(current_balance)
            total_pnl = current_value - self.initial_portfolio_value
            pnl_percentage = (
                (total_pnl / self.initial_portfolio_value * 100)
                if self.initial_portfolio_value > 0
                else 0.0
            )

            # Calculate unrealized P&L from open positions
            unrealized_pnl = 0.0
            for symbol, position in self.positions.items():
                try:
                    ticker = await self.exchange.get_ticker(symbol)
                    # Handle both dict and float returns
                    if isinstance(ticker, dict):
                        current_price = (
                            ticker.get("last", 0) or ticker.get("bid", 0) or 0
                        )
                    else:
                        current_price = ticker or 0

                    if current_price:
                        unrealized_pnl += (
                            current_price - position["entry_price"]
                        ) * position["amount"]
                except Exception as e:
                    self.logger.debug(f"Could not get price for {symbol}: {e}")

            return {
                "initial_value": self.initial_portfolio_value,
                "current_value": current_value,
                "total_pnl": total_pnl,
                "pnl_percentage": pnl_percentage,
                "realized_pnl": self.total_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "win_rate": (
                    self.winning_trades / self.total_trades * 100
                    if self.total_trades > 0
                    else 0.0
                ),
            }
        except Exception as e:
            self.logger.error(f"Error calculating P&L: {e}")
            return {"error": str(e)}

    def _calculate_portfolio_value(self, balance: Dict) -> float:
        """Calculate total portfolio value in USD"""
        total = 0.0
        for currency, data in balance.items():
            if isinstance(data, dict):
                amount = data.get("total", 0.0)
            else:
                amount = data

            # Assume USDT/USD/BUSD are 1:1
            if currency in ["USDT", "USD", "BUSD", "USDC"]:
                total += amount
            # For other currencies, would need to convert to USD
            # This is simplified - in production, fetch exchange rates

        return total

    async def get_health(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics"""
        health_data = {
            "system_status": "healthy" if self.running else "stopped",
            "uptime_seconds": (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time
                else 0
            ),
            "last_check": datetime.now().isoformat(),
        }

        # System metrics
        try:
            import psutil

            health_data["cpu_usage"] = psutil.cpu_percent(interval=0.1)
            health_data["memory_usage"] = psutil.virtual_memory().percent
            health_data["disk_usage"] = psutil.disk_usage("/").percent

            # Process-specific metrics
            process = psutil.Process()
            health_data["process_memory_mb"] = process.memory_info().rss / 1024 / 1024
            health_data["process_cpu_percent"] = process.cpu_percent(interval=0.1)
        except ImportError:
            self.logger.debug("psutil not available - skipping system metrics")
        except Exception as e:
            self.logger.debug(f"Error getting system metrics: {e}")

        # Portfolio balance
        if self.exchange:
            try:
                balance = await self.exchange.get_balance()
                if balance:
                    health_data["portfolio_balance"] = balance
                    health_data["portfolio_value"] = self._calculate_portfolio_value(
                        balance
                    )
            except Exception as e:
                self.logger.debug(f"Could not fetch balance: {e}")

        # Performance metrics
        health_data["open_positions"] = len(self.positions)
        health_data["total_trades"] = self.total_trades
        health_data["win_rate"] = (
            self.winning_trades / self.total_trades * 100
            if self.total_trades > 0
            else 0.0
        )

        return health_data

    def _save_metrics(self):
        """Save metrics to JSON file"""
        try:
            import json
            from pathlib import Path

            # Ensure reports directory exists
            Path("reports").mkdir(exist_ok=True)

            metrics = {
                "last_updated": datetime.now().isoformat(),
                "uptime_seconds": (
                    (datetime.now() - self.start_time).total_seconds()
                    if self.start_time
                    else 0
                ),
                "positions": self.positions,
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "total_pnl": self.total_pnl,
                "initial_portfolio_value": self.initial_portfolio_value,
                "portfolio_history_count": len(self.portfolio_history),
                "trade_history": self.trade_history[-100:],  # Last 100 trades
            }

            with open(self.metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)

            self.logger.info(f"📊 Metrics saved to {self.metrics_file}")
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")

    def _load_metrics(self):
        """Load metrics from JSON file if exists"""
        try:
            import json
            from pathlib import Path

            if Path(self.metrics_file).exists():
                with open(self.metrics_file, "r") as f:
                    metrics = json.load(f)

                self.positions = metrics.get("positions", {})
                self.total_trades = metrics.get("total_trades", 0)
                self.winning_trades = metrics.get("winning_trades", 0)
                self.losing_trades = metrics.get("losing_trades", 0)
                self.total_pnl = metrics.get("total_pnl", 0.0)
                self.trade_history = metrics.get("trade_history", [])

                self.logger.info(
                    f"📊 Loaded metrics: {self.total_trades} trades, ${self.total_pnl:,.2f} P&L"
                )
        except Exception as e:
            self.logger.debug(f"Could not load metrics: {e}")

    async def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "status": "active" if self.running else "stopped",
            "open_positions": len(self.positions),
            "total_trades": self.total_trades,
        }
