# VOLT-Trading System - Teknisk Rapport för Claude Code
**Datum:** 2026-02-13  
**System:** Lenovo ThinkPad X1 Nano Gen 1, Arch Linux 6.18.7  
**Projekt:** ~/VOLT-trading/

---

## 📋 SAMMANFATTNING

VOLT-Trading är ett komplett AI-drivet cryptocurrency trading system med:
- ✅ Real Binance API integration (ccxt)
- ✅ 5 AI-agenter (MarketData, Technical, Sentiment, Execution, Monitoring)
- ✅ Live Streamlit dashboard med Plotly charts
- ✅ Risk management & P&L tracking
- ✅ 36 passing unit/integration tests

**Mål:** Köra 12-timmars test med 20,000 SEK startkapital på Binance Testnet

**Problem:** Trading-processen kraschar efter initialisering utan felmeddelande i logs

---

## 🔧 NUVARANDE KONFIGURATION

### System Environment
```bash
OS: Arch Linux 6.18.7
Python: 3.14 (venv: ~/VOLT-trading/.venv/)
Working Dir: /home/omarchy/VOLT-trading/
```

### Installerade Paket (requirements.txt)
```
ccxt==4.5.37
pandas==2.3.3
numpy==2.4.2
streamlit>=1.31.0
plotly>=5.18.0
psutil
python-dotenv
aiohttp
```

### Trading Configuration (config/trading.json)
```json
{
  "trading": {
    "initial_capital": 20000,
    "currency": "SEK",
    "max_position_size": 0.10,
    "risk_per_trade": 0.025,
    "stop_loss": 0.05,
    "take_profit": 0.10,
    "max_drawdown": 0.15,
    "timeframe": "5m",
    "pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT"]
  },
  "exchange": {
    "name": "binance",
    "sandbox": true,
    "api_key": "wcWEErw9aNW2u4EmQ7GdwT9Kb8HrtmYu12pWExIBrPsHMLXmrmOoqDeo3oozGqGs",
    "api_secret": "nMDCdUDzbb6N3Dq82y3ArCMYUT7r6Aql7taAomzAQVwHsyj3jbib3uft3wDw3GkJ",
    "password": ""
  }
}
```

---

## 🐛 PROBLEM & FEL

### Problem 1: Trading Process Kraschar Efter Initialisering

**Observerat beteende:**
```
1. Trading engine startar ✅
2. Alla 5 agenter initialiseras ✅
3. Trading loop börjar ✅
4. Processen kraschar inom 5 sekunder ❌
5. Ingen tydlig error i logs ❌
```

**Sista loggrader (logs/12h_test_*.log):**
```
2026-02-13 16:20:23,227 - src.agents.market_data_agent - INFO - 🚀 Starting Market Data Agent...
2026-02-13 16:20:23,227 - src.agents.technical_agent - INFO - 🚀 Starting Technical Analysis Agent...
2026-02-13 16:20:23,227 - src.agents.simple_agents - INFO - 🚀 Sentiment Analysis Agent started
2026-02-13 16:20:23,228 - src.agents.simple_agents - INFO - 🚀 Execution Agent started
2026-02-13 16:20:23,228 - src.agents.simple_agents - INFO - 🚀 Monitoring Agent started
[INGEN MER OUTPUT - PROCESSEN KRASCHAR]
```

**Testade lösningar:**
1. ❌ `systemd-inhibit` orsakar HUP signal när detached
2. ❌ `nohup` fungerar inte med interactive script
3. ✅ `python main.py` fungerar i interactive terminal men inte detached

### Problem 2: systemd-inhibit Inkompatibilitet

**Fel:**
```
python terminated by signal HUP.
```

**Kontext:**
- `systemd-inhibit` används för att förhindra laptop-sleep
- När körs med `&` eller `nohup` skickas HUP signal
- Processen termineras innan trading loop börjar

### Problem 3: Inga Felmeddelanden i Exceptions

**Observerat:**
- Trading loop startar men producerar ingen output
- Ingen exception loggad
- Möjligt att async loop hänger sig utan att logga

---

## 📁 RELEVANT FILSTRUKTUR

```
VOLT-trading/
├── main.py                    # Entry point - startar alla komponenter
├── config/trading.json        # Trading configuration (gitignored)
├── src/
│   ├── core/
│   │   ├── trading_engine.py  # Main trading loop
│   │   └── config_manager.py  # Config loader
│   ├── exchanges/
│   │   ├── binance_exchange.py      # Real Binance ccxt wrapper
│   │   └── exchange_factory.py      # ExchangeFactory class
│   ├── strategies/
│   │   └── volt_strategy.py   # RSI, MACD, BB, ATR calculations
│   ├── risk/
│   │   └── risk_manager.py    # Position sizing, drawdown checks
│   ├── agents/
│   │   ├── agent_orchestrator.py    # Coordinates all agents
│   │   ├── market_data_agent.py     # Fetches OHLCV from Binance
│   │   ├── technical_agent.py       # Calculates indicators
│   │   └── simple_agents.py         # Sentiment, Execution, Monitoring
│   └── utils/
│       └── logger.py          # Logging setup
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── tests/
│   ├── test_binance_exchange.py     # 19 tests
│   ├── test_agents_integration.py   # 7 tests
│   └── test_fas2_agents.py          # 10 tests
├── logs/
│   ├── 12h_test_*.log         # Test run logs
│   ├── dashboard.log          # Dashboard logs
│   └── trading.log            # General trading logs
└── reports/
    ├── monitoring_metrics.json      # P&L, trades, positions
    └── test_run_metadata.json       # Test metadata
```

---

## 🔍 KRITISKA KODFILER

### main.py
```python
# Entry point - key sections:
# 1. Initializes TradingEngine, VOLTStrategy, RiskManager
# 2. Creates AgentOrchestrator with exchange & strategy dependencies
# 3. Starts all components via asyncio.create_task + gather
# 4. Runs until KeyboardInterrupt

# Known issue: No error handling around main async loop
```

### src/core/trading_engine.py
```python
# Main trading loop:
async def start(self):
    while True:
        # 1. Fetch market data
        # 2. Generate signals
        # 3. Execute orders
        # 4. Update positions
        # 5. Sleep for timeframe interval (5 min)
        
# Possible issue: Exception in loop not caught/logged?
```

### src/agents/agent_orchestrator.py
```python
# Coordinates 5 agents via asyncio tasks
# Possible issue: Agent task crashes silently?

async def start(self):
    await asyncio.gather(
        self.market_data_agent.start(),
        self.technical_agent.start(),
        self.sentiment_agent.start(),
        self.execution_agent.start(),
        self.monitoring_agent.start(),
    )
```

### src/agents/market_data_agent.py
```python
# Fetches live data from Binance every 5 minutes
# Uses exchange.get_ticker() and exchange.get_ohlcv()
# Possible issue: Network error not handled?
```

---

## 🧪 TESTER & VERIFIERING

### Test Status
```bash
pytest tests/ -v
# Result: 36/36 tests passing ✅
```

### Manual Verification Tests
```bash
# 1. API Keys Verification
cd ~/VOLT-trading
source .venv/bin/activate
python verify_api_keys.py
# Expected: ✅ Connects to Binance, fetches balance, gets BTC price
# Actual: ❌ ImportError fixed, needs re-test

# 2. Trading Engine Direct Run
python main.py
# Expected: Trading loop runs continuously
# Actual: ✅ Runs in interactive terminal
#         ❌ Crashes when detached/backgrounded

# 3. Dashboard
streamlit run dashboard/app.py --server.port=8501
# Result: ✅ Dashboard loads and displays data
```

---

## 📊 LOGS & OUTPUT

### Successful Initialization (Last 10 lines before crash)
```
2026-02-13 16:20:23,226 - src.agents.simple_agents - INFO - 📊 Loaded metrics: 5 trades, $250.50 P&L
2026-02-13 16:20:23,226 - src.agents.agent_orchestrator - INFO - ✅ Monitoring Agent initialized
2026-02-13 16:20:23,226 - src.agents.agent_orchestrator - INFO - ✅ Agent Orchestrator initialized
2026-02-13 16:20:23,226 - __main__ - INFO - ✅ VOLT Trading System initialized successfully
2026-02-13 16:20:23,227 - __main__ - INFO - 🎯 Starting VOLT Trading Engine...
2026-02-13 16:20:23,227 - __main__ - INFO - 📈 VOLT Trading is now running
2026-02-13 16:20:23,227 - src.core.trading_engine - INFO - 🚀 Starting Trading Engine...
2026-02-13 16:20:23,227 - src.core.trading_engine - INFO - 📊 Starting main trading loop...
2026-02-13 16:20:23,227 - src.agents.agent_orchestrator - INFO - 🚀 Starting Agent Orchestrator...
[NO MORE OUTPUT - PROCESS DIES]
```

### Expected Next Log Entries (Not Seen)
```
# Should see these but DON'T:
- "📊 Fetching market data for BTC/USDT..."
- "📈 Calculating indicators..."
- "💭 Analyzing sentiment..."
- "🛡️ Running risk checks..."
```

---

## 🎯 ÖNSKAD LÖSNING

### Primärt Mål
Få trading systemet att köra stabilt i 12 timmar utan krasch

### Sekundära Mål
1. Förhindra laptop från att somna (sleep prevention)
2. Logga alla errors ordentligt
3. Kunna köra systemet detached (background process)
4. Auto-restart vid krasch

### ThinkPad-Specifika Krav
- **System:** Lenovo ThinkPad X1 Nano Gen 1 (fanless!)
- **Temperatur:** Måste hålla <85°C (throttling risk)
- **Batteri:** Måste vara inkopplad på AC
- **Sleep:** Måste förhindras under hela testet

---

## 💡 FÖRESLAGNA UNDERSÖKNINGSOMRÅDEN

### 1. Async Loop Error Handling
```python
# I main.py och trading_engine.py:
# Lägg till try/except runt alla asyncio.gather() calls
# Logga ALL exceptions, även KeyboardInterrupt
```

### 2. Agent Task Monitoring
```python
# I agent_orchestrator.py:
# Övervaka varje agent task separat
# Logga vilken agent som kraschar
```

### 3. Network Error Handling
```python
# I market_data_agent.py:
# Lägg till retry logic för Binance API calls
# Catch ccxt.NetworkError och andra exceptions
```

### 4. Process Supervision
```bash
# Överväg:
# - supervisor/systemd service (auto-restart)
# - tmux/screen (persistent session)
# - Python multiprocessing med restart logic
```

### 5. Sleep Prevention
```bash
# Alternativ till systemd-inhibit:
# - caffeine package
# - xset commands
# - gnome-session-inhibit
# - custom dbus call
```

---

## 📝 SKAPADE SCRIPTS

### 1. run_12h_test.sh
- Fullständig test launcher
- API verification
- systemd-inhibit för sleep prevention
- **Problem:** systemd-inhibit kraschar detached process

### 2. quick_start_test.sh  
- Enklare version utan API verification
- Samma systemd-inhibit problem

### 3. start_test_simple.sh
- Simplaste versionen
- Använder `tee` för logging
- **Behöver testas**

### 4. optimize_thinkpad.sh
- Sätter CPU till performance mode
- Inaktiverar Wi-Fi power saving
- Konfigurerar SSD TRIM
- Installerar monitoring tools

### 5. check_test_status.sh
- Visar test progress
- System health (CPU, temp, memory)
- Trading metrics
- Time remaining

### 6. stop_test.sh
- Stoppar alla trading processer
- Uppdaterar test metadata
- Cleanup

---

## ⚙️ KONFIGURATIONSFILER

### .vscode/tasks.json
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "🚀 Start VOLT Trading (Dry-Run)",
      "type": "shell",
      "command": "./start_dryrun.sh",
      "group": { "kind": "build", "isDefault": true }
    },
    {
      "label": "📊 Launch Dashboard",
      "type": "shell",
      "command": "./launch_dashboard.sh"
    }
  ]
}
```

---

## 🔐 SÄKERHET

- ✅ API-nycklar är för Binance Testnet (inte production)
- ✅ config/trading.json är gitignored
- ✅ Sandbox mode aktiverat (inga riktiga pengar)
- ⚠️ API keys synliga i denna rapport (OK för testnet)

---

## 📚 DOKUMENTATION SKAPAD

1. **PROJECT_COMPLETE.md** - Fullständig projektöversikt
2. **FAS1_COMPLETE.md** - Core agents implementation
3. **FAS2_COMPLETE.md** - Monitoring & sentiment
4. **FAS3_COMPLETE.md** - Dashboard implementation
5. **THINKPAD_OPTIMIZATION.md** - 24/7 optimization guide
6. **12H_TEST_GUIDE.txt** - Test instructions
7. **API_KEY_SETUP.md** - API key configuration
8. **VSCODE_GUIDE.md** - VS Code usage guide

---

## 🎯 SPECIFIKA FRÅGOR TILL CLAUDE CODE

1. **Varför kraschar trading processen efter initialisering utan error?**
   - Finns det en silent exception i async loop?
   - Är det något med asyncio.gather() som inte hanteras?

2. **Hur kan vi få processen att köra detached?**
   - systemd-inhibit fungerar inte med & eller nohup
   - Alternativa metoder för sleep prevention?

3. **Hur debuggar vi async code som kraschar utan output?**
   - Borde vi lägga till mer logging?
   - Finns det sätt att fånga async exceptions bättre?

4. **Ska vi använda supervisor/systemd service istället?**
   - Mer robust än shell scripts?
   - Auto-restart på krasch?

5. **ThinkPad-specifik optimering:**
   - Hur förhindrar vi sleep på Arch Linux utan systemd-inhibit?
   - CPU thermal management för 12h körning?

---

## 🚀 NÄSTA STEG

1. ✅ Identifiera orsak till process crash
2. ✅ Implementera robust error handling
3. ✅ Få detached execution att fungera
4. ✅ Verifiera sleep prevention
5. ✅ Testa 12-timmars körning
6. ✅ Analysera resultat och optimera

---

## 📞 KONTAKT & KONTEXT

**User:** omarchy  
**System:** ~/VOLT-trading/  
**Mål:** 12-timmars automated trading test  
**Budget:** 20,000 SEK (testnet)  
**Timeline:** Nu - ska köra över natten  

**Status:** System är 95% komplett, bara process persistence som saknas!

---

**Tack för hjälpen! 🙏**
