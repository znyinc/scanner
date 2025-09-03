"""
Configuration management for the Stock Scanner application.
"""
import os
from typing import List
from pydantic import BaseModel, field_validator


class Settings(BaseModel):
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
    
    def __init__(self, **kwargs):
        # Load from environment
        env_data = {}
        for field_name, field_info in self.model_fields.items():
            env_key = field_name.upper()
            if env_key in os.environ:
                env_data[field_name] = os.environ[env_key]
        env_data.update(kwargs)
        super().__init__(**env_data)
    
    @field_validator('cors_origins', mode='before')
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