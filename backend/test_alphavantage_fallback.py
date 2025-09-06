#!/usr/bin/env python3
"""
Test script to verify AlphaVantage fallback functionality.
"""
import asyncio
import time
import os
from app.services.data_service import DataService
from app.config import get_settings

async def test_fallback_mechanism():
    """Test the yfinance -> AlphaVantage fallback mechanism."""
    print("Testing Data Service with AlphaVantage Fallback")
    print("=" * 50)
    
    # Check configuration
    settings = get_settings()
    print(f"AlphaVantage API Key: {'Set' if settings.alphavantage_api_key != 'demo' else 'Using demo key (limited)'}")
    
    # Initialize data service
    data_service = DataService(max_retries=2)
    
    # Test symbols
    symbols = ["AAPL", "MSFT"]
    
    try:
        print(f"\nTesting with symbols: {symbols}")
        print("This will try yfinance first, then fallback to AlphaVantage if needed...")
        
        start_time = time.time()
        
        # Test current data fetch with fallback
        result = await data_service.fetch_current_data(symbols, period="5d", interval="1h")
        
        end_time = time.time()
        print(f"\nFetch completed in {end_time - start_time:.2f}s")
        
        # Display results
        for symbol, data in result.items():
            print(f"\n{symbol}:")
            if data:
                print(f"  ✓ Data points: {len(data)}")
                latest = data[-1]
                print(f"  ✓ Latest: {latest.timestamp} - Close: ${latest.close:.2f}")
                print(f"  ✓ Volume: {latest.volume:,}")
            else:
                print(f"  ✗ No data available")
        
        # Test cache functionality
        print(f"\nCache stats: {data_service.get_cache_stats()}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

async def test_alphavantage_direct():
    """Test AlphaVantage API directly."""
    print("\n" + "=" * 50)
    print("Testing AlphaVantage Direct Access")
    print("=" * 50)
    
    try:
        from alpha_vantage.timeseries import TimeSeries
        settings = get_settings()
        
        if settings.alphavantage_api_key == "demo":
            print("⚠️  Using demo API key - limited functionality")
        
        ts = TimeSeries(key=settings.alphavantage_api_key, output_format='pandas')
        
        print("Fetching AAPL intraday data from AlphaVantage...")
        data, meta_data = ts.get_intraday(symbol='AAPL', interval='60min', outputsize='compact')
        
        if not data.empty:
            print(f"✓ AlphaVantage direct access successful")
            print(f"✓ Data points: {len(data)}")
            print(f"✓ Columns: {list(data.columns)}")
            print(f"✓ Date range: {data.index.min()} to {data.index.max()}")
        else:
            print("✗ AlphaVantage returned empty data")
            
    except ImportError:
        print("✗ alpha-vantage library not installed")
        print("Run: pip install alpha-vantage")
    except Exception as e:
        print(f"✗ AlphaVantage direct test failed: {e}")

def main():
    """Run all tests."""
    print("Stock Scanner - Data Service Fallback Test")
    print("This test verifies yfinance -> AlphaVantage fallback functionality")
    print()
    
    # Check if AlphaVantage is properly configured
    settings = get_settings()
    if settings.alphavantage_api_key == "demo":
        print("⚠️  WARNING: Using demo AlphaVantage API key")
        print("   For full functionality, get a free API key from:")
        print("   https://www.alphavantage.co/support/#api-key")
        print("   Then set ALPHAVANTAGE_API_KEY in your .env file")
        print()
    
    # Run tests
    asyncio.run(test_fallback_mechanism())
    asyncio.run(test_alphavantage_direct())
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNext steps:")
    print("1. If yfinance is working, you'll see data from yfinance")
    print("2. If yfinance fails, you should see AlphaVantage fallback")
    print("3. Get a free AlphaVantage API key for better reliability")

if __name__ == "__main__":
    main()