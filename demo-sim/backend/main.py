from fastapi import FastAPI, Response, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import time
import asyncio
import sqlite3
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional
import requests
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header
import surreal

# Simple config
SECRET_KEY = os.environ.get("DEMO_SECRET_KEY", "devsecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

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


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


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
    conn = get_db()
    cur = conn.cursor()
    password_hash = get_password_hash(password)
    try:
        cur.execute("INSERT INTO users (email, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
                    (email, password_hash, display_name or email.split('@')[0], datetime.utcnow().isoformat()))
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()
    token = create_access_token({"sub": str(user_id)})
    # Mirror to SurrealDB if configured
    try:
        SURREAL_URL = os.environ.get('SURREALDB_URL')
        if SURREAL_URL:
            # simple insert via SQL HTTP API
            sql = f"INSERT person CONTENT {{'id': {user_id}, 'email': '{email}', 'display_name': '{display_name or ''}'}}"
            requests.post(f"{SURREAL_URL}/sql", data=sql)
    except Exception:
        pass
    return {"access_token": token, "user_id": user_id}


# Compatibility endpoint for frontend: /api/v1/auth/register
@app.post("/api/v1/auth/register")
async def register_v1(email: str, password: str, display_name: Optional[str] = None):
    return await signup(email, password, display_name)


@app.post("/api/login")
async def login(email: str, password: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_id = row[0]
    pwd_hash = row[1]
    if not verify_password(password, pwd_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user_id)})
    return {"access_token": token, "user_id": user_id}


# Compatibility endpoint for frontend: /api/v1/auth/login
@app.post("/api/v1/auth/login")
async def login_v1(email: str, password: str):
    return await login(email, password)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), title: Optional[str] = "Untitled", owner_id: Optional[int] = None, current_user: int = Depends(get_current_user)):
    # Very small demo upload that saves file locally and registers metadata in sqlite
    conn = get_db()
    cur = conn.cursor()
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
    # Mirror video metadata to SurrealDB
    try:
        SURREAL_URL = os.environ.get('SURREALDB_URL')
        if SURREAL_URL:
            sql = f"INSERT video CONTENT {{'id': {video_id}, 'owner_id': {owner}, 'title': '{title}', 'filename': '{filename}', 'content_hash': '{content_hash}'}}"
            requests.post(f"{SURREAL_URL}/sql", data=sql)
    except Exception:
        pass
    return {"video_id": video_id, "content_hash": content_hash, "filename": filename}


@app.get("/api/playback/{video_id}")
async def playback_url(video_id: int):
    # Return a URL that the frontend can use to play the uploaded file via CDN
    # Prefer SurrealDB when available
    filename = None
    try:
        if surreal.is_available():
            vid = surreal.get_video(video_id)
            if vid and 'filename' in vid:
                filename = vid.get('filename')
    except Exception:
        # fall back to sqlite
        filename = None

    if not filename:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT filename FROM videos WHERE id = ?", (video_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        filename = row[0]

    # CDN is served on port 8003 in this demo; origin uploads are mounted at /uploads
    url = f"http://localhost:8003/uploads/{filename}"
    return {"playback_url": url}


@app.post("/api/views")
async def record_view(video_id: int, user_id: Optional[int] = None, duration: float = 0.0, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    counted_at = datetime.utcnow().isoformat()
    # Use authenticated user if user_id not provided
    uid = user_id or current_user
    cur.execute("INSERT INTO views (video_id, user_id, duration, counted_at) VALUES (?, ?, ?, ?)",
                (video_id, uid, duration, counted_at))
    # Add a ledger entry (very simple): 0.001 token per view
    amount = 0.001
    cur.execute("INSERT INTO ledger (user_id, amount, reason, reference_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, 'view_reward', video_id, counted_at))
    conn.commit()
    conn.close()
    return {"status": "ok", "credited": amount}


@app.get("/api/videos/{video_id}")
async def get_video(video_id: int):
    # Prefer SurrealDB when available
    try:
        if surreal.is_available():
            vid = surreal.get_video(video_id)
            if vid:
                return vid
    except Exception:
        pass

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, owner_id, title, filename, content_hash, status, created_at FROM videos WHERE id = ?", (video_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)


@app.get("/api/videos")
async def list_videos(limit: int = 50, offset: int = 0):
    # Prefer SurrealDB when available
    try:
        if surreal.is_available():
            raw = surreal.select_videos(limit=limit, offset=offset)
            return raw
    except Exception:
        pass

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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO likes (user_id, video_id) VALUES (?, ?)", (user_id, video_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.delete("/api/likes")
async def delete_like(user_id: int, video_id: int, current_user: int = Depends(get_current_user)):
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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.delete("/api/follows")
async def delete_follow(follower_id: int, following_id: int, current_user: int = Depends(get_current_user)):
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
    conn = get_db()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cur.execute("INSERT INTO comments (video_id, user_id, content, parent_id, created_at) VALUES (?, ?, ?, ?, ?)", (video_id, user_id, content, parent_id, created_at))
    conn.commit()
    conn.close()
    return { 'status': 'ok' }


@app.post("/api/gifts")
async def send_gift(from_user: int, to_user: int, amount: float, current_user: int = Depends(get_current_user)):
    # Simple ledger adjustment
    conn = get_db()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
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
    # update filename and status
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
