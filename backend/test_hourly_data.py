#!/usr/bin/env python3
"""
Test hourly data fetching to see if it helps with rate limiting.
"""
import asyncio
import time
from app.services.data_service import DataService

async def test_hourly_data():
    """Test hourly data fetching."""
    print("Testing hourly data fetching...")
    
    data_service = DataService(max_retries=2)
    
    # Test with a single symbol using hourly data
    symbols = ["AAPL"]
    
    try:
        print(f"Fetching hourly data for {symbols}...")
        start_time = time.time()
        
        # Use hourly interval with longer period
        result = await data_service.fetch_current_data(symbols, period="5d", interval="1h")
        
        end_time = time.time()
        print(f"Fetch completed in {end_time - start_time:.2f}s")
        
        for symbol, data in result.items():
            print(f"{symbol}: {len(data)} hourly data points")
            if data:
                latest = data[-1]
                print(f"  Latest: {latest.timestamp} - Close: ${latest.close:.2f}")
                print(f"  First: {data[0].timestamp} - Close: ${data[0].close:.2f}")
            else:
                print(f"  No data available for {symbol}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hourly_data())