"""
Demo script showing how to use the DataService for fetching market data.
This script demonstrates the main functionality of the data service.
"""
import asyncio
import sys
import os
from datetime import date, datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.data_service import DataService


async def demo_current_data():
    """Demonstrate fetching current market data."""
    print("=== Current Market Data Demo ===")
    
    data_service = DataService(cache_ttl_minutes=5)
    
    # Fetch current 1-minute data for popular stocks
    symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"Fetching current 1-minute data for: {', '.join(symbols)}")
    
    try:
        result = await data_service.fetch_current_data(symbols, period="1d", interval="1m")
        
        for symbol, data_list in result.items():
            print(f"\n{symbol}: {len(data_list)} data points")
            if data_list:
                latest = data_list[-1]  # Most recent data point
                print(f"  Latest: {latest.timestamp}")
                print(f"  Price: ${latest.close:.2f} (O: ${latest.open:.2f}, H: ${latest.high:.2f}, L: ${latest.low:.2f})")
                print(f"  Volume: {latest.volume:,}")
    
    except Exception as e:
        print(f"Error fetching current data: {e}")


async def demo_higher_timeframe():
    """Demonstrate fetching higher timeframe data."""
    print("\n=== Higher Timeframe Data Demo ===")
    
    data_service = DataService()
    
    symbols = ["AAPL"]
    print(f"Fetching 15-minute data for: {', '.join(symbols)}")
    
    try:
        result = await data_service.fetch_higher_timeframe_data(symbols, timeframe="15m", period="1d")
        
        for symbol, data_list in result.items():
            print(f"\n{symbol}: {len(data_list)} 15-minute candles")
            if data_list:
                for i, data in enumerate(data_list[-3:]):  # Show last 3 candles
                    print(f"  Candle {len(data_list)-2+i}: {data.timestamp.strftime('%H:%M')} - "
                          f"${data.close:.2f} (Vol: {data.volume:,})")
    
    except Exception as e:
        print(f"Error fetching higher timeframe data: {e}")


async def demo_historical_data():
    """Demonstrate fetching historical data."""
    print("\n=== Historical Data Demo ===")
    
    data_service = DataService()
    
    # Fetch last 5 days of daily data
    end_date = date.today()
    start_date = end_date - timedelta(days=5)
    
    symbols = ["AAPL"]
    print(f"Fetching historical daily data for {symbols[0]} from {start_date} to {end_date}")
    
    try:
        result = await data_service.fetch_historical_data(symbols, start_date, end_date, interval="1d")
        
        for symbol, data_list in result.items():
            print(f"\n{symbol}: {len(data_list)} daily candles")
            for data in data_list:
                print(f"  {data.timestamp.strftime('%Y-%m-%d')}: "
                      f"${data.close:.2f} (Change: {((data.close - data.open) / data.open * 100):+.2f}%)")
    
    except Exception as e:
        print(f"Error fetching historical data: {e}")


async def demo_caching():
    """Demonstrate caching functionality."""
    print("\n=== Caching Demo ===")
    
    data_service = DataService(cache_ttl_minutes=1)
    
    symbols = ["AAPL"]
    
    # First call - should fetch from API
    print("First call (should fetch from API)...")
    start_time = datetime.now()
    result1 = await data_service.fetch_current_data(symbols)
    first_call_time = (datetime.now() - start_time).total_seconds()
    
    # Second call - should use cache
    print("Second call (should use cache)...")
    start_time = datetime.now()
    result2 = await data_service.fetch_current_data(symbols)
    second_call_time = (datetime.now() - start_time).total_seconds()
    
    print(f"First call took: {first_call_time:.3f} seconds")
    print(f"Second call took: {second_call_time:.3f} seconds")
    print(f"Cache speedup: {first_call_time / second_call_time:.1f}x faster")
    
    # Show cache stats
    stats = data_service.get_cache_stats()
    print(f"Cache entries: {stats['size']}")


async def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===")
    
    data_service = DataService(max_retries=2)
    
    # Test with invalid symbols
    invalid_symbols = ["INVALID123", "NOTREAL456"]
    print(f"Testing with invalid symbols: {', '.join(invalid_symbols)}")
    
    result = await data_service.fetch_current_data(invalid_symbols)
    
    for symbol, data_list in result.items():
        print(f"{symbol}: {len(data_list)} data points (expected 0 for invalid symbols)")


async def main():
    """Run all demos."""
    print("DataService Demo")
    print("================")
    print("Note: This demo requires internet connection and may make real API calls to yfinance.")
    print("Some demos may be slow or fail if the market is closed or if there are API issues.\n")
    
    try:
        await demo_current_data()
        await demo_higher_timeframe()
        await demo_historical_data()
        await demo_caching()
        await demo_error_handling()
        
        print("\n=== Demo Complete ===")
        print("The DataService is ready for use in the stock scanner application!")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        print("This might be due to network issues or market being closed.")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())