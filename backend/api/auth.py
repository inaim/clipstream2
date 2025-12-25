from fastapi import APIRouter, HTTPException, Request, Response
from utils.config import settings
from pydantic import BaseModel, EmailStr
from db.surrealdb_client import db_client
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    existing = await db_client.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(req.password)
    user = await db_client.create_user(req.email, password_hash, req.display_name)
    # SurrealDB create returns a list of records
    if isinstance(user, list):
        user = user[0] if user else None
    if not user or 'id' not in user:
        raise HTTPException(status_code=500, detail="User creation failed")
    user_id = str(user['id'])
    await db_client.earn_tokens(user_id, 50, "early_adopter_bonus")

    access_token = create_access_token({"sub": user_id})
    return {"access_token": access_token, "user_id": user_id}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = await db_client.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Convert RecordID to string for JSON serialization
    user_id = str(user['id'])
    access_token = create_access_token({"sub": user_id})
    return {"access_token": access_token, "user_id": user_id}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Clear server-side session (used for OAuth flows) and explicitly expire the
    session cookie so browsers and intermediaries drop it immediately.
    """
    try:
        # Clear the Starlette session dict
        request.session.clear()

        # Explicitly delete the session cookie. Use the request host as the domain
        # so the Set-Cookie matches the cookie previously issued.
        domain = None
        try:
            # request.url.hostname returns the host (no port)
            domain = request.url.hostname
        except Exception:
            domain = None

        # Delete cookie (sets expires in the past / max_age=0)
        cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'clipstream_session')
        # Attempt deletion for the exact host
        response.delete_cookie(key=cookie_name, path='/', domain=domain)
        # Also attempt deletion for the parent domain (e.g. .finailabz.com) in case
        # the cookie was set for a parent domain by a proxy or earlier deployment.
        try:
            if domain and domain.count('.') >= 2:
                parts = domain.split('.')
                parent = '.' + '.'.join(parts[-2:])
                response.delete_cookie(key=cookie_name, path='/', domain=parent)
        except Exception:
            pass

        return {"detail": "signed out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {e}")
