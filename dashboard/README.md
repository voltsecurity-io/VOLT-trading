# VOLT Trading Dashboard

Web-based monitoring interface for VOLT Trading system.

## Features

- 📊 **Real-time Portfolio Metrics**
  - Portfolio value
  - Total P&L (realized + unrealized)
  - Win rate statistics
  - Open positions count

- 📈 **Live Price Charts**
  - Interactive candlestick charts (Plotly)
  - Volume indicators
  - Multiple symbols/pairs
  - Customizable timeframes

- 📋 **Position Management**
  - View all open positions
  - Entry prices and amounts
  - Entry timestamps

- 📜 **Trade History**
  - Recent trades log
  - Win/loss indicators
  - P&L per trade

- 🏥 **System Health**
  - CPU and memory usage
  - System uptime
  - Trading mode (sandbox/live)

- 🔄 **Auto-Refresh**
  - Configurable refresh interval (5-60 seconds)
  - Toggle on/off

## Installation

Dependencies are already installed if you completed Fas 3 setup:

```bash
pip install streamlit plotly
```

## Usage

### Start Dashboard

From VOLT-trading root directory:

```bash
streamlit run dashboard/app.py
```

Or use the launch script:

```bash
./launch_dashboard.sh
```

The dashboard will open in your default browser at `http://localhost:8501`

### Configuration

The dashboard automatically reads from:
- `config/trading.json` - Trading configuration
- `reports/monitoring_metrics.json` - Portfolio metrics

No additional configuration needed!

## Dashboard Layout

```
┌─────────────────────────────────────────────────┐
│          VOLT Trading Dashboard ⚡              │
├─────────────────────────────────────────────────┤
│  Portfolio │  Total P&L │ Win Rate │ Positions │
├─────────────────────────────────────────────────┤
│              Live Price Charts                  │
│  [BTC/USDT] [ETH/USDT] [BNB/USDT] [SOL/USDT]  │
│                                                 │
│  [Candlestick Chart + Volume]                  │
├─────────────────────────────────────────────────┤
│  Open Positions  │    Recent Trades            │
│  [Table]         │    [Table]                  │
├─────────────────────────────────────────────────┤
│             System Health                       │
│  Status │ Uptime │ CPU │ Memory                │
└─────────────────────────────────────────────────┘
```

## Sidebar

- 🎛️ **System Controls**
  - Trading mode indicator (Sandbox/Live)
  - Exchange name
  - Start/Stop buttons (placeholder)

- 🔄 **Auto Refresh Settings**
  - Enable/disable toggle
  - Interval slider (5-60s)

## Screenshots

(Screenshots would go here in production)

## Notes

- Dashboard is **read-only** - no trading actions can be executed
- Start/Stop buttons are placeholders (would integrate with control.py)
- Requires VOLT Trading system to be running for live data
- Works with both real exchange and stub data

## Troubleshooting

**Dashboard shows "No metrics available"**
- Start the VOLT Trading system: `python main.py`
- Or run demo: `python demo_fas2.py` to generate test data

**Charts not loading**
- Check exchange connection in logs
- Verify API keys in `config/trading.json`
- Check that exchange is initialized

**Slow performance**
- Increase auto-refresh interval
- Reduce number of symbols to display
- Check system resources (CPU/memory)

## Development

To modify the dashboard:

1. Edit `dashboard/app.py`
2. Save changes
3. Streamlit will auto-reload (if running)

## Future Enhancements

- [ ] Control panel integration (start/stop trading)
- [ ] Technical indicators overlay on charts
- [ ] Signal visualization
- [ ] Alert configuration
- [ ] Export metrics to CSV
- [ ] Dark mode theme
- [ ] Mobile responsive layout

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [Plotly](https://plotly.com/) - Interactive charts
- [Pandas](https://pandas.pydata.org/) - Data manipulation
