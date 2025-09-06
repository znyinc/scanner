"""
Configuration management for the Stock Scanner application.
"""
import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    cors_origins: str = "http://localhost:3000"
    
    # External API settings
    yfinance_timeout: int = 30
    yfinance_retry_count: int = 3
    
    # AlphaVantage API settings
    alphavantage_api_key: str = "demo"  # Default demo key, should be overridden in .env
    alphavantage_timeout: int = 30
    alphavantage_retry_count: int = 3
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Environment
    environment: str = "development"
    
    @field_validator('cors_origins')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


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


def get_database_url() -> str:
    """Get the database URL from settings."""
    return settings.database_url