import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("GATEWAY_DB_PATH", "/data/gateway.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                backend_host TEXT NOT NULL
            )
            """
        )


def get_user(username: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def upsert_user(username: str, password_hash: str, backend_host: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, backend_host)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                backend_host = excluded.backend_host
            """,
            (username, password_hash, backend_host),
        )


def delete_user(username: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        return cur.rowcount > 0


def list_users() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT username, backend_host FROM users").fetchall()
