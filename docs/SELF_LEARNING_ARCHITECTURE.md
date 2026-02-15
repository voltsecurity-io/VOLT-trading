# VOLT Självlärande Multi-Agent Trading System

## Översikt

Detta dokument beskriver arkitekturen för ett självlärande AI-trading system där agenter kommunicerar, kontrollerar varandra, lär sig från misstag och kontinuerligt förbättras.

---

## 1. Agentarkitektur

### 1.1 Kärnagenter (Core Agents)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      VOLT Agent Ekosystem                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │   STRATEGY     │    │    RISK         │    │   MARKET        │   │
│  │   AGENT        │◄──►│    AGENT        │◄──►│   AGENT         │   │
│  │                 │    │                 │    │                 │   │
│  │ - Signal gen   │    │ - Riskbedömning │    │ - Trendanalys   │   │
│  │ - Position     │    │ - Storlekscalc  │    │ - Volatilitet  │   │
│  │ - Entry/Exit   │    │ - Korrelation   │    │ - Momentum      │   │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘   │
│           │                       │                       │            │
│           ▼                       ▼                       ▼            │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              CONSENSUS & AUDIT LAYER                           │  │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │   │ EXECUTION  │  │  AUDITOR    │  │  LEARNING   │          │  │
│  │   │   AGENT    │  │   AGENT     │  │   AGENT     │          │  │
│  │   │             │  │             │  │             │          │  │
│  │   │ - Timing    │  │ - Cross-    │  │ - Outcome   │          │  │
│  │   │ - Ordertyp  │  │   check     │  │   tracking │          │  │
│  │   │ - Slippage  │  │ - Anomaly   │  │ - Pattern  │          │  │
│  │   │             │  │   detection │  │   discovery│          │  │
│  │   └─────────────┘  └─────────────┘  └─────────────┘          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              SPECIALIST AGENTS                                   │  │
│  │   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐ │  │
│  │   │ SENTIMENT│ │   FOREX   │ │   MACRO   │ │   GLOBAL      │ │  │
│  │   │   AGENT  │ │   AGENT   │ │   AGENT   │ │   ANALYTICS  │ │  │
│  │   └───────────┘ └───────────┘ └───────────┘ └───────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent-specifikationer

#### StrategyAgent
```
Ansvar: Generera handelssignaler
Input: Tekniska indikatorer, historisk data, agent-minne
Output: BUY/SELL/HOLD confidence och med storlek

Metoder:
- analyze_market_conditions() -> signal
- calculate_position_size() -> fraction
- suggest_entry_exit() -> (entry, exit, stop_loss)
- learn_from_outcome(trade_result) -> parameter_adjustments
```

#### RiskAgent
```
Ansvar: Riskbedömning och positionshantering
Input: Signal, nuvarande portfolio, marknadsförhållanden
Output: APPROVED/REJECTED med risk_score

Metoder:
- assess_trade_risk(signal) -> risk_assessment
- calculate_correlation_risk(new_position) -> float
- check_drawdown_limits() -> bool
- learn_from_rejections(mistakes) -> rule_adjustments
```

#### MarketAgent
```
Ansvar: Marknadsanalys och trenddetektering
Input: Prisdata, volumdata, nyhetsflöde
Output: BULLISH/BEARISH/NEUTRAL med styrka

Metoder:
- detect_trend() -> (direction, strength)
- identify_support_resistance() -> levels
- analyze_volume_pattern() -> volume_signal
- learn_market_cycles() -> seasonal_patterns
```

#### LearningAgent (NY!)
```
Ansvar: Koordinera lärande mellan alla agenter
Input: Alla agenters resultat, handelsutfall, felmeddelanden
Output: Uppdaterade parametrar, insikter, anomalidetektering

Metoder:
- track_outcome(prediction, actual) -> accuracy
- identify_error_patterns() -> error_signatures
- propose_agent_improvements() -> recommendations
- store_learning(session_data) -> vector_store
```

---

## 2. Kommunikation & Koordinering

### 2.1 Agent-meddelandesystem

```python
class AgentMessage:
    message_id: str
    timestamp: datetime
    from_agent: str
    to_agent: str | "BROADCAST"
    message_type: MessageType
    priority: Priority  # LOW, NORMAL, HIGH, CRITICAL
    payload: dict
    requires_response: bool
    response_deadline: datetime | None

class MessageType(Enum):
    # Beslut & Godkännande
    TRADE_PROPOSAL = "trade_proposal"
    RISK_APPROVAL = "risk_approval"
    EXECUTION_COMPLETE = "execution_complete"
    
    # Lärande & Feedback
    OUTCOME_REPORT = "outcome_report"
    ERROR_REPORT = "error_report"
    CORRECTION_REQUEST = "correction_request"
    PEER_REVIEW = "peer_review"
    
    # Koordinering
    DATA_REQUEST = "data_request"
    STATUS_UPDATE = "status_update"
    CONSENSUS_REQUEST = "consensus_request"
```

### 2.2 Konsensus-mekanism

```python
class ConsensusMechanism:
    """
    Agenter röstar och väger in varandras åsikter
    """
    
    def build_consensus(self, proposal: TradeProposal) -> ConsensusResult:
        # 1. Samla in röster från alla agenter
        votes = {}
        votes["strategy"] = strategy_agent.vote(proposal)
        votes["risk"] = risk_agent.vote(proposal)
        votes["market"] = market_agent.vote(proposal)
        votes["execution"] = execution_agent.vote(proposal)
        votes["sentiment"] = sentiment_agent.vote(proposal)
        
        # 2. Tillämpa vikter baserat på historisk precision
        weighted_votes = self._apply_weights(votes)
        
        # 3. Beräkna konsensus
        consensus = self._calculate_weighted_result(weighted_votes)
        
        # 4. Lär av tidigare konsensus-resultat
        self.learning_agent.record_consensus(proposal, consensus, votes)
        
        return consensus
```

### 2.3 Ömsesidig granskning (Peer Review)

```python
class PeerReview:
    """
    Agenter granskar varandras beslut innan execution
    """
    
    async def review_trade(self, trade: Trade) -> ReviewResult:
        reviews = await asyncio.gather(
            self.auditor_agent.review(trade),      # Kvalitetsgranskning
            self.risk_agent.review(trade),         # Riskgranskning
            self.learning_agent.review(trade)       # Historiagranskning
        )
        
        # Konsensus bland granskare
        approval_count = sum(1 for r in reviews if r.approved)
        
        if approval_count >= 2:
            return ReviewResult.APPROVED
        elif approval_count == 1:
            return ReviewResult.CAUTION  # Kräver extra övervakning
        else:
            return ReviewResult.REJECTED
```

---

## 3. Självlärande System

### 3.1 Feedback-loop från handelsutfall

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     LEARNING FEEDBACK LOOP                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐    │
│   │ TRADE   │────►│ OUTCOME  │────►│ PATTERN  │────►│ AGENT    │    │
│   │ EXECUTE │     │ TRACKER  │     │ ANALYSIS │     │ UPDATE   │    │
│   └──────────┘     └──────────┘     └──────────┘     └──────────┘    │
│       │                                                  │             │
│       │                                                  ▼             │
│       │                                        ┌──────────────────┐      │
│       │                                        │ PARAMETER       │      │
│       │                                        │ ADJUSTMENT      │      │
│       │                                        │                 │      │
│       │                                        │ - Confidence    │      │
│       │                                        │ - Thresholds    │      │
│       │                                        │ - Weights       │      │
│       │                                        └──────────────────┘      │
│       │                                                  │             │
│       └──────────────────────────────────────────────────┘             │
│                                                                         │
│   FEEDBACK TYPES:                                                     │
│   ───────────────                                                      │
│   1. Outcome Feedback: "Prediction was correct/incorrect"             │
│   2. Timing Feedback: "Entry was early/late"                          │
│   3. Risk Feedback: "Risk was underestimated/overestimated"           │
│   4. Error Feedback: "Error occurred - how to recover"               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Inlärnings-databas

```python
class LearningStore:
    """
    Persistent lagring av agenters erfarenheter
    Använder SQLite för strukturerad data + embeddings för semantisk sök
    """
    
    def __init__(self):
        self.db = sqlite3.connect("volt_learning.db")
        self.vector_store = ChromaClient()  # För embeddings
        
    def store_trade_outcome(self, outcome: TradeOutcome):
        """Lagra komplett handelsutfall"""
        self.db.execute("""
            INSERT INTO trade_outcomes 
            (trade_id, symbol, action, entry_price, exit_price, 
             pnl, duration, market_condition, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, outcome.to_tuple())
        
        # Lagra embedding för semantisk sökning av liknande situationer
        self.vector_store.add(
            collection="outcomes",
            text=outcome.to_embedding_text(),
            metadata=outcome.to_metadata()
        )
    
    def store_error(self, error: AgentError):
        """Lagra felmeddelanden för framtida referens"""
        self.db.execute("""
            INSERT INTO agent_errors
            (timestamp, agent, error_type, error_message, 
             recovery_action, resolved)
            VALUES (?, ?, ?, ?, ?, ?)
        """, error.to_tuple())
        
    def get_similar_outcomes(self, current_context: dict) -> list:
        """Hämta liknande tidigare utfall"""
        embedding = self.embeddings.embed(current_context)
        return self.vector_store.search(
            collection="outcomes",
            query_embedding=embedding,
            n=5
        )
    
    def get_error_patterns(self, agent: str) -> dict:
        """Analysera återkommande fel för en agent"""
        return self.db.execute("""
            SELECT error_type, COUNT(*) as count 
            FROM agent_errors 
            WHERE agent = ? 
            GROUP BY error_type 
            ORDER BY count DESC
        """, (agent,)).fetchall()
```

### 3.3 Agent-förbättring

```python
class AgentImprover:
    """
    Automatisk förbättring av agent-beteende baserat på erfarenhet
    """
    
    def analyze_and_improve(self, agent: Agent) -> ImprovementResult:
        outcomes = self.learning_store.get_outcomes_for_agent(agent.id)
        errors = self.learning_store.get_error_patterns(agent.id)
        
        # Analysera träffsäkerhet
        accuracy = self._calculate_accuracy(outcomes)
        
        # Identifiera förbättringsområden
        issues = []
        if accuracy < 0.5:
            issues.append("accuracy_too_low")
        if errors["timeout"] > 10:
            issues.append("too_many_timeouts")
            
        # Generera förbättringar
        improvements = []
        for issue in issues:
            improvement = self._generate_fix(issue, outcomes, errors)
            improvements.append(improvement)
            
        return ImprovementResult(
            applied=improvements,
            accuracy=accuracy,
            recommendations=self._generate_recommendations(outcomes)
        )
    
    def _generate_fix(self, issue: str, outcomes: list, errors: dict) -> Fix:
        """Generera specifik fix baserat på problem"""
        
        if issue == "accuracy_too_low":
            # Justera confidence threshold
            current_threshold = outcomes[0].confidence_threshold
            new_threshold = current_threshold * 1.1  # Högre krav
            
            return Fix(
                type="parameter_adjustment",
                target="confidence_threshold",
                old_value=current_threshold,
                new_value=new_threshold,
                reason="Accuracy below 50%, increasing threshold"
            )
            
        elif issue == "too_many_timeouts":
            # Sänk timeout eller byt modell
            return Fix(
                type="model_adjustment",
                target="timeout",
                old_value=60,
                new_value=30,
                reason="Too many timeouts, reducing timeout"
            )
```

---

## 4. Felhantering & Återhämtning

### 4.1 Felkategorier

```python
class ErrorCategory(Enum):
    NETWORK = "network"           # Timeout, connection lost
    EXCHANGE = "exchange"         # API-fel, rate limits
    MODEL = "model"               # LLM timeout, invalid response
    LOGIC = "logic"               # Buggar i agent-logic
    DATA = "data"                 # Saknad data, invalid format
    MARKET = "market"             # Oväntade marknadsförhållanden
```

### 4.2 Felhanterings-flöde

```python
class ErrorHandler:
    """
    Centraliserad felhantering med automatiska återhämtningsstrategier
    """
    
    async def handle_error(self, error: Exception, context: dict) -> ErrorResult:
        # 1. Klassificera felet
        category = self._classify_error(error)
        
        # 2. Logga och lagra felet
        self.learning_store.store_error(AgentError(
            agent=context.get("agent"),
            error_type=category,
            error_message=str(error),
            context=context
        ))
        
        # 3. Bestäm återhämtningsstrategi
        strategy = self._get_recovery_strategy(category, error)
        
        # 4. Applicera återhämtning
        result = await strategy.execute(context)
        
        # 5. Meddela relevanta agenter
        await self._notify_agents(category, result)
        
        return result
    
    def _get_recovery_strategy(self, category: ErrorCategory, error: Exception):
        """Välj lämplig återhämtningsstrategi"""
        
        strategies = {
            ErrorCategory.NETWORK: NetworkRecoveryStrategy(),
            ErrorCategory.EXCHANGE: ExchangeRecoveryStrategy(),
            ErrorCategory.MODEL: ModelFallbackStrategy(),
            ErrorCategory.LOGIC: LogicErrorStrategy(),
            ErrorCategory.DATA: DataFallbackStrategy(),
            ErrorCategory.MARKET: MarketCircuitBreaker(),
        }
        
        return strategies.get(category, DefaultRecoveryStrategy())
```

### 4.3 Återhämtningsstrategier

```python
class NetworkRecoveryStrategy:
    """Återhämtning från nätverksfel"""
    
    async def execute(self, context: dict) -> ErrorResult:
        # 1. Exponentiell backoff
        await self._exponential_backoff(context.get("attempt", 1))
        
        # 2. Försök igen
        try:
            result = await context["retry_function"]()
            return ErrorResult(resolved=True, action="retry_succeeded")
        except:
            # 3. Om det misslyckas igen, fallback
            return ErrorResult(
                resolved=False, 
                action="circuit_breaker_triggered",
                fallback_used=True
            )

class ModelFallbackStrategy:
    """Återhämtning från LLM-fel"""
    
    MODELS = ["qwen2.5-coder:7b", "gemma3:latest", "dolphin-llama3:latest"]
    
    async def execute(self, context: dict) -> ErrorResult:
        current_model = context.get("current_model")
        
        # Hitta nästa modell i prioritet
        try:
            next_model = self.MODELS[self.MODELS.index(current_model) + 1]
        except (ValueError, IndexError):
            # Alla modeller misslyckades
            return ErrorResult(
                resolved=False,
                action="all_models_failed",
                requires_human_intervention=True
            )
        
        # Byt modell och försök igen
        context["agent"].model = next_model
        return ErrorResult(
            resolved=True,
            action="model_switched",
            new_model=next_model
        )
```

---

## 5. Resultatanalys & Marknadsförståelse

### 5.1 P&L Analys-agent

```python
class PerformanceAnalyzer:
    """
    Analyserar handelsresultat för att identifiera mönster och förbättringsområden
    """
    
    def analyze_trade_performance(self, trades: list[Trade]) -> PerformanceReport:
        report = PerformanceReport()
        
        # 1. Grundläggande statistik
        report.total_trades = len(trades)
        report.winning_trades = sum(1 for t in trades if t.pnl > 0)
        report.losing_trades = sum(1 for t in trades if t.pnl < 0)
        report.win_rate = report.winning_trades / report.total_trades
        
        # 2. P&L-mått
        report.total_pnl = sum(t.pnl for t in trades)
        report.avg_win = self._average([t.pnl for t in trades if t.pnl > 0])
        report.avg_loss = self._average([t.pnl for t in trades if t.pnl < 0])
        report.largest_win = max(t.pnl for t in trades)
        report.largest_loss = min(t.pnl for t in trades)
        
        # 3. Tidsanalys
        report.avg_trade_duration = self._average(t.duration for t in trades)
        report.best_trading_hour = self._find_best_hour(trades)
        report.best_trading_day = self._find_best_day(trades)
        
        # 4. Symbolanalys
        report.per_symbol = self._analyze_by_symbol(trades)
        
        # 5. Mönsterdetektering
        report.patterns = self._detect_patterns(trades)
        
        # 6. Korrelationsanalys
        report.market_correlation = self._analyze_market_correlation(trades)
        
        return report
    
    def _detect_patterns(self, trades: list[Trade]) -> list[Pattern]:
        """Identifiera återkommande mönster"""
        patterns = []
        
        # Winning streak pattern
        winning_streaks = self._find_streaks(trades, min_length=3, positive=True)
        if winning_streaks:
            patterns.append(Pattern(
                type="winning_streak",
                frequency=len(winning_streaks),
                avg_length=sum(winning_streaks) / len(winning_streaks),
                recommendation="Consider increasing position size during streaks"
            ))
        
        # Losing streak pattern
        losing_streaks = self._find_streaks(trades, min_length=3, positive=False)
        if losing_streaks:
            patterns.append(Pattern(
                type="losing_streak",
                frequency=len(losing_streaks),
                avg_length=sum(losing_streaks) / len(losing_streaks),
                recommendation="Consider reducing position size or pausing"
            ))
        
        # Time-based pattern
        if report.best_trading_hour:
            patterns.append(Pattern(
                type="time_of_day",
                data=report.best_trading_hour,
                recommendation="Focus trading during peak performance hours"
            ))
        
        return patterns
```

### 5.2 Global Marknadsanalys

```python
class GlobalMarketAnalyzer:
    """
    Analyserar den globala marknaden för att förstå makrotrender
    """
    
    def __init__(self):
        self.data_sources = {
            "crypto": CryptoDataSource(),      # CoinGecko, Binance
            "forex": ForexDataSource(),         # Valutakurser
            "commodities": CommoditySource(),   # Guld, olja
            "indices": IndexSource(),           # S&P500, NASDAQ, etc
            "macro": MacroDataSource(),         # Räntor, inflation
            "news": NewsSource(),               # Nyhetsanalys
        }
    
    async def analyze_global_market(self) -> GlobalMarketReport:
        # Samla data parallellt
        data = await asyncio.gather(
            self.data_sources["crypto"].get_market_data(),
            self.data_sources["forex"].get_market_data(),
            self.data_sources["indices"].get_market_data(),
            self.data_sources["macro"].get_indicators(),
            self.data_sources["news"].get_sentiment(),
        )
        
        report = GlobalMarketReport()
        
        # Analysera marknadsregim
        report.regime = self._identify_regime(data)
        
        # Analysera risk-appetit
        report.risk_appetite = self._calculate_risk_appetite(data)
        
        # Korrelationsanalys
        report.correlations = self._calculate_correlations(data)
        
        # Förutsägelse av marknadsförhållanden
        report.forecast = self._generate_forecast(data)
        
        return report
    
    def _identify_regime(self, data: dict) -> MarketRegime:
        """Identifiera nuvarande marknadsregim"""
        
        vix = data["macro"].get("vix", 15)
        spx_trend = data["indices"]["spx"].trend
        btc_trend = data["crypto"]["btc"].trend
        btc_dominance = data["crypto"]["btc_dominance"]
        
        # Klassificera regim
        if vix > 30:
            return MarketRegime.HIGH_VOLATILITY
        elif vix < 15 and btc_trend == "bullish":
            return MarketRegime.BULL_MARKET
        elif btc_trend == "bearish":
            return MarketRegime.BEAR_MARKET
        elif btc_dominance > 50:
            return MarketRegime.BTC_DOMINANCE
        else:
            return MarketRegime.SIDEWAYS
```

---

## 6. Automatisk Start & Övervakning

### 6.1 Systemd-tjänst

```ini
# /home/.config/systemd/user/volt-trading.service
[Unit]
Description=VOLT Self-Learning Trading System
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=%u
WorkingDirectory=/home/omarchy/VOLT-trading
ExecStart=/usr/bin/python3 /home/omarchy/VOLT-trading/main.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/omarchy/VOLT-trading/logs/volt_trading.log
StandardError=append:/home/omarchy/VOLT-trading/logs/volt_errors.log

# Environment
Environment=PYTHONUNBUFFERED=1
Environment=VOLT_MODE=production

# Resource limits
MemoryMax=2G
CPUQuota=80%

[Install]
WantedBy=default.target
```

### 6.2 Healthcheck & Restart

```python
class HealthMonitor:
    """
    Övervakar systemhälsa och startar om vid behov
    """
    
    def __init__(self):
        self.checks = {
            "agents": self._check_agents,
            "exchange": self._check_exchange,
            "memory": self._check_memory,
            "errors": self._check_error_rate,
            "performance": self._check_performance,
        }
    
    async def health_check(self) -> HealthReport:
        results = {}
        for name, check in self.checks.items():
            results[name] = await check()
        
        return HealthReport(
            overall_health=self._calculate_overall(results),
            checks=results,
            recommendations=self._generate_recommendations(results)
        )
    
    async def _check_error_rate(self) -> CheckResult:
        """Kontrollera felfrekvens"""
        recent_errors = self.db.execute("""
            SELECT COUNT(*) FROM agent_errors 
            WHERE timestamp > datetime('now', '-1 hour')
        """).fetchone()[0]
        
        if recent_errors > 50:
            return CheckResult(
                status=Status.CRITICAL,
                message=f"High error rate: {recent_errors} errors/hour"
            )
        elif recent_errors > 20:
            return CheckResult(
                status=Status.WARNING,
                message=f"Elevated error rate: {recent_errors} errors/hour"
            )
        else:
            return CheckResult(
                status=Status.HEALTHY,
                message="Error rate normal"
            )
```

---

## 7. Implementations-plan

### Fas 1: Grundläggande infrastruktur
- [ ] Utöka AgentMessage-systemet med nya meddelandetyper
- [ ] Implementera LearningStore (SQLite + embeddings)
- [ ] Skapa LearningAgent
- [ ] Sätt upp systemd-tjänst för automatisk start

### Fas 2: Feedback-loop
- [ ] Implementera outcome tracking
- [ ] Bygg Pattern Analysis
- [ ] Skapa AgentImprover
- [ ] Implementera Peer Review

### Fas 3: Avancerat lärande
- [ ] Bygg GlobalMarketAnalyzer
- [ ] Implementera PerformanceAnalyzer
- [ ] Skapa automatiska parameter-justeringar
- [ ] Lägg till anomalidetektering

### Fas 4: Optimering
- [ ] Agent-modelloptimering baserat på resultat
- [ ] Implementera adaptive confidence
- [ ] Bygg prediktiv analys
- [ ] Skapadashboards för lärande-insikter

---

## 8. Teknisk Stack

| Komponent | Teknologi | Syfte |
|-----------|-----------|-------|
| Agent-ramverk | Ollama + Custom | AI-resonemang |
| Databas | SQLite | Strukturera handelsdata |
| Vektordatabas | ChromaDB | Semantisk sökning av erfarenheter |
| Message Queue | asyncio | Asynkron agentkommunikation |
| Logging | Custom + ELK | Felanalys och övervakning |
| Automation | Systemd | Automatisk start och återställning |

---

*Document version: 1.0*
*Last updated: 2026-02-15*
