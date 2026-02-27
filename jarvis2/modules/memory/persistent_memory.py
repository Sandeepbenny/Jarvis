# modules/memory/persistent_memory.py
"""
Persistent memory using SQLite.
Stores:
  - Conversation history (survives restarts)
  - Long-term facts about the user
  - Episodic memories (important events)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


JARVIS_DATA_DIR = Path.home() / ".jarvis"
JARVIS_DATA_DIR.mkdir(exist_ok=True)
DB_PATH = JARVIS_DATA_DIR / "memory.db"

MAX_HISTORY_TOKENS = 4000  # Approximate token budget for history


class PersistentMemory:
    """
    SQLite-backed memory that persists across sessions.
    Manages conversation history, user facts, and episodic memory.
    """

    def __init__(self, db_path: Path = DB_PATH, session_id: str = "default"):
        self.db_path = db_path
        self.session_id = session_id
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary TEXT NOT NULL,
                    importance INTEGER DEFAULT 5,
                    timestamp TEXT NOT NULL,
                    tags TEXT DEFAULT '[]'
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, id);
            """)

    # ─────────────────────────────────────────────────────
    # Conversation History
    # ─────────────────────────────────────────────────────

    def add_user_message(self, content: str) -> None:
        """Add a user message to the current session history."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.session_id, "human", content, datetime.now().isoformat())
            )

    def add_ai_message(self, content: str) -> None:
        """Add an AI response to the current session history."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.session_id, "ai", content, datetime.now().isoformat())
            )

    def get_messages(self, limit: int = 20) -> List:
        """
        Get the last N messages for the LangChain prompt, as LangChain message objects.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT role, content FROM messages 
                   WHERE session_id = ? 
                   ORDER BY id DESC LIMIT ?""",
                (self.session_id, limit)
            ).fetchall()

        rows = list(reversed(rows))
        
        messages = []
        for row in rows:
            if row["role"] == "human":
                messages.append(HumanMessage(content=row["content"]))
            elif row["role"] == "ai":
                messages.append(AIMessage(content=row["content"]))
        
        return messages

    def clear_session(self) -> None:
        """Clear current session conversation history."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (self.session_id,)
            )

    def get_all_sessions(self) -> List[str]:
        """Get list of all session IDs."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT session_id FROM messages ORDER BY session_id"
            ).fetchall()
        return [r["session_id"] for r in rows]

    # ─────────────────────────────────────────────────────
    # Long-Term User Facts
    # ─────────────────────────────────────────────────────

    def remember_fact(self, key: str, value: str, confidence: float = 1.0) -> None:
        """
        Store a long-term fact about the user.
        Example: remember_fact("name", "Tony"), remember_fact("location", "Mumbai")
        """
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO user_facts (key, value, confidence, updated_at) 
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET 
                       value=excluded.value,
                       confidence=excluded.confidence,
                       updated_at=excluded.updated_at""",
                (key.lower(), value, confidence, datetime.now().isoformat())
            )

    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a stored user fact."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM user_facts WHERE key = ?",
                (key.lower(),)
            ).fetchone()
        return row["value"] if row else None

    def get_all_facts(self) -> Dict[str, str]:
        """Get all stored user facts."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM user_facts ORDER BY key"
            ).fetchall()
        return {row["key"]: row["value"] for row in rows}

    def forget_fact(self, key: str) -> bool:
        """Remove a stored fact."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM user_facts WHERE key = ?",
                (key.lower(),)
            )
        return cursor.rowcount > 0

    # ─────────────────────────────────────────────────────
    # Episodic Memory (important moments)
    # ─────────────────────────────────────────────────────

    def add_episode(self, summary: str, importance: int = 5, tags: List[str] = []) -> None:
        """
        Store an important episode/event in memory.
        
        Args:
            summary: What happened
            importance: 1-10 scale (10 = very important)
            tags: Categories (e.g., ['work', 'meeting'])
        """
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO episodic_memory (summary, importance, timestamp, tags)
                   VALUES (?, ?, ?, ?)""",
                (summary, importance, datetime.now().isoformat(), json.dumps(tags))
            )

    def get_episodes(self, limit: int = 10, min_importance: int = 1) -> List[Dict]:
        """Get recent important episodes."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM episodic_memory 
                   WHERE importance >= ?
                   ORDER BY importance DESC, timestamp DESC
                   LIMIT ?""",
                (min_importance, limit)
            ).fetchall()
        
        return [{
            "id": r["id"],
            "summary": r["summary"],
            "importance": r["importance"],
            "timestamp": r["timestamp"],
            "tags": json.loads(r["tags"])
        } for r in rows]

    def get_memory_context(self) -> str:
        """
        Generate a context string for the system prompt
        that includes relevant user facts and recent episodes.
        """
        facts = self.get_all_facts()
        episodes = self.get_episodes(limit=5, min_importance=6)
        
        lines = []
        
        if facts:
            lines.append("=== Known Facts About User ===")
            for k, v in facts.items():
                lines.append(f"  {k}: {v}")
        
        if episodes:
            lines.append("\n=== Important Past Events ===")
            for ep in episodes:
                ts = ep["timestamp"][:10]
                lines.append(f"  [{ts}] {ep['summary']}")
        
        return "\n".join(lines) if lines else ""

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with self._get_conn() as conn:
            msg_count = conn.execute(
                "SELECT COUNT(*) as c FROM messages WHERE session_id = ?",
                (self.session_id,)
            ).fetchone()["c"]
            
            total_msg = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
            facts_count = conn.execute("SELECT COUNT(*) as c FROM user_facts").fetchone()["c"]
            episodes_count = conn.execute("SELECT COUNT(*) as c FROM episodic_memory").fetchone()["c"]
        
        return {
            "current_session_messages": msg_count,
            "total_messages_all_sessions": total_msg,
            "stored_facts": facts_count,
            "stored_episodes": episodes_count,
            "session_id": self.session_id,
        }
