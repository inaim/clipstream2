from fastapi import APIRouter, HTTPException
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
    
    await db_client.earn_tokens(user['id'], 50, "early_adopter_bonus")
    
    access_token = create_access_token({"sub": user['id']})
    return {"access_token": access_token, "user_id": user['id']}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = await db_client.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user['id']})
    return {"access_token": access_token, "user_id": user['id']}
