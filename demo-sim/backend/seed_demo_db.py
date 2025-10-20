#!/usr/bin/env python3
"""
Create a small demo sqlite database with users and videos for migration testing.
"""
import sqlite3
import os
from datetime import datetime

DB = os.environ.get('DEMO_DB', './demo.db')

def ensure_schema(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        title TEXT,
        filename TEXT,
        content_hash TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    conn.commit()

def seed():
    existed = os.path.exists(DB)
    conn = sqlite3.connect(DB)
    ensure_schema(conn)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    # Insert two users (explicit ids via INSERT OR REPLACE with rowid if needed)
    users = [
        (1001, 'alice@example.com', 'hash_alice', 'Alice', now),
        (1002, 'bob@example.com', 'hash_bob', 'Bob', now),
    ]
    for u in users:
        try:
            cur.execute("INSERT OR IGNORE INTO users (id, email, password_hash, display_name, created_at) VALUES (?, ?, ?, ?, ?)", u)
        except Exception as e:
            print('user insert error', e)

    videos = [
        (2001, 1001, 'Demo Video 1', '2001_demo1.mp4', 'hash1', 'hot', now),
        (2002, 1002, 'Demo Video 2', '2002_demo2.mp4', 'hash2', 'hot', now),
    ]
    for v in videos:
        try:
            cur.execute("INSERT OR IGNORE INTO videos (id, owner_id, title, filename, content_hash, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", v)
        except Exception as e:
            print('video insert error', e)

    conn.commit()
    conn.close()
    print(f"Seeded DB at {DB} (existed before: {existed})")

if __name__ == '__main__':
    seed()
