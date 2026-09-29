import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant TEXT,
    amount REAL,
    purchased_at TEXT,
    raw_email_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'needs_details',  -- needs_details | complete | skipped
    category TEXT,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)


def insert_purchase(merchant, amount, purchased_at, raw_email_id):
    """Insert a new pending purchase. Ignored silently if raw_email_id
    already exists, so re-checking the inbox never creates duplicates."""
    with get_conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO purchases
               (merchant, amount, purchased_at, raw_email_id, status)
               VALUES (?, ?, ?, ?, 'needs_details')""",
            (merchant, amount, purchased_at, raw_email_id),
        )


def get_pending():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM purchases WHERE status = 'needs_details' ORDER BY purchased_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def complete_purchase(purchase_id, category, note):
    with get_conn() as conn:
        conn.execute(
            "UPDATE purchases SET status='complete', category=?, note=? WHERE id=?",
            (category, note, purchase_id),
        )


def skip_purchase(purchase_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE purchases SET status='skipped' WHERE id=?", (purchase_id,)
        )


def get_transactions(limit=200):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM purchases WHERE status='complete'
               ORDER BY purchased_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_totals_by_category():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT category, SUM(amount) as total, COUNT(*) as count
               FROM purchases WHERE status='complete'
               GROUP BY category ORDER BY total DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
