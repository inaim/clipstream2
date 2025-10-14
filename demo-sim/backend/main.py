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
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header

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
    return {"video_id": video_id, "content_hash": content_hash, "filename": filename}


@app.get("/api/playback/{video_id}")
async def playback_url(video_id: int):
    # Return a URL that the frontend can use to play the uploaded file via CDN
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM videos WHERE id = ?", (video_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    filename = row[0]
    # CDN is served on port 8001; origin uploads are mounted at /uploads
    url = f"http://localhost:8001/uploads/{filename}"
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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, owner_id, title, filename, content_hash, status, created_at FROM videos WHERE id = ?", (video_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)


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
