"""
Configuration management for the Stock Scanner application.
"""
import os
from typing import List
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with environment-specific configuration."""
    
    # Database settings
    database_url: str = "postgresql://stock_scanner:password123@localhost:5432/stock_scanner"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # External API settings
    yfinance_timeout: int = 30
    yfinance_retry_count: int = 3
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Environment
    environment: str = "development"
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.environment.lower() == "development"


def is_staging() -> bool:
    """Check if running in staging environment."""
    return settings.environment.lower() == "staging"