"""
VOLT Learning Agent
Ansvarar för att samla in, analysera och lagra lärande från agenters erfarenheter
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import logging


@dataclass
class TradeOutcome:
    trade_id: str
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percent: float
    duration_minutes: int
    confidence: float
    agents_involved: List[str]
    market_condition: str
    errors: List[str]
    timestamp: str


@dataclass
class AgentError:
    timestamp: str
    agent: str
    error_type: str
    error_message: str
    context: Dict[str, Any]
    recovery_action: str
    resolved: bool


class LearningStore:
    """
    Persistent lagring av agenters erfarenheter
    """

    def __init__(self, db_path: str = "volt_learning.db"):
        self.db_path = db_path
        self._init_database()
        self.logger = logging.getLogger(__name__)

    def _init_database(self):
        """Initiera databasen med tabeller"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Trade outcomes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                symbol TEXT,
                action TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl REAL,
                pnl_percent REAL,
                duration_minutes INTEGER,
                confidence REAL,
                agents_involved TEXT,
                market_condition TEXT,
                errors TEXT,
                timestamp TEXT
            )
        """)

        # Agent errors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent TEXT,
                error_type TEXT,
                error_message TEXT,
                context TEXT,
                recovery_action TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)

        # Agent performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                predictions_total INTEGER DEFAULT 0,
                predictions_correct INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)

        # Learning insights
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT,
                description TEXT,
                agents_affected TEXT,
                confidence REAL,
                applied INTEGER DEFAULT 0,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def store_trade_outcome(self, outcome: TradeOutcome):
        """Lagra handelsutfall"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO trade_outcomes 
            (trade_id, symbol, action, entry_price, exit_price, 
             pnl, pnl_percent, duration_minutes, confidence, 
             agents_involved, market_condition, errors, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                outcome.trade_id,
                outcome.symbol,
                outcome.action,
                outcome.entry_price,
                outcome.exit_price,
                outcome.pnl,
                outcome.pnl_percent,
                outcome.duration_minutes,
                outcome.confidence,
                json.dumps(outcome.agents_involved),
                outcome.market_condition,
                json.dumps(outcome.errors),
                outcome.timestamp,
            ),
        )

        conn.commit()
        conn.close()
        self.logger.info(
            f"📚 Stored trade outcome: {outcome.trade_id} - PnL: ${outcome.pnl:.2f}"
        )

    def store_error(self, error: AgentError):
        """Lagra agent-fel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO agent_errors 
            (timestamp, agent, error_type, error_message, context, recovery_action, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                error.timestamp,
                error.agent,
                error.error_type,
                error.error_message,
                json.dumps(error.context),
                error.recovery_action,
                1 if error.resolved else 0,
            ),
        )

        conn.commit()
        conn.close()
        self.logger.warning(f"⚠️ Stored error from {error.agent}: {error.error_type}")

    def update_agent_accuracy(self, agent: str, prediction_correct: bool):
        """Uppdatera agentens precision"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hämta nuvarande
        cursor.execute(
            """
            SELECT predictions_total, predictions_correct 
            FROM agent_performance WHERE agent = ?
        """,
            (agent,),
        )

        row = cursor.fetchone()

        if row:
            total, correct = row
            total += 1
            correct += 1 if prediction_correct else 0
            accuracy = correct / total if total > 0 else 0

            cursor.execute(
                """
                UPDATE agent_performance 
                SET predictions_total = ?, predictions_correct = ?, 
                    accuracy = ?, last_updated = ?
                WHERE agent = ?
            """,
                (total, correct, accuracy, datetime.now().isoformat(), agent),
            )
        else:
            cursor.execute(
                """
                INSERT INTO agent_performance 
                (agent, predictions_total, predictions_correct, accuracy, last_updated)
                VALUES (?, 1, ?, ?, ?)
            """,
                (
                    agent,
                    1 if prediction_correct else 0,
                    1.0 if prediction_correct else 0.0,
                    datetime.now().isoformat(),
                ),
            )

        conn.commit()
        conn.close()

    def get_agent_performance(self, agent: str) -> Dict[str, Any]:
        """Hämta agentens prestanda"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT predictions_total, predictions_correct, accuracy, last_updated
            FROM agent_performance WHERE agent = ?
        """,
            (agent,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "total_predictions": row[0],
                "correct_predictions": row[1],
                "accuracy": row[2],
                "last_updated": row[3],
            }
        return {"total_predictions": 0, "correct_predictions": 0, "accuracy": 0.0}

    def get_recent_outcomes(self, limit: int = 50) -> List[Dict]:
        """Hämta senaste handelsutfall"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT trade_id, symbol, action, pnl, pnl_percent, 
                   confidence, market_condition, timestamp
            FROM trade_outcomes 
            ORDER BY timestamp DESC LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "trade_id": r[0],
                "symbol": r[1],
                "action": r[2],
                "pnl": r[3],
                "pnl_percent": r[4],
                "confidence": r[5],
                "market_condition": r[6],
                "timestamp": r[7],
            }
            for r in rows
        ]

    def get_error_patterns(self, hours: int = 24) -> Dict[str, int]:
        """Analysera felmönster"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT error_type, COUNT(*) as count 
            FROM agent_errors 
            WHERE timestamp > datetime('now', '-{} hours')
            GROUP BY error_type 
            ORDER BY count DESC
        """.format(hours),
            (),
        )

        rows = cursor.fetchall()
        conn.close()

        return {r[0]: r[1] for r in rows}

    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Sammanfattning av prestanda"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total P&L
        cursor.execute(
            """
            SELECT SUM(pnl), COUNT(*), AVG(pnl)
            FROM trade_outcomes 
            WHERE timestamp > datetime('now', '-{} days')
        """.format(days)
        )
        pnl_row = cursor.fetchone()

        # Win rate
        cursor.execute(
            """
            SELECT COUNT(*) FROM trade_outcomes 
            WHERE pnl > 0 AND timestamp > datetime('now', '-{} days')
        """.format(days)
        )
        wins = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM trade_outcomes 
            WHERE timestamp > datetime('now', '-{} days')
        """.format(days)
        )
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "total_pnl": pnl_row[0] or 0,
            "total_trades": pnl_row[1] or 0,
            "avg_pnl": pnl_row[2] or 0,
            "win_rate": (wins / total * 100) if total > 0 else 0,
            "period_days": days,
        }


class LearningAgent:
    """
    Agent som samlar in och analyserar lärande från systemet
    """

    def __init__(self, config_manager=None, exchange=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.exchange = exchange
        self.learning_store = LearningStore()
        self.running = False

        self.performance_history = []
        self.improvement_threshold = 0.55  # Under detta görs justeringar

    async def initialize(self):
        self.logger.info("🧠 Initializing Learning Agent...")

        # Ladda tidigare prestanda
        performance = self.learning_store.get_performance_summary(7)
        self.logger.info(f"📊 7-day performance: {performance}")

        # Analysera felmönster
        error_patterns = self.learning_store.get_error_patterns(24)
        if error_patterns:
            self.logger.warning(f"⚠️ Recent error patterns: {error_patterns}")

        self.logger.info("✅ Learning Agent initialized")

    async def start(self):
        self.running = True
        self.logger.info("🚀 Learning Agent started")

        if self.running:
            asyncio.create_task(self._learning_loop())

    async def stop(self):
        self.running = False
        self.logger.info("🛑 Learning Agent stopped")

    async def _learning_loop(self):
        """Bakgrundsloop för kontinuerligt lärande"""
        while self.running:
            try:
                # Analysera prestanda var 30:e minut
                await self._analyze_performance()

                # Kontrollera felmönster
                await self._check_error_patterns()

                await asyncio.sleep(1800)  # 30 minuter
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(300)

    async def record_trade_outcome(self, trade: Dict[str, Any]):
        """Registrera handelsutfall för analys"""
        outcome = TradeOutcome(
            trade_id=trade.get("id", "unknown"),
            symbol=trade.get("symbol", ""),
            action=trade.get("side", ""),
            entry_price=trade.get("entry_price", 0),
            exit_price=trade.get("exit_price", 0),
            pnl=trade.get("pnl", 0),
            pnl_percent=trade.get("pnl_percent", 0),
            duration_minutes=trade.get("duration_minutes", 0),
            confidence=trade.get("confidence", 0),
            agents_involved=trade.get("agents", []),
            market_condition=trade.get("market_condition", "unknown"),
            errors=trade.get("errors", []),
            timestamp=datetime.now().isoformat(),
        )

        self.learning_store.store_trade_outcome(outcome)

        # Uppdatera agent-precision
        for agent in outcome.agents_involved:
            is_correct = outcome.pnl > 0
            self.learning_store.update_agent_accuracy(agent, is_correct)

    async def record_error(
        self,
        agent: str,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        recovery_action: str = "none",
    ):
        """Registrera fel för framtida referens"""
        error = AgentError(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            error_type=error_type,
            error_message=error_message,
            context=context,
            recovery_action=recovery_action,
            resolved=False,
        )

        self.learning_store.store_error(error)

    async def _analyze_performance(self):
        """Analysera prestanda och generera insikter"""
        summary = self.learning_store.get_performance_summary(1)

        self.logger.info(
            f"📈 Daily performance: {summary['total_trades']} trades, "
            f"${summary['total_pnl']:.2f} P&L, "
            f"{summary['win_rate']:.1f}% win rate"
        )

        # Kontrollera om vi behöver justera
        if summary["win_rate"] < 50 and summary["total_trades"] > 10:
            self.logger.warning(
                f"⚠️ Low win rate ({summary['win_rate']:.1f}%) - "
                "consider adjusting parameters"
            )

    async def _check_error_patterns(self):
        """Kontrollera och analysera felmönster"""
        patterns = self.learning_store.get_error_patterns(1)

        if patterns:
            total_errors = sum(patterns.values())
            if total_errors > 20:
                self.logger.error(
                    f"🚨 High error rate: {total_errors} errors in last 24h"
                )
                self.logger.error(f"   Patterns: {patterns}")

    async def get_insights(self) -> Dict[str, Any]:
        """Hämta insikter för agenterna"""
        return {
            "performance_7d": self.learning_store.get_performance_summary(7),
            "performance_1d": self.learning_store.get_performance_summary(1),
            "recent_outcomes": self.learning_store.get_recent_outcomes(10),
            "error_patterns_24h": self.learning_store.get_error_patterns(24),
            "agent_performance": {
                "strategy_agent": self.learning_store.get_agent_performance(
                    "strategy_agent"
                ),
                "risk_agent": self.learning_store.get_agent_performance("risk_agent"),
                "market_agent": self.learning_store.get_agent_performance(
                    "market_agent"
                ),
            },
        }

    async def suggest_improvements(self) -> List[Dict[str, str]]:
        """Generera förbättringsförslag baserat på data"""
        suggestions = []

        # Kolla agent-precision
        for agent in ["strategy_agent", "risk_agent", "market_agent"]:
            perf = self.learning_store.get_agent_performance(agent)
            if perf["total_predictions"] > 5:
                if perf["accuracy"] < 0.5:
                    suggestions.append(
                        {
                            "agent": agent,
                            "issue": "low_accuracy",
                            "suggestion": f"Consider adjusting {agent} confidence threshold",
                            "current_accuracy": f"{perf['accuracy']:.1%}",
                        }
                    )

        # Kolla felmönster
        errors = self.learning_store.get_error_patterns(24)
        for error_type, count in errors.items():
            if count > 10:
                suggestions.append(
                    {
                        "type": "error_pattern",
                        "issue": error_type,
                        "suggestion": f"Review {error_type} handling - {count} occurrences",
                    }
                )

        return suggestions
