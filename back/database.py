# ============================================================
# database.py — SQLite setup and connection
# ============================================================

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "uniadmit.db")


def get_connection():
    """Open a connection. Rows accessible by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create all tables on startup.
    Called once from main.py @startup event.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # ── users table ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── applications table ───────────────────────────────────
    # Stores the entire submitted application as a JSON blob.
    # Each column group maps to one block of the form.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            basic_info      TEXT NOT NULL,       -- Block 1 as JSON
            experience      TEXT NOT NULL,       -- Block 2 as JSON
            motivation      TEXT NOT NULL,       -- Block 3 as JSON
            psychometric    TEXT NOT NULL,       -- Block 4 as JSON (q1..q40)
            consents        TEXT NOT NULL,       -- Block 5 as JSON
            submitted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database tables ready.")
