# 🧠 ULTRA-OPTIMERAD VOLT-TRADING: MULTI-AGENT OLLAMA SYSTEM

**Datum:** 2026-02-14 07:36 CET  
**Vision:** Självförbättrande multi-agent trading system med Ollama LLMs + IDE-integration  
**Mål:** Nästa generations AI-drivet trading där agenter samarbetar, korrigerar varandra och kontinuerligt optimerar strategier

---

## 🔥 **BREAKTHROUGH: GITLAB INVESTMENT-INTELLIGENCE-PLATFORM**

**Repository klonad:** `~/investment-intelligence-platform`  
**Kritiska insikter för VOLT:** 7 system som fattas helt i nuvarande implementation

### **🎯 NYA PRIORITERINGAR från GitLab-analysen:**

#### **1. Multi-Agent Weighted Consensus** (investment_agents.py)
**Problem med nuvarande VOLT:** Single strategy, ingen oversight  
**Lösning från platform:**
```python
# Weighted voting baserat på agent track-record
agent_weights = {
    "volatility_assessor": 0.40,    # VOLT-specifik agent (saknas!)
    "hedge_optimizer": 0.35,        # Options-strategi (saknas!)
    "trend_analyzer": 0.25          # Finns men inte viktad
}

# Dynamic thresholds baserat på market regime
thresholds = {
    "normal_market": 0.55,     # 55% confidence = trade
    "high_volatility": 0.70,   # VIX > 25 = kräv mer säkerhet
    "crash_mode": 0.80         # Extrema lägen
}
```
**Varför kritiskt:** Vårt 12h-test hade 4 trades på grund av hårdkodad 0.6 threshold!

---

#### **2. Volatility-Specific Data Sources** (collectors/)
**Vad som FATTAS i VOLT:**
- ❌ VIX futures term structure
- ❌ IV (Implied Volatility) rank & percentile
- ❌ Options skew (tail risk)
- ❌ Options flow (smart money)
- ❌ Earnings calendar (volatility events)

**Implementation needed:**
```python
# NYTT: src/collectors/volt_data_sources.py
class VoltDataCollector:
    sources = {
        "cboe_vix": "VIX futures term structure",
        "options_chains": "IV rank, skew, OI",
        "crypto_options": "Deribit BTC/ETH volatility",
        "earnings_dates": "Volatility event tracking"
    }
```

---

#### **3. Greeks Tracking för Options** (tracker.py)
**Nuvarande:** Bara spot price tracking  
**Behövs:**
```python
class VoltPortfolioTracker:
    def track_greeks(self):
        return {
            "delta_exposure": 0.75,      # Net directional risk
            "theta_decay": -250,          # Daily time decay
            "vega_exposure": 5000,        # IV sensitivity
            "gamma_risk": 0.02            # Acceleration risk
        }
    
    def calculate_hedge_efficiency(self):
        """Hur väl skyddar våra options position?"""
        # Platform har detta - VOLT saknar helt!
```

---

#### **4. Risk Management - Options Specific** 
**GitLab platform har:**
- VaR (Value at Risk)
- Sharpe ratio
- Max drawdown
- Win rate tracking

**VOLT SAKNAR:**
```python
class VoltOptionsRiskManager:
    def calculate_options_risks(self):
        return {
            "pinning_risk": 0.15,              # Strike clustering
            "volatility_crush": 0.30,          # IV kan falla 30% post-event
            "early_assignment_risk": 0.05,     # ITM options risk
            "liquidity_risk": 0.03,            # Bid-ask spread
            "gamma_flip": False,               # Dealers hedge flip
            "volatility_convexity": 1200       # Vega P&L
        }
```

---

#### **5. Probability-Based Decision Making**
**Från example_analysis_results.json:**
```json
{
  "options_strategy": {
    "recommended": "Short Call Spread",
    "probability_of_profit": 0.72,    // 72% PoP!
    "max_risk": 500,
    "max_reward": 200,
    "risk_reward_ratio": "1:2.5"
  }
}
```

**Detta är GULD för VOLT!** Istället för "RSI < 30 = buy", använd:
- 72% probability of profit
- Defined max risk/reward
- Position sizing baserat på PoP

---

#### **6. Dynamic Stop-Loss baserat på VIX**
```python
# Från platform risk logic:
def dynamic_stop_losses(vix_level):
    if vix_level > 25:
        return 0.02  # 2% tight stop vid hög volatilitet
    elif vix_level < 12:
        return 0.05  # 5% vid låg volatilitet
    else:
        return 0.03  # 3% normal
```

**VOLT använder:** Statisk stop-loss (hardcoded)  
**Borde använda:** VIX-adaptiv stop-loss

---

#### **7. Structured Output Format för ML Training**
**Platform's JSON structure är PERFEKT för Ollama training:**
```json
{
  "timestamp": "2026-01-28T13:00:00",
  "agent_results": {
    "risk_assessor": {"decision": "HOLD", "confidence": 0.65}
  },
  "consensus_decision": {
    "vote_breakdown": {"BUY": 1, "SELL": 0, "HOLD": 4}
  },
  "recommendations": [...]
}
```

**VOLT saknar:** Strukturerad output för senare analys  
**Resultat:** Ingen data för Ollama att lära från!

---

## 🚀 **UPPDATERAD PRIORITERING**

**Tidigare plan:** Ollama → OSINT → Journal → IDE → Feedback  
**NY PLAN med GitLab insikter:**

### **FAS 0: KRITISKA GAPS (Vecka 0 - Omedelbart)**
- [ ] 0.1: Implementera VoltDataCollector (VIX, IV, skew)
- [ ] 0.2: Lägg till Greeks tracking i MonitoringAgent
- [ ] 0.3: Skapa options-specific RiskManager
- [ ] 0.4: Dynamic thresholds baserat på VIX
- [ ] 0.5: Strukturerad JSON output för alla beslut

**Motivering:** Dessa är FOUNDATION för allt annat. Utan VIX-data kan vi inte göra VOLT-strategier!

---

## 🎯 PROJEKTÖVERSIKT

### **Vad vi bygger:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOLT-TRADING MEGA-SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   OLLAMA     │◄──►│   NEOVIM     │◄──►│   OBSIDIAN   │      │
│  │   AGENTS     │    │  (LazyVim)   │    │    VAULT     │      │
│  │              │    │              │    │              │      │
│  │ • Strategy   │    │ • Editing    │    │ • Analysis   │      │
│  │ • Risk       │    │ • Debug      │    │ • Journal    │      │
│  │ • Market     │    │ • LSP        │    │ • Knowledge  │      │
│  │ • Execution  │    │              │    │              │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         └───────────────────┴───────────────────┘              │
│                             │                                  │
│                    ┌────────▼────────┐                         │
│                    │   VOLT-TRADING  │                         │
│                    │   CORE ENGINE   │                         │
│                    │                 │                         │
│                    │ • Python async  │                         │
│                    │ • WebSocket     │                         │
│                    │ • SQLite state  │                         │
│                    │ • REST API      │                         │
│                    └────────┬────────┘                         │
│                             │                                  │
│         ┌───────────────────┼───────────────────┐              │
│         │                   │                   │              │
│    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐        │
│    │ Binance │         │  VS     │         │Dashboard│        │
│    │ Exchange│         │  Code   │         │Streamlit│        │
│    └─────────┘         └─────────┘         └─────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 VARFÖR DESSA SPECIFIKA DELAR?

### **1. OLLAMA Multi-Agent System** 🤖

**Varför:**
- **Lokal kontroll:** Inga API-kostnader, inga rate limits
- **Låg latens:** <100ms svar vs 1-3s för cloud API:er
- **Privacy:** Trading strategier stannar lokalt
- **Experimentell frihet:** Testa olika modeller (llama3.3, qwen2.5, deepseek)
- **Self-healing:** Agenter kan övervaka och rätta varandra

**Teknisk motivering:**
```python
# Problem med nuvarande system:
# 1. Agenter är "dumma" - bara hämtar data, ingen intelligens
# 2. Ingen feedback-loop mellan komponenter
# 3. Strategier är statiska, anpassar sig inte

# Lösning med Ollama:
class OllamaStrategyAgent:
    """LLM som analyserar market data OCH lär från historik"""
    
    async def analyze_trade(self, market_data, trade_history):
        # Ollama får:
        # 1. Real-time RSI/MACD/BB data
        # 2. Senaste 50 trades med outcome
        # 3. Nuvarande P&L
        
        # Ollama returnerar:
        # 1. BUY/SELL/HOLD decision med reasoning
        # 2. Confidence score (0-1)
        # 3. Risk assessment
        # 4. Strategy adjustment förslag
```

**Val av modeller:**
- **qwen2.5-coder:7b** - Kod/logik analys (strategier)
- **llama3.3:8b** - Generell reasoning (market analys)  
- **deepseek-r1:8b** - Deep thinking (risk management)

---

### **2. OSINT Signal System från Decentralizedinvestmentplatform** 📡

**Varför:**
- **Tråkig sanning:** Tekniska indikatorer (RSI/MACD) ger false positives
- **Insikt från analys:** Platform har 67% win rate med OSINT signals
- **Bevis:** Vårt test hade 4 trades på 11h → För få datapunkter

**Konkret implementation:**

```python
# INNAN (bara tekniska indikatorer):
class VOLTStrategy:
    def generate_signal(self, market_data):
        rsi = calculate_rsi(market_data)
        macd = calculate_macd(market_data)
        # Problem: Ingen kontext utanför chart
        if rsi < 30 and macd > 0:
            return "BUY"

# EFTER (+ OSINT):
class EnhancedVOLTStrategy:
    def generate_signal(self, market_data, osint_signals):
        # Tekniska
        rsi = calculate_rsi(market_data)
        macd = calculate_macd(market_data)
        
        # OSINT-lager
        whale_activity = osint_signals['whale_movements']  # +34% vol
        social_sentiment = osint_signals['twitter_buzz']   # Bullish trend
        tvl_change = osint_signals['defi_tvl']             # +$120M i pool
        gas_spike = osint_signals['gas_price']              # +25% urgency
        
        # Weighted scoring
        technical_score = (rsi_weight * rsi_signal) + (macd_weight * macd_signal)
        osint_score = (
            whale_activity.confidence * 0.3 +
            social_sentiment.confidence * 0.2 +
            tvl_change.confidence * 0.3 +
            gas_spike.confidence * 0.2
        )
        
        final_score = (technical_score * 0.6) + (osint_score * 0.4)
        
        # LLM får båda för final decision
        return ollama_agent.decide(technical_score, osint_score, reasoning)
```

**Datakällor att integrera:**
1. **Whale Alert API** - Stora transferer (>$1M)
2. **Twitter/X API** - Sentiment analys på crypto keywords
3. **DeFiLlama API** - TVL förändringar per protokoll
4. **Etherscan/BSCScan** - On-chain gas prices + contract events
5. **CoinGecko API** - Trending coins + volume spikes

**Förväntad förbättring:**
- Trades per 12h: 4 → 12-25 (från analys)
- Win rate: 50% (break-even) → 60-67% (platform benchmark)
- False positives: -30-40% (OSINT filtrerar brus)

---

### **3. Decision Journal från Decentralizedinvestmentplatform** 📝

**Varför:**
- **Problem:** Vi vet inte VARFÖR trades fungerade/misslyckades
- **Insight:** Platform har systematisk outcome tracking (PENDING → CORRECT/FALSE)
- **Machine Learning:** Journalen blir träningsdata för Ollama agenter

**Implementation:**

```python
# Ny modul: src/journal/trade_journal.py
class TradeJournal:
    """Strukturerad trade-logging med outcome tracking"""
    
    def log_decision(self, trade):
        entry = {
            "timestamp": datetime.now(),
            "asset": trade.symbol,
            "action": trade.action,  # BUY/SELL/HOLD
            "price": trade.entry_price,
            "size": trade.quantity,
            
            # Reasoning (från Ollama agent)
            "technical_signals": {
                "rsi": trade.rsi_value,
                "macd": trade.macd_value,
                "bb_position": trade.bb_position
            },
            "osint_signals": {
                "whale_activity": trade.whale_score,
                "sentiment": trade.sentiment_score,
                "tvl_change": trade.tvl_delta
            },
            "llm_reasoning": trade.ollama_explanation,  # Text från agent
            "confidence": trade.ollama_confidence,       # 0-1
            
            # Targets
            "take_profit": trade.tp_price,
            "stop_loss": trade.sl_price,
            
            # Outcome (uppdateras senare)
            "outcome": "PENDING",  # PENDING/CORRECT/FALSE_POSITIVE/STOPPED
            "exit_price": None,
            "pnl": None,
            "duration": None
        }
        
        self.save_to_obsidian(entry)  # Markdown note
        self.save_to_sqlite(entry)     # Database
        return entry.id

    def update_outcome(self, entry_id, exit_data):
        """Uppdateras när trade stängs"""
        entry = self.load(entry_id)
        entry['outcome'] = self._classify_outcome(entry, exit_data)
        entry['exit_price'] = exit_data.price
        entry['pnl'] = exit_data.price - entry['price']
        entry['duration'] = exit_data.timestamp - entry['timestamp']
        
        # Feed tillbaka till Ollama för learning
        self.ollama_feedback_loop(entry)
```

**Obsidian integration:**
- Varje trade = En markdown note
- Auto-länkar mellan relaterade trades
- Dataview queries för pattern analys
- Grafer i Obsidian Canvas

**Exempel journal entry:**
```markdown
---
trade_id: TRADE_2026_02_14_001
asset: ETH/USDT
action: BUY
entry: 2340.50
confidence: 0.78
outcome: PENDING
---

# Trade Analysis: ETH/USDT Long

## Signals
- **RSI:** 32 (oversold) ✓
- **MACD:** Bullish crossover ✓
- **Whale Activity:** +34% volume last 1h ✓
- **Social Sentiment:** 0.71 bullish (Twitter trending)

## LLM Reasoning
"Strong confluence: Technical oversold + whale accumulation. 
Risk: General market downturn could override. 
Recommended allocation: 8% of capital."

## Targets
- Take Profit: $2,600 (+11%)
- Stop Loss: $2,200 (-6%)
- Risk/Reward: 1:1.8

## Outcome
_Will be updated when trade closes_
```

---

### **4. Multi-Agent Communication Protocol** 🔄

**Varför:**
- **Single point of failure:** En buggig agent kan krascha hela systemet
- **No oversight:** Ingen kontrollerar om beslut är vettiga
- **Static strategies:** Ingen anpassning baserat på performance

**Design:**

```python
# src/ollama_agents/agent_network.py

class AgentNetwork:
    """Coordinator för Ollama agenter som pratar med varandra"""
    
    agents = {
        'strategy': StrategyAgent(model='qwen2.5-coder:7b'),
        'risk': RiskAgent(model='deepseek-r1:8b'),
        'market': MarketAnalysisAgent(model='llama3.3:8b'),
        'execution': ExecutionAgent(model='qwen2.5-coder:7b'),
        'auditor': AuditorAgent(model='deepseek-r1:8b')  # Övervakar andra
    }
    
    async def propose_trade(self, market_data):
        # 1. Strategy agent föreslår trade
        proposal = await self.agents['strategy'].analyze(market_data)
        
        # 2. Risk agent granskar
        risk_check = await self.agents['risk'].review(proposal)
        
        if risk_check.rejected:
            # 3. Auditor medierar konflikt
            resolution = await self.agents['auditor'].mediate(
                strategy_view=proposal,
                risk_view=risk_check
            )
            return resolution
        
        # 4. Execution agent optimerar timing
        execution_plan = await self.agents['execution'].optimize(proposal)
        
        # 5. Auditor loggar konsensus
        await self.agents['auditor'].log_decision({
            'proposal': proposal,
            'risk_assessment': risk_check,
            'execution': execution_plan,
            'consensus': 'APPROVED'
        })
        
        return execution_plan

# Conversation format mellan agenter:
{
    "from": "strategy_agent",
    "to": "risk_agent",
    "message": {
        "type": "TRADE_PROPOSAL",
        "action": "BUY",
        "asset": "ETH/USDT",
        "confidence": 0.82,
        "reasoning": "RSI oversold + whale accumulation",
        "request": "Please assess portfolio impact"
    }
}

{
    "from": "risk_agent",
    "to": "strategy_agent",
    "message": {
        "type": "RISK_REVIEW",
        "status": "APPROVED_WITH_MODIFICATIONS",
        "concerns": [
            "Proposed 15% allocation exceeds single-position limit (10%)",
            "ETH correlation with BTC currently 0.95 (high)"
        ],
        "modifications": {
            "allocation": "8% instead of 15%",
            "stop_loss": "Tighter SL at -5% instead of -8%"
        }
    }
}
```

**Self-correction mechanism:**

```python
class AuditorAgent:
    """Övervakar andra agenter och korrigerar misstag"""
    
    async def monitor_execution(self, trade_id):
        """Kollar varje trade efter exekvering"""
        
        trade = load_trade(trade_id)
        
        # Hämta original reasoning från strategy agent
        original_proposal = trade.metadata['proposal']
        
        # Jämför med faktiskt utförande
        actual_execution = trade.metadata['execution']
        
        # Detect discrepancies
        issues = []
        
        if actual_execution.price != original_proposal.target_price:
            slippage = abs(actual_execution.price - original_proposal.target_price)
            if slippage > 0.01:  # >1% slippage
                issues.append({
                    'type': 'EXCESSIVE_SLIPPAGE',
                    'severity': 'HIGH',
                    'value': slippage,
                    'message': f'Execution agent allowed {slippage:.2%} slippage'
                })
        
        if actual_execution.size > original_proposal.size * 1.1:
            issues.append({
                'type': 'POSITION_SIZE_VIOLATION',
                'severity': 'CRITICAL',
                'message': 'Execution exceeded approved position size'
            })
        
        if issues:
            # Skicka feedback till execution agent
            await self.send_correction(
                to='execution_agent',
                issues=issues,
                action='ADJUST_PARAMETERS'
            )
            
            # Logga till journal
            await self.journal.log_agent_error(trade_id, issues)
```

---

### **5. IDE Integration (Neovim + Obsidian + VS Code)** 🛠️

**Varför:**
- **Development velocity:** Live code editing med LSP + Ollama suggestions
- **Knowledge management:** Obsidian som "trade brain"
- **Debugging:** Neovim för snabb fix, VS Code för deep dive

**Setup:**

```
📁 ~/VOLT-trading/
├── 📁 obsidian-vault/          # Ny Obsidian vault
│   ├── 📁 Trades/              # Journal entries
│   ├── 📁 Analysis/            # Market analysis notes
│   ├── 📁 Strategies/          # Strategy documentation
│   ├── 📁 Agent-Logs/          # Ollama agent conversations
│   └── 📁 Performance/         # Backtest results
│
├── 📁 .nvim/                   # Neovim workspace config
│   ├── lua/plugins/
│   │   ├── ollama.lua         # Ollama integration
│   │   └── trading.lua        # Custom trading commands
│   └── sessions/
│       └── volt-trading.vim   # Saved layout
│
├── 📁 .vscode/
│   ├── settings.json          # Python LSP config
│   ├── launch.json            # Debug configs
│   └── tasks.json             # Build tasks
│
└── 📁 src/
    └── 📁 ollama_agents/      # Ny modul
```

**Neovim integration:**

```lua
-- ~/.config/nvim/lua/plugins/ollama.lua

return {
  {
    "nomnivore/ollama.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    opts = {
      model = "qwen2.5-coder:7b",
      serve = {
        on_start = true,
        command = "ollama",
        args = { "serve" }
      }
    }
  },
  
  -- Custom VOLT trading commands
  {
    "custom/volt-trading.nvim",
    config = function()
      -- :VoltAnalyze - Kör Ollama analys på current trade
      vim.api.nvim_create_user_command("VoltAnalyze", function()
        local bufnr = vim.api.nvim_get_current_buf()
        local content = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
        
        -- Skicka till Ollama för analys
        require("ollama").prompt(
          "Analyze this trade strategy and suggest improvements:\n" ..
          table.concat(content, "\n")
        )
      end, {})
      
      -- :VoltBacktest - Kör backtest från Neovim
      vim.api.nvim_create_user_command("VoltBacktest", function(opts)
        local symbol = opts.args
        vim.fn.jobstart(
          string.format("python ~/VOLT-trading/backtest.py --symbol %s", symbol),
          {
            on_stdout = function(_, data)
              vim.api.nvim_echo({{table.concat(data, "\n"), "Normal"}}, false, {})
            end
          }
        )
      end, { nargs = 1 })
    end
  }
}
```

**Obsidian Dataview queries:**

```dataview
TABLE 
  action AS "Action",
  entry AS "Entry",
  exit_price AS "Exit",
  pnl AS "P&L",
  outcome AS "Result"
FROM "Trades"
WHERE outcome = "CORRECT"
SORT pnl DESC
LIMIT 10
```

**VS Code tasks.json:**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "VOLT: Start Ollama Service",
      "type": "shell",
      "command": "systemctl --user start ollama",
      "problemMatcher": []
    },
    {
      "label": "VOLT: Run 12h Test",
      "type": "shell",
      "command": "python run_dryrun_12h.py --hours 12 --capital 20000",
      "problemMatcher": []
    },
    {
      "label": "VOLT: Analyze Last Test",
      "type": "shell",
      "command": "python -m src.ollama_agents.post_test_analyzer",
      "problemMatcher": []
    }
  ]
}
```

---

## 🔬 TEKNISK IMPLEMENTATION PLAN

### **Fas 1: Ollama Foundation (Vecka 1)**

**Mål:** Få Ollama agents att köra och prata med varandra

- [ ] 1.1: Starta Ollama service permanent
  ```bash
  sudo systemctl enable --now ollama
  ollama pull qwen2.5-coder:7b
  ollama pull llama3.3:8b
  ollama pull deepseek-r1:8b
  ```

- [ ] 1.2: Skapa `src/ollama_agents/` modul struktur
  ```
  src/ollama_agents/
  ├── __init__.py
  ├── base_agent.py          # Abstract base class
  ├── strategy_agent.py      # Trading strategy beslut
  ├── risk_agent.py          # Risk management
  ├── market_agent.py        # Market analys
  ├── execution_agent.py     # Order execution
  ├── auditor_agent.py       # Oversight & correction
  └── agent_network.py       # Communication protocol
  ```

- [ ] 1.3: Implementera BaseAgent class
  ```python
  class BaseAgent:
      def __init__(self, model_name, role):
          self.model = model_name
          self.role = role
          self.ollama_client = OllamaClient()
          
      async def think(self, prompt, context=None):
          """Core reasoning method"""
          
      async def communicate(self, to_agent, message):
          """Send message to another agent"""
          
      async def receive(self, from_agent, message):
          """Handle incoming message"""
  ```

- [ ] 1.4: Test agent-to-agent communication
  - Strategy föreslår trade → Risk granskar → Auditor loggar
  - Verifiera att messages sparas i SQLite för historik

- [ ] 1.5: Integration med befintliga agenter
  - Wrap `VOLTStrategy` med `StrategyAgent`
  - Wrap `RiskManager` med `RiskAgent`
  - Keep existing logic, add LLM layer

---

### **Fas 2: OSINT Signal Integration (Vecka 1-2)**

**Mål:** Lägga till external data sources för bättre beslut

- [ ] 2.1: Skapa `src/osint/` modul
  ```
  src/osint/
  ├── __init__.py
  ├── whale_tracker.py       # Whale Alert API
  ├── sentiment_analyzer.py  # Twitter/Reddit scraping
  ├── defi_monitor.py        # DeFiLlama TVL tracking
  ├── onchain_monitor.py     # Etherscan/BSCScan data
  └── signal_aggregator.py   # Kombinerar alla källor
  ```

- [ ] 2.2: Implementera Whale Alert integration
  ```python
  class WhaleTracker:
      async def get_large_transfers(self, min_value_usd=1000000):
          """Hämta transfers >$1M senaste timmen"""
          
      def calculate_whale_score(self, symbol, transfers):
          """0-1 score baserat på whale activity"""
  ```

- [ ] 2.3: Sentiment analyzer (Twitter/X)
  ```python
  class SentimentAnalyzer:
      async def get_twitter_sentiment(self, symbol):
          """Scrape trending tweets om $ETH etc"""
          
      def calculate_sentiment_score(self, tweets):
          """0-1 score, 0=bearish, 1=bullish"""
  ```

- [ ] 2.4: DeFi TVL monitor
  ```python
  class DeFiMonitor:
      async def get_tvl_change(self, protocol, timeframe='1h'):
          """TVL delta från DeFiLlama"""
          
      def detect_liquidity_events(self, tvl_data):
          """Alert på stora förändringar"""
  ```

- [ ] 2.5: Signal Aggregator
  ```python
  class SignalAggregator:
      async def get_all_signals(self, symbol):
          whale = await whale_tracker.get_score(symbol)
          sentiment = await sentiment_analyzer.get_score(symbol)
          tvl = await defi_monitor.get_score(symbol)
          
          return {
              'whale_activity': whale,
              'social_sentiment': sentiment,
              'tvl_change': tvl,
              'composite_score': weighted_average(whale, sentiment, tvl)
          }
  ```

- [ ] 2.6: Integration i VOLTStrategy
  ```python
  # Modify volt_strategy.py
  async def generate_signal(self, market_data):
      # Existing technical analysis
      technical_score = self._calculate_technical_score(market_data)
      
      # NEW: OSINT analysis
      osint_signals = await self.osint_aggregator.get_all_signals(self.symbol)
      osint_score = osint_signals['composite_score']
      
      # Combined decision med Ollama
      final_decision = await self.strategy_agent.decide(
          technical=technical_score,
          osint=osint_score,
          market_data=market_data
      )
      
      return final_decision
  ```

---

### **Fas 3: Decision Journal System (Vecka 2)**

**Mål:** Strukturerad logging för ML training data

- [ ] 3.1: Skapa `src/journal/` modul
  ```
  src/journal/
  ├── __init__.py
  ├── trade_journal.py       # Core journal class
  ├── obsidian_sync.py       # Markdown export
  ├── sqlite_store.py        # Database storage
  └── outcome_tracker.py     # Update outcomes
  ```

- [ ] 3.2: TradeJournal implementation (se design ovan)

- [ ] 3.3: Obsidian vault setup
  ```bash
  mkdir -p ~/VOLT-trading/obsidian-vault/{Trades,Analysis,Strategies,Agent-Logs,Performance}
  
  # Skapa templates
  cat > ~/VOLT-trading/obsidian-vault/Templates/trade-entry.md <<EOF
  ---
  trade_id: {{trade_id}}
  asset: {{asset}}
  action: {{action}}
  entry: {{entry_price}}
  confidence: {{confidence}}
  outcome: PENDING
  ---
  # Trade Analysis: {{asset}} {{action}}
  
  ## Signals
  {{technical_signals}}
  {{osint_signals}}
  
  ## LLM Reasoning
  {{ollama_reasoning}}
  
  ## Targets
  - Take Profit: {{take_profit}}
  - Stop Loss: {{stop_loss}}
  EOF
  ```

- [ ] 3.4: Auto-sync till Obsidian
  ```python
  class ObsidianSync:
      def create_trade_note(self, trade_entry):
          """Skapa markdown note från trade"""
          template = load_template('trade-entry.md')
          content = template.render(**trade_entry)
          
          filepath = f"obsidian-vault/Trades/{trade_entry.id}.md"
          write_file(filepath, content)
  ```

- [ ] 3.5: Outcome tracker med callback
  ```python
  # I TradingEngine när trade stängs:
  async def close_position(self, symbol):
      exit_data = await self.exchange.close_position(symbol)
      
      # Update journal
      await self.trade_journal.update_outcome(
          trade_id=position.journal_id,
          exit_data=exit_data
      )
      
      # Feed back to Ollama för learning
      await self.strategy_agent.learn_from_outcome(
          original_proposal=position.metadata['proposal'],
          outcome=exit_data
      )
  ```

---

### **Fas 4: IDE Integration (Vecka 2-3)**

**Mål:** Smidig development workflow

- [ ] 4.1: Neovim Ollama plugin installation
  ```bash
  # Lägg till i ~/.config/nvim/lua/plugins/ollama.lua
  # (Se config ovan)
  ```

- [ ] 4.2: Custom Neovim commands
  - `:VoltAnalyze` - Analysera current buffer med Ollama
  - `:VoltBacktest <symbol>` - Kör backtest
  - `:VoltJournal` - Öppna senaste trade journal
  - `:VoltAgentStatus` - Visa agent network status

- [ ] 4.3: Obsidian Dataview setup
  ```bash
  # Install Dataview plugin i Obsidian
  # Skapa dashboard note:
  
  cat > ~/VOLT-trading/obsidian-vault/Dashboard.md <<EOF
  # VOLT Trading Dashboard
  
  ## Recent Trades
  \`\`\`dataview
  TABLE action, entry, exit_price, pnl, outcome
  FROM "Trades"
  SORT file.ctime DESC
  LIMIT 20
  \`\`\`
  
  ## Performance Metrics
  \`\`\`dataview
  TABLE 
    length(filter(rows.outcome, (x) => x = "CORRECT")) AS Wins,
    length(filter(rows.outcome, (x) => x = "FALSE_POSITIVE")) AS Losses,
    sum(rows.pnl) AS Total_PnL
  FROM "Trades"
  WHERE outcome != "PENDING"
  GROUP BY date(file.ctime).year + "-" + date(file.ctime).month
  \`\`\`
  EOF
  ```

- [ ] 4.4: VS Code workspace setup
  ```json
  // .vscode/settings.json
  {
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "files.watcherExclude": {
      "**/obsidian-vault/.obsidian/**": true
    },
    "terminal.integrated.env.linux": {
      "OLLAMA_HOST": "http://localhost:11434"
    }
  }
  ```

- [ ] 4.5: Hot-reload development mode
  ```python
  # src/dev_server.py - Watchdog för auto-restart
  
  from watchdog.observers import Observer
  from watchdog.events import FileSystemEventHandler
  
  class VOLTReloader(FileSystemEventHandler):
      def on_modified(self, event):
          if event.src_path.endswith('.py'):
              print(f"🔄 Detected change in {event.src_path}")
              restart_trading_engine()
  ```

---

### **Fas 5: Self-Improving Feedback Loop (Vecka 3-4)**

**Mål:** Agenter lär från misstag och förbättrar sig

- [ ] 5.1: Outcome analysis pipeline
  ```python
  class OutcomeAnalyzer:
      async def analyze_closed_trades(self, lookback_hours=24):
          """Analysera alla trades senaste 24h"""
          
          trades = self.journal.get_trades(
              status='CLOSED',
              since=datetime.now() - timedelta(hours=lookback_hours)
          )
          
          patterns = {
              'winning_signals': [],
              'losing_signals': [],
              'common_mistakes': []
          }
          
          for trade in trades:
              if trade.outcome == 'CORRECT':
                  patterns['winning_signals'].append(trade.signals)
              elif trade.outcome == 'FALSE_POSITIVE':
                  patterns['losing_signals'].append(trade.signals)
          
          # Skicka till Ollama för pattern detection
          insights = await self.strategy_agent.find_patterns(patterns)
          
          return insights
  ```

- [ ] 5.2: Dynamic strategy adjustment
  ```python
  class AdaptiveStrategy(VOLTStrategy):
      async def adjust_parameters(self, insights):
          """Modifiera thresholds baserat på recent performance"""
          
          if insights.rsi_oversold_failures > 5:
              # RSI 35 verkar för aggressivt, höj till 38
              self.rsi_oversold = min(self.rsi_oversold + 3, 40)
              self.logger.info(f"📊 Adjusted RSI oversold to {self.rsi_oversold}")
          
          if insights.whale_signal_success_rate > 0.7:
              # Whale signals funkar bra, öka weight
              self.osint_weights['whale_activity'] += 0.05
  ```

- [ ] 5.3: Agent performance metrics
  ```python
  class AgentMetrics:
      """Tracka varje agents performance"""
      
      metrics = {
          'strategy_agent': {
              'proposals_made': 0,
              'proposals_approved': 0,
              'avg_confidence': 0.0,
              'win_rate': 0.0
          },
          'risk_agent': {
              'reviews_made': 0,
              'rejections': 0,
              'modifications': 0,
              'prevented_losses': 0.0
          }
      }
      
      def update_after_trade(self, trade_outcome):
          """Uppdatera metrics efter stängd trade"""
  ```

- [ ] 5.4: Weekly optimization job
  ```python
  # Cron job som körs varje söndag
  
  async def weekly_optimization():
      """Djup analys av veckas trading"""
      
      # 1. Samla all data
      week_trades = journal.get_trades(since=datetime.now() - timedelta(days=7))
      
      # 2. Ollama deep analysis
      report = await auditor_agent.generate_weekly_report(week_trades)
      
      # 3. Föreslå ändringar
      suggestions = await auditor_agent.suggest_improvements(report)
      
      # 4. Spara till Obsidian
      obsidian_sync.create_note(
          path='Performance/Week_{week_number}.md',
          content=report
      )
      
      # 5. Email/Discord notification
      notify_user(report.summary)
  ```

---

## 🎯 VARFÖR DESSA PRIORITERINGAR?

### **Foundational först:**
1. **Ollama agents** - Utan dessa har vi ingen intelligens
2. **OSINT signals** - Fixar "4 trades problem" genom mer datakällor
3. **Journal** - Skapar träningsdata för agents att lära från

### **Infrastructure sedan:**
4. **IDE integration** - Gör development snabbare när vi itererar
5. **Feedback loops** - Self-improvement kräver att allt annat funkar

### **Tidsplan:**
- **Vecka 1:** Ollama + OSINT (aggressivt, men feasible)
- **Vecka 2:** Journal + IDE setup (parallellt work)
- **Vecka 3-4:** Feedback loops + tuning

---

## 📊 FÖRVÄNTADE RESULTAT

### **Efter Fas 1-2 (2 veckor):**
- [ ] Trades per 12h: 4 → 15-25
- [ ] Signal sources: 3 (RSI/MACD/BB) → 8 (+ whale/sentiment/TVL/gas/contracts)
- [ ] Decision reasoning: None → Full LLM explanations
- [ ] Agent consensus: Manual → Automated multi-agent approval

### **Efter Fas 3-4 (3 veckor):**
- [ ] Trade history: Lost after restart → Permanent SQLite + Obsidian
- [ ] Pattern detection: Manual → Automated Dataview queries
- [ ] Development speed: Slow (restart required) → Hot-reload
- [ ] Code quality: No AI assist → Ollama suggestions i Neovim

### **Efter Fas 5 (4 veckor):**
- [ ] Strategy optimization: Manual → Self-adjusting parameters
- [ ] Win rate: 50% → 60-65% (based on learning)
- [ ] Agent oversight: None → Auditor prevents bad trades
- [ ] Reporting: None → Weekly analysis reports

---

## 🚀 NÄSTA STEG

1. **Review denna plan** - Godkänn eller justera
2. **Start Ollama service** - `sudo systemctl enable --now ollama`
3. **Pull models** - `ollama pull qwen2.5-coder:7b llama3.3:8b deepseek-r1:8b`
4. **Skapa first agent** - `src/ollama_agents/base_agent.py`
5. **Test communication** - Two agents talking to each other

**Vill du:**
- A) Starta implementation direkt (börja med Fas 1.1)?
- B) Justera planen först (andra prioriteringar)?
- C) Se proof-of-concept (minimal working example)?

---

**Total estimated effort:** 80-120 timmar över 4 veckor
**Risk level:** Medium (Ollama integration är experimentellt)
**Reward potential:** Hög (self-improving trading system är cutting edge)
