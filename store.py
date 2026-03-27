import sqlite3
import time

DB_PATH = "pimail.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            message_id TEXT PRIMARY KEY,
            sender TEXT,
            subject TEXT,
            date TEXT,
            summary TEXT,
            verification_code TEXT,
            fetched_at REAL
        )
    """)
    conn.commit()
    conn.close()


def has_email(message_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM emails WHERE message_id = ?", (message_id,)
    ).fetchone()
    conn.close()
    return row is not None


def store_email(message_id, sender, subject, date, summary, verification_code):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO emails
           (message_id, sender, subject, date, summary, verification_code, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (message_id, sender, subject, date, summary, verification_code, time.time()),
    )
    conn.commit()
    conn.close()


def get_recent_emails(n=8):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM emails ORDER BY fetched_at DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cleanup_old(max_age_hours=24):
    cutoff = time.time() - (max_age_hours * 3600)
    conn = get_connection()
    conn.execute("DELETE FROM emails WHERE fetched_at < ?", (cutoff,))
    conn.commit()
    conn.close()
