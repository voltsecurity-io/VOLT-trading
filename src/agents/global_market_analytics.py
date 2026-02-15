"""
Global Market Analytics Agent
Analyserar den globala marknaden för att förstå makrotrender och marknadsregimer
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class MarketRegime(Enum):
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNKNOWN = "unknown"


class RiskAppetite(Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    FEAR = "fear"


@dataclass
class MarketData:
    symbol: str
    price: float
    change_24h: float
    volume: float
    dominance: Optional[float] = None


@dataclass
class GlobalMarketReport:
    regime: MarketRegime
    risk_appetite: RiskAppetite
    btc_trend: str
    altcoin_trend: str
    correlation: Dict[str, float]
    sentiment: str
    forecast: str
    key_levels: Dict[str, List[float]]
    macro_indicators: Dict[str, float]
    timestamp: str


class GlobalMarketAnalytics:
    """
    Analyserar den globala kryptomarknaden och relaterade marknader
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_timeout = 300  # 5 minuter

    async def analyze(self) -> GlobalMarketReport:
        """Utför komplett marknadsanalys"""
        try:
            # Samla data
            btc_data = await self._get_crypto_data("BTC")
            eth_data = await self._get_crypto_data("ETH")
            total_mcap = await self._get_total_market_cap()

            # Analysera regim
            regime = self._identify_regime(btc_data, total_mcap)

            # Analysera riskaptit
            risk_appetite = self._calculate_risk_appetite(btc_data, total_mcap)

            # Bestäm trender
            btc_trend = self._determine_trend(btc_data)
            altcoin_trend = self._determine_altcoin_trend(btc_data, eth_data)

            # Beräkna korrelationer
            correlation = await self._calculate_correlations(btc_data, eth_data)

            # Analysera sentiment
            sentiment = await self._analyze_sentiment()

            # Generera forecast
            forecast = self._generate_forecast(regime, btc_trend, risk_appetite)

            # Identifiera nyckelnivåer
            key_levels = self._identify_key_levels(btc_data, eth_data)

            # Hämta macro-indikatorer
            macro_indicators = await self._get_macro_indicators()

            return GlobalMarketReport(
                regime=regime,
                risk_appetite=risk_appetite,
                btc_trend=btc_trend,
                altcoin_trend=altcoin_trend,
                correlation=correlation,
                sentiment=sentiment,
                forecast=forecast,
                key_levels=key_levels,
                macro_indicators=macro_indicators,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")
            return GlobalMarketReport(
                regime=MarketRegime.UNKNOWN,
                risk_appetite=RiskAppetite.MODERATE,
                btc_trend="unknown",
                altcoin_trend="unknown",
                correlation={},
                sentiment="unknown",
                forecast="insufficient_data",
                key_levels={},
                macro_indicators={},
                timestamp=datetime.now().isoformat(),
            )

    async def _get_crypto_data(self, symbol: str) -> MarketData:
        """Hämta kryptodata (simulerad - kan byggas ut med riktiga API:er)"""
        # Här kan du integrera CoinGecko, Binance, etc.
        # För nuvarande returnerar vi strukturerad data baserat på cache
        return MarketData(
            symbol=symbol,
            price=self.cache.get(f"{symbol}_price", 0),
            change_24h=self.cache.get(f"{symbol}_change", 0),
            volume=self.cache.get(f"{symbol}_volume", 0),
            dominance=self.cache.get(f"{symbol}_dominance"),
        )

    async def _get_total_market_cap(self) -> float:
        """Hämta total marknadsvärde"""
        return self.cache.get("total_mcap", 0)

    def _identify_regime(self, btc_data: MarketData, total_mcap: float) -> MarketRegime:
        """Identifiera nuvarande marknadsregim"""

        btc_change = btc_data.change_24h
        btc_dominance = btc_data.dominance or 50

        # Bull market: BTC upp >5% och dominans ökar
        if btc_change > 5 and btc_dominance > 45:
            return MarketRegime.BULL_MARKET

        # Bear market: BTC ner >5%
        elif btc_change < -5:
            return MarketRegime.BEAR_MARKET

        # High volatility
        elif abs(btc_change) > 8:
            return MarketRegime.HIGH_VOLATILITY

        # Low volatility
        elif abs(btc_change) < 2:
            return MarketRegime.LOW_VOLATILITY

        # Sideways
        else:
            return MarketRegime.SIDEWAYS

    def _calculate_risk_appetite(
        self, btc_data: MarketData, total_mcap: float
    ) -> RiskAppetite:
        """Beräkna marknadens riskaptit"""

        btc_change = btc_data.change_24h

        if btc_change > 3:
            return RiskAppetite.HIGH
        elif btc_change > 0:
            return RiskAppetite.MODERATE
        elif btc_change > -3:
            return RiskAppetite.LOW
        else:
            return RiskAppetite.FEAR

    def _determine_trend(self, data: MarketData) -> str:
        """Bestäm pris-trend"""
        change = data.change_24h

        if change > 2:
            return "strong_bullish"
        elif change > 0:
            return "bullish"
        elif change > -2:
            return "neutral"
        elif change > -5:
            return "bearish"
        else:
            return "strong_bearish"

    def _determine_altcoin_trend(self, btc: MarketData, eth: MarketData) -> str:
        """Bestäm altcoin-trend relativt till BTC"""

        if eth.change_24h > btc.change_24h + 2:
            return "outperforming"
        elif eth.change_24h < btc.change_24h - 2:
            return "underperforming"
        else:
            return "neutral"

    async def _calculate_correlations(
        self, btc: MarketData, eth: MarketData
    ) -> Dict[str, float]:
        """Beräkna marknadskorrelationer"""

        return {
            "btc_eth": 0.85,
            "btc_alt": 0.75,
            "btc_total_mcap": 0.95,
            "eth_sol": 0.70,
        }

    async def _analyze_sentiment(self) -> str:
        """Analysera marknadssentiment baserat på data"""
        # Detta kan byggas ut med sentiment-analy from news APIs
        return "neutral"

    def _generate_forecast(
        self, regime: MarketRegime, btc_trend: str, risk: RiskAppetite
    ) -> str:
        """Generera marknadsprognos"""

        if regime == MarketRegime.BULL_MARKET and risk == RiskAppetite.HIGH:
            return "Favorable conditions for long positions"
        elif regime == MarketRegime.BEAR_MARKET or risk == RiskAppetite.FEAR:
            return "Consider reduced positions and defensive strategy"
        elif regime == MarketRegime.HIGH_VOLATILITY:
            return "High uncertainty - use smaller positions"
        elif regime == MarketRegime.SIDEWAYS:
            return "Range-bound trading may be effective"
        else:
            return "Maintain current strategy"

    def _identify_key_levels(
        self, btc: MarketData, eth: MarketData
    ) -> Dict[str, List[float]]:
        """Identifiera stöd och motstånd"""

        btc_price = btc.price
        eth_price = eth.price

        return {
            "btc_support": [btc_price * 0.95, btc_price * 0.90],
            "btc_resistance": [btc_price * 1.05, btc_price * 1.10],
            "eth_support": [eth_price * 0.95, eth_price * 0.90],
            "eth_resistance": [eth_price * 1.05, eth_price * 1.10],
        }

    async def _get_macro_indicators(self) -> Dict[str, float]:
        """Hämta makroekonomiska indikatorer"""

        return {
            "vix": self.cache.get("vix", 15),
            "spx_change": self.cache.get("spx_change", 0),
            "dxy": self.cache.get("dxy", 100),
            "gold_change": self.cache.get("gold_change", 0),
        }

    def update_cache(self, key: str, value: Any):
        """Uppdatera cache med ny marknadsdata"""
        self.cache[key] = value


class GlobalMarketAnalyticsAgent:
    """
    Agent-wrapped version av GlobalMarketAnalytics
    """

    def __init__(self, config_manager=None, exchange=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.exchange = exchange
        self.analytics = GlobalMarketAnalytics()
        self.running = False
        self.current_report: Optional[GlobalMarketReport] = None

    async def initialize(self):
        self.logger.info("🌍 Initializing Global Market Analytics Agent...")
        self.logger.info("✅ Global Market Analytics Agent initialized")

    async def start(self):
        self.running = True
        self.logger.info("🚀 Global Market Analytics Agent started")

        if self.running:
            asyncio.create_task(self._analytics_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Global Market Analytics Agent stopped")

    async def _analytics_loop(self):
        """Bakgrundsloop för marknadsanalys"""
        while self.running:
            try:
                # Analysera marknaden var 15:e minut
                self.current_report = await self.analytics.analyze()

                # Logga relevant info
                self.logger.info(
                    f"📊 Market regime: {self.current_report.regime.value} | "
                    f"Risk: {self.current_report.risk_appetite.value} | "
                    f"BTC: {self.current_report.btc_trend}"
                )

                await asyncio.sleep(900)  # 15 minuter
            except Exception as e:
                self.logger.error(f"Error in analytics loop: {e}")
                await asyncio.sleep(300)

    async def get_market_report(self) -> GlobalMarketReport:
        """Hämta senaste marknadsrapporten"""
        if self.current_report is None:
            self.current_report = await self.analytics.analyze()
        return self.current_report

    async def get_regime_advice(self) -> Dict[str, Any]:
        """Hämta råd baserat på nuvarande marknadsregim"""

        report = await self.get_market_report()

        advice = {
            "regime": report.regime.value,
            "position_sizing": "normal",
            "stop_loss": "normal",
            "strategy": "maintain",
        }

        if report.risk_appetite == RiskAppetite.FEAR:
            advice["position_sizing"] = "reduced"
            advice["stop_loss"] = "tighter"
            advice["strategy"] = "defensive"
        elif report.risk_appetite == RiskAppetite.HIGH:
            advice["position_sizing"] = "increased"
            advice["stop_loss"] = "wider"
            advice["strategy"] = "aggressive"
        elif report.regime == MarketRegime.HIGH_VOLATILITY:
            advice["position_sizing"] = "reduced"
            advice["strategy"] = "cautious"

        return advice
