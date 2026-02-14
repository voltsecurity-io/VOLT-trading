# VOLT Trading - 12H Test Monitoring Guide

## Test Information
- **Started:** 2026-02-14 12:56:26 CET
- **Ends:** 2026-02-14 00:56:26 CET (12 hours)
- **Capital:** $20,000
- **Mode:** VIX + Pure TA (agents disabled)
- **Pairs:** BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, AVAX/USDT

## Quick Status Commands

### Check if test is running
```bash
systemctl --user status volt-dryrun
```

### View live logs (last 30 lines)
```bash
tail -30 ~/VOLT-trading/logs/dryrun_service.log
```

### Follow logs in real-time
```bash
journalctl --user -u volt-dryrun -f
```

### Check test progress
```bash
cat ~/VOLT-trading/reports/dryrun_state.json | jq '.'
```

### Quick stats
```bash
cat ~/VOLT-trading/reports/dryrun_state.json | jq '{
  duration: .duration_hours,
  trades: .trades_count,
  loops: .trading_loops,
  errors: .total_errors
}'
```

### View trades
```bash
cat ~/VOLT-trading/reports/dryrun_trades.json | jq '.[-5:]'  # Last 5 trades
```

## Expected Behavior

### First 5 Minutes
- Fetching market data
- Building candle history
- Calculating indicators
- No trades expected yet

### After 5-10 Minutes
- First signals generated
- VIX threshold checks
- Potential first trades

### Every 5 Minutes
- New candle processed
- Indicators updated
- Signal generation
- Portfolio rebalancing

## Warning Signs

### ❌ Test Stopped
```bash
systemctl --user status volt-dryrun
# Shows: "inactive" or "failed"
```
**Fix:** `systemctl --user restart volt-dryrun`

### ⚠️ High Memory
```bash
free -h
# Available < 1GB
```
**Fix:** Close browser tabs, stop other apps

### 🔴 No Trades After 1 Hour
```bash
cat ~/VOLT-trading/reports/dryrun_trades.json
# Empty or very few trades
```
**Normal:** Low volatility market
**Check:** VIX thresholds in logs

## Final Report (After 12h)

The test will automatically generate a report at:
- `~/VOLT-trading/reports/dryrun_12h_report.json`

View summary:
```bash
cat ~/VOLT-trading/reports/dryrun_12h_report.json | jq '{
  status: .status,
  duration_hours: .duration_hours,
  total_trades: .total_trades,
  win_rate: .win_rate,
  profit_loss: .total_pnl,
  sharpe_ratio: .sharpe_ratio
}'
```

## Useful Aliases (Optional)

Add to `~/.bashrc`:
```bash
alias volt-status='systemctl --user status volt-dryrun'
alias volt-logs='tail -50 ~/VOLT-trading/logs/dryrun_service.log'
alias volt-stats='cat ~/VOLT-trading/reports/dryrun_state.json | jq .'
alias volt-trades='cat ~/VOLT-trading/reports/dryrun_trades.json | jq .'
```

Then reload: `source ~/.bashrc`
