#!/usr/bin/env python3
"""
Demo script showing the FastAPI endpoints in action.
"""
import asyncio
import json
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.main import app

def demo_api_endpoints():
    """Demonstrate all API endpoints."""
    client = TestClient(app)
    
    print("=== Stock Scanner API Demo ===\n")
    
    # 1. Test root endpoint
    print("1. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # 2. Test settings endpoints
    print("2. Testing settings endpoints...")
    
    # Get default settings
    response = client.get("/settings/")
    print(f"   GET /settings/ - Status: {response.status_code}")
    print(f"   Default settings: {json.dumps(response.json(), indent=2)}\n")
    
    # Update settings
    new_settings = {
        "atr_multiplier": 2.5,
        "ema5_rising_threshold": 0.025,
        "higher_timeframe": "30m"
    }
    response = client.put("/settings/", json=new_settings)
    print(f"   PUT /settings/ - Status: {response.status_code}")
    print(f"   Updated settings: {json.dumps(response.json(), indent=2)}\n")
    
    # Reset settings
    response = client.post("/settings/reset")
    print(f"   POST /settings/reset - Status: {response.status_code}")
    print(f"   Reset settings: {json.dumps(response.json(), indent=2)}\n")
    
    # 3. Test validation
    print("3. Testing input validation...")
    
    # Invalid symbols
    response = client.post("/scan/", json={"symbols": []})
    print(f"   Empty symbols - Status: {response.status_code}")
    print(f"   Error: {response.json().get('detail', 'No error details')}\n")
    
    # Invalid date range
    response = client.post("/backtest/", json={
        "symbols": ["AAPL"],
        "start_date": "2023-12-31",
        "end_date": "2023-01-01"  # End before start
    })
    print(f"   Invalid date range - Status: {response.status_code}")
    print(f"   Error: {response.json().get('detail', 'No error details')}\n")
    
    # Invalid settings
    response = client.put("/settings/", json={"atr_multiplier": -1.0})
    print(f"   Invalid settings - Status: {response.status_code}")
    print(f"   Error: {response.json().get('detail', 'No error details')}\n")
    
    print("4. API Documentation...")
    print("   OpenAPI docs available at: http://localhost:8000/docs")
    print("   ReDoc docs available at: http://localhost:8000/redoc\n")
    
    print("=== Demo Complete ===")
    print("Note: Scan and backtest endpoints require database connection and market data.")
    print("Run with a proper database setup to test those endpoints fully.")

if __name__ == "__main__":
    demo_api_endpoints()