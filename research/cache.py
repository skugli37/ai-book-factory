import sqlite3
import json
import time
from typing import Optional, Any
from pathlib import Path

class ResearchCache:
    """SQLite-based persistent cache for research results."""
    
    def __init__(self, db_path: str = "research_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at REAL
                )
            """)
            conn.commit()

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves a value from the cache if not expired."""
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM cache WHERE key = ? AND expires_at > ?", 
                (key, now)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    async def set(self, key: str, value: Any, ttl: int = 86400):
        """Stores a value in the cache with a TTL (seconds)."""
        expires_at = time.time() + ttl
        serialized = json.dumps(value)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, serialized, expires_at)
            )
            conn.commit()
            
    def clear_expired(self):
        """Manually clear expired entries."""
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE expires_at < ?", (now,))
            conn.commit()
