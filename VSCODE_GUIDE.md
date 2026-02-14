# 🚀 VS Code Quick Start Guide

VOLT-Trading är nu igång i **DRY-RUN MODE**!

## ✅ Vad körs just nu

### 1️⃣ Trading Engine
- **Terminal:** Se output i terminalen där du körde `./start_dryrun.sh`
- **Status:** ✅ RUNNING
- **Mode:** Binance Testnet (Sandbox)
- **Fungerar:** Hämtar live market data, beräknar indikatorer, genererar signaler

### 2️⃣ Streamlit Dashboard
- **URL:** http://localhost:8501
- **Status:** ✅ RUNNING
- **Features:** 
  - Live price charts (candlestick + volume)
  - Portfolio metrics (P&L, win rate)
  - Open positions table
  - Recent trades log
  - System health monitoring

---

## 📊 Så här använder du VS Code Tasks

Tryck `Ctrl+Shift+P` och skriv "Tasks: Run Task", välj sedan:

| Task | Beskrivning |
|------|-------------|
| 🚀 Start VOLT Trading (Dry-Run) | Startar trading engine i sandbox mode |
| 📊 Launch Dashboard | Startar Streamlit dashboard på :8501 |
| 🛑 Stop All | Stoppar alla processer |
| 📝 View Logs | Visar live trading logs |
| 📈 View Metrics | Visar portfolio metrics JSON |
| 🧪 Run Tests | Kör alla 36 unit/integration tests |

**Snabbkommando:** Tryck `Ctrl+Shift+B` för att starta trading (default build task)

---

## 🌐 Öppna Dashboard

### I VS Code (Enklast)
1. Tryck `Ctrl+Shift+P`
2. Skriv "Simple Browser"
3. Välj "Simple Browser: Show"
4. Ange URL: `http://localhost:8501`

### I extern webbläsare
- **Lokal:** http://localhost:8501
- **Nätverk:** http://192.168.18.201:8501
- **Extern:** http://217.61.226.213:8501

---

## 📁 Filstruktur att känna till

```
VOLT-trading/
├── main.py                    # 👈 Entry point - startar trading engine
├── start_dryrun.sh           # 👈 Quick start script (kör detta!)
├── launch_dashboard.sh       # 👈 Dashboard starter
├── DRY_RUN_STATUS.md         # 👈 Läs denna för status!
│
├── config/
│   └── trading.json          # 👈 Konfiguration (sandbox: true)
│
├── src/
│   ├── agents/               # 📊 MarketData, Technical, Execution, Monitoring
│   ├── core/                 # 🔧 TradingEngine, ConfigManager
│   ├── exchanges/            # 💱 BinanceExchange (live data!)
│   ├── strategies/           # 🧠 VOLTStrategy (RSI, MACD, BB)
│   └── risk/                 # 🛡️ RiskManager
│
├── dashboard/
│   └── app.py                # 📊 Streamlit dashboard
│
├── reports/
│   └── monitoring_metrics.json  # 💾 Portfolio metrics
│
└── tests/                    # 🧪 36 passing tests
```

---

## 🔍 Vad händer i bakgrunden?

### Trading Loop (varje 5 minuter)
1. **MarketDataAgent** hämtar live priser från Binance
2. **TechnicalAnalysisAgent** beräknar RSI, MACD, Bollinger Bands
3. **SentimentAnalysisAgent** returnerar neutral sentiment (ingen API)
4. **VOLTStrategy** genererar BUY/SELL signaler (om ALLA 4 villkor uppfylls)
5. **RiskManager** validerar position size, drawdown, correlation
6. **ExecutionAgent** skulle placera order (men SKIPPAR pga inga API-nycklar)
7. **MonitoringAgent** trackar P&L och system health

### Dashboard (auto-refresh var 10:e sekund)
1. Läser `reports/monitoring_metrics.json`
2. Hämtar live OHLCV från Binance via exchange
3. Ritar candlestick charts med Plotly
4. Visar positions, trades, P&L
5. Uppdaterar system health (CPU, memory, uptime)

---

## ⚠️ VIKTIGT: Dry-Run Läge

**Ingen riktig trading sker just nu!**

- ✅ Live market data (riktiga priser från Binance)
- ✅ Tekniska indikatorer beräknas
- ✅ Trading signaler genereras
- ❌ **Inga orders placeras** (ingen API-nyckel = ingen execution)

### För att aktivera riktig trading (TESTNET):
1. Skaffa Binance Testnet API-nycklar: https://testnet.binance.vision/
2. Lägg till i `config/trading.json`:
   ```json
   {
     "exchange": {
       "api_key": "DIN_TESTNET_KEY",
       "api_secret": "DIN_TESTNET_SECRET"
     }
   }
   ```
3. Starta om: `./start_dryrun.sh`

---

## 🐛 Felsökning

### "Dashboard laddar inte?"
```bash
# Kontrollera att Streamlit körs
ps aux | grep streamlit

# Om inte, starta:
./launch_dashboard.sh
```

### "Ser inga trading signals?"
Detta är NORMALT! VOLT-strategin kräver ALLA 4 villkor samtidigt:
- RSI < 30 (översålt)
- MACD crossover (bullish)
- Pris under BB lower band
- Volym spike (>1.5x average)

Signaler är sällsynta men av hög kvalitet!

### "Trading engine crashade?"
```bash
# Kolla logs
cat logs/trading.log

# Eller live:
tail -f logs/trading.log
```

---

## 📈 Nästa Steg

1. **Övervaka i 30 minuter** - Se att allt fungerar smidigt
2. **Öppna dashboard** - http://localhost:8501
3. **Kolla metrics** - `cat reports/monitoring_metrics.json`
4. **Läs DRY_RUN_STATUS.md** - Fullständig statusrapport
5. **Eventuellt:** Lägg till Testnet API-nycklar för riktig order execution

---

## 🛑 Stoppa systemet

### Alt 1: Ctrl+C
Tryck `Ctrl+C` i terminalen där trading engine körs

### Alt 2: VS Code Task
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Välj "🛑 Stop All"

### Alt 3: Control script
```bash
python control.py stop
```

---

## 📚 Dokumentation

- **DRY_RUN_STATUS.md** - Aktuell systemstatus
- **PROJECT_COMPLETE.md** - Fullständig projektöversikt
- **FAS1_COMPLETE.md** - Core agents implementation
- **FAS2_COMPLETE.md** - Monitoring & sentiment
- **FAS3_COMPLETE.md** - Dashboard implementation
- **dashboard/README.md** - Dashboard guide

---

**System Status:** 🟢 HEALTHY  
**Mode:** DRY-RUN (Testnet)  
**Safety:** ✅ No real money at risk

**Lycka till med trading!** 📈🚀
