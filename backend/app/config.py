import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "CloudOptima"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    _DEFAULT_DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloudoptima.db").replace("\\", "/")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")
    
    # Security / Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-cloudoptima-key-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Operation Modes
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    AUTO_REMEDIATE_LOW_RISK_DEFAULT: bool = False
    
    # Scheduler
    SCAN_INTERVAL_MINUTES: int = int(os.getenv("SCAN_INTERVAL_MINUTES", "180")) # every 3 hours
    
    # Risk Classification Thresholds
    RISK_LOW_MAX: float = 35.0
    RISK_MED_MAX: float = 70.0
    
    # Currency
    CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"
    USD_TO_INR_RATE: float = 85.0
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
