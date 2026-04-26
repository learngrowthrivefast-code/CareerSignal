# core/database.py
import sqlite3
import uuid
from datetime import datetime
from config.settings import SQLITE_PATH
import os

def get_connection():
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    return sqlite3.connect(SQLITE_PATH, check_same_thread=False)

def init_db():
    """Create tables on first run."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    TEXT PRIMARY KEY,
            email      TEXT UNIQUE NOT NULL,
            name       TEXT NOT NULL,
            password   TEXT NOT NULL,
            tier       TEXT DEFAULT 'free',
            cohort     TEXT,
            created_at TEXT,
            last_login TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_counts (
            user_id    TEXT,
            month      TEXT,
            count      INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, month)
        )
    """)
    conn.commit()
    conn.close()

def create_user(email: str, name: str, hashed_password: str) -> str:
    """Insert new user. Returns user_id."""
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
            (user_id, email.lower(), name, hashed_password, 'free', None, now, now)
        )
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError("Email already registered.")
    finally:
        conn.close()

def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower(),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    cols = ["user_id","email","name","password","tier","cohort","created_at","last_login"]
    return dict(zip(cols, row))

def update_last_login(user_id: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET last_login = ? WHERE user_id = ?",
        (datetime.utcnow().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def update_user_cohort(user_id: str, cohort: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET cohort = ? WHERE user_id = ?",
        (cohort, user_id)
    )
    conn.commit()
    conn.close()

def increment_session_count(user_id: str) -> int:
    """Track monthly message count for free tier limits."""
    month = datetime.utcnow().strftime("%Y-%m")
    conn = get_connection()
    conn.execute("""
        INSERT INTO session_counts (user_id, month, count) VALUES (?,?,1)
        ON CONFLICT(user_id, month) DO UPDATE SET count = count + 1
    """, (user_id, month))
    conn.commit()
    count = conn.execute(
        "SELECT count FROM session_counts WHERE user_id=? AND month=?",
        (user_id, month)
    ).fetchone()[0]
    conn.close()
    return count
