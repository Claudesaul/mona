"""Persistent query and conversation logging via SQLite."""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "mona_log.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Call at app startup."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                message_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES conversations(id)
            );

            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                database_label TEXT,
                query_text TEXT,
                row_count INTEGER,
                duration_ms INTEGER,
                error TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES conversations(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
            CREATE INDEX IF NOT EXISTS idx_tool_calls_executed ON tool_calls(executed_at);
        """)
        conn.commit()
        logger.info("Query log database initialized at %s", _DB_PATH)
    finally:
        conn.close()


def log_conversation(session_id: str) -> None:
    """Upsert a conversation record."""
    now = datetime.now().isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO conversations (id, started_at, last_active, message_count)
               VALUES (?, ?, ?, 0)
               ON CONFLICT(id) DO UPDATE SET last_active = ?, message_count = message_count + 1""",
            (session_id, now, now, now),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to log conversation %s", session_id)
    finally:
        conn.close()


def log_message(session_id: str, role: str, content: str) -> None:
    """Log a user or assistant message."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to log message for session %s", session_id)
    finally:
        conn.close()


def log_tool_call(
    session_id: str,
    tool_name: str,
    database_label: str,
    query_text: str,
    row_count: int = 0,
    duration_ms: int = 0,
    error: str | None = None,
) -> None:
    """Log a tool/database call."""
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO tool_calls
               (session_id, tool_name, database_label, query_text, row_count, duration_ms, error)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, tool_name, database_label, query_text, row_count, duration_ms, error),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to log tool call for session %s", session_id)
    finally:
        conn.close()


def get_recent_queries(limit: int = 50) -> list[dict]:
    """Get recent tool calls with conversation context."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT
                tc.executed_at,
                tc.session_id,
                tc.tool_name,
                tc.database_label,
                tc.query_text,
                tc.row_count,
                tc.duration_ms,
                tc.error,
                (SELECT m.content FROM messages m
                 WHERE m.session_id = tc.session_id AND m.role = 'user'
                 AND m.created_at <= tc.executed_at
                 ORDER BY m.created_at DESC LIMIT 1) AS user_question
            FROM tool_calls tc
            ORDER BY tc.executed_at DESC
            LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats() -> dict:
    """Return usage statistics."""
    conn = _get_conn()
    try:
        # Total counts
        total_conversations = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        total_queries = conn.execute("SELECT COUNT(*) FROM tool_calls").fetchone()[0]

        # Queries by database
        by_database = conn.execute(
            """SELECT database_label, COUNT(*) as count, AVG(duration_ms) as avg_ms
               FROM tool_calls GROUP BY database_label ORDER BY count DESC"""
        ).fetchall()

        # Messages per day (last 30 days)
        daily = conn.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as count
               FROM messages WHERE role = 'user'
               AND created_at >= DATE('now', '-30 days')
               GROUP BY DATE(created_at) ORDER BY day DESC"""
        ).fetchall()

        # Most common user questions (by first words)
        top_questions = conn.execute(
            """SELECT content, COUNT(*) as count
               FROM messages WHERE role = 'user'
               GROUP BY content ORDER BY count DESC LIMIT 20"""
        ).fetchall()

        # Error rate
        error_count = conn.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE error IS NOT NULL"
        ).fetchone()[0]

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_queries": total_queries,
            "error_count": error_count,
            "error_rate": round(error_count / max(total_queries, 1) * 100, 1),
            "queries_by_database": [dict(r) for r in by_database],
            "daily_usage": [dict(r) for r in daily],
            "top_questions": [dict(r) for r in top_questions],
        }
    finally:
        conn.close()
