from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import List
import os


# Determine which .env file to load
def get_env_file():
    """Load .env file from backend directory"""
    # Get the backend directory (where this config.py file is)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(backend_dir, ".env")

    env = os.getenv("ENVIRONMENT", "development").lower()
    print(f"[CONFIG] Loading environment file: {env_file} (ENVIRONMENT={env})")
    print(f"[CONFIG] .env file exists: {os.path.exists(env_file)}")
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
            cors_line = [l for l in lines if 'CORS_ORIGINS' in l]
            if cors_line:
                print(f"[CONFIG] CORS_ORIGINS line in .env: {cors_line[0].strip()}")
    return env_file


class Settings(BaseSettings):
    # Environment detection
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")  # development, staging, production
    
    # SurrealDB - Auto-detect based on environment
    SURREALDB_URL: str = Field(
        default="ws://localhost:8000/rpc",
        env="SURREALDB_URL"
    )
    SURREALDB_USER: str = Field("root", env="SURREALDB_USER")
    SURREALDB_PASS: str = Field("root", env="SURREALDB_PASS")
    SURREALDB_NS: str = Field("clipstream", env="SURREALDB_NS")
    SURREALDB_DB: str = Field("production", env="SURREALDB_DB")

    # Redis / Celery (optional for Cloud Run)
    REDIS_URL: str = Field("redis://:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")

    # IPFS (optional for Cloud Run)
    IPFS_URL: str = Field("/ip4/127.0.0.1/tcp/5001/http", env="IPFS_URL")
    ENABLE_IPFS: bool = Field(False, env="ENABLE_IPFS")  # Disabled by default for Cloud Run

    # Auth / JWT
    SECRET_KEY: str = Field("change-me-in-production", env="SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Frontend / upload - CORS origins (read from env as comma-separated string)
    CORS_ORIGINS_STR: str = Field(
        default="http://localhost:5173,http://localhost:8081",
        env="CORS_ORIGINS"
    )
    ALLOWED_ORIGINS: List[str] = Field(default_factory=list)
    MAX_UPLOAD_SIZE: int = Field(524288000, env="MAX_UPLOAD_SIZE")  # 500MB
    UPLOAD_DIR: str = Field("uploads", env="UPLOAD_DIR")

    # Feature flags
    ENABLE_AI_PROCESSING: bool = Field(False, env="ENABLE_AI_PROCESSING")
    ENABLE_TOKEN_REWARDS: bool = Field(True, env="ENABLE_TOKEN_REWARDS")
    EARLY_ADOPTER_MULTIPLIER: int = Field(5, env="EARLY_ADOPTER_MULTIPLIER")

    # Base URLs - Auto-detect based on environment
    BACKEND_BASE_URL: str = Field("http://localhost:8081", env="BACKEND_BASE_URL")
    FRONTEND_BASE_URL: str = Field("http://localhost:5173", env="FRONTEND_BASE_URL")

    # Development helpers
    DEV_SMS: bool = Field(False, env="DEV_SMS")

    # OAuth
    GOOGLE_CLIENT_ID: str = Field("", env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field("", env="GOOGLE_CLIENT_SECRET")
    FACEBOOK_CLIENT_ID: str = Field("", env="FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET: str = Field("", env="FACEBOOK_CLIENT_SECRET")
    
    # Cloud Run specific
    PORT: int = Field(8080, env="PORT")  # Cloud Run sets this automatically
    
    # Google Cloud Storage (for Cloud Run file uploads)
    GCS_BUCKET_NAME: str = Field("", env="GCS_BUCKET_NAME")
    ENABLE_GCS: bool = Field(False, env="ENABLE_GCS")
    
    # Parse CORS_ORIGINS_STR into ALLOWED_ORIGINS after model creation
    @model_validator(mode="after")
    def _parse_cors_origins(self):
        """Parse CORS_ORIGINS_STR from environment variable"""
        cors_str = self.CORS_ORIGINS_STR
        if cors_str:
            try:
                # Try JSON list first
                if cors_str.startswith("["):
                    import json
                    self.ALLOWED_ORIGINS = json.loads(cors_str)
                    print(f"[CONFIG] Parsed ALLOWED_ORIGINS from JSON: {self.ALLOWED_ORIGINS}")
                else:
                    # Comma-separated
                    self.ALLOWED_ORIGINS = [s.strip() for s in cors_str.split(",") if s.strip()]
                    print(f"[CONFIG] Parsed ALLOWED_ORIGINS from comma-separated: {self.ALLOWED_ORIGINS}")
            except Exception as e:
                print(f"[CONFIG] Error parsing CORS_ORIGINS: {e}, using defaults")
        else:
            print(f"[CONFIG] No CORS_ORIGINS_STR, using defaults: {self.ALLOWED_ORIGINS}")
        return self

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_cloud_run(self) -> bool:
        """Detect if running on Google Cloud Run"""
        return os.getenv("K_SERVICE") is not None

    # Use model_config for Pydantic v2
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()

# Debug: Print loaded settings
print(f"[CONFIG] ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"[CONFIG] BACKEND_BASE_URL: {settings.BACKEND_BASE_URL}")
print(f"[CONFIG] FRONTEND_BASE_URL: {settings.FRONTEND_BASE_URL}")
print(f"[CONFIG] SURREALDB_URL: {settings.SURREALDB_URL}")
print(f"[CONFIG] SURREALDB_DB: {settings.SURREALDB_DB}")

# Auto-configure based on environment
if settings.is_cloud_run():
    # Running on Cloud Run - adjust settings
    if not settings.SURREALDB_URL.startswith("wss://"):
        # Force WSS for production SurrealDB Cloud
        settings.SURREALDB_URL = os.getenv(
            "SURREALDB_URL",
            "wss://ancient-valley-06cu6ilhgptbp4ttr1a04b77oc.aws-euw1.surreal.cloud"
        )