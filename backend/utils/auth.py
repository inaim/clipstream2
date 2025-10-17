from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.config import settings
import logging

logger = logging.getLogger(__name__)

# Use auto_error=False so we can return a clearer 401 when credentials are missing
security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password with bcrypt (max 72 bytes)"""
    # Ensure password is string
    if not isinstance(password, str):
        password = str(password)
    # Truncate to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        # Ensure password is string
        if not isinstance(plain_password, str):
            plain_password = str(plain_password)
        # Truncate to 72 bytes for bcrypt
        password_bytes = plain_password.encode('utf-8')[:72]
        # Ensure hashed password is bytes
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
        # Verify
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user ID from JWT token"""
    try:
        # If credentials are not provided, HTTPBearer returned None (auto_error=False)
        if credentials is None:
            logger.info("Auth: missing credentials (no Authorization header)")
            raise HTTPException(status_code=401, detail="Missing authorization credentials")
        # Log masked token length for debugging (do not log token contents)
        try:
            token_snippet = f"len={len(credentials.credentials)}"
        except Exception:
            token_snippet = "len=unknown"
        logger.debug(f"Auth: Authorization header present ({token_snippet})")

        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError as e:
        print(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
