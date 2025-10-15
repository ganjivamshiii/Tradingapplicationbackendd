from pydantic_settings import BaseSettings
from typing import List
import os
import secrets

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Algo Trading System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    
    # CORS - Accept string and convert to list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # Database
    DATABASE_URL: str = "sqlite:///./trading.db"  # SQLite for simplicity

    
    # Trading Settings
    INITIAL_CAPITAL: float = 100000.0  # Starting capital for paper trading
    COMMISSION: float = 0.001  # 0.1% commission per trade
    
    # Data Settings
    DEFAULT_SYMBOL: str = "AAPL"
    DEFAULT_INTERVAL: str = "1d"  # 1d, 1h, 5m, etc.
    
    # WebSocket
    WS_HEARTBEAT: int = 30  # seconds
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()