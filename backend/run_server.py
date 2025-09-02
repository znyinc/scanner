#!/usr/bin/env python3
"""
Script to run the FastAPI development server.
"""
import uvicorn
from app.main import app
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print("Starting Stock Scanner API server...")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print("API Documentation will be available at:")
    print(f"  - Swagger UI: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"  - ReDoc: http://{settings.api_host}:{settings.api_port}/redoc")
    print(f"  - OpenAPI JSON: http://{settings.api_host}:{settings.api_port}/openapi.json")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )