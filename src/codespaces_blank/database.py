import sqlite3
from contextlib import closing
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[2] / "feedback.db"


def create_table():
    with closing(sqlite3.connect(DB_FILE)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                label TEXT NOT NULL,
                score INTEGER NOT NULL,
                theme TEXT NOT NULL
            )
            """
        )


def add_feedback_batch(feedback: list[dict[str, str | int]]) -> None:
    with closing(sqlite3.connect(DB_FILE)) as connection, connection:
        connection.executemany(
            "INSERT INTO feedback (text, label, score, theme) VALUES (?, ?, ?, ?)",
            [
                (
                    item["text"],
                    item["label"],
                    item["score"],
                    item["theme"],
                )
                for item in feedback
            ],
        )


def load_feedback() -> list[dict[str, str | int]]:
    with closing(sqlite3.connect(DB_FILE)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM feedback ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]
