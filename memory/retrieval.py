import sqlite3
from pathlib import Path
from typing import List, Tuple


class MemoryRetrieval:
    def __init__(self, db_path: Path = None):
        self.path = Path(db_path or Path.cwd() / "friday_memory.db")

    def search_notes(self, query: str, limit: int = 10) -> List[Tuple]:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, content, created_at FROM memory WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        results = cursor.fetchall()
        conn.close()
        return results
