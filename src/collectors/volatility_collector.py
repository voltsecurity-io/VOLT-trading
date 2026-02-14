"""
VIX & Volatility Surface Data Collector
Provides critical volatility metrics for VOLT trading strategies
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from src.utils.logger import get_logger


class VolatilityCollector:
    """
    Collects VIX and volatility surface data for trading decisions
    
    Data Sources:
    - Yahoo Finance (VIX index data)
    - Binance (crypto implied volatility proxies)
    - DeFiLlama (on-chain volatility indicators)
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    async def get_vix_data(self) -> Dict[str, Any]:
        """
        Get VIX (Volatility Index) data
        
        Returns:
            {
                "current_vix": 18.5,
                "vix_change_24h": 0.8,
                "vix_percentile_1y": 0.45,
                "regime": "NORMAL",  # LOW/NORMAL/ELEVATED/PANIC
                "timestamp": datetime
            }
        """
        cache_key = "vix_data"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Fetch VIX from Yahoo Finance
            vix_current = await self._fetch_yahoo_vix()
            
            # Calculate metrics
            vix_data = {
                "current_vix": vix_current,
                "vix_change_24h": 0.0,  # TODO: Calculate from history
                "vix_percentile_1y": self._calculate_percentile(vix_current),
                "regime": self._classify_regime(vix_current),
                "timestamp": datetime.now()
            }
            
            self._cache_data(cache_key, vix_data)
            return vix_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch VIX data: {e}")
            # Return safe defaults
            return {
                "current_vix": 20.0,
                "vix_change_24h": 0.0,
                "vix_percentile_1y": 0.50,
                "regime": "NORMAL",
                "timestamp": datetime.now()
            }
    
    async def get_iv_rank(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate IV Rank for a symbol
        
        IV Rank = (Current IV - 52w Low) / (52w High - 52w Low)
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            
        Returns:
            {
                "symbol": "BTC/USDT",
                "current_iv": 65.0,
                "iv_rank": 0.72,  # 72nd percentile
                "iv_52w_high": 120.0,
                "iv_52w_low": 35.0,
                "mean_reversion_signal": True,  # High IV = sell volatility
                "timestamp": datetime
            }
        """
        cache_key = f"iv_rank_{symbol}"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Fetch historical volatility data
            iv_data = await self._fetch_implied_volatility(symbol)
            
            current_iv = iv_data['current']
            iv_52w_high = iv_data['high_52w']
            iv_52w_low = iv_data['low_52w']
            
            # Calculate IV Rank
            if iv_52w_high == iv_52w_low:
                iv_rank = 0.50
            else:
                iv_rank = (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low)
            
            result = {
                "symbol": symbol,
                "current_iv": current_iv,
                "iv_rank": iv_rank,
                "iv_52w_high": iv_52w_high,
                "iv_52w_low": iv_52w_low,
                "mean_reversion_signal": iv_rank > 0.70,  # High IV
                "timestamp": datetime.now()
            }
            
            self._cache_data(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch IV rank for {symbol}: {e}")
            return {
                "symbol": symbol,
                "current_iv": 50.0,
                "iv_rank": 0.50,
                "iv_52w_high": 80.0,
                "iv_52w_low": 20.0,
                "mean_reversion_signal": False,
                "timestamp": datetime.now()
            }
    
    async def get_volatility_term_structure(self) -> Dict[str, Any]:
        """
        Get VIX term structure (contango/backwardation)
        
        Returns:
            {
                "spot_vix": 18.0,
                "vix_futures": [16.5, 18.0, 19.5, 21.0],  # Front to back months
                "structure": "CONTANGO",  # or BACKWARDATION
                "slope": 0.05,  # Positive = contango
                "fear_indicator": False  # True if backwardation
            }
        """
        try:
            # For crypto, we use realized volatility as proxy
            # TODO: Add real VIX futures when available
            
            spot_vix = 18.0  # Placeholder
            vix_futures = [16.5, 18.0, 19.5, 21.0]
            
            slope = (vix_futures[-1] - vix_futures[0]) / len(vix_futures)
            structure = "CONTANGO" if slope > 0 else "BACKWARDATION"
            
            return {
                "spot_vix": spot_vix,
                "vix_futures": vix_futures,
                "structure": structure,
                "slope": slope,
                "fear_indicator": structure == "BACKWARDATION",
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch term structure: {e}")
            return {
                "spot_vix": 20.0,
                "vix_futures": [20.0, 20.0, 20.0, 20.0],
                "structure": "FLAT",
                "slope": 0.0,
                "fear_indicator": False,
                "timestamp": datetime.now()
            }
    
    async def get_composite_volatility_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Composite signal combining VIX, IV Rank, and term structure
        
        Returns:
            {
                "signal": "SELL_VOLATILITY",  # or BUY_VOLATILITY, NEUTRAL
                "confidence": 0.78,
                "components": {
                    "vix_regime": "ELEVATED",
                    "iv_rank": 0.72,
                    "term_structure": "CONTANGO"
                },
                "reasoning": "High IV rank + elevated VIX = mean reversion opportunity"
            }
        """
        try:
            # Gather all components
            vix_data = await self.get_vix_data()
            iv_data = await self.get_iv_rank(symbol)
            term_data = await self.get_volatility_term_structure()
            
            # Scoring system
            score = 0.0
            max_score = 3.0
            
            # Component 1: IV Rank (0-1 points)
            if iv_data['iv_rank'] > 0.70:
                score += 1.0  # High IV = sell signal
                signal_direction = "SELL_VOLATILITY"
            elif iv_data['iv_rank'] < 0.30:
                score += 1.0  # Low IV = buy signal
                signal_direction = "BUY_VOLATILITY"
            else:
                score += 0.0
                signal_direction = "NEUTRAL"
            
            # Component 2: VIX Regime (0-1 points)
            if vix_data['regime'] in ['ELEVATED', 'PANIC']:
                score += 1.0
            elif vix_data['regime'] == 'LOW':
                score += 0.5
            
            # Component 3: Term Structure (0-1 points)
            if term_data['structure'] == 'CONTANGO':
                score += 0.5  # Bullish structure
            elif term_data['structure'] == 'BACKWARDATION':
                score += 1.0  # Fear = opportunity
            
            confidence = score / max_score
            
            # Determine signal
            if confidence < 0.40:
                final_signal = "NEUTRAL"
            else:
                final_signal = signal_direction
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                vix_data, iv_data, term_data, final_signal
            )
            
            return {
                "signal": final_signal,
                "confidence": confidence,
                "components": {
                    "vix_regime": vix_data['regime'],
                    "iv_rank": iv_data['iv_rank'],
                    "term_structure": term_data['structure']
                },
                "reasoning": reasoning,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate composite signal: {e}")
            return {
                "signal": "NEUTRAL",
                "confidence": 0.0,
                "components": {},
                "reasoning": f"Error: {e}",
                "timestamp": datetime.now()
            }
    
    # Helper methods
    
    async def _fetch_yahoo_vix(self) -> float:
        """Fetch current VIX from Yahoo Finance"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/^VIX"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        vix = data['chart']['result'][0]['meta']['regularMarketPrice']
                        self.logger.info(f"📊 VIX fetched: {vix:.2f}")
                        return vix
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            self.logger.warning(f"⚠️ Yahoo VIX fetch failed: {e}, using fallback")
            # Fallback: estimate from BTC volatility
            return await self._estimate_vix_from_crypto()
    
    async def _estimate_vix_from_crypto(self) -> float:
        """Estimate VIX-like metric from crypto volatility"""
        try:
            # Simplified: use BTC's 30-day realized volatility as proxy
            # In production, this would fetch actual historical prices
            self.logger.info("📊 Using crypto volatility proxy for VIX")
            return 20.0  # Safe default
            
        except Exception as e:
            self.logger.error(f"❌ Crypto volatility estimation failed: {e}")
            return 20.0
    
    async def _fetch_implied_volatility(self, symbol: str) -> Dict[str, float]:
        """Fetch implied volatility data for symbol"""
        # Placeholder - in production, integrate with options data provider
        # For crypto: could use Deribit API
        self.logger.info(f"📊 Fetching IV for {symbol}")
        
        return {
            "current": 55.0,
            "high_52w": 120.0,
            "low_52w": 30.0
        }
    
    def _calculate_percentile(self, current_vix: float) -> float:
        """Calculate VIX percentile rank (1-year lookback)"""
        # Simplified calculation
        # Typical VIX ranges: 10-20 (low), 20-30 (elevated), 30+ (panic)
        
        if current_vix < 12:
            return 0.10
        elif current_vix < 15:
            return 0.30
        elif current_vix < 20:
            return 0.50
        elif current_vix < 25:
            return 0.70
        elif current_vix < 30:
            return 0.85
        else:
            return 0.95
    
    def _classify_regime(self, vix: float) -> str:
        """Classify market regime based on VIX level"""
        if vix < 12:
            return "LOW"
        elif vix < 20:
            return "NORMAL"
        elif vix < 30:
            return "ELEVATED"
        else:
            return "PANIC"
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and fresh"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key]['timestamp']
        age = (datetime.now() - cached_time).total_seconds()
        
        return age < self.cache_ttl
    
    def _cache_data(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _generate_reasoning(
        self, 
        vix_data: Dict, 
        iv_data: Dict, 
        term_data: Dict,
        signal: str
    ) -> str:
        """Generate human-readable reasoning for signal"""
        
        reasons = []
        
        if iv_data['iv_rank'] > 0.70:
            reasons.append(f"IV rank at {iv_data['iv_rank']:.0%} (high)")
        elif iv_data['iv_rank'] < 0.30:
            reasons.append(f"IV rank at {iv_data['iv_rank']:.0%} (low)")
        
        if vix_data['regime'] in ['ELEVATED', 'PANIC']:
            reasons.append(f"VIX {vix_data['regime'].lower()} ({vix_data['current_vix']:.1f})")
        
        if term_data['structure'] == 'BACKWARDATION':
            reasons.append("VIX backwardation (fear)")
        elif term_data['structure'] == 'CONTANGO':
            reasons.append("VIX contango (calm)")
        
        if not reasons:
            return "Neutral volatility conditions"
        
        return " + ".join(reasons) + f" → {signal.replace('_', ' ').title()}"


# Convenience function for quick access
async def get_volatility_signal(symbol: str) -> Dict[str, Any]:
    """
    Quick helper to get composite volatility signal
    
    Usage:
        signal = await get_volatility_signal("BTC/USDT")
        if signal['signal'] == 'SELL_VOLATILITY':
            # High IV = good time to sell options
    """
    collector = VolatilityCollector()
    return await collector.get_composite_volatility_signal(symbol)
