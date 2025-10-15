from fastapi import FastAPI, Response, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import time
import asyncio
import sqlite3
import os
import json
import logging
import hashlib
import os
import binascii

PBKDF2_ITERATIONS = int(os.environ.get('DEMO_PBKDF2_ITERS', '100000'))

app = FastAPI()

def get_password_hash(password: str) -> str:
    """Return a PBKDF2 hashed password in the form iterations$salt$hashhex"""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ITERATIONS}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3:
            return False
        it = int(parts[0])
        salt = binascii.unhexlify(parts[1])
        expected = parts[2]
        dk = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, it)
        return binascii.hexlify(dk).decode() == expected
    except Exception:
        return False
from jose import JWTError, jwt
from typing import Optional
import requests
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header
from surrealdb import Surreal

# Instantiate SurrealDB client
surreal = Surreal(os.environ.get("SURREALDB_URL", "ws://localhost:8000/rpc"))
surreal.signin({
    "username": os.environ.get("SURREALDB_USER", "root"),
    "password": os.environ.get("SURREALDB_PASS", "root")
})
surreal.use(
    os.environ.get("SURREALDB_NS", "clipstream"),
    os.environ.get("SURREALDB_DB", "production")
)

# Surreal toggles
SURREAL_AUTHORITATIVE = os.environ.get('SURREAL_AUTHORITATIVE', 'false').lower() in ('1', 'true', 'yes')
# Optional secret header for transcoder callbacks
TRANSCODER_SECRET = os.environ.get('TRANSCODER_SECRET')

# Simple config
SECRET_KEY = os.environ.get("DEMO_SECRET_KEY", "devsecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Logger
LOG = logging.getLogger("demo-backend")
LOG.setLevel(logging.INFO)

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("DEMO_DB", "./demo.db")
STORAGE_DIR = os.environ.get("DEMO_STORAGE", "./storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER,
        user_id INTEGER,
        duration REAL,
        counted_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        reason TEXT,
        reference_id INTEGER,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


init_db()




def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate JWT and return user_id (sub)
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return int(sub)
    except JWTError:
        raise credentials_exception


@app.get("/api/hello")
async def hello():
    return {"hello": "world"}


@app.get("/api/content")
async def content(response: Response):
    # Return dynamic content with Cache-Control header so CDN can cache it.
    response.headers["Cache-Control"] = "public, max-age=10"
    # Expose helpful debug header for TTL (seconds)
    response.headers["X-Cache-TTL"] = "10"
    return {
        "content": "This is dynamic origin content",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "unix": time.time()
    }


@app.get("/api/slow-content")
async def slow_content(response: Response):
    # Simulate a slow cold retrieval (e.g., IPFS fetch)
    # This helps demonstrate CDN MISS -> subsequent HIT behavior
    await asyncio.sleep(5)
    response.headers["Cache-Control"] = "public, max-age=30"
    response.headers["X-Cache-TTL"] = "30"
    return {
        "content": "This is simulated slow cold content (simulating IPFS)",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "unix": time.time()
    }


@app.post("/api/signup")
async def signup(email: str, password: str, display_name: Optional[str] = None):
    """Create a user in SurrealDB and return a JWT. If Surreal is unavailable and not authoritative, fall back to sqlite."""
    password_hash = get_password_hash(password)
    if surreal.is_available():
        try:
            uid = surreal.create_user_with_password(email, password_hash, display_name or '')
            if uid and uid != -1:
                token = create_access_token({"sub": str(uid)})
                return {"access_token": token, "user_id": uid}
        except Exception as e:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail="SurrealDB unavailable or write failed")

    # Non-authoritative fallback to sqlite for demo convenience
    if not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (email, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
                        (email, password_hash, display_name or email.split('@')[0], datetime.utcnow().isoformat()))
            conn.commit()
            user_id = cur.lastrowid
            conn.close()
            token = create_access_token({"sub": str(user_id)})
            return {"access_token": token, "user_id": user_id}
        except sqlite3.IntegrityError:
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")

    raise HTTPException(status_code=503, detail="User creation failed")


# Compatibility endpoint for frontend: /api/v1/auth/register
@app.post("/api/v1/auth/register")
async def register_v1(email: str, password: str, display_name: Optional[str] = None):
    return await signup(email, password, display_name)


@app.post("/api/login")
async def login(email: str, password: str):
    # Prefer SurrealDB for auth lookup
    if surreal.is_available():
        try:
            p = surreal.get_person_by_email(email)
            if p and 'password_hash' in p and verify_password(password, p['password_hash']):
                user_id = p.get('id')
                token = create_access_token({"sub": str(user_id)})
                return {"access_token": token, "user_id": user_id}
            raise HTTPException(status_code=401, detail="Invalid credentials")
        except HTTPException:
            raise
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail="SurrealDB unavailable")

    # Fallback to sqlite if allowed
    if not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        conn.close()
        if not row or not verify_password(password, row[1]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(row[0])})
    return {"access_token": token, "user_id": row[0]}

    raise HTTPException(status_code=401, detail="Invalid credentials")


# Compatibility endpoint for frontend: /api/v1/auth/login
@app.post("/api/v1/auth/login")
async def login_v1(email: str, password: str):
    return await login(email, password)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), title: Optional[str] = "Untitled", owner_id: Optional[int] = None, current_user: int = Depends(get_current_user)):
    # Upload: write file locally (storage) and create video record in SurrealDB first
    timestamp = datetime.utcnow().isoformat()
    filename = f"{int(time.time())}_{file.filename}"
    dest_dir = os.path.join(STORAGE_DIR, "uploads")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    with open(dest_path, "wb") as out:
        content = await file.read()
        out.write(content)
    # compute a crude content hash
    import hashlib
    h = hashlib.sha256()
    h.update(content)
    content_hash = h.hexdigest()
    # Use authenticated user if owner_id not provided
    owner = owner_id or current_user

    # Create video record in SurrealDB (authoritative). If Surreal not available and non-authoritative, fall back to sqlite.
    if surreal.is_available():
        try:
            vid = surreal.create_video(owner, title, filename, content_hash)
            if vid and vid != -1:
                video_id = vid
            else:
                raise Exception('surreal create_video returned invalid id')
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail="SurrealDB unavailable or write failed")
            video_id = None
    else:
        video_id = None

    if not video_id and not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO videos (owner_id, title, filename, content_hash, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (owner, title, filename, content_hash, 'hot', timestamp))
        conn.commit()
        video_id = cur.lastrowid
        conn.close()

    # create a todo marker file so the transcoder service can pick it up
    try:
        marker = os.path.join(dest_dir, f"{filename}.todo")
        with open(marker, "w") as m:
            m.write("")
    except Exception:
        pass

    return {"video_id": video_id, "content_hash": content_hash, "filename": filename}


@app.get("/api/playback/{video_id}")
async def playback_url(video_id: int):
    # Return a URL that the frontend can use to play the uploaded file via CDN
    # Prefer SurrealDB when available
    filename = None
    # Prefer SurrealDB when available
    filename = None
    if surreal.is_available():
        try:
            vid = surreal.get_video(video_id)
            if vid and 'filename' in vid:
                filename = vid.get('filename')
        except Exception:
            filename = None

    if not filename and not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT filename FROM videos WHERE id = ?", (video_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        filename = row[0]
    if not filename:
        raise HTTPException(status_code=404, detail="Not found")

    # CDN is served on port 8003 in this demo; origin uploads are mounted at /uploads
    url = f"http://localhost:8003/uploads/{filename}"
    return {"playback_url": url}


@app.post("/api/views")
async def record_view(video_id: int, user_id: Optional[int] = None, duration: float = 0.0, current_user: int = Depends(get_current_user)):
    counted_at = datetime.utcnow().isoformat()
    # Use authenticated user if user_id not provided
    uid = user_id or current_user
    amount = 0.001
    # Try to write view and ledger to Surreal first
    if surreal.is_available():
        try:
            view_payload = { 'video_id': int(video_id), 'user_id': int(uid), 'duration': float(duration), 'counted_at': counted_at }
            surreal.exec_sql(f"INSERT view CONTENT {json.dumps(view_payload)};")
            ledger_payload = { 'user_id': int(uid), 'amount': amount, 'reason': 'view_reward', 'reference_id': int(video_id), 'created_at': counted_at }
            surreal.exec_sql(f"INSERT ledger CONTENT {json.dumps(ledger_payload)};")
            return { 'status': 'ok', 'credited': amount }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            # fall back to sqlite if allowed

    if not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO views (video_id, user_id, duration, counted_at) VALUES (?, ?, ?, ?)",
                    (video_id, uid, duration, counted_at))
        cur.execute("INSERT INTO ledger (user_id, amount, reason, reference_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    (uid, amount, 'view_reward', video_id, counted_at))
        conn.commit()
        conn.close()
        return { 'status': 'ok', 'credited': amount }

    raise HTTPException(status_code=503, detail='SurrealDB unavailable')


@app.get("/api/videos/{video_id}")
async def get_video(video_id: int):
    # Prefer SurrealDB when available
    # Prefer SurrealDB when available
    if surreal.is_available():
        try:
            vid = surreal.get_video(video_id)
            if vid:
                return vid
        except Exception:
            pass

    if not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, owner_id, title, filename, content_hash, status, created_at FROM videos WHERE id = ?", (video_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return dict(row)

    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/videos")
async def list_videos(limit: int = 50, offset: int = 0):
    if surreal.is_available():
        try:
            raw = surreal.select_videos(limit=limit, offset=offset)
            return raw
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable')

    if not SURREAL_AUTHORITATIVE:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, owner_id, title, filename, content_hash, status, created_at FROM videos ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
        videos = []
        for r in rows:
            vid = dict(r)
            # fetch owner profile
            cur.execute("SELECT id as user_id, email, display_name FROM users WHERE id = ?", (vid['owner_id'],))
            u = cur.fetchone()
            profile = { 'user_id': u[0], 'email': u[1], 'display_name': u[2] } if u else None
            # construct video_url via CDN
            vid['video_url'] = f"http://localhost:8003/uploads/{vid['filename']}"
            vid['profiles'] = profile
            # placeholder counts
            cur.execute("SELECT COUNT(*) FROM views WHERE video_id = ?", (vid['id'],))
            vid['views_count'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM (SELECT 1 FROM likes WHERE video_id = ?)", (vid['id'],))
            try:
                vid['likes_count'] = cur.fetchone()[0]
            except Exception:
                vid['likes_count'] = 0
            videos.append(vid)
        conn.close()
        return videos

    raise HTTPException(status_code=503, detail='SurrealDB unavailable')


@app.get("/api/likes")
async def get_like(user_id: Optional[int] = None, video_id: Optional[int] = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT id FROM likes WHERE 1=1"
    params = []
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    if video_id is not None:
        query += " AND video_id = ?"
        params.append(video_id)
    cur.execute(query, tuple(params))
    row = cur.fetchone()
    conn.close()
    return { 'data': { 'id': row[0] } if row else None }


@app.post("/api/likes")
async def create_like(user_id: int, video_id: int, current_user: int = Depends(get_current_user)):
    # Try Surreal first
    if surreal.is_available():
        try:
            payload = { 'user_id': int(user_id), 'video_id': int(video_id) }
            surreal.exec_sql(f"INSERT likes CONTENT {json.dumps(payload)};")
            return { 'status': 'ok' }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            pass
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO likes (user_id, video_id) VALUES (?, ?)", (user_id, video_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.delete("/api/likes")
async def delete_like(user_id: int, video_id: int, current_user: int = Depends(get_current_user)):
    if surreal.is_available():
        try:
            surreal.exec_sql(f"DELETE FROM likes WHERE user_id = {int(user_id)} AND video_id = {int(video_id)};")
            return { 'status': 'ok' }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            pass
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM likes WHERE user_id = ? AND video_id = ?", (user_id, video_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.get("/api/follows")
async def get_follow(follower_id: Optional[int] = None, following_id: Optional[int] = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT id FROM follows WHERE 1=1"
    params = []
    if follower_id is not None:
        query += " AND follower_id = ?"
        params.append(follower_id)
    if following_id is not None:
        query += " AND following_id = ?"
        params.append(following_id)
    cur.execute(query, tuple(params))
    row = cur.fetchone()
    conn.close()
    return { 'data': { 'id': row[0] } if row else None }


@app.post("/api/follows")
async def create_follow(follower_id: int, following_id: int, current_user: int = Depends(get_current_user)):
    if surreal.is_available():
        try:
            payload = { 'follower_id': int(follower_id), 'following_id': int(following_id) }
            surreal.exec_sql(f"INSERT follows CONTENT {json.dumps(payload)};")
            return { 'status': 'ok' }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            pass
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.delete("/api/follows")
async def delete_follow(follower_id: int, following_id: int, current_user: int = Depends(get_current_user)):
    if surreal.is_available():
        try:
            surreal.exec_sql(f"DELETE FROM follows WHERE follower_id = {int(follower_id)} AND following_id = {int(following_id)};")
            return { 'status': 'ok' }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            pass
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.get("/api/comments")
async def list_comments(video_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, video_id, user_id, content, parent_id, created_at FROM comments WHERE video_id = ? ORDER BY created_at ASC", (video_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/comments")
async def create_comment(video_id: int, user_id: int, content: str, parent_id: Optional[int] = None, current_user: int = Depends(get_current_user)):
    created_at = datetime.utcnow().isoformat()
    if surreal.is_available():
        try:
            payload = { 'video_id': int(video_id), 'user_id': int(user_id), 'content': content, 'parent_id': parent_id, 'created_at': created_at }
            surreal.exec_sql(f"INSERT comments CONTENT {json.dumps(payload)};")
            return { 'status': 'ok' }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            pass
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO comments (video_id, user_id, content, parent_id, created_at) VALUES (?, ?, ?, ?, ?)", (video_id, user_id, content, parent_id, created_at))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.post("/api/gifts")
async def send_gift(from_user: int, to_user: int, amount: float, current_user: int = Depends(get_current_user)):
    # Simple ledger adjustment
    created_at = datetime.utcnow().isoformat()
    if surreal.is_available():
        try:
            entry_to = { 'user_id': int(to_user), 'amount': float(amount), 'reason': 'gift_received', 'reference_id': None, 'created_at': created_at }
            entry_from = { 'user_id': int(from_user), 'amount': -float(amount), 'reason': 'gift_sent', 'reference_id': None, 'created_at': created_at }
            surreal.exec_sql(f"INSERT ledger CONTENT {json.dumps(entry_to)};")
            surreal.exec_sql(f"INSERT ledger CONTENT {json.dumps(entry_from)};")
            return { 'status': 'ok' }
        except Exception:
            if SURREAL_AUTHORITATIVE:
                raise HTTPException(status_code=503, detail='SurrealDB unavailable or write failed')
            pass
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO ledger (user_id, amount, reason, reference_id, created_at) VALUES (?, ?, ?, ?, ?)", (to_user, amount, 'gift_received', None, created_at))
    cur.execute("INSERT INTO ledger (user_id, amount, reason, reference_id, created_at) VALUES (?, ?, ?, ?, ?)", (from_user, -amount, 'gift_sent', None, created_at))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }



@app.post("/api/transcode_complete")
async def transcode_complete(payload: dict):
    """Called by the transcoder service when a transcode finishes.
    Expects JSON: { original: '<orig-filename>', transcoded: '<new-filename>' }
    """
    orig = payload.get('original')
    transcoded = payload.get('transcoded')
    # Validate optional secret header inside payload (transcoder may post it)
    secret = payload.get('secret')
    if TRANSCODER_SECRET and secret != TRANSCODER_SECRET:
        raise HTTPException(status_code=401, detail='invalid transcode secret')
    if not orig or not transcoded:
        raise HTTPException(status_code=400, detail="invalid payload")
    conn = get_db()
    cur = conn.cursor()
    # find video by filename
    cur.execute("SELECT id FROM videos WHERE filename = ?", (orig,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="video not found")
    video_id = row[0]
    # When Surreal is authoritative, update it first
    try:
        if surreal.is_available():
            try:
                surreal.update_video_filename(video_id, transcoded, status='ready')
            except Exception:
                if SURREAL_AUTHORITATIVE:
                    conn.close()
                    raise HTTPException(status_code=503, detail='SurrealDB unavailable or update failed')
                # otherwise continue and update sqlite cache
                pass
    except Exception:
        if SURREAL_AUTHORITATIVE:
            conn.close()
            raise
        pass

    # update filename and status in sqlite (local cache)
    cur.execute("UPDATE videos SET filename = ?, status = ? WHERE id = ?", (transcoded, 'ready', video_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok', 'video_id': video_id }


# Compatibility endpoint for frontend to fetch profile: /api/v1/users/{user_id}
@app.get("/api/v1/users/{user_id}")
async def get_user_v1(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id as user_id, email, display_name FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {"user_id": row[0], "email": row[1], "display_name": row[2]}


@app.get("/api/ledger/{user_id}")
async def get_ledger(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, amount, reason, reference_id, created_at FROM ledger WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
