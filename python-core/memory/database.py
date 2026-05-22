import sqlite3
import threading
from pathlib import Path


class MemoryDatabase:
    def __init__(self, path=None):
        self.path = Path(path or Path.cwd() / "friday_memory.db")
        self.connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        self.lock = threading.RLock()
        self._create_tables()

    def _create_tables(self):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.commit()

    def save(self, category: str, content: str):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO memory (category, content) VALUES (?, ?)", (category, content))
            self.connection.commit()

    def get_recent(self, limit: int = 10):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT category, content, created_at FROM memory ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()

    def close(self):
        with self.lock:
            self.connection.close()
