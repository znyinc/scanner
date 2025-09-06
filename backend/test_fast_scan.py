#!/usr/bin/env python3
"""
Test script to verify fast scan mode without AlphaVantage delays.
"""
import asyncio
import time
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.scanner_service import ScannerService
from app.models.signals import AlgorithmSettings

async def test_fast_scan():
    """Test the fast scan mode without AlphaVantage delays."""
    print("Testing Fast Scan Mode (No AlphaVantage Fallback)")
    print("=" * 60)
    
    scanner = ScannerService()
    symbols = ["AAPL", "MSFT", "GOOGL"]  # Three symbols for testing
    settings = AlgorithmSettings()  # Default settings
    
    print(f"Starting fast scan for {symbols}...")
    print("Expected behavior: Skip AlphaVantage fallback for faster response")
    start_time = time.time()
    
    try:
        result = await scanner.scan_stocks(symbols, settings)
        end_time = time.time()
        
        print(f"\n✅ Fast scan completed in {end_time - start_time:.2f}s")
        print(f"Scan ID: {result.id}")
        print(f"Symbols scanned: {result.symbols_scanned}")
        print(f"Signals found: {len(result.signals_found)}")
        print(f"Execution time: {result.execution_time:.2f}s")
        
        # Analyze performance
        print(f"\n📊 Performance Analysis:")
        print(f"   • Total time: {end_time - start_time:.2f}s")
        print(f"   • Time per symbol: {(end_time - start_time) / len(symbols):.2f}s")
        
        if end_time - start_time < 15:  # Should be much faster than 57s
            print(f"   ✅ FAST MODE SUCCESS: Scan completed quickly!")
            print(f"   ✅ No long AlphaVantage delays detected")
            return True
        else:
            print(f"   ❌ STILL TOO SLOW: Expected < 15s, got {end_time - start_time:.2f}s")
            return False
        
    except Exception as e:
        end_time = time.time()
        print(f"\n❌ Fast scan failed after {end_time - start_time:.2f}s")
        print(f"Error: {e}")
        return False

def main():
    """Run fast scan test."""
    print("Stock Scanner - Fast Scan Test")
    print("This test verifies that scans complete quickly without AlphaVantage delays")
    print()
    
    try:
        success = asyncio.run(test_fast_scan())
        
        if success:
            print(f"\n{'=' * 60}")
            print("✅ FAST SCAN MODE WORKING")
            print("✅ No AlphaVantage delays")
            print("✅ Quick response for manual scans")
            print("✅ Users can retry manually if needed")
        else:
            print(f"\n{'=' * 60}")
            print("❌ FAST SCAN MODE FAILED")
            print("❌ Still experiencing delays")
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()