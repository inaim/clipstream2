from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    SURREALDB_URL: str = "ws://localhost:8000/rpc"
    SURREALDB_USER: str = "root"
    SURREALDB_PASS: str = "root"
    SURREALDB_NS: str = "clipstream"
    SURREALDB_DB: str = "production"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    IPFS_URL: str = "/ip4/127.0.0.1/tcp/5001/http"
    ENABLE_IPFS: bool = True
    
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    MAX_UPLOAD_SIZE: int = 524288000
    UPLOAD_DIR: str = "uploads"
    
    ENABLE_AI_PROCESSING: bool = False
    ENABLE_TOKEN_REWARDS: bool = True
    EARLY_ADOPTER_MULTIPLIER: int = 5

    # Local/Deployment base URLs used for building redirect URIs
    BACKEND_BASE_URL: str = os.environ.get('BACKEND_BASE_URL', 'http://localhost:8001')
    FRONTEND_BASE_URL: str = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:5173')

    GOOGLE_CLIENT_ID: str = os.environ.get('GOOGLE_CLIENT_ID', '235194927143-j2i2l1v0uf80rddpsd7qucejn3roo31a.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET: str = os.environ.get('GOOGLE_CLIENT_SECRET', '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')
    FACEBOOK_CLIENT_ID: str = os.environ.get('FACEBOOK_CLIENT_ID', 'your-facebook-client-id')
    FACEBOOK_CLIENT_SECRET: str = os.environ.get('FACEBOOK_CLIENT_SECRET', 'your-facebook-client-secret')
    
    class Config:
        env_file = ".env"

settings = Settings()
