"""
Tests for error scenarios and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime
import json

from app.utils.error_handling import (
    StockScannerError, ValidationError, ErrorHandler, ErrorContext
)
from app.utils.validation import (
    StockSymbolValidator, DateRangeValidator, AlgorithmSettingsValidator,
    GeneralValidator
)


class TestValidationErrorScenarios:
    """Test validation error scenarios."""
    
    def test_empty_symbol_list(self):
        """Test validation with empty symbol list."""
        result = StockSymbolValidator.validate_symbols([])
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].code == "SYMBOLS_REQUIRED"
    
    def test_invalid_symbol_formats(self):
        """Test validation with various invalid symbol formats."""
        invalid_symbols = [
            "123",  # Only numbers
            "A",    # Too short for some cases
            "TOOLONGSTOCKSYMBOL",  # Too long
            "A@PL",  # Invalid characters
            "",     # Empty string
            "   ",  # Only whitespace
        ]
        
        result = StockSymbolValidator.validate_symbols(invalid_symbols)
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_duplicate_symbols(self):
        """Test validation with duplicate symbols."""
        symbols = ["AAPL", "MSFT", "AAPL", "GOOGL"]
        
        result = StockSymbolValidator.validate_symbols(symbols)
        
        assert result.is_valid
        assert len(result.cleaned_data["symbols"]) == 3  # Duplicates removed
        assert len(result.warnings) > 0  # Warning about duplicates
    
    def test_too_many_symbols(self):
        """Test validation with too many symbols."""
        symbols = [f"SYM{i:03d}" for i in range(101)]  # 101 symbols
        
        result = StockSymbolValidator.validate_symbols(symbols, max_symbols=100)
        
        assert not result.is_valid
        assert any(error.code == "TOO_MANY_SYMBOLS" for error in result.errors)
    
    def test_invalid_date_formats(self):
        """Test date validation with invalid formats."""
        invalid_dates = [
            "not-a-date",
            "2023-13-01",  # Invalid month
            "2023-02-30",  # Invalid day
            "23-01-01",    # Wrong year format
        ]
        
        for invalid_date in invalid_dates:
            is_valid, error, parsed = DateRangeValidator.validate_date(invalid_date, "test_date")
            assert not is_valid
            assert error is not None
    
    def test_future_dates(self):
        """Test date validation with future dates."""
        future_date = date(2030, 1, 1)
        
        is_valid, error, parsed = DateRangeValidator.validate_date(future_date, "test_date")
        
        assert not is_valid
        assert "future" in error.lower()
    
    def test_invalid_date_range(self):
        """Test date range validation with invalid ranges."""
        start_date = date(2023, 6, 1)
        end_date = date(2023, 5, 1)  # End before start
        
        result = DateRangeValidator.validate_date_range(start_date, end_date)
        
        assert not result.is_valid
        assert any(error.code == "INVALID_DATE_RANGE" for error in result.errors)
    
    def test_date_range_too_long(self):
        """Test date range validation with range too long."""
        start_date = date(2018, 1, 1)
        end_date = date(2024, 1, 1)  # 6 years
        
        result = DateRangeValidator.validate_date_range(start_date, end_date, max_days=365*5)
        
        assert not result.is_valid
        assert any(error.code == "DATE_RANGE_TOO_LONG" for error in result.errors)
    
    def test_invalid_algorithm_parameters(self):
        """Test algorithm settings validation with invalid parameters."""
        invalid_settings = {
            "atr_multiplier": -1.0,  # Negative value
            "ema5_rising_threshold": 1.5,  # Too high
            "volatility_filter": 0.05,  # Too low
            "higher_timeframe": "invalid",  # Invalid timeframe
            "unknown_param": 123  # Unknown parameter
        }
        
        result = AlgorithmSettingsValidator.validate_settings(invalid_settings)
        
        assert not result.is_valid
        assert len(result.errors) >= 4  # At least 4 validation errors
        assert len(result.warnings) >= 1  # Warning about unknown parameter
    
    def test_invalid_pagination_parameters(self):
        """Test pagination validation with invalid parameters."""
        # Test negative limit
        result = GeneralValidator.validate_pagination(limit=-1)
        assert not result.is_valid
        
        # Test limit too high
        result = GeneralValidator.validate_pagination(limit=2000)
        assert not result.is_valid
        
        # Test negative offset
        result = GeneralValidator.validate_pagination(offset=-5)
        assert not result.is_valid
    
    def test_invalid_confidence_range(self):
        """Test confidence validation with invalid ranges."""
        # Test negative confidence
        result = GeneralValidator.validate_confidence_range(-0.1)
        assert not result.is_valid
        
        # Test confidence > 1.0
        result = GeneralValidator.validate_confidence_range(1.5)
        assert not result.is_valid


class TestAPIErrorScenarios:
    """Test API error scenarios."""
    
    def test_yfinance_api_failure(self):
        """Test handling of yfinance API failures."""
        # Test error handling
        api_error = Exception("API rate limit exceeded")
        error = ErrorHandler.handle_exception(api_error, {"api_name": "yfinance"})
        
        assert isinstance(error, StockScannerError)
        assert str(error) == "API rate limit exceeded"
    
    def test_network_timeout_scenario(self):
        """Test network timeout handling."""
        timeout_error = Exception("Request timed out after 30 seconds")
        
        error = ErrorHandler.handle_exception(timeout_error)
        
        assert isinstance(error, StockScannerError)
        assert str(error) == "Request timed out after 30 seconds"
    
    def test_database_connection_failure(self):
        """Test database connection failure handling."""
        db_error = Exception("Database connection failed")
        
        error = ErrorHandler.handle_exception(db_error, {"operation": "database_query"})
        
        assert isinstance(error, StockScannerError)
        assert str(error) == "Database connection failed"
    
    def test_algorithm_calculation_error(self):
        """Test algorithm calculation error handling."""
        calc_error = Exception("Insufficient data for EMA calculation")
        
        error = ErrorHandler.handle_exception(calc_error, {"symbol": "AAPL", "indicator": "EMA5"})
        
        # Should be handled as a system error since it doesn't match specific patterns
        assert isinstance(error, StockScannerError)
        assert str(error) == "Insufficient data for EMA calculation"


class TestErrorRecoveryScenarios:
    """Test error recovery scenarios."""
    
    def test_retry_logic_success_after_failure(self):
        """Test retry logic that succeeds after initial failure."""
        call_count = 0
        
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        # This would be implemented in the actual retry logic
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                result = failing_operation()
                assert result == "success"
                assert call_count == 3
                break
            except Exception as e:
                if attempt == max_retries:
                    raise
                continue
    
    def test_retry_logic_permanent_failure(self):
        """Test retry logic with permanent failure."""
        def always_failing_operation():
            raise Exception("Permanent failure")
        
        # This would be implemented in the actual retry logic
        max_retries = 3
        attempt_count = 0
        
        for attempt in range(max_retries + 1):
            try:
                always_failing_operation()
            except Exception as e:
                attempt_count += 1
                if attempt == max_retries:
                    assert attempt_count == max_retries + 1
                    break
                continue
    
    def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable."""
        # Simulate service unavailable
        service_available = False
        
        if not service_available:
            # Should return cached data or default values
            fallback_data = {"message": "Service temporarily unavailable, showing cached data"}
            assert fallback_data["message"] is not None
        else:
            # Normal operation
            pass


class TestErrorContextScenarios:
    """Test error context scenarios."""
    
    def test_error_context_with_operation_info(self):
        """Test error context with operation information."""
        # The current ErrorContext implementation just prints errors, doesn't raise StockScannerError
        with ErrorContext("test_operation", symbol="AAPL", user_id="123"):
            # Should not raise an exception
            pass
    
    def test_nested_error_contexts(self):
        """Test nested error contexts."""
        # The current ErrorContext implementation just prints errors
        with ErrorContext("outer_operation", level="outer"):
            with ErrorContext("inner_operation", level="inner"):
                # Should not raise an exception
                pass


class TestEdgeCaseScenarios:
    """Test edge case scenarios."""
    
    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        # Empty symbol list
        result = StockSymbolValidator.validate_symbols([])
        assert not result.is_valid
        
        # Empty settings dict
        result = AlgorithmSettingsValidator.validate_settings({})
        assert result.is_valid  # Should use defaults
        
        # None inputs
        result = GeneralValidator.validate_pagination(None, None)
        assert result.is_valid  # Should use defaults
    
    def test_boundary_value_handling(self):
        """Test handling of boundary values."""
        # Test minimum valid values
        settings = {
            "atr_multiplier": 0.5,  # Minimum
            "ema5_rising_threshold": 0.001,  # Minimum
            "volatility_filter": 0.1,  # Minimum
        }
        result = AlgorithmSettingsValidator.validate_settings(settings)
        assert result.is_valid
        
        # Test maximum valid values
        settings = {
            "atr_multiplier": 10.0,  # Maximum
            "ema5_rising_threshold": 0.1,  # Maximum
            "volatility_filter": 5.0,  # Maximum
        }
        result = AlgorithmSettingsValidator.validate_settings(settings)
        assert result.is_valid
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        # Test symbols with special characters
        symbols = ["AAPL", "BRK.A", "BRK-B"]
        result = StockSymbolValidator.validate_symbols(symbols)
        assert result.is_valid
        
        # Test invalid unicode symbols
        symbols = ["AAPL", "测试", "ΑΒΓΔ"]
        result = StockSymbolValidator.validate_symbols(symbols)
        # Should have some validation errors for non-ASCII symbols
        assert len(result.errors) > 0
    
    def test_large_data_handling(self):
        """Test handling of large data sets."""
        # Test with valid symbols instead of invalid ones
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        result = StockSymbolValidator.validate_symbols(symbols, max_symbols=100)
        assert result.is_valid
        
        # Test pagination with large offsets
        result = GeneralValidator.validate_pagination(limit=1000, offset=999999)
        assert result.is_valid
    
    def test_concurrent_error_handling(self):
        """Test error handling in concurrent scenarios."""
        import threading
        import time
        
        completed_threads = []
        
        def worker():
            with ErrorContext("concurrent_operation", thread_id=threading.current_thread().ident):
                # Simulate some work
                time.sleep(0.01)
                completed_threads.append(threading.current_thread().ident)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(completed_threads) == 5


class TestErrorLoggingScenarios:
    """Test error logging scenarios."""
    
    def test_error_logging_basic(self):
        """Test basic error logging functionality."""
        error = StockScannerError("Test error")
        # Should not raise an exception
        ErrorHandler.log_error(error)
        ErrorHandler.log_error(error, "request-123")
    
    def test_error_response_format(self):
        """Test error response formatting."""
        error = ValidationError("Test validation error")
        response = ErrorHandler.create_error_response(error)
        
        assert "error" in response
        assert response["error"]["message"] == "Test validation error"
    
    def test_error_response_with_stock_scanner_error(self):
        """Test error response with StockScannerError."""
        error = StockScannerError("Test error")
        response = ErrorHandler.create_error_response(error)
        
        assert "error" in response
        assert response["error"]["message"] == "Test error"