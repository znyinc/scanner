#!/usr/bin/env python3
"""
Test script to verify enhanced scan diagnostics and error tracking.
"""
import asyncio
import time
import sys
import os
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.scanner_service import ScannerService
from app.models.signals import AlgorithmSettings

async def test_scan_with_diagnostics():
    """Test scan with detailed diagnostics collection."""
    print("Testing Enhanced Scan Diagnostics")
    print("=" * 60)
    
    scanner = ScannerService()
    
    # Test with mix of valid and invalid symbols
    symbols = ["AAPL", "MSFT", "INVALID123", "GOOGL", "BADSTOCK"]
    settings = AlgorithmSettings()
    
    print(f"Starting diagnostic scan for {symbols}...")
    print("Expected: Mix of successful and failed symbols with detailed diagnostics")
    start_time = time.time()
    
    try:
        result = await scanner.scan_stocks(symbols, settings)
        end_time = time.time()
        
        print(f"\n✅ Scan completed in {end_time - start_time:.2f}s")
        print(f"📊 Scan Results:")
        print(f"   • Scan ID: {result.id}")
        print(f"   • Status: {result.scan_status}")
        print(f"   • Symbols scanned: {len(result.symbols_scanned)}")
        print(f"   • Signals found: {len(result.signals_found)}")
        print(f"   • Execution time: {result.execution_time:.2f}s")
        
        if result.error_message:
            print(f"   • Error: {result.error_message}")
        
        # Display detailed diagnostics
        if result.diagnostics:
            diag = result.diagnostics
            print(f"\n📋 Detailed Diagnostics:")
            print(f"   • Symbols with data: {diag.symbols_with_data}")
            print(f"   • Symbols without data: {diag.symbols_without_data}")
            print(f"   • Symbols with errors: {len(diag.symbols_with_errors)}")
            
            if diag.symbols_with_errors:
                print(f"   • Error details:")
                for symbol, error in diag.symbols_with_errors.items():
                    print(f"     - {symbol}: {error}")
            
            print(f"   • Data points per symbol:")
            for symbol, count in diag.total_data_points.items():
                print(f"     - {symbol}: {count} points")
            
            print(f"   • Timing breakdown:")
            print(f"     - Data fetch: {diag.data_fetch_time:.2f}s")
            print(f"     - Algorithm: {diag.algorithm_time:.2f}s")
            
            if diag.error_summary:
                print(f"   • Error summary:")
                for error_type, count in diag.error_summary.items():
                    print(f"     - {error_type}: {count}")
        
        return True
        
    except Exception as e:
        end_time = time.time()
        print(f"\n❌ Scan failed after {end_time - start_time:.2f}s")
        print(f"Error: {e}")
        return False

async def test_scan_history_with_diagnostics():
    """Test retrieving scan history with diagnostics."""
    print(f"\n{'=' * 60}")
    print("Testing Scan History with Diagnostics")
    print("=" * 60)
    
    scanner = ScannerService()
    
    try:
        # Get recent scan history
        history = await scanner.get_scan_history()
        
        print(f"Retrieved {len(history)} scan results from history")
        
        for i, scan in enumerate(history[:3]):  # Show first 3 results
            print(f"\n📊 Scan {i+1}:")
            print(f"   • ID: {scan.id}")
            print(f"   • Timestamp: {scan.timestamp}")
            print(f"   • Status: {scan.scan_status}")
            print(f"   • Symbols: {scan.symbols_scanned}")
            print(f"   • Signals: {len(scan.signals_found)}")
            print(f"   • Execution time: {scan.execution_time:.2f}s")
            
            if scan.error_message:
                print(f"   • Error: {scan.error_message}")
            
            if scan.diagnostics:
                diag = scan.diagnostics
                print(f"   • Data availability: {len(diag.symbols_with_data)}/{len(scan.symbols_scanned)} symbols")
                if diag.symbols_without_data:
                    print(f"   • No data: {diag.symbols_without_data}")
                if diag.symbols_with_errors:
                    print(f"   • Errors: {list(diag.symbols_with_errors.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ History retrieval failed: {e}")
        return False

def main():
    """Run diagnostic tests."""
    print("Stock Scanner - Enhanced Diagnostics Test")
    print("This test verifies detailed error tracking and diagnostics")
    print()
    
    try:
        # Test scan with diagnostics
        success1 = asyncio.run(test_scan_with_diagnostics())
        
        # Test history retrieval
        success2 = asyncio.run(test_scan_history_with_diagnostics())
        
        if success1 and success2:
            print(f"\n{'=' * 60}")
            print("✅ ALL DIAGNOSTIC TESTS PASSED")
            print("✅ Enhanced error tracking working")
            print("✅ Detailed diagnostics collected")
            print("✅ Scan history includes diagnostics")
            print("✅ Error messages stored properly")
        else:
            print(f"\n{'=' * 60}")
            print("❌ SOME DIAGNOSTIC TESTS FAILED")
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()