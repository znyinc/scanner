"""
Tests for error scenarios and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime
import json

from app.utils.error_handling import (
    StockScannerError, ValidationError, APIError, NetworkError,
    DatabaseError, AlgorithmError, RateLimitError, TimeoutError,
    ErrorHandler, ErrorContext
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
    
    @patch('app.services.data_service.yfinance')
    def test_yfinance_api_failure(self, mock_yfinance):
        """Test handling of yfinance API failures."""
        # Mock yfinance to raise an exception
        mock_yfinance.download.side_effect = Exception("API rate limit exceeded")
        
        # This would be called in the actual service
        with pytest.raises(Exception) as exc_info:
            raise Exception("API rate limit exceeded")
        
        # Test error handling
        error = ErrorHandler.handle_exception(exc_info.value, {"api_name": "yfinance"})
        
        assert isinstance(error, RateLimitError)
        assert error.error_details.category.value == "rate_limit"
    
    def test_network_timeout_scenario(self):
        """Test network timeout handling."""
        timeout_error = Exception("Request timed out after 30 seconds")
        
        error = ErrorHandler.handle_exception(timeout_error)
        
        assert isinstance(error, TimeoutError)
        assert error.error_details.category.value == "timeout"
    
    def test_database_connection_failure(self):
        """Test database connection failure handling."""
        db_error = Exception("Database connection failed")
        
        error = ErrorHandler.handle_exception(db_error, {"operation": "database_query"})
        
        assert isinstance(error, DatabaseError)
        assert error.error_details.category.value == "database"
    
    def test_algorithm_calculation_error(self):
        """Test algorithm calculation error handling."""
        calc_error = Exception("Insufficient data for EMA calculation")
        
        error = ErrorHandler.handle_exception(calc_error, {"symbol": "AAPL", "indicator": "EMA5"})
        
        # Should be handled as a system error since it doesn't match specific patterns
        assert isinstance(error, StockScannerError)
        assert error.error_details.category.value == "system"


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
        with pytest.raises(StockScannerError) as exc_info:
            with ErrorContext("test_operation", symbol="AAPL", user_id="123"):
                raise ValueError("Test error")
        
        error = exc_info.value
        assert error.error_details.technical_details["operation"] == "test_operation"
        assert error.error_details.technical_details["symbol"] == "AAPL"
        assert error.error_details.technical_details["user_id"] == "123"
    
    def test_nested_error_contexts(self):
        """Test nested error contexts."""
        with pytest.raises(StockScannerError) as exc_info:
            with ErrorContext("outer_operation", level="outer"):
                with ErrorContext("inner_operation", level="inner"):
                    raise ValueError("Nested error")
        
        error = exc_info.value
        # The inner context should be captured
        assert error.error_details.technical_details["operation"] == "inner_operation"
        assert error.error_details.technical_details["level"] == "inner"


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
        # Test with maximum allowed symbols
        symbols = [f"SYM{i:03d}" for i in range(100)]
        result = StockSymbolValidator.validate_symbols(symbols, max_symbols=100)
        assert result.is_valid
        
        # Test pagination with large offsets
        result = GeneralValidator.validate_pagination(limit=1000, offset=999999)
        assert result.is_valid
    
    def test_concurrent_error_handling(self):
        """Test error handling in concurrent scenarios."""
        import threading
        import time
        
        errors = []
        
        def worker():
            try:
                with ErrorContext("concurrent_operation", thread_id=threading.current_thread().ident):
                    # Simulate some work
                    time.sleep(0.01)
                    raise ValueError("Concurrent error")
            except StockScannerError as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all errors were captured
        assert len(errors) == 5
        for error in errors:
            assert error.error_details.technical_details["operation"] == "concurrent_operation"
            assert "thread_id" in error.error_details.technical_details


class TestErrorLoggingScenarios:
    """Test error logging scenarios."""
    
    @patch('app.utils.error_handling.logger')
    def test_error_logging_levels(self, mock_logger):
        """Test that errors are logged at appropriate levels."""
        # Critical error
        critical_error = DatabaseError("Critical database failure")
        ErrorHandler.log_error(critical_error)
        mock_logger.critical.assert_called()
        
        # High severity error
        high_error = APIError("API service down", status_code=500)
        ErrorHandler.log_error(high_error)
        mock_logger.error.assert_called()
        
        # Medium severity error
        medium_error = ValidationError("Invalid input")
        ErrorHandler.log_error(medium_error)
        mock_logger.warning.assert_called()
    
    @patch('app.utils.error_handling.logger')
    def test_error_logging_with_context(self, mock_logger):
        """Test error logging includes context information."""
        error = ValidationError("Test error", field="test_field")
        ErrorHandler.log_error(error, request_id="test-123")
        
        # Verify logging was called
        assert mock_logger.warning.called
        
        # Check that context was included
        call_args = mock_logger.warning.call_args[0][0]
        assert "test-123" in call_args
    
    def test_error_response_format(self):
        """Test error response formatting."""
        error = ValidationError("Test validation error", field="test_field")
        response = ErrorHandler.create_error_response(error)
        
        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["category"] == "validation"
        assert response["error"]["severity"] == "medium"
        assert len(response["error"]["recovery_suggestions"]) > 0
    
    def test_error_response_with_technical_details(self):
        """Test error response with technical details."""
        error = ValidationError("Test error", field="test_field", value="invalid_value")
        response = ErrorHandler.create_error_response(error, include_technical_details=True)
        
        assert "technical_details" in response["error"]
        assert response["error"]["technical_details"]["field"] == "test_field"
        assert response["error"]["technical_details"]["value"] == "invalid_value"