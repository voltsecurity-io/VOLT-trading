"""
VOLT Trading Dashboard
Real-time monitoring and control interface built with Streamlit
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager
from src.exchanges.exchange_factory import ExchangeFactory
from src.agents.simple_agents import MonitoringAgent, SentimentAnalysisAgent

# Page config
st.set_page_config(
    page_title="VOLT Trading Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive { color: #00ff00; }
    .negative { color: #ff0000; }
    .neutral { color: #888888; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_config_and_exchange():
    """Initialize config and exchange (cached)"""
    config_manager = ConfigManager()
    exchange_config = config_manager.get_exchange_config()
    
    # Run async initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    exchange = ExchangeFactory.create_exchange(
        exchange_config["name"], exchange_config
    )
    loop.run_until_complete(exchange.initialize())
    
    return config_manager, exchange, loop


def load_monitoring_metrics():
    """Load metrics from MonitoringAgent file"""
    metrics_file = Path("reports/monitoring_metrics.json")
    if metrics_file.exists():
        with open(metrics_file, "r") as f:
            return json.load(f)
    return None


async def fetch_live_price(exchange, symbol):
    """Fetch live price for a symbol"""
    try:
        price = await exchange.get_ticker(symbol)
        return price
    except Exception as e:
        st.error(f"Error fetching price for {symbol}: {e}")
        return None


async def fetch_ohlcv(exchange, symbol, timeframe="5m", limit=100):
    """Fetch OHLCV data for charting"""
    try:
        data = await exchange.get_ohlcv(symbol, timeframe, limit)
        if data:
            df = pd.DataFrame(
                data, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df
        return None
    except Exception as e:
        st.error(f"Error fetching OHLCV for {symbol}: {e}")
        return None


def create_candlestick_chart(df, symbol):
    """Create candlestick chart with volume"""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f"{symbol} Price", "Volume"),
        row_heights=[0.7, 0.3],
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # Volume bars
    colors = [
        "green" if df["close"].iloc[i] >= df["open"].iloc[i] else "red"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(x=df["timestamp"], y=df["volume"], name="Volume", marker_color=colors),
        row=2,
        col=1,
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0),
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Price (USDT)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig


def main():
    """Main dashboard function"""
    
    # Header
    st.title("⚡ VOLT Trading Dashboard")
    st.markdown("---")

    # Initialize
    config_manager, exchange, loop = get_config_and_exchange()
    trading_config = config_manager.get_trading_config()
    exchange_config = config_manager.get_exchange_config()

    # Sidebar - System Controls
    with st.sidebar:
        st.header("🎛️ System Controls")
        
        # System mode
        mode = "🟡 SANDBOX" if exchange_config.get("sandbox", True) else "🔴 LIVE"
        st.metric("Trading Mode", mode)
        
        # Exchange info
        st.metric("Exchange", exchange_config.get("name", "Unknown"))
        
        st.markdown("---")
        
        # Control buttons (placeholder - would integrate with control.py)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start", use_container_width=True):
                st.info("Start trading (integration with control.py needed)")
        with col2:
            if st.button("⏸️ Stop", use_container_width=True):
                st.info("Stop trading (integration with control.py needed)")
        
        st.markdown("---")
        
        # Refresh settings
        st.subheader("🔄 Auto Refresh")
        auto_refresh = st.checkbox("Enable Auto-Refresh", value=True)
        refresh_interval = st.slider("Interval (seconds)", 5, 60, 10)
        
        if auto_refresh:
            st.info(f"Refreshing every {refresh_interval}s")

    # Load monitoring metrics
    metrics = load_monitoring_metrics()

    # Row 1: Key Metrics
    st.header("📊 Portfolio Overview")
    col1, col2, col3, col4 = st.columns(4)

    if metrics:
        with col1:
            portfolio_value = metrics.get("initial_portfolio_value", 0)
            st.metric(
                "Portfolio Value",
                f"${portfolio_value:,.2f}",
                help="Initial portfolio value",
            )

        with col2:
            total_pnl = metrics.get("total_pnl", 0)
            pnl_color = "positive" if total_pnl >= 0 else "negative"
            st.metric(
                "Total P&L",
                f"${total_pnl:,.2f}",
                delta=f"{(total_pnl/portfolio_value*100) if portfolio_value > 0 else 0:.2f}%",
                help="Realized profit/loss",
            )

        with col3:
            total_trades = metrics.get("total_trades", 0)
            winning = metrics.get("winning_trades", 0)
            win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1f}%", help=f"{winning}/{total_trades} trades")

        with col4:
            open_positions = len(metrics.get("positions", {}))
            st.metric("Open Positions", open_positions)
    else:
        st.warning("No monitoring metrics available. Start trading to see data.")
        col1.metric("Portfolio Value", "$0.00")
        col2.metric("Total P&L", "$0.00")
        col3.metric("Win Rate", "0%")
        col4.metric("Open Positions", "0")

    st.markdown("---")

    # Row 2: Live Price Charts
    st.header("📈 Live Price Charts")
    
    symbols = trading_config.get("pairs", ["BTC/USDT", "ETH/USDT"])
    timeframe = trading_config.get("timeframe", "5m")
    
    tabs = st.tabs([symbol.replace("/", "-") for symbol in symbols[:4]])  # Max 4 charts

    for idx, symbol in enumerate(symbols[:4]):
        with tabs[idx]:
            # Fetch OHLCV data
            df = loop.run_until_complete(fetch_ohlcv(exchange, symbol, timeframe, 100))
            
            if df is not None and len(df) > 0:
                # Create chart
                fig = create_candlestick_chart(df, symbol)
                st.plotly_chart(fig, use_container_width=True)
                
                # Current price
                current_price = df.iloc[-1]["close"]
                price_change = df.iloc[-1]["close"] - df.iloc[0]["close"]
                price_change_pct = (price_change / df.iloc[0]["close"]) * 100
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Price", f"${current_price:,.2f}")
                col2.metric("Change", f"${price_change:,.2f}", f"{price_change_pct:.2f}%")
                col3.metric("Volume", f"{df.iloc[-1]['volume']:,.0f}")
            else:
                st.error(f"Could not load data for {symbol}")

    st.markdown("---")

    # Row 3: Open Positions & Recent Trades
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Open Positions")
        if metrics and metrics.get("positions"):
            positions_data = []
            for symbol, pos in metrics["positions"].items():
                positions_data.append(
                    {
                        "Symbol": symbol,
                        "Amount": f"{pos['amount']:.4f}",
                        "Entry Price": f"${pos['entry_price']:,.2f}",
                        "Entry Time": pos["entry_time"][:19],  # Truncate timestamp
                    }
                )
            st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
        else:
            st.info("No open positions")

    with col2:
        st.subheader("📜 Recent Trades")
        if metrics and metrics.get("trade_history"):
            trades = metrics["trade_history"][-10:]  # Last 10 trades
            trades_data = []
            for trade in trades:
                pnl = trade.get("pnl", 0)
                trades_data.append(
                    {
                        "Symbol": trade["symbol"],
                        "Entry": f"${trade['entry_price']:,.2f}",
                        "Exit": f"${trade['exit_price']:,.2f}",
                        "P&L": f"${pnl:,.2f}",
                        "Result": "✅ Win" if pnl > 0 else "❌ Loss",
                    }
                )
            st.dataframe(pd.DataFrame(trades_data), use_container_width=True)
        else:
            st.info("No trade history")

    st.markdown("---")

    # Row 4: System Health
    st.header("🏥 System Health")
    
    # Create monitoring agent to get health
    monitoring = MonitoringAgent(config_manager, exchange)
    loop.run_until_complete(monitoring.initialize())
    health = loop.run_until_complete(monitoring.get_health())

    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("System Status", health.get("system_status", "unknown").upper())
    col2.metric("Uptime", f"{health.get('uptime_seconds', 0):.0f}s")
    
    if "cpu_usage" in health:
        col3.metric("CPU Usage", f"{health['cpu_usage']:.1f}%")
    if "memory_usage" in health:
        col4.metric("Memory Usage", f"{health['memory_usage']:.1f}%")

    # Footer
    st.markdown("---")
    st.caption(
        f"VOLT Trading Dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
