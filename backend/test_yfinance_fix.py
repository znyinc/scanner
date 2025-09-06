#!/usr/bin/env python3
"""
Test script to verify yfinance rate limiting fixes.
"""
import asyncio
import time
from app.services.data_service import DataService

async def test_data_fetch():
    """Test data fetching with rate limiting."""
    print("Testing yfinance data fetching with rate limiting...")
    
    data_service = DataService(max_retries=2)
    
    # Test with a single symbol first
    symbols = ["AAPL"]
    
    try:
        print(f"Fetching data for {symbols}...")
        start_time = time.time()
        
        result = await data_service.fetch_current_data(symbols, period="1d", interval="1h")
        
        end_time = time.time()
        print(f"Fetch completed in {end_time - start_time:.2f}s")
        
        for symbol, data in result.items():
            print(f"{symbol}: {len(data)} data points")
            if data:
                latest = data[-1]
                print(f"  Latest: {latest.timestamp} - Close: ${latest.close:.2f}")
            else:
                print(f"  No data available for {symbol}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_data_fetch())