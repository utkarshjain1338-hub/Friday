import threading
from pathlib import Path

from memory.database import MemoryDatabase


def test_memory_database_thread_safe(tmp_path):
    db_path = tmp_path / "test_memory.db"
    db = MemoryDatabase(path=db_path)

    def save_note():
        db.save("note", "hello from thread")

    thread = threading.Thread(target=save_note)
    thread.start()
    thread.join()

    entries = db.get_recent(1)
    assert entries
    category, content, created_at = entries[0]
    assert category == "note"
    assert content == "hello from thread"
    assert created_at is not None

    db.close()
