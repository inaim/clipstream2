#!/usr/bin/env python3
"""
Migration script to copy SQLite users and videos into SurrealDB.
Run with SURREALDB_URL set and the demo sqlite DB present.
"""
import os
import sqlite3
import asyncio
from surrealdb import Surreal

DB = os.environ.get('DEMO_DB', './demo.db')
SURREAL_URL = os.environ.get('SURREALDB_URL')
SURREAL_USER = os.environ.get('SURREALDB_USER')
SURREAL_PASS = os.environ.get('SURREALDB_PASS')
SURREAL_NS = os.environ.get('SURREALDB_NS')
SURREAL_DB = os.environ.get('SURREALDB_DB')


async def run():
    if not SURREAL_URL:
        raise SystemExit('Please set SURREALDB_URL (ws://.../rpc)')

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    client = Surreal(SURREAL_URL)
    try:
        client.signin({'user': SURREAL_USER, 'pass': SURREAL_PASS})
    except Exception:
        # Some builds use username/password keys
        client.signin({'username': SURREAL_USER, 'password': SURREAL_PASS})

    if SURREAL_NS and SURREAL_DB:
        client.use(SURREAL_NS, SURREAL_DB)

    print('Migrating users...')
    cur.execute('SELECT id, email, display_name, created_at FROM users')
    for row in cur.fetchall():
        uid, email, display_name, created_at = row
        content = {
            'id': int(uid),
            'email': email,
            'display_name': display_name or '',
            'created_at': created_at,
        }
        try:
            res = client.create('person', content)
            print('created person', res)
        except Exception as e:
            print('person create error', e)

    print('Migrating videos...')
    cur.execute('SELECT id, owner_id, title, filename, content_hash, created_at FROM videos')
    for row in cur.fetchall():
        vid, owner_id, title, filename, content_hash, created_at = row
        content = {
            'id': int(vid),
            'owner_id': int(owner_id) if owner_id is not None else None,
            'title': title,
            'filename': filename,
            'content_hash': content_hash,
            'created_at': created_at,
        }
        try:
            res = client.create('video', content)
            print('created video', res)
        except Exception as e:
            print('video create error', e)

    conn.close()
    print('done')


if __name__ == '__main__':
    asyncio.run(run())

