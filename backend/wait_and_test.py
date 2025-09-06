#!/usr/bin/env python3
"""
Wait and test yfinance periodically until rate limit resets.
"""
import yfinance as yf
import time
import datetime

def test_yfinance():
    """Test if yfinance is working."""
    try:
        ticker = yf.Ticker('AAPL')
        data = ticker.history(period='1d')
        return not data.empty
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Testing yfinance availability...")
    print(f"Current time: {datetime.datetime.now()}")
    
    if test_yfinance():
        print("✅ yfinance is working!")
        return True
    else:
        print("❌ yfinance is still rate-limited")
        print("Suggestions:")
        print("1. Wait 1-24 hours for rate limit to reset")
        print("2. Use a VPN to change your IP address")
        print("3. Use alternative data sources")
        return False

if __name__ == "__main__":
    main()