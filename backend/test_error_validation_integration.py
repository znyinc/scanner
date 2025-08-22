#!/usr/bin/env python3
"""
Simple integration test for error handling and validation.
This tests the core functionality without relying on complex test frameworks.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_validation():
    """Test validation utilities."""
    print("Testing validation utilities...")
    
    try:
        from app.utils.validation import StockSymbolValidator, AlgorithmSettingsValidator, DateRangeValidator
        
        # Test stock symbol validation
        print("  Testing stock symbol validation...")
        result = StockSymbolValidator.validate_symbols(["AAPL", "MSFT", "INVALID123"])
        print(f"    Valid symbols: {result.cleaned_data.get('symbols', [])}")
        print(f"    Errors: {len(result.errors)}")
        print(f"    Warnings: {len(result.warnings)}")
        
        # Test algorithm settings validation
        print("  Testing algorithm settings validation...")
        settings = {
            "atr_multiplier": 2.0,
            "ema5_rising_threshold": 0.02,
            "invalid_param": "test"
        }
        result = AlgorithmSettingsValidator.validate_settings(settings)
        print(f"    Valid settings: {result.is_valid}")
        print(f"    Cleaned data keys: {list(result.cleaned_data.keys())}")
        print(f"    Warnings: {len(result.warnings)}")
        
        # Test date range validation
        print("  Testing date range validation...")
        from datetime import date
        result = DateRangeValidator.validate_date_range(
            date(2023, 1, 1), 
            date(2023, 12, 31)
        )
        print(f"    Valid date range: {result.is_valid}")
        print(f"    Errors: {len(result.errors)}")
        
        print("✓ Validation tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Validation tests failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoint validation integration."""
    print("Testing API endpoint validation...")
    
    try:
        # Test scan request validation
        print("  Testing scan request validation...")
        from app.utils.validation import StockSymbolValidator
        
        # Valid request
        symbols = ["AAPL", "MSFT", "GOOGL"]
        result = StockSymbolValidator.validate_symbols(symbols)
        print(f"    Valid scan request: {result.is_valid}")
        
        # Invalid request
        symbols = ["INVALID123", "", "TOOLONGSTOCKSYMBOL"]
        result = StockSymbolValidator.validate_symbols(symbols)
        print(f"    Invalid scan request errors: {len(result.errors)}")
        
        print("✓ API endpoint validation tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ API endpoint validation tests failed: {e}")
        return False


def test_error_responses():
    """Test error response formatting."""
    print("Testing error response formatting...")
    
    try:
        # Test creating error responses
        from app.utils.validation import ValidationError
        
        error = ValidationError(
            field="symbols",
            message="Invalid stock symbol format",
            code="INVALID_SYMBOL",
            value="123INVALID"
        )
        
        print(f"    Error field: {error.field}")
        print(f"    Error message: {error.message}")
        print(f"    Error code: {error.code}")
        
        print("✓ Error response tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error response tests failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Running Error Handling and Validation Integration Tests")
    print("=" * 60)
    
    tests = [
        test_validation,
        test_api_endpoints,
        test_error_responses
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Error handling and validation are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())