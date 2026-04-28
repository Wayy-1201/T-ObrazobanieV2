import sqlite3
from config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                tcoins  INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS talked_chars (
                user_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                PRIMARY KEY (user_id, char_id)
            );
            CREATE TABLE IF NOT EXISTS dialogues (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                char_id    TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                char_id    TEXT NOT NULL,
                content    TEXT NOT NULL
            );
        """)




def ensure_user(user_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, tcoins) VALUES (?, 0)",
            (user_id,)
        )


def get_tcoins(user_id: int) -> int:
    ensure_user(user_id)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT tcoins FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
    return row[0] if row else 0


def add_tcoins(user_id: int, amount: int):
    ensure_user(user_id)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET tcoins = tcoins + ? WHERE user_id=?",
            (amount, user_id)
        )


def spend_tcoins(user_id: int, amount: int) -> bool:
    ensure_user(user_id)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT tcoins FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
        if not row or row[0] < amount:
            return False
        conn.execute(
            "UPDATE users SET tcoins = tcoins - ? WHERE user_id=?",
            (amount, user_id)
        )
    return True




def mark_talked(user_id: int, char_id: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO talked_chars (user_id, char_id) VALUES (?,?)",
            (user_id, char_id)
        )


def get_talked_chars(user_id: int) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT char_id FROM talked_chars WHERE user_id=?",
            (user_id,)
        ).fetchall()
    return [r[0] for r in rows]


def add_message(user_id: int, char_id: str, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO dialogues (user_id, char_id, role, content) VALUES (?,?,?,?)",
            (user_id, char_id, role, content)
        )


def get_history(user_id: int, char_id: str, limit: int = 20) -> list[tuple]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM dialogues WHERE user_id=? AND char_id=? ORDER BY id DESC LIMIT ?",
            (user_id, char_id, limit)
        ).fetchall()
    return list(reversed(rows))


def add_note(user_id: int, char_id: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notes (user_id, char_id, content) VALUES (?,?,?)",
            (user_id, char_id, content)
        )


def get_notes(user_id: int) -> list[tuple]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT char_id, content FROM notes WHERE user_id=? ORDER BY id",
            (user_id,)
        ).fetchall()


def reset_user(user_id: int):
    """Сбрасывает прогресс игры, но НЕ трогает T-coins."""
    with get_conn() as conn:
        conn.execute("DELETE FROM talked_chars WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM dialogues WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM notes WHERE user_id=?", (user_id,))


def has_active_game(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM dialogues WHERE user_id=? LIMIT 1",
            (user_id,)
        ).fetchone()
        if row:
            return True
        row = conn.execute(
            "SELECT 1 FROM talked_chars WHERE user_id=? LIMIT 1",
            (user_id,)
        ).fetchone()
        return row is not None
