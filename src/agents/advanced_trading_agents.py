"""
Advanced Trading Agents for Forex, Macro Economy, Micro Economy and Global Factors
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.exchanges.exchange_factory import BaseExchange


class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class ForexTradingAgent:
    """Agent for Forex (currency) trading analysis and signals"""

    def __init__(
        self, config_manager: ConfigManager, exchange: Optional[BaseExchange] = None
    ):
        self.config_manager = config_manager
        self.exchange = exchange
        self.logger = get_logger(__name__)
        self.running = False

        self.forex_pairs = [
            "EUR/USD",
            "GBP/USD",
            "USD/JPY",
            "USD/CHF",
            "AUD/USD",
            "USD/CAD",
            "NZD/USD",
            "EUR/GBP",
            "EUR/JPY",
            "GBP/JPY",
        ]

        self.pair_data = {}
        self.correlation_matrix = {}
        self.cache_timeout = 300

    async def initialize(self):
        self.logger.info("💱 Initializing Forex Trading Agent...")
        self.forex_pairs = self.config_manager.get("forex.pairs", self.forex_pairs)
        self.logger.info(f"📊 Tracking {len(self.forex_pairs)} Forex pairs")

    async def start(self):
        self.running = True
        self.logger.info("🚀 Forex Trading Agent started")
        if self.exchange:
            asyncio.create_task(self._forex_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Forex Trading Agent stopped")

    async def _forex_loop(self):
        while self.running:
            try:
                await self._fetch_forex_data()
                await self._calculate_correlations()
                await asyncio.sleep(300)
            except Exception as e:
                self.logger.error(f"Error in forex loop: {e}")
                await asyncio.sleep(60)

    async def _fetch_forex_data(self):
        if not self.exchange:
            return

        for pair in self.forex_pairs:
            try:
                ticker = await self.exchange.get_ticker(pair)
                # Handle case where pair doesn't exist on exchange
                if not ticker or (isinstance(ticker, dict) and not ticker.get("last")):
                    continue

                if isinstance(ticker, dict):
                    self.pair_data[pair] = {
                        "bid": ticker.get("bid", 0),
                        "ask": ticker.get("ask", 0),
                        "last": ticker.get("last", 0),
                        "volume": ticker.get("volume", 0),
                        "change_24h": ticker.get("percentage", 0)
                        or ticker.get("change_24h", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    self.pair_data[pair] = {
                        "bid": ticker,
                        "ask": ticker,
                        "last": ticker,
                        "volume": 0,
                        "change_24h": 0,
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception as e:
                self.logger.debug(f"Could not fetch {pair}: {e}")

    async def _calculate_correlations(self):
        pairs = list(self.pair_data.keys())
        for i, pair1 in enumerate(pairs):
            for pair2 in pairs[i + 1 :]:
                try:
                    p1_change = self.pair_data[pair1].get("change_24h", 0)
                    p2_change = self.pair_data[pair2].get("change_24h", 0)

                    if p1_change != 0 and p2_change != 0:
                        correlation = (p1_change * p2_change) / abs(
                            p1_change * p2_change
                        )
                    else:
                        correlation = 0

                    self.correlation_matrix[f"{pair1}_{pair2}"] = correlation
                except:
                    pass

    async def get_forex_analysis(self, pair: str) -> Dict[str, Any]:
        if pair not in self.pair_data:
            return {"error": f"Pair {pair} not found"}

        data = self.pair_data[pair]
        spread = (
            (data["ask"] - data["bid"]) / data["last"] * 10000 if data["last"] else 0
        )

        trend = TrendDirection.NEUTRAL
        if data.get("change_24h", 0) > 0.5:
            trend = TrendDirection.BULLISH
        elif data.get("change_24h", 0) < -0.5:
            trend = TrendDirection.BEARISH

        return {
            "pair": pair,
            "bid": data.get("bid"),
            "ask": data.get("ask"),
            "last": data.get("last"),
            "spread_pips": round(spread, 2),
            "change_24h": data.get("change_24h", 0),
            "trend": trend.value,
            "timestamp": data.get("timestamp"),
        }

    async def get_correlation(self, pair1: str, pair2: str) -> float:
        key = f"{pair1}_{pair2}"
        reverse_key = f"{pair2}_{pair1}"
        return (
            self.correlation_matrix.get(key)
            or self.correlation_matrix.get(reverse_key)
            or 0
        )

    async def get_all_forex_data(self) -> Dict[str, Any]:
        return {
            "pairs": {
                pair: await self.get_forex_analysis(pair)
                for pair in self.forex_pairs
                if pair in self.pair_data
            },
            "correlations": self.correlation_matrix,
            "last_update": datetime.now().isoformat(),
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "pairs_tracked": len(self.pair_data),
            "status": "active" if self.running else "stopped",
        }


class MacroEconomicAgent:
    """Agent for macroeconomic analysis affecting financial markets"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.running = False

        self.economic_indicators = {}
        self.central_bank_rates = {}
        self.calendar_events = []

        self.api_keys = {
            "fred": config_manager.get("macro.fred_api_key", None),
            "newsapi": config_manager.get("macro.newsapi_key", None),
        }

        self.cache_timeout = 3600

    async def initialize(self):
        self.logger.info("🏛️ Initializing Macro Economic Agent...")

        if self.api_keys["fred"]:
            self.logger.info("✅ FRED API configured")
        else:
            self.logger.info("⚠️ No FRED API - using cached/static data")

        self.economic_indicators = {
            "us_dollar_index": {"value": 0, "source": "calculated"},
            "fear_greed_index": {"value": 50, "source": "default"},
            "vix_index": {"value": 20, "source": "default"},
            "us_10y_yield": {"value": 0, "source": "default"},
            "us_2y_yield": {"value": 0, "source": "default"},
        }

    async def start(self):
        self.running = True
        self.logger.info("🚀 Macro Economic Agent started")
        asyncio.create_task(self._macro_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Macro Economic Agent stopped")

    async def _macro_loop(self):
        while self.running:
            try:
                await self._fetch_economic_indicators()
                await self._fetch_central_bank_rates()
                await self._fetch_upcoming_events()
                await asyncio.sleep(3600)
            except Exception as e:
                self.logger.error(f"Error in macro loop: {e}")
                await asyncio.sleep(1800)

    async def _fetch_economic_indicators(self):
        try:
            import aiohttp

            if self.api_keys.get("fred"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://api.stlouisfed.org/fred/series/observations",
                        params={
                            "series_id": "DTINTH",
                            "api_key": self.api_keys["fred"],
                            "observation_start": "2024-01-01",
                        },
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            observations = data.get("observations", [])
                            if observations:
                                latest = observations[-1]
                                self.economic_indicators["us_dollar_index"] = {
                                    "value": float(latest.get("value", 0)),
                                    "source": "fred",
                                }
        except ImportError:
            self.logger.debug("aiohttp not available")
        except Exception as e:
            self.logger.debug(f"Could not fetch FRED data: {e}")

    async def _fetch_central_bank_rates(self):
        self.central_bank_rates = {
            "US_FED": {"rate": 5.25, "last_update": "2024-01-01"},
            "ECB": {"rate": 4.50, "last_update": "2024-01-01"},
            "BOJ": {"rate": -0.10, "last_update": "2024-01-01"},
            "BOE": {"rate": 5.25, "last_update": "2024-01-01"},
        }

    async def _fetch_upcoming_events(self):
        self.calendar_events = [
            {"date": "2025-03-20", "event": "FOMC Meeting", "impact": "high"},
            {"date": "2025-04-03", "event": "ECB Meeting", "impact": "high"},
            {"date": "2025-04-10", "event": "US CPI Release", "impact": "high"},
        ]

    async def get_macro_analysis(self) -> Dict[str, Any]:
        return {
            "indicators": self.economic_indicators,
            "central_bank_rates": self.central_bank_rates,
            "upcoming_events": self.calendar_events,
            "market_sentiment": self._calculate_macro_sentiment(),
            "last_update": datetime.now().isoformat(),
        }

    def _calculate_macro_sentiment(self) -> str:
        vix = self.economic_indicators.get("vix_index", {}).get("value", 20)
        if vix < 15:
            return "bullish"
        elif vix > 30:
            return "fearful"
        return "neutral"

    async def get_impact_assessment(self, event_type: str) -> Dict[str, Any]:
        high_impact_events = [
            e for e in self.calendar_events if e.get("impact") == "high"
        ]

        return {
            "event_type": event_type,
            "high_impact_count": len(high_impact_events),
            "next_high_impact": high_impact_events[0] if high_impact_events else None,
            "recommended_action": "reduce_exposure"
            if len(high_impact_events) > 2
            else "maintain",
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "indicators_tracked": len(self.economic_indicators),
            "events_upcoming": len(self.calendar_events),
            "status": "active" if self.running else "stopped",
        }


class MicroEconomicAgent:
    """Agent for microeconomic analysis - company/project specific factors"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.running = False

        self.crypto_data = {}
        self.token_metrics = {}
        self.onchain_metrics = {}

    async def initialize(self):
        self.logger.info("🏢 Initializing Micro Economic Agent...")

        self.tracked_assets = self.config_manager.get(
            "micro.tracked_assets", ["BTC", "ETH", "BNB", "SOL", "XRP"]
        )

    async def start(self):
        self.running = True
        self.logger.info("🚀 Micro Economic Agent started")
        asyncio.create_task(self._micro_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Micro Economic Agent stopped")

    async def _micro_loop(self):
        while self.running:
            try:
                await self._fetch_token_metrics()
                await self._fetch_onchain_metrics()
                await asyncio.sleep(600)
            except Exception as e:
                self.logger.error(f"Error in micro loop: {e}")
                await asyncio.sleep(300)

    async def _fetch_token_metrics(self):
        self.token_metrics = {
            "BTC": {
                "network_growth": 2.5,
                "active_addresses": 1200000,
                "hash_rate": 500,
            },
            "ETH": {"network_growth": 3.1, "active_addresses": 500000, "gas_gwei": 20},
            "SOL": {"network_growth": 5.2, "active_addresses": 80000, "tps": 3000},
        }

    async def _fetch_onchain_metrics(self):
        self.onchain_metrics = {
            "total_value_locked": 150000000000,
            "defi_total": 20000000000,
            "stablecoin_mcap": 160000000000,
            "nft_volume_24h": 50000000,
        }

    async def get_micro_analysis(self, asset: str) -> Dict[str, Any]:
        token_data = self.token_metrics.get(asset, {})

        supply_growth = token_data.get("network_growth", 0)
        demand_score = 0

        if supply_growth < 3:
            demand_score = 0.8
        elif supply_growth < 5:
            demand_score = 0.5
        else:
            demand_score = 0.2

        return {
            "asset": asset,
            "network_growth": token_data.get("network_growth"),
            "active_addresses": token_data.get("active_addresses"),
            "demand_score": demand_score,
            "supply_pressure": "low" if supply_growth < 3 else "high",
            "fundamentals": "strong" if demand_score > 0.6 else "weak",
        }

    async def get_defi_overview(self) -> Dict[str, Any]:
        return {
            "total_value_locked": self.onchain_metrics.get("total_value_locked"),
            "defi_total": self.onchain_metrics.get("defi_total"),
            "stablecoin_mcap": self.onchain_metrics.get("stablecoin_mcap"),
            "nft_volume_24h": self.onchain_metrics.get("nft_volume_24h"),
            "sector_health": self._assess_defi_health(),
        }

    def _assess_defi_health(self) -> str:
        tvl = self.onchain_metrics.get("total_value_locked", 0)
        if tvl > 100000000000:
            return "strong"
        elif tvl > 50000000000:
            return "moderate"
        return "weak"

    async def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "assets_tracked": len(self.token_metrics),
            "status": "active" if self.running else "stopped",
        }


class GlobalFactorsAgent:
    """Agent for analyzing global factors affecting currency and crypto values"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.running = False

        self.geopolitical_events = []
        self.regulation_news = []
        self.market_sentiment = {}
        self.weather_impact = {}

    async def initialize(self):
        self.logger.info("🌍 Initializing Global Factors Agent...")

    async def start(self):
        self.running = True
        self.logger.info("🚀 Global Factors Agent started")
        asyncio.create_task(self._global_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Global Factors Agent stopped")

    async def _global_loop(self):
        while self.running:
            try:
                await self._fetch_geopolitical_events()
                await self._fetch_regulation_news()
                await self._assess_sentiment()
                await asyncio.sleep(1800)
            except Exception as e:
                self.logger.error(f"Error in global loop: {e}")
                await asyncio.sleep(900)

    async def _fetch_geopolitical_events(self):
        self.geopolitical_events = [
            {"region": "EU", "event": "EU Regulation Update", "impact": "medium"},
            {"region": "US", "event": "Trade Policy Updates", "impact": "high"},
            {"region": "APAC", "event": "China Economic Data", "impact": "high"},
        ]

    async def _fetch_regulation_news(self):
        self.regulation_news = [
            {"country": "US", "regulation": "SEC Guidelines", "status": "pending"},
            {"country": "EU", "regulation": "MiCA Framework", "status": "active"},
            {"country": "UK", "regulation": "FCA Rules", "status": "active"},
        ]

    async def _assess_sentiment(self):
        self.market_sentiment = {
            "overall": "neutral",
            "risk_appetite": "moderate",
            "flight_to_safety": False,
            "innovation_sentiment": "positive",
        }

    async def get_global_analysis(self) -> Dict[str, Any]:
        return {
            "geopolitical_events": self.geopolitical_events,
            "regulation_news": self.regulation_news,
            "sentiment": self.market_sentiment,
            "risk_factors": self._identify_risks(),
            "opportunities": self._identify_opportunities(),
            "last_update": datetime.now().isoformat(),
        }

    def _identify_risks(self) -> List[Dict[str, str]]:
        risks = []

        for event in self.geopolitical_events:
            if event.get("impact") == "high":
                risks.append(
                    {
                        "type": "geopolitical",
                        "region": event.get("region"),
                        "description": event.get("event"),
                        "severity": "high",
                    }
                )

        for reg in self.regulation_news:
            if reg.get("status") == "pending":
                risks.append(
                    {
                        "type": "regulatory",
                        "country": reg.get("country"),
                        "description": reg.get("regulation"),
                        "severity": "medium",
                    }
                )

        return risks

    def _identify_opportunities(self) -> List[Dict[str, str]]:
        opportunities = []

        if self.market_sentiment.get("innovation_sentiment") == "positive":
            opportunities.append(
                {
                    "type": "innovation",
                    "description": "Positive regulatory clarity in major markets",
                    "potential": "high",
                }
            )

        return opportunities

    async def get_regulation_impact(self, country: str) -> Dict[str, Any]:
        country_reg = [r for r in self.regulation_news if r.get("country") == country]

        return {
            "country": country,
            "regulations": country_reg,
            "status": country_reg[0].get("status") if country_reg else "unknown",
            "compliance_risk": "high"
            if any(r.get("status") == "pending" for r in country_reg)
            else "low",
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "events_tracked": len(self.geopolitical_events),
            "regulations_tracked": len(self.regulation_news),
            "status": "active" if self.running else "stopped",
        }
